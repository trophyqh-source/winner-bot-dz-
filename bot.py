import os
import re
import time
import requests
from urllib.parse import unquote

# --- CONFIGURATION TELEGRAM ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

NB_PAR_ENVOI = 5

# Requetes de recherche ciblees sur les produits DZ
QUERIES = [
    'site:tiktok.com "58 wilayas" "livraison"',
    'site:tiktok.com "livraison disponible" "algerie"',
    'site:tiktok.com "commander" "wilaya"',
    'site:tiktok.com "prix" "dzd" "livraison"'
]

EXCLUDE_WORDS = [
    "bento", "cake", "cookie", "gateau", "patisserie", "brownie",
    "food", "chocolat", "restaurant", "fast food",
    "salon", "coiffeur", "ongles", "location", "auto ecole",
    "maquillage", "makeup", "robe", "abaya", "hijab"
]

def send_telegram(text):
    """Envoie un message textuel a Telegram"""
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

def search_duckduckgo(query):
    """Scrape DuckDuckGo HTML directement sans passer par Apify (0 blocage)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"
    }
    url = "https://html.duckduckgo.com/html/"
    try:
        res = requests.post(url, data={"q": query}, headers=headers, timeout=20)
        if res.status_code != 200:
            return []

        # Extraction des titres et liens
        matches = re.findall(r'class="result__a"\ href="([^"]+)">(.*?)</a>', res.text)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', res.text)

        items = []
        for idx, (raw_url, raw_title) in enumerate(matches):
            title = re.sub(r'<[^>]+>', '', raw_title).strip()
            
            # Extraction du vrai lien nettoyé
            link = raw_url
            if 'uddg=' in raw_url:
                link = unquote(raw_url.split('uddg=')[1].split('&')[0])

            snippet = ""
            if idx < len(snippets):
                snippet = re.sub(r'<[^>]+>', '', snippets[idx]).strip()

            items.append({
                "title": title,
                "url": link,
                "snippet": snippet
            })
        return items
    except Exception as e:
        print(f"Erreur recherche : {e}")
        return []

def fetch_winners():
    """Récupère les produits winners DZ"""
    print("Recherche directe des winners DZ...")
    products = []
    seen_urls = set()

    # Alternance dynamique de la requête
    query = QUERIES[int(time.time()) % len(QUERIES)]
    raw_results = search_duckduckgo(query)

    for item in raw_results:
        link = item["url"]
        title = item["title"]
        snippet = item["snippet"]
        full_text = (title + " " + snippet).lower()

        if link in seen_urls:
            continue

        # Filtrage des mots exclus
        if any(bad in full_text for bad in EXCLUDE_WORDS):
            continue

        clean_title = title.replace(" - TikTok", "").replace("TikTok", "").strip()
        if len(clean_title) < 5:
            clean_title = "Produit E-Commerce DZ"

        products.append({
            "title": clean_title,
            "link": link,
            "snippet": snippet if snippet else "Produit E-commerce disponible avec livraison 58 wilayas."
        })

        seen_urls.add(link)

        if len(products) >= NB_PAR_ENVOI:
            break

    return products

def run_bot():
    send_telegram("🇩🇿 <b>WinnerBotDZ : Scan direct des Winners E-Commerce DZ...</b>")
    
    prods = fetch_winners()
    
    if not prods:
        send_telegram("⚠️ <i>Aucun nouveau lien trouvé sur ce cycle. Relance au prochain passage.</i>")
        return

    send_telegram("🔥 <b>Top Winners E-Commerce DZ Trouvés</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(prods, 1):
        msg = f"🏆 <b>WINNER DZ #{idx}</b>\n\n"
        msg += f"📦 <b>Produit :</b> {item['title']}\n"
        msg += f"📝 <b>Aperçu :</b> {item['snippet']}\n\n"
        msg += f"🎬 <a href=\"{item['link']}\">Voir la vidéo TikTok</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
