import os
import requests
from apify_client import ApifyClient

# 1. Configuration des variables d'environnement (GitHub Secrets / Local)
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Validation des accès
if not all([APIFY_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise ValueError("Erreur: Les variables d'environnement ne sont pas correctement configurées.")

# Initialisation du client Apify
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
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Échec de l'envoi Telegram : {e}")


def filter_product(item):
    """Filtre les publicités selon les mots-clés e-commerce et exclut les services/nourriture."""
    title = str(item.get("title", "")).lower()
    description = str(item.get("body", "") or item.get("description", "")).lower()
    text = f"{title} {description}"

    # Mots-clés requis pour l'Algérie / E-commerce
    keywords = ["livraison", "commande", "prix", "da", "dz", "promo", "vente", "commander", "boutique"]
    
    # Mots à exclure (Services, fast-food, etc.)
    exclusions = ["restaurant", "pizza", "burger", "coiffure", "salon", "formation", "recrutement"]

    # Vérification des exclusions
    if any(ex in text for ex in exclusions):
        return False

    # Vérification de la présence d'au moins un mot-clé
    if any(kw in text for kw in keywords):
        return True

    return False


def run_tiktok_scraper():
    print("[INFO] Lancement du scraping TikTok via Apify...")

    # Paramètres de l'Actor TikTok Creative Center / TikTok Ads Scraper sur Apify
    run_input = {
        "countryCode": "DZ",
        "maxItems": 20,
        "period": 7  # Publicités actives ces 7 derniers jours
    }

    try:
        # Exécution de l'Actor Apify (clockworks/tiktok-ads-scraper ou similaire)
        run = apify_client.actor("clockworks/free-tiktok-ads-scraper").call(run_input=run_input)
        dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        
        print(f"[INFO] {len(dataset_items)} éléments récupérés depuis Apify.")

        count = 0
        for item in dataset_items:
            if filter_product(item):
                ad_title = item.get("title") or "Produit sans titre"
                ad_url = item.get("link") or item.get("videoUrl") or "Lien indisponible"
                brand_name = item.get("brandName") or "Marque / Annonceur"
                cover_image = item.get("coverUrl") or item.get("image")

                # Formatage du message Telegram
                message = (
                    f"🔥 <b>Nouveau Produit Winner TikTok !</b>\n\n"
                    f"📌 <b>Produit / Titre :</b> {ad_title}\n"
                    f"🏢 <b>Annonceur :</b> {brand_name}\n"
                    f"🔗 <b>Lien :</b> {ad_url}\n\n"
                    f"🇩🇿 <i>Cible : Algérie</i>"
                )

                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message, cover_image)
                count += 1

        print(f"[SUCCESS] {count} produits envoyés sur Telegram avec succès.")

    except Exception as e:
        print(f"[ERROR] Une erreur est survenue pendant le traitement TikTok : {e}")


if __name__ == "__main__":
    run_tiktok_scraper()
