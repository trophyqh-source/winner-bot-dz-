import os
import sys
import logging
import requests
from apify_client import ApifyClient

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Récupération des secrets depuis les variables d'environnement
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

def verify_credentials():
    """Vérifie que tous les secrets requis sont bien configurés."""
    missing = []
    if not TELEGRAM_TOKEN:
        missing.append("TELEGRAM_TOKEN")
    if not CHAT_ID:
        missing.append("CHAT_ID")
    if not APIFY_TOKEN:
        missing.append("APIFY_TOKEN")
        
    if missing:
        logging.error(f"❌ ERREUR : Variable(s) manquante(s) dans l'environnement : {', '.join(missing)}")
        sys.exit(1)
        
    logging.info("✅ Tous les secrets (Telegram & Apify) sont détectés avec succès.")

def send_telegram_message(message: str) -> bool:
    """Envoie un message formaté en HTML via l'API Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # Emploi de HTML pour éviter les erreurs de caractères spéciaux
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        if response.status_code == 200 and result.get("ok"):
            logging.info("🚀 Message envoyé sur Telegram avec succès !")
            return True
        else:
            logging.error(f"❌ Échec de l'envoi Telegram : {result}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Erreur de connexion avec l'API Telegram : {e}")
        return False

def get_winning_products():
    """Récupère les produits gagnants via un Actor Apify."""
    logging.info("🔍 Lancement du scraping sur Apify...")
    
    client = ApifyClient(APIFY_TOKEN)
    
    # Remplacez "apify/web-scraper" par l'ID exact de l'Actor que vous utilisez sur Apify
    actor_id = "apify/web-scraper"
    
    # Adaptez `run_input` aux paramètres requis par votre Actor Apify
    run_input = {
        "maxItems": 5,
        # "search": "winning products",
    }
    
    try:
        # Exécution de l'Actor
        run = client.actor(actor_id).call(run_input=run_input)
        
        produits = []
        # Parcours du Dataset de résultats généré par Apify
        dataset_items = client.dataset(run["defaultDatasetId"]).iterate_items()
        
        for item in dataset_items:
            # Adaptez ces clés aux champs réels retournés par votre Actor Apify
            nom = item.get("title") or item.get("name") or "Produit sans nom"
            prix = item.get("price") or item.get("priceText") or "N/A"
            lien = item.get("url") or item.get("link") or "#"
            
            produits.append({
                "nom": nom,
                "prix": str(prix),
                "lien": lien
            })
            
        return produits

    except Exception as e:
        logging.error(f"❌ Erreur lors de la récupération des données Apify : {e}")
        return []

def main():
    logging.info("=== DÉMARRAGE DU BOT WINNERBOTDZ ===")
    
    # 1. Vérification des identifiants
    verify_credentials()
    
    # 2. Récupération des produits depuis Apify
    produits = get_winning_products()
    
    if not produits:
        logging.info("ℹ️ Aucun produit trouvé lors de cette exécution.")
        send_telegram_message("🔎 <b>WinnerBotDZ</b> : Exécution terminée, aucun nouveau produit détecté.")
        return

    # 3. Traitement et envoi des notifications
    logging.info(f"📦 {len(produits)} produit(s) trouvé(s). Envoi de la notification...")
    
    for prod in produits:
        msg = (
            f"🔥 <b>Nouveau Produit Winner Détecté !</b>\n\n"
            f"📌 <b>Nom</b> : {prod['nom']}\n"
            f"💰 <b>Prix</b> : {prod['prix']}\n"
            f"🔗 <a href=\"{prod['lien']}\">Voir le produit</a>"
        )
        send_telegram_message(msg)

    logging.info("=== FIN DE L'EXÉCUTION ===")

if __name__ == "__main__":
    main()
