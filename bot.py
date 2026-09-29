import json
import os
import time
import urllib.parse
import requests

# --- CONFIGURATION API & BOT ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_eSD9fRMu37Y6Vrf2Dyn4bFIhIVRKYE1fD8h1")

SEEN_FILE = "seen_products.json"
NB_PAR_ENVOI = 5
STATUS = "🔥 Produit Tendance TikTok Ads"

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

def fetch_apify_tiktok_ads():
    """Interroge Apify pour scraper des vidéos / pubs TikTok tendance"""
    print("Démarrage de la recherche Apify...")
    
    # Utilisation d'un Actor Apify standard et rapide pour TikTok
    url = f"https://api.apify.com/v2/acts/clockworks~free-tiktok-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    payload = {
        "searchQueries": ["viral product", "dropshipping", "must have"],
        "resultsPerPage": 5,
        "searchType": "video"
    }

    try:
        # Exécution synchrone (réponse directe)
        res = requests.post(url, json=payload, timeout=45)
        if res.status_code not in [200, 201]:
            print(f"Erreur Apify status code : {res.status_code}")
            return []

        items = res.json()
        if not isinstance(items, list) or len(items) == 0:
            print("Apify n'a renvoyé aucun item.")
            return []

        products = []
        for idx, item in enumerate(items[:NB_PAR_ENVOI], 1):
            text = item.get("text") or item.get("desc") or f"Produit TikTok #{idx}"
            title = text.split("\n")[0][:50] # Prend la première ligne du texte
            play_count = item.get("playCount", "10K+")
            digg_count = item.get("diggCount", "1K+")
            share_count = item.get("shareCount", "500+")

            products.append({
                "id": f"apify_{item.get('id', idx)}",
                "name": title if len(title) > 5 else f"Gadget Tendance TikTok #{idx}",
                "status": STATUS,
                "likes": f"{digg_count} J'aime / {play_count} Vues",
                "comments": "Actif sur TikTok",
                "shares": f"{share_count}",
            })
        return products

    except Exception as e:
        print(f"Exception Apify : {e}")
        return []

def run_bot():
    send_telegram("🤖 <b>WinnerBotDZ : Scraping Apify en cours...</b>")
    
    prods = fetch_apify_tiktok_ads()
    
    if not prods:
        send_telegram("⚠️ <i>L'API Apify n'a pas renvoyé de données cette fois-ci. Vérifie tes crédits Apify ou le token.</i>")
        return

    send_telegram("🔥 <b>Top 5 Nouveaux Produits Détectés en Direct</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(prods, 1):
        query_encoded = urllib.parse.quote(item["name"])
        ali_link = f"https://www.aliexpress.com/wholesale?SearchText={query_encoded}"
        tiktok_link = f"https://www.tiktok.com/search?q={query_encoded}"
        img_link = f"https://www.google.com/search?tbm=isch&q={query_encoded}"

        msg = f"🏆 <b>PRODUIT WINNER DZ #{idx}</b>\n\n"
        msg += f"📦 <b>Nom / Description :</b> {item['name']}\n"
        msg += f"📈 <b>Statut :</b> {item['status']}\n\n"
        msg += "📊 <b>Engagement TikTok :</b>\n"
        msg += f"• 👁️ {item['likes']}\n"
        msg += f"• 🔁 {item['shares']} Partages\n\n"
        msg += "🔍 <b>Recherche rapide en 1 clic :</b>\n"
        msg += f'• 🛍️ <a href="{ali_link}">Voir sur AliExpress</a>\n'
        msg += f'• 🎵 <a href="{tiktok_link}">Voir sur TikTok</a>\n'
        msg += f'• 🖼️ <a href="{img_link}">Voir sur Google Images</a>\n\n'
        msg += "🚀 <i>Prêt pour le test e-commerce !</i>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
