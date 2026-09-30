import json
import os
import time
import requests

# --- CONFIGURATION API & BOT ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_NHjmiStXhLV8j9cCkGn7QLqEMKwqEc0W7tuw")

NB_PAR_ENVOI = 5

KEYWORDS_VARIES = [
    "livraison 58 wilayas",
    "commander algerie",
    "produit algerie",
    "boutique algerie",
    "pantalon homme algerie",
    "mini aspirateur portable algerie",
    "gadget maison algerie"
]

EXCLUDE_WORDS = [
    "bento", "cake", "cookie", "gateau", "patisserie", "brownie", "sweet",
    "food", "chocolat", "manger", "restaurant", "fast food", "snack",
    "salon", "coiffeur", "ongles", "location", "auto ecole",
    "maquillage", "makeup", "robe", "abaya", "hijab", "talons", "epilation"
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

def fetch_apify_winner_products():
    """Scrape TikTok pour trouver des produits DZ sans filtre d'engagement"""
    print("Recherche de produits DZ sur TikTok (sans filtres d'engagement)...")
    
    url = f"https://api.apify.com/v2/acts/clockworks~free-tiktok-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    payload = {
        "searchQueries": KEYWORDS_VARIES,
        "resultsPerPage": 30,
        "searchType": "video"
    }

    try:
        res = requests.post(url, json=payload, timeout=90)
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

            # 2. Exclusions (nourriture, beauté femme, etc.)
            if any(bad_word in text for bad_word in EXCLUDE_WORDS):
                continue

            # Métriques à titre indicatif uniquement
            digg_count = item.get("diggCount", 0)       # Likes
            comment_count = item.get("commentCount", 0) # Commentaires
            share_count = item.get("shareCount", 0)     # Partages
            collect_count = item.get("collectCount", 0) # Enregistrements

            raw_title = item.get("text") or item.get("desc") or ""
            title = raw_title.split("\n")[0][:70].strip()
            if len(title) < 3:
                title = f"Produit E-commerce DZ (@{author})"

            play_count = item.get("playCount", 0)
            video_url = item.get("webVideoUrl") or f"https://www.tiktok.com/@{author}/video/{item.get('id', '')}"
            bio_link = item.get("authorMeta", {}).get("bioLink", "")

            products.append({
                "name": title,
                "views": f"{play_count:,}".replace(",", " "),
                "likes": f"{digg_count:,}".replace(",", " "),
                "comments": f"{comment_count:,}".replace(",", " "),
                "shares": f"{share_count:,}".replace(",", " "),
                "saves": f"{collect_count:,}".replace(",", " "),
                "url": video_url,
                "landing": bio_link if bio_link else "Lien en Bio TikTok / Contact Direct"
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
    send_telegram("🇩🇿 <b>WinnerBotDZ : Scan des vidéos E-commerce DZ...</b>")
    
    prods = fetch_apify_winner_products()
    
    if not prods:
        send_telegram("⚠️ <i>Aucun produit trouvé lors de ce passage. Relance automatique au prochain cycle.</i>")
        return

    send_telegram("🔥 <b>Top Produits E-commerce DZ Trouvés</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(prods, 1):
        msg = f"🏆 <b>WINNER DZ #{idx}</b>\n\n"
        msg += f"📦 <b>Produit :</b> {item['name']}\n"
        msg += f"🌐 <b>Site / Bio :</b> {item['landing']}\n\n"
        msg += "📊 <b>Statistiques :</b>\n"
        msg += f"• 👁️ Vues : {item['views']}\n"
        msg += f"• ❤️ Likes : {item['likes']}\n"
        msg += f"• 💬 Commentaires : {item['comments']}\n"
        msg += f"• 🔖 Enregistrements : {item['saves']}\n"
        msg += f"• 🔁 Partages : {item['shares']}\n"
        
        if item['url']:
            msg += f"\n🎬 <a href=\"{item['url']}\">Voir la vidéo sur TikTok</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
