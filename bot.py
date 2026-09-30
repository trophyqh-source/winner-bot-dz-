import os
import time
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Configuration depuis les variables d'environnement GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SEEN_FILE = "seen_links.txt"

# Clés optionnelles pour l'API Google Search officielle (zéro blocage)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

# Mots-clés E-commerce Algérie
QUERIES = [
    'site:tiktok.com "58 wilayas" "livraison"',
    'site:tiktok.com "livraison gratuite" "algerie"',
    'site:tiktok.com "prix" "commander" "wilaya"',
    'site:tiktok.com "boutique" "alger"'
]

def send_telegram_message(message):
    """Envoie une notification sur Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Erreur envoi Telegram : {e}")
        return False

def load_seen_links():
    """Charge l'historique des liens déjà envoyés."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen_links(seen):
    """Sauvegarde les liens vus."""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        for link in seen:
            f.write(f"{link}\n")

def fetch_google_api(query):
    """Recherche via Google API officielle (si configurée)."""
    links = []
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return links
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": 10
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("items", []):
                link = item.get("link")
                if link and "tiktok.com" in link:
                    links.append(link)
    except Exception as e:
        print(f"⚠️ Erreur Google API : {e}")
    return links

def fetch_duckduckgo_ddgs(query):
    """Recherche via le package duckduckgo_search."""
    links = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))
            for r in results:
                url = r.get("href")
                if url and "tiktok.com" in url:
                    links.append(url)
    except Exception as e:
        print(f"⚠️ Erreur DuckDuckGo DDGS : {e}")
    return links

def run():
    seen_links = load_seen_links()
    new_found = 0

    print("🚀 Début de la recherche de produits gagnants TikTok...")

    for query in QUERIES:
        print(f"🔎 Recherche pour : {query}")
        
        # 1. Tentative via Google API officielle si disponible
        links = fetch_google_api(query)
        
        # 2. Sinon, secours via DuckDuckGo
        if not links:
            links = fetch_duckduckgo_ddgs(query)

        for link in links:
            # Nettoyage de l'URL
            clean_link = link.split('?')[0]

            if clean_link not in seen_links:
                seen_links.add(clean_link)
                msg = f"🛒 <b>Nouveau produit / Vidéo TikTok trouvé !</b>\n\n🔗 {clean_link}"
                
                if send_telegram_message(msg):
                    print(f"✅ Envoyé sur Telegram : {clean_link}")
                    new_found += 1
                    time.sleep(2)  # Pause pour éviter d'être bloqué par Telegram
                else:
                    print(f"❌ Échec envoi : {clean_link}")

        time.sleep(3)

    save_seen_links(seen_links)
    print(f"🎉 Fin du cycle. {new_found} nouveau(x) lien(s) trouvé(s) et envoyé(s).")

if __name__ == "__main__":
    run()
