import json
import os
import time
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION API & BOT ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_eSD9fRMu37Y6Vrf2Dyn4bFIhIVRKYE1fD8h1")

NB_PAR_ENVOI = 5
MAX_DAYS_OLD = 60  # Maximum 2 mois (60 jours)

# Mots-clés de recherche très variés (Algérie + E-commerce)
KEYWORDS_VARIES = [
    "pantalon homme algerie 58 wilayas",
    "mini aspirateur portable algerie livraison",
    "imprimante portable algerie site",
    "gourde motivante algerie commande site",
    "produit utile algerie 58 wilayas site web",
    "gadget maison algerie commande lien bio",
    "accessoire pratique algerie livraison domicile"
]

# Exclusions strictes (Nourriture, Services locaux, Cosmétiques 100% femme)
EXCLUDE_WORDS = [
    "bento", "cake", "cookie", "gateau", "patisserie", "brownie", "sweet",
    "food", "chocolat", "manger", "restaurant", "fast food", "snack",
    "salon", "coiffeur", "ongles", "location", "auto ecole",
    "maquillage", "makeup", "robe", "abaya", "hijab", "talons", "epilation"
]

# Indicateurs stricts Algérie
DZ_INDICATORS = ["algerie", "alger", "dz", "58 wilayas", "58 wilaya", "wilaya", "dinars", "da"]

# Indicateurs de présence d'une Landing Page / Site Web de commande
LANDING_DOMAINS = [".com", ".dz", ".shop", ".store", ".site", "youcan", "shopify", "dropify", "coot"]
LANDING_TEXTS = ["lien en bio", "link in bio", "commandez sur le site", "lien dans la bio", "sur le site"]

# --- SEUILS MINIMAUX D'ENGAGEMENT ---
MIN_LIKES = 5000
MIN_COMMENTS = 500
MIN_SAVES = 500
MIN_SHARES = 300

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

def is_recent(create_time):
    """Vérifie si la vidéo a moins de 60 jours (2 mois)"""
    if not create_time:
        return True  # Par sécurité si l'API ne renvoie pas la date
    try:
        video_date = datetime.fromtimestamp(create_time)
        return video_date >= (datetime.now() - timedelta(days=MAX_DAYS_OLD))
    except Exception:
        return True

def fetch_apify_winner_products():
    """Scrape TikTok : Produits DZ + Landing Page + < 2 mois + Gros Engagement"""
    print("Recherche des Winners DZ stricts...")
    
    url = f"https://api.apify.com/v2/acts/clockworks~free-tiktok-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    payload = {
        "searchQueries": KEYWORDS_VARIES,
        "resultsPerPage": 40,
        "searchType": "video"
    }

    try:
        res = requests.post(url, json=payload, timeout=60)
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
            bio_link = item.get("authorMeta", {}).get("bioLink", "")
            
            # 1. Dédoublonnage des comptes
            if author and author in seen_authors:
                continue

            # 2. Exclure la nourriture / services / makeup
            if any(bad_word in text for bad_word in EXCLUDE_WORDS):
                continue

            # 3. FILTRE GEOLOCALISATION : Strictement Algérie
            is_dz = any(dz_word in text for dz_word in DZ_INDICATORS)
            if not is_dz:
                continue

            # 4. FILTRE DATE : Maximum 2 mois (60 jours)
            create_time = item.get("createTime")
            if not is_recent(create_time):
                continue

            # 5. FILTRE LANDING PAGE / SITE WEB OBLIGATOIRE
            has_landing_link = bool(bio_link and any(dom in bio_link.lower() for dom in LANDING_DOMAINS))
            has_landing_mention = any(indicator in text for indicator in LANDING_TEXTS)
            
            if not (has_landing_link or has_landing_mention):
                continue

            # 6. FILTRE ENGAGEMENT ELEVE
            digg_count = item.get("diggCount", 0)       # Likes
            comment_count = item.get("commentCount", 0) # Commentaires
            share_count = item.get("shareCount", 0)     # Partages
            collect_count = item.get("collectCount", 0) # Enregistrements / Favoris

            has_high_engagement = (
                digg_count >= MIN_LIKES or
                comment_count >= MIN_COMMENTS or
                collect_count >= MIN_SAVES or
                share_count >= MIN_SHARES
            )

            if not has_high_engagement:
                continue

            # 7. Titre et URL
            raw_title = item.get("text") or item.get("desc") or ""
            title = raw_title.split("\n")[0][:65].strip()
            
            if len(title) < 5:
                continue

            play_count = item.get("playCount", 0)
            video_url = item.get("webVideoUrl") or f"https://www.tiktok.com/@{author}/video/{item.get('id', '')}"
            landing_display = bio_link if bio_link else "Lien en Bio / Site Web"

            products.append({
                "name": title,
                "views": f"{play_count:,}".replace(",", " "),
                "likes": f"{digg_count:,}".replace(",", " "),
                "comments": f"{comment_count:,}".replace(",", " "),
                "shares": f"{share_count:,}".replace(",", " "),
                "saves": f"{collect_count:,}".replace(",", " "),
                "url": video_url,
                "landing": landing_display
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
    send_telegram("🇩🇿 <b>WinnerBotDZ : Verification des Ads DZ + Landing Page (<2 mois)...</b>")
    
    prods = fetch_apify_winner_products()
    
    if not prods:
        send_telegram("⚠️ <i>Aucun produit 100% DZ avec Landing Page (<2 mois) et gros engagement trouvé sur ce passage. Réessai automatique au prochain run.</i>")
        return

    send_telegram("🔥 <b>Top Ads Winners E-Commerce DZ (Avec Landing Page)</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(prods, 1):
        msg = f"🏆 <b>WINNER DZ #{idx}</b>\n\n"
        msg += f"📦 <b>Produit :</b> {item['name']}\n"
        msg += f"🌐 <b>Landing Page / Site :</b> {item['landing']}\n\n"
        msg += "📊 <b>Performance Ad :</b>\n"
        msg += f"• 👁️ Vues : {item['views']}\n"
        msg += f"• ❤️ J'aime : {item['likes']}\n"
        msg += f"• 💬 Commentaires : {item['comments']}\n"
        msg += f"• 🔖 Enregistrements : {item['saves']}\n"
        msg += f"• 🔁 Partages : {item['shares']}\n"
        
        if item['url']:
            msg += f"\n🎬 <a href=\"{item['url']}\">Voir la vidéo de la pub TikTok</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
