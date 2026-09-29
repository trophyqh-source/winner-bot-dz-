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

# Mots-clés très variés (Mode, Gadgets, Maison, Tech)
KEYWORDS_VARIES = [
    "pantalon homme algerie 58 wilayas",
    "mini aspirateur portable algerie",
    "imprimante portable algerie",
    "gourde motivante algerie",
    "produit utile algerie commande site",
    "gadget maison algerie livraison",
    "accessoire pratique algerie site web"
]

# Exclusions strictes (Nourriture, Restos, Services locaux, Cosmétiques 100% femme)
EXCLUDE_WORDS = [
    "bento", "cake", "cookie", "gateau", "patisserie", "brownie", "sweet",
    "food", "chocolat", "manger", "restaurant", "fast food", "snack",
    "salon", "coiffeur", "ongles", "location", "auto ecole",
    "maquillage", "makeup", "robe", "abaya", "hijab", "talons", "epilation"
]

# Indicateurs de présence d'une Landing Page / Site Web
LANDING_INDICATORS = [
    "lien en bio", "link in bio", "site web", "commandez sur notre site",
    "lien dans la bio", "sur le site", ".com", ".dz", "store", "shop"
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

def fetch_apify_varied_landing_products():
    """Scrape TikTok pour trouver des produits variés AVEC Landing Page / Site Web"""
    print("Recherche de produits variés avec Landing Page DZ...")
    
    url = f"https://api.apify.com/v2/acts/clockworks~free-tiktok-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    payload = {
        "searchQueries": KEYWORDS_VARIES,
        "resultsPerPage": 30,
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
        seen_authors = set()

        for item in items:
            author = item.get("authorMeta", {}).get("name", "").lower()
            text = (item.get("text") or item.get("desc") or "").lower()
            
            # 1. Dédoublonnage des comptes
            if author and author in seen_authors:
                continue

            # 2. Exclure la nourriture / services / makeup
            if any(bad_word in text for bad_word in EXCLUDE_WORDS):
                continue

            # 3. Vérifier la présence d'une Landing Page / Site Web (ou lien en bio)
            has_landing = any(indicator in text for indicator in LANDING_INDICATORS) or item.get("authorMeta", {}).get("bioLink")
            
            # Si aucune trace de landing page/site web, on passe
            if not has_landing:
                continue

            # 4. Traiter le titre
            raw_title = item.get("text") or item.get("desc") or ""
            title = raw_title.split("\n")[0][:65].strip()
            
            if len(title) < 5:
                continue

            play_count = item.get("playCount", 0)
            digg_count = item.get("diggCount", 0)
            video_url = item.get("webVideoUrl") or f"https://www.tiktok.com/@{author}/video/{item.get('id', '')}"
            bio_link = item.get("authorMeta", {}).get("bioLink", "")

            products.append({
                "name": title,
                "views": f"{play_count:,}".replace(",", " "),
                "likes": f"{digg_count:,}".replace(",", " "),
                "url": video_url,
                "landing": bio_link if bio_link else "Lien en Bio TikTok"
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
    send_telegram("🇩🇿 <b>WinnerBotDZ : Filtrage Produits Variés + Landing Page...</b>")
    
    prods = fetch_apify_varied_landing_products()
    
    if not prods:
        send_telegram("⚠️ <i>Aucun produit avec Landing Page trouvé lors de ce passage. Réessai automatique au prochain run.</i>")
        return

    send_telegram("🔥 <b>Top Produits E-commerce Variés (Avec Landing Page)</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(prods, 1):
        msg = f"🏆 <b>WINNER DZ #{idx}</b>\n\n"
        msg += f"📦 <b>Produit :</b> {item['name']}\n"
        msg += f"🌐 <b>Site / Landing :</b> {item['landing']}\n"
        msg += f"👁️ <b>Vues :</b> {item['views']}\n"
        msg += f"❤️ <b>J'aime :</b> {item['likes']}\n"
        
        if item['url']:
            msg += f"\n🎬 <a href=\"{item['url']}\">Voir la vidéo sur TikTok</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
