import json
import os
import random
import time
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def get_high_potential_products():
  """Grande liste de produits e-commerce avec photos de référence pour le marché algérien"""
  return [
      {
          "name": "Mini Aspirateur Sans Fil Portable (Voiture/Maison)",
          "niche": "Auto & Maison",
          "duration": "14 jours",
          "likes": "12 500 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=600"
          ),
      },
      {
          "name": "Pistolet de Massage Musculaire Pro",
          "niche": "Bien-être & Sport",
          "duration": "21 jours",
          "likes": "18 300 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=600"
          ),
      },
      {
          "name": "Support Téléphone Magnétique MagSafe avec Chargeur",
          "niche": "Accessoires Téléphone & Auto",
          "duration": "10 jours",
          "likes": "9 400 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600"
          ),
      },
      {
          "name": "Correcteur de Posture Intelligent à Capteur",
          "niche": "Santé & Gadgets",
          "duration": "30 jours",
          "likes": "25 000 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600"
          ),
      },
      {
          "name": "Diffuseur d'Huiles Essentielles Effet Flamme 3D",
          "niche": "Déco & Ambiance",
          "duration": "12 jours",
          "likes": "14 200 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=600"
          ),
      },
      {
          "name": "Gourde Motivante Dégradée avec Marqueur de Temps (2L)",
          "niche": "Fitness & Lifestyle",
          "duration": "45 jours",
          "likes": "31 000 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600"
          ),
      },
      {
          "name": "Épilateur à Lumière Pulsée (IPL) Maison",
          "niche": "Beauté & Soin",
          "duration": "25 jours",
          "likes": "19 800 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600"
          ),
      },
      {
          "name": "Mini Imprimante Thermique Bluetooth (Étiquettes Colis)",
          "niche": "E-commerce & Pro",
          "duration": "18 jours",
          "likes": "11 500 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1612815154858-60aa4c59eaa6?w=600"
          ),
      },
      {
          "name": "Correcteur de Posture pour Dos et Épaules Réglable",
          "niche": "Santé & Bien-être",
          "duration": "15 jours",
          "likes": "8 900 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600"
          ),
      },
      {
          "name": "Lampe Bureau LED Tactile avec Chargeur Sans Fil",
          "niche": "Bureau & High-Tech",
          "duration": "11 jours",
          "likes": "10 200 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=600"
          ),
      },
      {
          "name": "Organisateur de Maquillage Rotatif à 360 Degrés",
          "niche": "Beauté & Rangement",
          "duration": "19 jours",
          "likes": "15 400 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=600"
          ),
      },
      {
          "name": "Ceinture de Sudation Amincissante Néoprène",
          "niche": "Sport & Fitness",
          "duration": "22 jours",
          "likes": "16 000 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=600"
          ),
      },
      {
          "name": "Housse de Canapé Extensible Anti-Poils",
          "niche": "Maison & Déco",
          "duration": "35 jours",
          "likes": "28 000 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600"
          ),
      },
      {
          "name": "Brosse de Nettoyage Électrique Sans Fil Multi-usages",
          "niche": "Maison & Ménage",
          "duration": "16 jours",
          "likes": "21 500 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf?w=600"
          ),
      },
      {
          "name": "Lampe Solaire Extérieure à Détecteur de Mouvement",
          "niche": "Jardin & Sécurité",
          "duration": "28 jours",
          "likes": "13 900 J'aime",
          "image": (
              "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=600"
          ),
      },
  ]


def send_telegram_photo(photo_url, caption):
  """Fonction pour envoyer une photo avec sa description sur Telegram"""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "photo": photo_url,
      "caption": caption,
      "parse_mode": "Markdown",
  }
  requests.post(url, json=payload)


def send_telegram_text(message):
  """Fonction de secours pour envoyer du texte simple"""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
  requests.post(url, json=payload)


def run_bot():
  all_products = get_high_potential_products()

  # Mélange aléatoire basé sur le temps
  random.seed(time.time())
  products = random.sample(all_products, min(10, len(all_products)))

  # En-tête global
  send_telegram_text(
      "🚀 *RAPPORT E-COMMERCE DZ* 🇩🇿\n*Sélection exclusive avec visuels : Top"
      " 10 Winner du jour*\n━━━━━━━━━━━━━━━━━━"
  )

  for idx, prod in enumerate(products, 1):
    # Description propre intégrée directement dans la légende de la photo
    msg = f"🏆 *WINNER #{idx}* — *{prod['name']}*\n\n"
    msg += f"📂 *Niche :* `{prod['niche']}`\n"
    msg += f"📊 *Statistiques Ads :*\n"
    msg += f"  • Durée de diffusion : *{prod['duration']}*\n"
    msg += f"  • Engagement min. : *{prod['likes']}*\n\n"
    msg += f"💡 *Statut :* Validé pour test marché DZ 🎯"

    # Envoi de la photo avec les détails du produit
    send_telegram_photo(prod["image"], msg)


if __name__ == "__main__":
  run_bot()
