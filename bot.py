import html
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests

# ==================================================================
# Configuration (les secrets viennent de GitHub Actions)
# ==================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

SEEN_FILE = "seen_products.json"

# Sources actives (mets False pour en désactiver une)
USE_FACEBOOK_VIDEOS = True      # vidéos Facebook trouvées par mots-clés
USE_INSTAGRAM = True            # Reels Instagram trouvés par hashtags
USE_AD_LIBRARY = True           # pubs de la Meta Ad Library (Facebook + Instagram)

# Scrapers Apify utilisés
FB_VIDEO_ACTOR = "natanielsantos~facebook-video-search-scraper"
INSTAGRAM_ACTOR = "apify~instagram-hashtag-scraper"
AD_LIBRARY_ACTOR = "apify~facebook-ads-scraper"

# --- Mots-clés ---
FB_VIDEO_QUERIES = [
    "livraison 58 wilayas",
    "الدفع عند الاستلام",
    "توصيل 58 ولاية",
]
INSTAGRAM_HASHTAGS = [          # sans le #
    "livraison_58_wilaya",
    "livraison_disponible_58_wilaya",
    "boutique_en_ligne_algerie",
    "algerie_shopping",
]
AD_LIBRARY_COUNTRY = "DZ"       # DZ = Algérie
AD_LIBRARY_KEYWORDS = [
    "livraison 58 wilayas",
    "livraison gratuite algerie",
    "الدفع عند الاستلام",
    "توصيل 58 ولاية",
]

# --- Volumes (plus c'est grand, plus ça coûte) ---
FB_VIDEOS_PER_QUERY = 30        # vidéos Facebook récupérées par mot-clé (maximum 100)
INSTAGRAM_PER_HASHTAG = 30      # reels récupérés par hashtag
ADS_PER_KEYWORD = 50            # pubs récupérées par mot-clé
MAX_COST_PER_SOURCE = 1.5       # plafond de sécurité en dollars par source et par scan

MAX_SEND_PER_SOURCE = 3         # produits envoyés par source et par exécution
MIN_HOURS_BETWEEN_SCANS = 20    # 1 scan par jour maximum, même si le workflow tourne toutes les 6 h

# --- Filtres vidéos Facebook / Reels Instagram ---
MIN_AGE_DAYS = 7                # la vidéo/pub existe depuis au moins 7 jours
MAX_AGE_DAYS = 60               # ... et depuis 2 mois maximum
MIN_LIKES = 500                 # minimum de j'aime / réactions
MIN_COMMENT_RATIO = 0.4         # commentaires >= 40 % des j'aime
MIN_SHARE_RATIO = 0.05          # partages >= 5 % des j'aime (appliqué seulement si les partages sont connus)

# --- Filtres Meta Ad Library ---
MIN_AD_VERSIONS = 2             # nombre minimum de versions de la même pub
ONLY_ACTIVE_ADS = True          # garder seulement les pubs encore actives

# Sites qui ne sont PAS une landing page (réseaux sociaux)
SOCIAL_DOMAINS = (
    "facebook.com", "fb.com", "fb.watch", "fb.me", "instagram.com", "tiktok.com",
    "youtube.com", "youtu.be", "wa.me", "whatsapp.com", "t.me", "twitter.com", "x.com",
)


