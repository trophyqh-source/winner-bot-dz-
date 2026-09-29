import os
import time
import requests

# --- CONFIGURATION API & BOT ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_eSD9fRMu37Y6Vrf2Dyn4bFIhIVRKYE1fD8h1")

NB_PAR_ENVOI = 5

KEYWORDS_TIKTOK = [
    "livraison 58 wilayas",
    "commander",
    "livraison gratuite",
    "boutique algerie",
    "promo algerie"
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

def fetch_tiktok_ads():
    """Scrape le TikTok Creative Center / Ads pour trouver des produits E-commerce DZ"""
    print("Recherche de TikTok Ads Winners DZ...")
    
    # Acteur Apify pour TikTok Ads Library / Scraper
    url = f"https://api.apify.com/v2/acts/clockworks~tiktok-ads-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    
    payload = {
        "searchKeywords": KEYWORDS_TIKTOK,
        "countryCode": "DZ",
        "limit": 30
    }

    items = []
    try:
        res = requests.post(url, json=payload, timeout=90)
        if res.status_code in [200, 201]:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                items = data
    except Exception as e:
        print(f"Erreur lors du scraping TikTok: {e}")

    if not items:
        print("Aucune donnée retournée par le scraper TikTok.")
        return []

    ads = []
    seen_ids = set()

    for item in items:
        ad_id = item.get("ad_id") or item.get("id") or ""
        brand_name = item.get("brand_name") or item.get("advertiser_name") or "Boutique TikTok DZ"
        ad_text = item.get("ad_title") or item.get("title") or item.get("caption") or ""
        text_lower = ad_text.lower()
        
        if ad_id in seen_ids:
            continue

        if any(bad_word in text_lower for bad_word in EXCLUDE_WORDS):
            continue

        landing_url = item.get("landing_page_url") or item.get("target_url") or item.get("link") or ""
        
        title = ad_text.split("\n")[0][:80].strip() if ad_text else "Produit Tendance TikTok DZ"
        tiktok_ad_url = item.get("ad_url") or f"https://ads.tiktok.com/business/creativecenter/topads/{ad_id}" if ad_id else ""

        ads.append({
            "brand": brand_name,
            "title": title,
            "landing": landing_url if landing_url else "Lien dans la bio / Pub",
            "tiktok_url": tiktok_ad_url
        })

        seen_ids.add(ad_id)

        if len(ads) >= NB_PAR_ENVOI:
            break

    return ads

def run_bot():
    send_telegram("🇩🇿 <b>WinnerBotDZ : Scan TikTok Ads (Algérie)...</b>")
    
    ads = fetch_tiktok_ads()
    
    if not ads:
        send_telegram("⚠️ <i>Aucune pub TikTok valide trouvée sur ce passage. Relance automatique lors du prochain cycle.</i>")
        return

    send_telegram("🔥 <b>Top Ads Winners TikTok E-Commerce DZ</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(ads, 1):
        msg = f"🎵 <b>WINNER TIKTOK DZ #{idx}</b>\n\n"
        msg += f"📢 <b>Marque / Compte :</b> {item['brand']}\n"
        msg += f"📦 <b>Pub :</b> {item['title']}\n\n"
        msg += f"🌐 <b>Landing Page :</b> {item['landing']}\n"
        
        if item['tiktok_url']:
            msg += f"\n🔗 <a href=\"{item['tiktok_url']}\">Voir la vidéo / Pub TikTok</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
