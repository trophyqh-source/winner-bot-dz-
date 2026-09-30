import json
import os
import time
import requests

# --- CONFIGURATION API & BOT ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_NHjmiStXhLV8j9cCkGn7QLqEMKwqEc0W7tuw")

NB_PAR_ENVOI = 5

# Mots-clés simples et efficaces E-commerce DZ
KEYWORDS_VARIES = [
    "livraison 58 wilayas",
    "commander algerie",
    "produit algerie",
    "boutique algerie"
]

EXCLUDE_WORDS = [
    "bento", "cake", "cookie", "gateau", "patisserie", "brownie", "sweet",
    "food", "chocolat", "manger", "restaurant", "fast food", "snack",
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

def fetch_apify_winner_products():
    """Scrape TikTok via l'acteur officiel apify~tiktok-scraper"""
    print("Recherche de produits DZ sur TikTok...")
    
    # Utilisation de l'acteur officiel TikTok d'Apify
    url = f"https://api.apify.com/v2/acts/apify~tiktok-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    payload = {
        "searchKeywords": KEYWORDS_VARIES,
        "resultsPerPage": 30,
        "searchSection": "/video"
    }

    try:
        res = requests.post(url, json=payload, timeout=90)
        
        # En cas d'échec, tentative de secours avec format alternatif
        if res.status_code not in [200, 201]:
            print(f"Tentative alternative (status {res.status_code})...")
            url = f"https://api.apify.com/v2/acts/clockworks~free-tiktok-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
            payload = {
                "searchQueries": ["livraison 58 wilayas", "commander algerie"],
                "resultsPerPage": 20
            }
            res = requests.post(url, json=payload, timeout=90)

        if res.status_code not in [200, 201]:
            print(f"Erreur Apify status code : {res.status_code}")
            return []

        items = res.json()
        if not isinstance(items, list) or len(items) == 0:
            print("Aucun élément retourné par l'API")
            return []

        products = []
        seen_authors = set()

        for item in items:
            author = item.get("authorMeta", {}).get("name", "") or item.get("author", "")
            author = author.lower()
            
            text = (item.get("text") or item.get("desc") or "").lower()
            
            # 1. Dédoublonnage
            if author and author in seen_authors:
                continue

            # 2. Exclusions
            if any(bad_word in text for bad_word in EXCLUDE_WORDS):
                continue

            digg_count = item.get("diggCount") or item.get("stats", {}).get("diggCount", 0)
            comment_count = item.get("commentCount") or item.get("stats", {}).get("commentCount", 0)
            share_count = item.get("shareCount") or item.get("stats", {}).get("shareCount", 0)
            collect_count = item.get("collectCount") or item.get("stats", {}).get("collectCount", 0)
            play_count = item.get("playCount") or item.get("stats", {}).get("playCount", 0)

            raw_title = item.get("text") or item.get("desc") or ""
            title = raw_title.split("\n")[0][:70].strip()
            if len(title) < 3:
                title = f"Produit E-commerce DZ (@{author})"

            video_url = item.get("webVideoUrl") or item.get("videoUrl") or f"https://www.tiktok.com/@{author}/video/{item.get('id', '')}"
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
    send_telegram("🇩🇿 <b>WinnerBotDZ : Scan TikTok E-Commerce DZ...</b>")
    
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
