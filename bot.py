import json
import os
import time
import requests

# --- CONFIGURATION API & BOT ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_eSD9fRMu37Y6Vrf2Dyn4bFIhIVRKYE1fD8h1")

NB_PAR_ENVOI = 5

def send_telegram(text):
    """Envoie un message textuel à Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    requests.post(url, json=payload, timeout=30)

def fetch_apify_dz_ads():
    """Scrape les pubs TikTok Ads ciblant spécifiquement l'Algérie (DZ)"""
    print("Recherche des Ads TikTok Algérie via Apify...")
    
    # Scraper ciblé TikTok Ads Library
    actor_id = "clockworks~tiktok-ads-scraper"
    url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    # Filtres ciblés : Pays DZ (Algérie), pubs actives (>= 7 jours)
    payload = {
        "countryCode": "DZ",          # Algérie
        "period": "30",               # Ce mois-ci (30 derniers jours)
        "minDaysActive": 7,           # Pubs qui tournent depuis au moins 7 jours
        "limit": 10
    }

    try:
        res = requests.post(url, json=payload, timeout=50)
        if res.status_code not in [200, 201]:
            print(f"Erreur Apify status code : {res.status_code}")
            return []

        items = res.json()
        if not isinstance(items, list) or len(items) == 0:
            print("Aucune pub DZ trouvée avec ces critères.")
            return []

        products = []
        for idx, item in enumerate(items[:NB_PAR_ENVOI], 1):
            title = item.get("adTitle") or item.get("brandName") or item.get("text") or f"Produit Winner DZ #{idx}"
            days_active = item.get("daysActive", "7+")
            impressions = item.get("impressions", "Élevé")
            ad_url = item.get("adUrl") or item.get("videoUrl") or ""

            products.append({
                "name": title.strip().replace("\n", " ")[:60],
                "days": days_active,
                "views": impressions,
                "url": ad_url
            })
        return products

    except Exception as e:
        print(f"Exception Apify : {e}")
        return []

def run_bot():
    send_telegram("🇩🇿 <b>WinnerBotDZ : Recherche des Ads en Algérie (> 7 jours)...</b>")
    
    prods = fetch_apify_dz_ads()
    
    if not prods:
        send_telegram("⚠️ <i>Aucune nouvelle pub TikTok Ads trouvée pour l'Algérie ce mois-ci pour le moment.</i>")
        return

    send_telegram("🔥 <b>Top Ads TikTok Algérie Détectées</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(prods, 1):
        # Format épuré et concis
        msg = f"🏆 <b>WINNER DZ #{idx}</b>\n\n"
        msg += f"📦 <b>Produit / Pub :</b> {item['name']}\n"
        msg += f"⏳ <b>Durée active :</b> > {item['days']} jours en 🇩🇿\n"
        msg += f"📊 <b>Impressions :</b> {item['views']}\n"
        
        if item['url']:
            msg += f"\n🔗 <a href=\"{item['url']}\">Voir la vidéo de la pub</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
