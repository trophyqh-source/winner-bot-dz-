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

# Mots-clés ciblés Gadgets Homme / High-Tech / Auto / Utilitaires
KEYWORDS_GADGETS = [
    "accessoire voiture algerie",
    "gadget tech algerie",
    "outil utile algerie",
    "accessoire telephone algerie",
    "produit astucieux algerie 58 wilayas",
    "ecouteur bluetooth algerie"
]

# Exclusion stricte de la nourriture, services ET produits 100% féminins/cosmétiques
EXCLUDE_WORDS = [
    # Nourriture / Services
    "bento", "cake", "cookie", "gateau", "patisserie", "brownie", "sweet",
    "food", "chocolat", "manger", "restaurant", "fast food", "snack",
    "salon", "coiffeur", "ongles", "location", "auto ecole",
    # Beauté / Mode / Produits exclusivement féminins
    "maquillage", "makeup", "robe", "abaya", "hijab", "sac femme", "talons",
    "epilation", "skincare", "serum visage", "perruque", "extensions", 
    "vernis", "rouge a levre", "palette", "collant", "lingerie"
]

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

def fetch_apify_gadgets_dz():
    """Scrape TikTok pour trouver des gadgets High-Tech, Auto et Outillage DZ"""
    print("Recherche de gadgets High-Tech & Auto DZ...")
    
    url = f"https://api.apify.com/v2/acts/clockworks~free-tiktok-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    payload = {
        "searchQueries": KEYWORDS_GADGETS,
        "resultsPerPage": 25,
        "searchType": "video"
    }

    try:
        res = requests.post(url, json=payload, timeout=50)
        if res.status_code not in [200, 201]:
            print(f"Erreur Apify status code : {res.status_code}")
            return []

        items = res.json()
        if not isinstance(items, list) or len(items) == 0:
            return []

        products = []
        seen_authors = set()  # Dédoublonnage des comptes

        for item in items:
            author = item.get("authorMeta", {}).get("name", "").lower()
            text = (item.get("text") or item.get("desc") or "").lower()
            
            # 1. Ignorer si le compte a déjà donné un produit dans ce scan
            if author and author in seen_authors:
                continue

            # 2. Filtrer la nourriture, services et cosmétiques féminins
            if any(bad_word in text for bad_word in EXCLUDE_WORDS):
                continue

            # 3. Traiter le titre
            raw_title = item.get("text") or item.get("desc") or ""
            title = raw_title.split("\n")[0][:65].strip()
            
            if len(title) < 6:
                continue

            play_count = item.get("playCount", 0)
            digg_count = item.get("diggCount", 0)
            video_url = item.get("webVideoUrl") or f"https://www.tiktok.com/@{author}/video/{item.get('id', '')}"

            products.append({
                "name": title,
                "views": f"{play_count:,}".replace(",", " "),
                "likes": f"{digg_count:,}".replace(",", " "),
                "url": video_url
            })

            if author:
                seen_authors.add(author)

            if len(products) >= NB_PAR_ENVOI:
                break

        return products

    except Exception as e:
        print(f"Exception Apify : {e}")
        return []

def run_bot():
    send_telegram("🇩🇿 <b>WinnerBotDZ : Filtrage Gadgets High-Tech & Auto...</b>")
    
    prods = fetch_apify_gadgets_dz()
    
    if not prods:
        send_telegram("⚠️ <i>Aucun gadget correspondant trouvé lors de ce scan. Réessai automatique au prochain cycle.</i>")
        return

    send_telegram("🔥 <b>Top Gadgets High-Tech & Auto DZ (58 Wilayas)</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(prods, 1):
        msg = f"🏆 <b>WINNER GADGET #{idx}</b>\n\n"
        msg += f"📦 <b>Produit :</b> {item['name']}\n"
        msg += f"👁️ <b>Vues :</b> {item['views']}\n"
        msg += f"❤️ <b>J'aime :</b> {item['likes']}\n"
        
        if item['url']:
            msg += f"\n🎬 <a href=\"{item['url']}\">Voir la vidéo sur TikTok</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
