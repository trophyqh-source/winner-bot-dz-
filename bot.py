import os
import requests
from apify_client import ApifyClient

# 1. Configuration des variables d'environnement (GitHub Secrets)
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([APIFY_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise ValueError("Erreur : Les variables d'environnement (APIFY_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) sont manquantes.")

apify_client = ApifyClient(APIFY_TOKEN)


def send_telegram_message(bot_token, chat_id, text, image_url=None):
    """Envoie un message ou une photo avec légende à Telegram."""
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
        print(f"[TELEGRAM] Message envoyé avec succès (status {res.status_code}).")
    except Exception as e:
        print(f"[ERROR] Échec de l'envoi Telegram : {e}")


def run_tiktok_scraper():
    print("[INFO] Lancement du scraping rapide TikTok via Apify...")

    # Paramètres ajustés pour éviter les blocages de hashtag
    run_input = {
        "searchKeywords": "dz",
        "countryCode": "DZ",
        "maxItems": 10,
        "period": 30
    }

    try:
        # Lancement de l'Actor Apify
        run_res = apify_client.actor("clockworks/tiktok-ads-scraper").call(run_input=run_input)
        
        # Récupération sécurisée du defaultDatasetId (compatible dictionnaire ou objet)
        dataset_id = run_res.get("defaultDatasetId") if isinstance(run_res, dict) else getattr(run_res, "default_dataset_id", run_res.get("defaultDatasetId", None))
        
        if not dataset_id:
            print("[ERROR] Impossible de récupérer l'identifiant du dataset Apify.")
            return

        dataset_items = apify_client.dataset(dataset_id).list_items().items
        print(f"[INFO] {len(dataset_items)} éléments récupérés depuis Apify.")

        if not dataset_items:
            print("[WARNING] Aucun résultat renvoyé par Apify pour ces critères.")
            return

        count = 0
        for item in dataset_items:
            ad_title = item.get("title") or item.get("adTitle") or "Produit TikTok DZ"
            ad_url = item.get("link") or item.get("videoUrl") or item.get("targetUrl") or "Lien indisponible"
            brand_name = item.get("brandName") or item.get("advertiserName") or "Annonceur"
            cover_image = item.get("coverUrl") or item.get("imageUrl") or item.get("image")

            message = (
                f"🔥 <b>Nouveau Produit Winner TikTok !</b>\n\n"
                f"📌 <b>Titre :</b> {ad_title}\n"
                f"🏢 <b>Annonceur :</b> {brand_name}\n"
                f"🔗 <b>Lien :</b> {ad_url}\n\n"
                f"🇩🇿 <i>Cible : Algérie</i>"
            )

            send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message, cover_image)
            count += 1

        print(f"[SUCCESS] {count} produits envoyés sur Telegram.")

    except Exception as e:
        print(f"[ERROR] Une erreur est survenue pendant le traitement TikTok : {e}")


if __name__ == "__main__":
    run_tiktok_scraper()
