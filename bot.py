import os
import requests
from apify_client import ApifyClient

# 1. Configuration des variables d'environnement (GitHub Secrets)
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([APIFY_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise ValueError("Erreur: Les variables d'environnement (APIFY_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) sont manquantes.")

apify_client = ApifyClient(APIFY_TOKEN)


def send_telegram_message(bot_token, chat_id, text, image_url=None):
    """Envoie une notification ou photo sur Telegram."""
    if image_url:
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": text,
            "parse_mode": "HTML"
        }
    else:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        print(f"[TELEGRAM] Message envoyé (Code: {res.status_code})")
    except Exception as e:
        print(f"[ERROR] Échec de l'envoi Telegram : {e}")


def run_tiktok_scraper():
    print("[INFO] Lancement du scraping TikTok Ads via Apify...")

    # Paramètres de recherche efficaces pour trouver des pubs en Algérie
    run_input = {
        "searchKeywords": "livraison algerie",
        "hashtags": ["algerie", "dz", "ecom"],
        "countryCode": "DZ",
        "maxItems": 15,
        "period": 30
    }

    try:
        # Appel de l'Actor TikTok Ads Scraper sur Apify
        run = apify_client.actor("clockworks/tiktok-ads-scraper").call(run_input=run_input)
        
        # Récupération sécurisée du Dataset ID
        dataset_id = run.get("defaultDatasetId") if isinstance(run, dict) else run.default_dataset_id
        dataset_items = apify_client.dataset(dataset_id).list_items().items
        
        print(f"[INFO] {len(dataset_items)} publicités récupérées depuis Apify.")

        if not dataset_items:
            print("[WARNING] Aucune publicité trouvée sur cette session.")
            send_telegram_message(
                TELEGRAM_BOT_TOKEN, 
                TELEGRAM_CHAT_ID, 
                "⚠️ <b>WinnerBotDZ : Scan TikTok Ads</b>\n\nAucune pub TikTok valide trouvée sur ce passage. Relance automatique lors du prochain cycle."
            )
            return

        count = 0
        for item in dataset_items:
            ad_title = item.get("title") or item.get("adTitle") or "Produit Winner TikTok"
            ad_url = item.get("link") or item.get("videoUrl") or item.get("targetUrl") or "Lien indisponible"
            brand_name = item.get("brandName") or item.get("advertiserName") or "Annonceur DZ"
            cover_image = item.get("coverUrl") or item.get("imageUrl") or item.get("image")

            message = (
                f"🇩🇿 <b>WinnerBotDZ : Scan TikTok Ads</b>\n\n"
                f"🔥 <b>Nouveau Produit Winner TikTok !</b>\n\n"
                f"📌 <b>Produit / Titre :</b> {ad_title}\n"
                f"🏢 <b>Annonceur :</b> {brand_name}\n"
                f"🔗 <b>Lien :</b> {ad_url}\n\n"
                f"🇩🇿 <i>Cible : Algérie</i>"
            )

            send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message, cover_image)
            count += 1

        print(f"[SUCCESS] {count} publicités envoyées sur Telegram.")

    except Exception as e:
        print(f"[ERROR] Une erreur est survenue pendant le traitement TikTok : {e}")


if __name__ == "__main__":
    run_tiktok_scraper()
