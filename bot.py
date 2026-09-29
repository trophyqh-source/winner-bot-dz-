import json
import os
import time
import requests

# --- CONFIGURATION API & BOT ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "apify_api_eSD9fRMu37Y6Vrf2Dyn4bFIhIVRKYE1fD8h1")

NB_PAR_ENVOI = 5

# Mots-clés très larges E-commerce DZ pour Meta
KEYWORDS_FB = [
    "livraison 58 wilayas",
    "commander site web",
    "livraison a domicile",
    "pantalon homme",
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
    
    # Utilisation d'un endpoint plus stable pour Meta Ad Library
    url = f"https://api.apify.com/v2/acts/curious_coder~facebook-ads-library-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    payload = {
        "searchTerms": KEYWORDS_FB,
        "countryCode": "DZ",
        "adActiveStatus": "ACTIVE",
        "limit": 40
    }

    try:
        res = requests.post(url, json=payload, timeout=90)
        
        # Si l'acteur principal échoue, tentative avec le second acteur
        if res.status_code not in [200, 201]:
            print(f"Changement d'acteur Apify (status {res.status_code})...")
            url = f"https://api.apify.com/v2/acts/apify~facebook-ads-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
            payload = {
                "searchTerms": ["58 wilayas", "livraison domicile"],
                "country": "DZ",
                "resultsLimit": 30
            }
            res = requests.post(url, json=payload, timeout=90)

        if res.status_code not in [200, 201]:
            print(f"Erreur Apify status code : {res.status_code}")
            return []

        items = res.json()
        if not isinstance(items, list) or len(items) == 0:
            print("Aucune pub renvoyée")
            return []

        ads = []
        seen_pages = set()

        for item in items:
            page_name = item.get("pageName") or item.get("page_name") or "Page DZ"
            ad_text = item.get("adBody") or item.get("ad_creative_body") or item.get("title") or ""
            text_lower = ad_text.lower()
            
            if page_name in seen_pages:
                continue

            if any(bad_word in text_lower for bad_word in EXCLUDE_WORDS):
                continue

            # Extrait le lien de la Landing Page
            link_url = item.get("linkUrl") or item.get("snapshotUrl") or item.get("target_url") or ""
            
            if not link_url:
                # Recherche d'URL dans le texte
                words = ad_text.split()
                for w in words:
                    if "http" in w or "www" in w or ".com" in w or ".dz" in w:
                        link_url = w
                        break

            title = ad_text.split("\n")[0][:80].strip() if ad_text else "Produit E-Commerce DZ"
            ad_id = item.get("adArchiveID") or item.get("ad_id") or ""
            fb_ad_url = f"https://www.facebook.com/ads/library/?id={ad_id}" if ad_id else ""

            ads.append({
                "page": page_name,
                "title": title,
                "landing": link_url if link_url else "Lien direct sur la pub FB",
                "fb_url": fb_ad_url
            })

            seen_pages.add(page_name)

            if len(ads) >= NB_PAR_ENVOI:
                break

        return ads

    except Exception as e:
        print(f"Exception Facebook Ads : {e}")
        return []

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
