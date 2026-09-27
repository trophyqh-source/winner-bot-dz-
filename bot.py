import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
META_API_TOKEN = os.environ.get("META_API_TOKEN")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def fetch_ads():
    send_telegram("🤖 *Bot Winner DZ : Recherche via API Meta...*")

    if not META_API_TOKEN:
        send_telegram("❌ *Erreur : META_API_TOKEN manquant dans GitHub Secrets.*")
        return

    url = "https://graph.facebook.com/v19.0/ads_archive"
    
    params = {
        'access_token': META_API_TOKEN,
        'ad_type': 'ALL',
        'ad_reached_countries': "['DZ']",
        'search_terms': 'Prix choc',
        'limit': 5,
        'fields': 'id,ad_creative_bodies,ad_snapshot_url'
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data:
        send_telegram(f"❌ *Erreur Meta API :* {data['error'].get('message', 'Inconnue')}")
        return

    data_list = data.get('data', [])
    if not data_list:
        send_telegram("⚠️ *Aucune annonce trouvée.*")
        return

    send_telegram(f"🔥 *{len(data_list)} publicités trouvées !*")

    for idx, ad in enumerate(data_list, 1):
        bodies = ad.get('ad_creative_bodies', ['Pas de description'])
        text_preview = bodies[0][:150] if bodies else "Annonce sans texte"
        snapshot = ad.get('ad_snapshot_url', '#')

        msg = f"🔥 *PRODUIT WINNER DZ #{idx}*\n\n"
        msg += f"📝 *Aperçu :* {text_preview}...\n\n"
        msg += f"🔗 [Voir l'annonce]({snapshot})"

        send_telegram(msg)

if __name__ == "__main__":
    fetch_ads()
