import json
import os
import time
import requests

# --- CONFIGURATION API & BOT ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_eSD9fRMu37Y6Vrf2Dyn4bFIhIVRKYE1fD8h1")

NB_PAR_ENVOI = 5

KEYWORDS_FB = [
    "livraison 58 wilayas",
    "commander",
    "livraison a domicile",
    "boutique algerie"
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

def fetch_facebook_ads():
    """Scrape la Meta Ad Library pour trouver des pubs E-commerce DZ"""
    print("Recherche de Facebook Ads Winners DZ...")
    
    # Tentative 1 : Acteur apify/facebook-ads-scraper
    url1 = f"https://api.apify.com/v2/acts/apify~facebook-ads-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    payload1 = {
        "startUrls": [{"url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=DZ&q=livraison%2058%20wilayas"}],
        "resultsLimit": 30
    }

    items = []
    try:
        print("Essai méthode 1 (Start URL)...")
        res1 = requests.post(url1, json=payload1, timeout=90)
        if res1.status_code in [200, 201]:
            data = res1.json()
            if isinstance(data, list) and len(data) > 0:
                items = data
    except Exception as e:
        print(f"Erreur méthode 1: {e}")

    # Tentative 2 (Fallback) : Acteur curious_coder
    if not items:
        try:
            print("Essai méthode 2 (Keywords Search)...")
            url2 = f"https://api.apify.com/v2/acts/curious_coder~facebook-ads-library-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
            payload2 = {
                "searchTerms": KEYWORDS_FB,
                "countryCode": "DZ",
                "limit": 30
            }
            res2 = requests.post(url2, json=payload2, timeout=90)
            if res2.status_code in [200, 201]:
                data = res2.json()
                if isinstance(data, list) and len(data) > 0:
                    items = data
        except Exception as e:
            print(f"Erreur méthode 2: {e}")

    if not items:
        print("Aucune donnée retournée par les scrapers.")
        return []

    ads = []
    seen_pages = set()

    for item in items:
        page_name = item.get("pageName") or item.get("page_name") or item.get("publisherPlatform") or "Boutique DZ"
        ad_text = item.get("adBody") or item.get("ad_creative_body") or item.get("title") or item.get("snapshot", {}).get("body", {}).get("text", "") or ""
        text_lower = ad_text.lower()
        
        if page_name in seen_pages:
            continue

        if any(bad_word in text_lower for bad_word in EXCLUDE_WORDS):
            continue

        link_url = item.get("linkUrl") or item.get("snapshotUrl") or item.get("target_url") or ""
        
        if not link_url:
            words = ad_text.split()
            for w in words:
                if "http" in w or "www" in w or ".com" in w or ".dz" in w:
                    link_url = w
                    break

        title = ad_text.split("\n")[0][:80].strip() if ad_text else "Offre E-Commerce DZ"
        ad_id = item.get("adArchiveID") or item.get("ad_id") or item.get("id") or ""
        fb_ad_url = f"https://www.facebook.com/ads/library/?id={ad_id}" if ad_id else ""

        ads.append({
            "page": page_name,
            "title": title,
            "landing": link_url if link_url else "Lien sur la publicité Facebook",
            "fb_url": fb_ad_url
        })

        seen_pages.add(page_name)

        if len(ads) >= NB_PAR_ENVOI:
            break

    return ads

def run_bot():
    send_telegram("🇩🇿 <b>WinnerBotDZ : Scan Meta Ad Library (Algérie)...</b>")
    
    ads = fetch_facebook_ads()
    
    if not ads:
        send_telegram("⚠️ <i>Aucune pub valide trouvée sur ce passage. Relance automatique lors du prochain cycle.</i>")
        return

    send_telegram("🔥 <b>Top Ads Winners Facebook E-Commerce DZ</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(ads, 1):
        msg = f"🏆 <b>WINNER FB DZ #{idx}</b>\n\n"
        msg += f"📢 <b>Page Facebook :</b> {item['page']}\n"
        msg += f"📦 <b>Pub :</b> {item['title']}\n\n"
        msg += f"🌐 <b>Landing Page :</b> {item['landing']}\n"
        
        if item['fb_url']:
            msg += f"\n🔗 <a href=\"{item['fb_url']}\">Voir dans la Meta Ad Library</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