# ==================================================================
# Telegram
# ==================================================================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code != 200:
            print(f"Telegram a répondu {r.status_code} : {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"Erreur Telegram : {e}")
        return False


# ==================================================================
# Historique (évite les doublons + limite les scans)
# ==================================================================
def load_state():
    seen = set()
    last_run = None
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                seen = {str(x) for x in data.get("videos", []) if isinstance(x, (str, int))}
                last_run = data.get("last_run")
            elif isinstance(data, list):
                seen = {str(x) for x in data if isinstance(x, (str, int))}
        except Exception as e:
            print(f"Historique illisible, on repart de zéro : {e}")
    return seen, last_run


def save_state(seen, last_run):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_run": last_run, "videos": sorted(seen)}, f, ensure_ascii=False, indent=1)


# ==================================================================
# Apify
# ==================================================================
def run_actor(actor, payload, max_cost):
    """Lance un scraper Apify, attend la fin, et renvoie la liste des résultats."""
    base = "https://api.apify.com/v2"
    params = {"token": APIFY_TOKEN, "maxTotalChargeUsd": max_cost}

    r = requests.post(f"{base}/acts/{actor}/runs", params=params, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Apify a répondu {r.status_code} : {r.text[:300]}")
    run = r.json().get("data") or {}
    run_id = run.get("id")
    dataset_id = run.get("defaultDatasetId")
    if not run_id or not dataset_id:
        raise RuntimeError(f"Réponse Apify inattendue : {str(run)[:300]}")

    deadline = time.time() + 25 * 60
    status = run.get("status")
    while status in ("READY", "RUNNING"):
        if time.time() > deadline:
            raise RuntimeError("Le scan Apify prend trop de temps (plus de 25 minutes).")
        time.sleep(10)
        rr = requests.get(f"{base}/actor-runs/{run_id}", params={"token": APIFY_TOKEN}, timeout=30)
        if rr.status_code != 200:
            raise RuntimeError(f"Apify a répondu {rr.status_code} : {rr.text[:300]}")
        run = rr.json().get("data") or {}
        status = run.get("status")

    if status != "SUCCEEDED":
        raise RuntimeError(f"Le scan Apify s'est terminé avec le statut : {status}")

    ri = requests.get(
        f"{base}/datasets/{dataset_id}/items",
        params={"token": APIFY_TOKEN, "format": "json", "clean": "true"},
        timeout=120,
    )
    if ri.status_code != 200:
        raise RuntimeError(f"Apify a répondu {ri.status_code} : {ri.text[:300]}")
    data = ri.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Réponse Apify inattendue : {str(data)[:300]}")
    return data


# ==================================================================
# Outils communs
# ==================================================================
def parse_count(value):
    """Transforme 1234, '1 234', '1,2K', '3.4 M' ... en nombre entier."""
    if value is None:
        return 0
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(int(value), 0)
    s = str(value).lower().replace("\u202f", " ").replace("\xa0", " ").strip()
    m = re.search(r"(\d[\d\s.,]*)\s*(mille|mio|[kmb])?(?![a-z])", s)
    if not m:
        return 0
    number = m.group(1).strip().replace(" ", "")
    suffix = m.group(2)
    if suffix:
        try:
            n = float(number.replace(",", "."))
        except ValueError:
            return 0
        mult = {"k": 1e3, "mille": 1e3, "m": 1e6, "mio": 1e6, "b": 1e9}[suffix]
        return int(n * mult)
    digits = re.sub(r"[.,]", "", number)
    return int(digits) if digits.isdigit() else 0


def parse_age_text(value):
    """'3 weeks ago', 'il y a 2 mois', '5d', '1y' ... -> nombre de jours (ou None si inconnu)."""
    if not value:
        return None
    s = str(value).lower()
    m = re.search(
        r"(\d+)\s*(minutes?|min|hours?|hrs?|h|heures?|days?|d|jours?|j|weeks?|w|semaines?|sem|months?|mo|mois|years?|y|ans?)\b",
        s,
    )
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    if unit.startswith(("min", "h")):
        return 0
    if unit.startswith(("d", "j")):
        return n
    if unit.startswith(("w", "sem")):
        return 7 * n
    if unit.startswith(("mo", "mois")):
        return 30 * n
    if unit.startswith(("y", "an")):
        return 365 * n
    return None


def age_from_timestamp(ts):
    """Timestamp (secondes) ou texte ISO -> nombre de jours depuis la publication."""
    d = None
    if isinstance(ts, (int, float)) and ts > 0:
        if ts > 1e11:   # millisecondes
            ts = ts / 1000
        d = datetime.fromtimestamp(ts, tz=timezone.utc)
    elif isinstance(ts, str) and ts:
        try:
            d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d is None:
        return None
    return (datetime.now(timezone.utc) - d).days


def find_landing_links(*texts):
    """Cherche dans les textes des liens qui ne sont pas des réseaux sociaux (= landing page probable)."""
    found = []
    for text in texts:
        if not isinstance(text, str):
            continue
        for url in re.findall(r"https?://[^\s<>\"']+", text):
            url = url.rstrip(".,;:!?)]}»")
            host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()
            if any(host == d or host.endswith("." + d) for d in SOCIAL_DOMAINS):
                continue
            if url not in found:
                found.append(url)
    return found


def short(text, n):
    return html.escape((text or "").strip().replace("\n", " ")[:n])


# ==================================================================
# Filtres et messages : vidéos Facebook / Reels Instagram
# ==================================================================
def is_winner_post(p):
    if p["age_days"] is not None and not (MIN_AGE_DAYS <= p["age_days"] <= MAX_AGE_DAYS):
        return False
    likes = p["likes"]
    if likes < MIN_LIKES:
        return False
    if p["comments"] < likes * MIN_COMMENT_RATIO:
        return False
    if p["shares"] is not None and p["shares"] < likes * MIN_SHARE_RATIO:
        return False
    return True


def post_score(p):
    bonus = 500 if p["links"] else 0
    return p["likes"] + 5 * p["comments"] + 5 * (p["shares"] or 0) + bonus


def build_post_message(p):
    lines = [
        f"🔥 <b>Vidéo gagnante potentielle ({p['platform']})</b>",
        "",
        f"👤 {short(p['author'], 60) or '?'}",
    ]
    if p["age_days"] is not None:
        lines.append(f"⏱ Publiée il y a {p['age_days']} jours")
    stats = f"👍 {p['likes']:,}   💬 {p['comments']:,}"
    if p["shares"] is not None:
        stats += f"   🔁 {p['shares']:,}"
    lines.append(stats)
    if p["views"]:
        lines.append(f"▶️ {p['views']:,} vues")
    lines += ["", f"📝 {short(p['text'], 220) or '(sans texte)'}", ""]
    if p["links"]:
        lines.append(f"🛒 Landing page : {html.escape(p['links'][0])}")
    lines.append(f"🔗 Voir la vidéo : {html.escape(p['url'])}")
    return "\n".join(lines)


def posts_to_items(posts, seen):
    best = {}
    for p in posts:
        key = "post:" + p["key"]
        if key in seen or not is_winner_post(p):
            continue
        if key not in best or post_score(p) > post_score(best[key]):
            best[key] = p
    return [{"key": k, "score": post_score(p), "message": build_post_message(p)} for k, p in best.items()]


# ==================================================================
# Source 1 : vidéos Facebook
# ==================================================================
def collect_facebook_videos(seen):
    rows = run_actor(
        FB_VIDEO_ACTOR,
        {"searchTerms": FB_VIDEO_QUERIES, "maxItems": FB_VIDEOS_PER_QUERY},
        MAX_COST_PER_SOURCE,
    )
    posts = []
    for r in rows:
        url = r.get("videoUrl")
        if not url:
            continue
        description = r.get("description") or ""
        author = r.get("author") or {}
        shares = r.get("shareCount")
        posts.append({
            "platform": "Facebook",
            "key": "fb:" + str(r.get("postId") or url),
            "url": url,
            "author": (author.get("name") if isinstance(author, dict) else None) or "?",
            "text": description,
            "likes": parse_count(r.get("totalReactionCount")),
            "comments": parse_count(r.get("commentCount")),
            "shares": parse_count(shares) if shares is not None else None,
            "views": parse_count(r.get("viewCount")),
            "age_days": age_from_timestamp(r.get("creationTime")),
            "links": find_landing_links(description),
        })
    return len(rows), posts_to_items(posts, seen)


# ==================================================================
# Source 2 : Reels Instagram
# ==================================================================
def collect_instagram(seen):
    rows = run_actor(
        INSTAGRAM_ACTOR,
        {"hashtags": INSTAGRAM_HASHTAGS, "resultsType": "reels", "resultsLimit": INSTAGRAM_PER_HASHTAG},
        MAX_COST_PER_SOURCE,
    )
    posts = []
    for r in rows:
        url = r.get("url")
        if not url:
            continue
        caption = r.get("caption") or ""
        views = r.get("videoPlayCount") or r.get("videoViewCount") or 0
        posts.append({
            "platform": "Instagram",
            "key": "ig:" + str(r.get("shortCode") or r.get("id") or url),
            "url": url,
            "author": r.get("ownerUsername") or "?",
            "text": caption,
            "likes": parse_count(r.get("likesCount")),
            "comments": parse_count(r.get("commentsCount")),
            "shares": None,
            "views": parse_count(views),
            "age_days": age_from_timestamp(r.get("timestamp")),
            "links": find_landing_links(caption),
        })
    return len(rows), posts_to_items(posts, seen)


# ==================================================================
# Source 3 : Meta Ad Library (Facebook + Instagram)
# ==================================================================
def library_url(keyword):
    return (
        "https://www.facebook.com/ads/library/"
        "?active_status=active&ad_type=all"
        f"&country={AD_LIBRARY_COUNTRY}&is_targeted_country=false&media_type=all"
        f"&q={quote(keyword)}&search_type=keyword_unordered"
    )


def ad_id(ad):
    return str(ad.get("adArchiveID") or ad.get("adArchiveId") or "")


def ad_group_key(ad):
    return str(ad.get("collationId") or ad_id(ad))


def ad_days(ad):
    ts = ad.get("startDate")
    if ts is None:
        ts = ad.get("startDateFormatted")
    return age_from_timestamp(ts)


def ad_versions(ad):
    try:
        return int(ad.get("collationCount") or 1)
    except (TypeError, ValueError):
        return 1


def is_winner_ad(ad):
    if ONLY_ACTIVE_ADS and ad.get("isActive") is False:
        return False
    days = ad_days(ad)
    if days is None or not (MIN_AGE_DAYS <= days <= MAX_AGE_DAYS):
        return False
    return ad_versions(ad) >= MIN_AD_VERSIONS


def ad_score(ad):
    return ad_versions(ad) * 100 + min(ad_days(ad) or 0, MAX_AGE_DAYS)


def ad_text(ad):
    snap = ad.get("snapshot") or {}
    candidates = [(snap.get("body") or {}).get("text")]
    cards = snap.get("cards") or []
    if cards:
        candidates += [cards[0].get("body"), cards[0].get("title")]
    candidates.append(snap.get("title"))
    for c in candidates:
        if isinstance(c, str) and c.strip() and "{{" not in c:
            return c.strip()
    return ""


def ad_landing(ad):
    snap = ad.get("snapshot") or {}
    link = snap.get("linkUrl")
    if not link:
        cards = snap.get("cards") or []
        if cards:
            link = cards[0].get("linkUrl")
    return link


def ad_platforms(ad):
    names = {"FACEBOOK": "Facebook", "INSTAGRAM": "Instagram", "MESSENGER": "Messenger",
             "AUDIENCE_NETWORK": "Audience Network", "THREADS": "Threads", "WHATSAPP": "WhatsApp"}
    raw = ad.get("publisherPlatform") or []
    return ", ".join(names.get(p, str(p).title()) for p in raw) or "?"


def build_ad_message(ad):
    snap = ad.get("snapshot") or {}
    page = html.escape(str(ad.get("pageName") or snap.get("pageName") or "?"))
    cta = html.escape(str(snap.get("ctaText") or ""))
    lines = [
        "🔥 <b>Pub gagnante potentielle (Ad Library)</b>",
        "",
        f"🏪 {page}",
        f"📱 {ad_platforms(ad)}",
        f"⏱ Active depuis {ad_days(ad)} jours",
        f"🧬 {ad_versions(ad)} version(s) de la pub",
    ]
    if cta:
        lines.append(f"👆 Bouton : {cta}")
    lines += ["", f"📝 {short(ad_text(ad), 220) or '(sans texte)'}", ""]
    link = ad_landing(ad)
    if link:
        lines.append(f"🛒 Landing page : {html.escape(link)}")
    lines.append(f"🔗 Voir la pub : https://www.facebook.com/ads/library/?id={ad_id(ad)}")
    return "\n".join(lines)


def collect_ad_library(seen):
    ads = run_actor(
        AD_LIBRARY_ACTOR,
        {
            "startUrls": [{"url": library_url(k)} for k in AD_LIBRARY_KEYWORDS],
            "resultsLimit": ADS_PER_KEYWORD,
            "onlyTotal": False,
            "includeAboutPage": False,
            "isDetailsPerAd": False,
            "enrichWithEcommerceData": False,
        },
        MAX_COST_PER_SOURCE,
    )
    best = {}
    for ad in ads:
        if not ad_id(ad):
            continue
        key = "fb:" + ad_group_key(ad)
        if key in seen or not is_winner_ad(ad):
            continue
        if key not in best or ad_score(ad) > ad_score(best[key]):
            best[key] = ad
    items = [{"key": k, "score": ad_score(a), "message": build_ad_message(a)} for k, a in best.items()]
    return len(ads), items


# ==================================================================
# Programme principal
# ==================================================================
def is_credit_error(err):
    s = str(err)
    return "not-enough-usage" in s or "402" in s


def run():
    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", TELEGRAM_TOKEN),
            ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID),
            ("APIFY_TOKEN", APIFY_TOKEN),
        )
        if not value
    ]
    if missing:
        print("Secrets manquants ou vides : " + ", ".join(missing))
        sys.exit(1)

    seen, last_run = load_state()
    print(f"{len(seen)} éléments déjà envoyés dans l'historique.")

    # Protection du crédit Apify : un lancement manuel passe toujours
    manual = os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
    now = time.time()
    if not manual and isinstance(last_run, (int, float)):
        hours = (now - last_run) / 3600
        if hours < MIN_HOURS_BETWEEN_SCANS:
            print(f"Dernier scan il y a {hours:.1f} h : on attend, pas de scan cette fois.")
            return

    sources = []
    if USE_FACEBOOK_VIDEOS:
        sources.append(("Vidéos Facebook", collect_facebook_videos))
    if USE_INSTAGRAM:
        sources.append(("Reels Instagram", collect_instagram))
    if USE_AD_LIBRARY:
        sources.append(("Ad Library", collect_ad_library))

    total_sent = 0
    report = []   # une ligne de résumé par source

    for name, collect in sources:
        print(f"--- Source : {name} ---")
        try:
            analysed, items = collect(seen)
        except Exception as e:
            print(f"Erreur sur {name} : {e}")
            if is_credit_error(e):
                send_telegram(
                    "⚠️ WinnerBotDZ : ton crédit Apify est épuisé. "
                    "Le bot reprendra quand le crédit sera renouvelé ou rechargé."
                )
                break   # inutile d'essayer les autres sources
            send_telegram(f"⚠️ WinnerBotDZ : erreur sur « {name} »\n<code>{html.escape(str(e)[:300])}</code>")
            report.append(f"{name} : erreur")
            continue

        items.sort(key=lambda it: it["score"], reverse=True)
        sent = 0
        for it in items[:MAX_SEND_PER_SOURCE]:
            if send_telegram(it["message"]):
                seen.add(it["key"])
                sent += 1
                time.sleep(2)
        total_sent += sent
        report.append(f"{name} : {analysed} analysés, {sent} envoyé(s)")
        print(f"{name} : {analysed} analysés, {len(items)} gagnants potentiels, {sent} envoyé(s).")

    if total_sent == 0 and report:
        send_telegram(
            "ℹ️ WinnerBotDZ : scan terminé, aucun produit ne passe tes filtres aujourd'hui.\n"
            + "\n".join("• " + line for line in report)
        )

    save_state(seen, now)
    print(f"Terminé : {total_sent} élément(s) envoyé(s).")


if __name__ == "__main__":
    run()
