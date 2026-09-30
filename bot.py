import html
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

# ------------------------------------------------------------------
# Configuration (les secrets viennent de GitHub Actions)
# ------------------------------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

SEEN_FILE = "seen_videos.json"
APIFY_ACTOR = "clockworks~tiktok-scraper"

# Recherches TikTok (e-commerce Algérie)
QUERIES = [
    "livraison 58 wilayas",
    "livraison gratuite algerie",
    "commander wilaya prix",
    "boutique alger",
]

RESULTS_PER_QUERY = int(os.getenv("RESULTS_PER_QUERY", "15"))  # limite le coût Apify
MAX_SEND = int(os.getenv("MAX_SEND", "5"))                     # produits envoyés par exécution
MAX_AGE_DAYS = int(os.getenv("MAX_AGE_DAYS", "30"))            # ignore les vidéos trop vieilles

# Une vidéo est retenue si AU MOINS UN seuil est atteint
MIN_LIKES = 5000
MIN_COMMENTS = 500
MIN_SHARES = 500
MIN_SAVES = 300


# ------------------------------------------------------------------
# Telegram
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# Historique (évite les doublons)
# ------------------------------------------------------------------
def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"Historique illisible, on repart de zéro : {e}")
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=0)


# ------------------------------------------------------------------
# Apify
# ------------------------------------------------------------------
def fetch_videos():
    """Lance le scraper TikTok sur Apify et renvoie la liste des vidéos."""
    url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items"
    payload = {
        "searchQueries": QUERIES,
        "resultsPerPage": RESULTS_PER_QUERY,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadSlideshowImages": False,
    }
    r = requests.post(url, params={"token": APIFY_TOKEN}, json=payload, timeout=330)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Apify a répondu {r.status_code} : {r.text[:300]}")
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Réponse Apify inattendue : {str(data)[:300]}")
    return data


# ------------------------------------------------------------------
# Analyse des vidéos
# ------------------------------------------------------------------
def num(video, key):
    try:
        return int(video.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def video_date(video):
    ts = video.get("createTime")
    if isinstance(ts, (int, float)) and ts > 0:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    iso = video.get("createTimeISO")
    if isinstance(iso, str):
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def is_recent(video):
    d = video_date(video)
    if d is None:
        return True  # date inconnue : on ne l'écarte pas
    return (datetime.now(timezone.utc) - d).days <= MAX_AGE_DAYS


def is_winner(video):
    return (
        num(video, "diggCount") >= MIN_LIKES
        or num(video, "commentCount") >= MIN_COMMENTS
        or num(video, "shareCount") >= MIN_SHARES
        or num(video, "collectCount") >= MIN_SAVES
    )


def score(video):
    return (
        num(video, "diggCount")
        + 5 * num(video, "commentCount")
        + 5 * num(video, "shareCount")
        + 5 * num(video, "collectCount")
    )


def video_url(video):
    url = video.get("webVideoUrl")
    if url:
        return url.split("?")[0]
    author = (video.get("authorMeta") or {}).get("name")
    vid = video.get("id")
    if author and vid:
        return f"https://www.tiktok.com/@{author}/video/{vid}"
    return None


def build_message(video, url):
    text = html.escape((video.get("text") or "").strip()[:200]) or "(sans description)"
    author = html.escape((video.get("authorMeta") or {}).get("name") or "?")
    return (
        "🔥 <b>Produit potentiel (TikTok DZ)</b>\n\n"
        f"📝 {text}\n"
        f"👤 @{author}\n\n"
        f"👍 {num(video, 'diggCount'):,}   💬 {num(video, 'commentCount'):,}\n"
        f"🔁 {num(video, 'shareCount'):,}   🔖 {num(video, 'collectCount'):,}\n"
        f"▶️ {num(video, 'playCount'):,} vues\n\n"
        f"🔗 {url}"
    )


# ------------------------------------------------------------------
# Programme principal
# ------------------------------------------------------------------
def run():
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID and APIFY_TOKEN):
        print("Il manque TELEGRAM_TOKEN, TELEGRAM_CHAT_ID ou APIFY_TOKEN dans les secrets.")
        sys.exit(1)

    seen = load_seen()
    print(f"{len(seen)} vidéos déjà envoyées dans l'historique.")

    try:
        videos = fetch_videos()
    except Exception as e:
        print(f"Erreur Apify : {e}")
        send_telegram(f"⚠️ WinnerBotDZ : erreur Apify\n<code>{html.escape(str(e)[:300])}</code>")
        save_seen(seen)
        sys.exit(1)

    print(f"{len(videos)} vidéos récupérées.")

    # Dédoublonnage dans le lot + filtres
    candidates = {}
    for v in videos:
        vid = str(v.get("id") or "")
        if not vid or vid in seen or vid in candidates:
            continue
        if not is_recent(v) or not is_winner(v):
            continue
        if not video_url(v):
            continue
        candidates[vid] = v

    ranked = sorted(candidates.items(), key=lambda kv: score(kv[1]), reverse=True)
    print(f"{len(ranked)} nouveaux gagnants potentiels, envoi de {min(len(ranked), MAX_SEND)}.")

    sent = 0
    for vid, v in ranked[:MAX_SEND]:
        if send_telegram(build_message(v, video_url(v))):
            seen.add(vid)
            sent += 1
            time.sleep(2)

    save_seen(seen)
    print(f"Terminé : {sent} produit(s) envoyé(s).")


if __name__ == "__main__":
    run()
