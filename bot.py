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

# Mots-clés E-Commerce DZ pour Facebook Ads
KEYWORDS_FB = [
    "58 wilayas livraison",
    "commandez sur notre site",
    "livraison a domicile algerie",
    "prix choc algerie",
    "pantalon homme algerie",
    "accessoire maison algerie"
]

# Exclusions strictes (Nourriture, Services locaux, Cosmétiques 100% femme)
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

def fetch_facebook_ads():
    """Scrape la Meta Ad Library pour trouver des pubs E-commerce DZ avec Landing Page"""
    print("Recherche de Facebook Ads Winners DZ...")
    
    # Utilisation de l'acteur Apify Facebook Ads Scraper
    url = f"https://api.apify.com/v2/acts/apify~facebook-ads-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

    payload = {
        "searchTerms": KEYWORDS_FB,
        "country": "DZ",
        "adActiveStatus": "ACTIVE",
        "resultsLimit": 30
    }

    try:
        res = requests.post(url, json=payload, timeout=60)
        if res.status_code not in [200, 201]:
            print(f"Erreur Apify status code : {res.status_code}")
            return []

        items = res.json()
        if not isinstance(items, list) or len(items) == 0:
            print("Aucune pub renvoyée par Meta Ad Library")
            return []

        ads = []
        seen_pages = set()

        for item in items:
            page_name = item.get("pageName", "Page Inconnue")
            ad_text = item.get("adBody") or item.get("adTitle") or ""
            text_lower = ad_text.lower()
            
            # 1. Dédoublonnage par page
            if page_name in seen_pages:
                continue

            # 2. Filtre d'exclusion (nourriture, services, etc.)
            if any(bad_word in text_lower for bad_word in EXCLUDE_WORDS):
                continue

            # 3. Récupération de la Landing Page (Lien de destination du bouton)
            link_url = item.get("linkUrl") or item.get("targetUrl") or ""
            
            # Si pas de lien direct, on cherche un lien dans le texte de la pub
            if not link_url and ("http" in text_lower or "www" in text_lower):
                words = ad_text.split()
                for w in words:
                    if "http" in w or "www" in w:
                        link_url = w
                        break

            # S'il n'y a aucun site / landing page, on passe
            if not link_url:
                continue

            # 4. Formater la pub
            title = ad_text.split("\n")[0][:80].strip() if ad_text else "Publicité Produit DZ"
            ad_id = item.get("adArchiveID") or item.get("id") or ""
            fb_ad_url = f"https://www.facebook.com/ads/library/?id={ad_id}" if ad_id else ""

            ads.append({
                "page": page_name,
                "title": title,
                "landing": link_url,
                "fb_url": fb_ad_url
            })

            seen_pages.add(page_name)

            if len(ads) >= NB_PAR_ENVOI:
                break

        return ads

    except Exception as e:
        print(f"Exception Apify Facebook Ads : {e}")
        return []

def run_bot():
    send_telegram("🇩🇿 <b>WinnerBotDZ : Scan de Facebook Ads Library (Algérie)...</b>")
    
    ads = fetch_facebook_ads()
    
    if not ads:
        send_telegram("⚠️ <i>Aucune nouvelle pub Facebook DZ avec Landing Page trouvée sur ce passage. Prochain essai au prochain cycle !</i>")
        return

    send_telegram("🔥 <b>Top Ads Winners Facebook E-Commerce DZ</b> 🔥")
    time.sleep(1)

    for idx, item in enumerate(ads, 1):
        msg = f"🏆 <b>WINNER FB DZ #{idx}</b>\n\n"
        msg += f"📢 <b>Page Facebook :</b> {item['page']}\n"
        msg += f"📦 <b>Aperçu Pub :</b> {item['title']}\n\n"
        msg += f"🌐 <b>Landing Page (Site Web) :</b> {item['landing']}\n"
        
        if item['fb_url']:
            msg += f"\n🔗 <a href=\"{item['fb_url']}\">Voir la pub dans la Meta Ad Library</a>"

        send_telegram(msg)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
