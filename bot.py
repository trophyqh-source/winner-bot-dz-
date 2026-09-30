import json
import os
import time
import requests

# --- CONFIGURATION API & BOT ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_NHjmiStXhLV8j9cCkGn7QLqEMKwqEc0W7tuw")

NB_PAR_ENVOI = 5

# Requêtes ciblées sur Google pour choper les vidéos TikTok DZ
GOOGLE_TIKTOK_QUERIES = [
    'site:tiktok.com "58 wilayas" "livraison"',
    'site:tiktok.com "commander" "algerie" "livraison"',
    'site:tiktok.com "livraison a domicile" "wilaya"',
    'site:youcan.shop "58 wilayas" "nom" "telephone"'
]

EXCLUDE_WORDS = [
    "bento", "cake", "cookie", "gateau", "patisserie", "brownie",
    "food", "chocolat", "restaurant", "fast food",
    "salon", "coiffeur", "ongles", "location", "auto ecole",
    "maquillage", "makeup", "robe", "abaya", "hijab"
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
    try:
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print(f"Erreur envoi Telegram : {e}")

def fetch_winners_via_google():
    """Scrape Google pour trouver les TikToks et Landing Pages DZ sans aucun blocage IP"""
    print("Recherche de winners DZ via Google Search Index...")
    
    url = f"https://api.apify.com/v2/acts/apify~google-search-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    # Alternance des requêtes à chaque passage
    query = GOOGLE_TIKTOK_QUERIES[int(time.time()) % len(GOOGLE_TIKTOK_QUERIES)]

    payload = {
        "queries": query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": 25,
        "countryCode": "dz"
    }

    try:
        res = requests.post(url, json=payload, timeout=90)
        if res.status_code not in [200, 201]:
            print(f"Erreur Apify status code : {res.status_code}")
            return []

        data = res.json()
        if not isinstance(data, list) or len(data) == 0:
            return []

        organic_results = data[0].get("organicResults", [])
        if not organic_results:
            return []

        products = []
        seen_links = set()

        for item in organic_results:
            title = item.get("title", "")
            link = item.get("url", "")
            snippet = item.get("description", "")
            full_text = (title + " " + snippet).lower()

            if link in seen_links:
                continue

            # Filtre des mots exclus
            if any(bad in full_text for bad in EXCLUDE_WORDS):
                continue

            # Nettoyage du titre
            clean_title = title.replace(" - TikTok", "").replace("TikTok", "").strip()
            if len(clean_title) < 5:
                clean_title = "Produit Winner E-Commerce DZ"

            products.append({
                "title": clean_title,
                "link": link,
                "desc": snippet[:110] if snippet else "Produit E-commerce DZ avec livraison 58 wilayas"
            })

            seen_links.add(link)

            if len(products) >= NB_PAR_ENVOI:
                break

        return products

    except Exception as e:
        print(f"Exception Google Scraper : {e}")
        return []

def run_bot():
    send_telegram("🇩🇿 <b>WinnerBotDZ : Scan des Winners E-Commerce DZ...</b>")
    
    prods = fetch_winners_via_google()
    
    if not prods:
        send_telegram("⚠️ <i>Aucun résultat sur ce cycle. Relance automatique au prochain passage.</i>")
        return

    send_telegram("🔥 <b>Top Winners E-Commerce DZ Trouvés</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(prods, 1):
        msg = f"🏆 <b>WINNER DZ #{idx}</b>\n\n"
        msg += f"📦 <b>Produit / Titre :</b> {item['title']}\n"
        msg += f"📝 <b>Aperçu :</b> {item['desc']}...\n\n"
        
        if "tiktok.com" in item['link']:
            msg += f"🎬 <a href=\"{item['link']}\">Voir la vidéo TikTok</a>"
        else:
            msg += f"🌐 <a href=\"{item['link']}\">Voir le site / Landing Page</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
