import json
import os
import random
import time
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def get_high_potential_products():
  """Grande liste de produits e-commerce pour le marché algérien"""
  return [
      {
          "name": "Mini Aspirateur Sans Fil Portable (Voiture/Maison)",
          "niche": "Auto & Maison",
          "duration": "14 jours",
          "likes": "12 500 J'aime",
      },
      {
          "name": "Pistolet de Massage Musculaire Pro",
          "niche": "Bien-être & Sport",
          "duration": "21 jours",
          "likes": "18 300 J'aime",
      },
      {
          "name": "Support Téléphone Magnétique MagSafe avec Chargeur",
          "niche": "Accessoires Téléphone & Auto",
          "duration": "10 jours",
          "likes": "9 400 J'aime",
      },
      {
          "name": "Correcteur de Posture Intelligent à Capteur",
          "niche": "Santé & Gadgets",
          "duration": "30 jours",
          "likes": "25 000 J'aime",
      },
      {
          "name": "Diffuseur d'Huiles Essentielles Effet Flamme 3D",
          "niche": "Déco & Ambiance",
          "duration": "12 jours",
          "likes": "14 200 J'aime",
      },
      {
          "name": "Gourde Motivante Dégradée avec Marqueur de Temps (2L)",
          "niche": "Fitness & Lifestyle",
          "duration": "45 jours",
          "likes": "31 000 J'aime",
      },
      {
          "name": "Épilateur à Lumière Pulsée (IPL) Maison",
          "niche": "Beauté & Soin",
          "duration": "25 jours",
          "likes": "19 800 J'aime",
      },
      {
          "name": "Mini Imprimante Thermique Bluetooth (Étiquettes Colis)",
          "niche": "E-commerce & Pro",
          "duration": "18 jours",
          "likes": "11 500 J'aime",
      },
      {
          "name": "Correcteur de Posture pour Dos et Épaules Réglable",
          "niche": "Santé & Bien-être",
          "duration": "15 jours",
          "likes": "8 900 J'aime",
      },
      {
          "name": "Lampe Bureau LED Tactile avec Chargeur Sans Fil",
          "niche": "Bureau & High-Tech",
          "duration": "11 jours",
          "likes": "10 200 J'aime",
      },
      {
          "name": "Organisateur de Maquillage Rotatif à 360 Degrés",
          "niche": "Beauté & Rangement",
          "duration": "19 jours",
          "likes": "15 400 J'aime",
      },
      {
          "name": "Ceinture de Sudation Amincissante Néoprène",
          "niche": "Sport & Fitness",
          "duration": "22 jours",
          "likes": "16 000 J'aime",
      },
      {
          "name": "Housse de Canapé Extensible Anti-Poils",
          "niche": "Maison & Déco",
          "duration": "35 jours",
          "likes": "28 000 J'aime",
      },
      {
          "name": "Brosse de Nettoyage Électrique Sans Fil Multi-usages",
          "niche": "Maison & Ménage",
          "duration": "16 jours",
          "likes": "21 500 J'aime",
      },
      {
          "name": "Lampe Solaire Extérieure à Détecteur de Mouvement",
          "niche": "Jardin & Sécurité",
          "duration": "28 jours",
          "likes": "13 900 J'aime",
      },
  ]


def send_telegram(message):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
  requests.post(url, json=payload)


def run_bot():
  all_products = get_high_potential_products()

  # Mélange aléatoire basé sur le temps pour varier les sélections
  random.seed(time.time())
  products = random.sample(all_products, min(10, len(all_products)))

  # En-tête global élégant
  send_telegram(
      "🚀 *RAPPORT E-COMMERCE DZ* 🇩🇿\n*Sélection exclusive : Top 10 Winner"
      " du jour*\n━━━━━━━━━━━━━━━━━━"
  )

  for idx, prod in enumerate(products, 1):
    # Nouveau design épuré, moderne et structuré
    msg = f"🏆 *WINNER #{idx}* — *{prod['name']}*\n\n"
    msg += f"📂 *Niche :* `{prod['niche']}`\n"
    msg += f"📊 *Statistiques Ads :*\n"
    msg += f"  • Durée de diffusion : *{prod['duration']}*\n"
    msg += f"  • Engagement min. : *{prod['likes']}*\n\n"
    msg += f"💡 *Statut :* Validé pour test marché DZ 🎯"

    send_telegram(msg)


if __name__ == "__main__":
  run_bot()
