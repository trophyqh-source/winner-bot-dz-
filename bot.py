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
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

SEEN_FILE = "seen_products.json"
APIFY_ACTOR = "clockworks~tiktok-scraper"

# Recherches TikTok (e-commerce Algérie)
QUERIES = [
    "livraison 58 wilayas",
    "livraison gratuite algerie",
    "commander wilaya prix",
    "boutique alger",
]

RESULTS_PER_QUERY = 50          # vidéos récupérées par recherche (4 recherches = 200 vidéos par scan)
MAX_COST_PER_SCAN = 1.5         # plafond de sécurité en dollars par scan (Apify arrête le scan au-delà)
MAX_SEND = 5                    # produits envoyés par exécution
MIN_HOURS_BETWEEN_SCANS = 20    # protège ton crédit Apify gratuit (1 scan par jour max)

# Âge de la pub : elle doit tourner depuis plus de 7 jours, jusqu'à ~2 mois
MIN_AGE_DAYS = 7
MAX_AGE_DAYS = 60

# Filtres d'engagement
MIN_LIKES = 500                 # minimum de j'aime pour être pris en compte
MIN_COMMENT_RATIO = 0.4         # commentaires >= 40 % des j'aime (ex : 1000 j'aime -> 400 commentaires)
MIN_SHARE_RATIO = 0.05          # partages >= 5 % des j'aime (mets 0 pour désactiver)


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
# Historique (évite les doublons + limite les scans)
# ------------------------------------------------------------------
def load_state():
    """Renvoie (ensemble des IDs déjà envoyés, date du dernier scan)."""
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
                # ancien format : simple liste
                seen = {str(x) for x in data if isinstance(x, (str, int))}
        except Exception as e:
            print(f"Historique illisible, on repart de zéro : {e}")
    return seen, last_run


def save_state(seen, last_run):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"last_run": last_run, "videos": sorted(seen)},
            f,
            ensure_ascii=False,
            indent=1,
        )


# ------------------------------------------------------------------
# Apify
# ------------------------------------------------------------------
def fetch_videos():
    """Lance le scraper TikTok sur Apify, attend la fin, et renvoie la liste des vidéos."""
    base = "https://api.apify.com/v2"
    params = {"token": APIFY_TOKEN, "maxTotalChargeUsd": MAX_COST_PER_SCAN}
    payload = {
        "searchQueries": QUERIES,
        "resultsPerPage": RESULTS_PER_QUERY,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadSlideshowImages": False,
    }

    # 1. Démarrer le scan
    r = requests.post(f"{base}/acts/{APIFY_ACTOR}/runs", params=params, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Apify a répondu {r.status_code} : {r.text[:300]}")
    run = r.json().get("data") or {}
    run_id = run.get("id")
    dataset_id = run.get("defaultDatasetId")
    if not run_id or not dataset_id:
        raise RuntimeError(f"Réponse Apify inattendue : {str(run)[:300]}")

    # 2. Attendre la fin du scan (jusqu'à 25 minutes)
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

    # 3. Récupérer les vidéos
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
    age = (datetime.now(timezone.utc) - d).days
    return MIN_AGE_DAYS <= age <= MAX_AGE_DAYS


def is_winner(video):
    likes = num(video, "diggCount")
    comments = num(video, "commentCount")
    shares = num(video, "shareCount")
    if likes < MIN_LIKES:
        return False
    if comments < likes * MIN_COMMENT_RATIO:
        return False
    if shares < likes * MIN_SHARE_RATIO:
        return False
    return True


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
    print(f"{len(seen)} vidéos déjà envoyées dans l'historique.")

    # Protection du crédit Apify : un lancement manuel passe toujours
    manual = os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
    now = time.time()
    if not manual and isinstance(last_run, (int, float)):
        hours = (now - last_run) / 3600
        if hours < MIN_HOURS_BETWEEN_SCANS:
            print(f"Dernier scan il y a {hours:.1f} h : on attend, pas de scan cette fois.")
            return

    try:
        videos = fetch_videos()
    except Exception as e:
        print(f"Erreur Apify : {e}")
        if "not-enough-usage" in str(e) or "402" in str(e):
            send_telegram(
                "⚠️ WinnerBotDZ : ton crédit gratuit Apify est épuisé pour ce mois. "
                "Le bot reprendra tout seul quand le crédit sera renouvelé."
            )
        else:
            send_telegram(f"⚠️ WinnerBotDZ : erreur Apify\n<code>{html.escape(str(e)[:300])}</code>")
        # On mémorise l'essai pour ne pas renvoyer ce message toutes les 6 heures
        save_state(seen, now)
        return

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

    if sent == 0:
        send_telegram(
            f"ℹ️ WinnerBotDZ : scan terminé, {len(videos)} vidéos analysées, "
            "aucune ne passe tes filtres aujourd'hui."
        )

    save_state(seen, now)
    print(f"Terminé : {sent} produit(s) envoyé(s).")


if __name__ == "__main__":
    run()
