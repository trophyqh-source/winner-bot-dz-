import json
import os
import time
import urllib.parse
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

def fetch_apify_dz_products():
    """Scrape TikTok pour trouver les vidéos e-commerce ciblant l'Algérie"""
    print("Recherche des produits DZ sur TikTok via Apify...")
    
    url = f"https://api.apify.com/v2/acts/clockworks~free-tiktok-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    # Mots-clés utilisés par les vendeurs e-commerce en Algérie
    payload = {
        "searchQueries": [
            "livraison 58 wilayas",
            "livraison gratuite algerie",
            "produit algerie ecommerce",
            "disponible en algerie"
        ],
        "resultsPerPage": 10,
        "searchType": "video"
    }

    try:
        res = requests.post(url, json=payload, timeout=50)
        if res.status_code not in [200, 201]:
            print(f"Erreur Apify status code : {res.status_code}")
            return []

        items = res.json()
        if not isinstance(items, list) or len(items) == 0:
            print("Aucun produit DZ trouvé.")
            return []

        products = []
        for item in items:
            text = item.get("text") or item.get("desc") or ""
            
            # Filtrer pour ne garder que le contenu pertinent
            title = text.split("\n")[0][:60]
            if len(title) < 5:
                continue

            play_count = item.get("playCount", 0)
            digg_count = item.get("diggCount", 0)
            video_url = item.get("webVideoUrl") or f"https://www.tiktok.com/@{item.get('authorMeta', {}).get('name', '')}/video/{item.get('id', '')}"

            products.append({
                "name": title.strip(),
                "views": f"{play_count:,}".replace(",", " "),
                "likes": f"{digg_count:,}".replace(",", " "),
                "url": video_url
            })

            if len(products) >= NB_PAR_ENVOI:
                break

        return products

    except Exception as e:
        print(f"Exception Apify : {e}")
        return []

def run_bot():
    send_telegram("🇩🇿 <b>WinnerBotDZ : Recherche des produits e-commerce DZ...</b>")
    
    prods = fetch_apify_dz_products()
    
    if not prods:
        send_telegram("⚠️ <i>Impossible de récupérer les produits DZ actuellement. Réessaie plus tard.</i>")
        return

    send_telegram("🔥 <b>Produits E-commerce Détectés en Algérie (58 Wilayas)</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(prods, 1):
        # Format épuré sans liens inutiles
        msg = f"🏆 <b>WINNER DZ #{idx}</b>\n\n"
        msg += f"📦 <b>Produit / Titre :</b> {item['name']}\n"
        msg += f"👁️ <b>Vues :</b> {item['views']}\n"
        msg += f"❤️ <b>J'aime :</b> {item['likes']}\n"
        
        if item['url']:
            msg += f"\n🎬 <a href=\"{item['url']}\">Voir la vidéo sur TikTok</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
