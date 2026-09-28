import json
import os
import random
import time
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GH_TOKEN = os.environ.get("GH_TOKEN")


def get_all_products():
  """Base de données élargie de produits e-commerce DZ"""
  return [
      {
          "id": "prod_1",
          "name": "Mini Aspirateur Sans Fil Portable (Voiture/Maison)",
          "niche": "Auto & Maison",
          "duration": "14 jours",
          "likes": "12 500 J'aime",
      },
      {
          "id": "prod_2",
          "name": "Pistolet de Massage Musculaire Pro",
          "niche": "Bien-être & Sport",
          "duration": "21 jours",
          "likes": "18 300 J'aime",
      },
      {
          "id": "prod_3",
          "name": "Support Téléphone Magnétique MagSafe avec Chargeur",
          "niche": "Accessoires Téléphone & Auto",
          "duration": "10 jours",
          "likes": "9 400 J'aime",
      },
      {
          "id": "prod_4",
          "name": "Correcteur de Posture Intelligent à Capteur",
          "niche": "Santé & Gadgets",
          "duration": "30 jours",
          "likes": "25 000 J'aime",
      },
      {
          "id": "prod_5",
          "name": "Diffuseur d'Huiles Essentielles Effet Flamme 3D",
          "niche": "Déco & Ambiance",
          "duration": "12 jours",
          "likes": "14 200 J'aime",
      },
      {
          "id": "prod_6",
          "name": "Gourde Motivante Dégradée avec Marqueur de Temps (2L)",
          "niche": "Fitness & Lifestyle",
          "duration": "45 jours",
          "likes": "31 000 J'aime",
      },
      {
          "id": "prod_7",
          "name": "Épilateur à Lumière Pulsée (IPL) Maison",
          "niche": "Beauté & Soin",
          "duration": "25 jours",
          "likes": "19 800 J'aime",
      },
      {
          "id": "prod_8",
          "name": "Mini Imprimante Thermique Bluetooth (Étiquettes Colis)",
          "niche": "E-commerce & Pro",
          "duration": "18 jours",
          "likes": "11 500 J'aime",
      },
      {
          "id": "prod_9",
          "name": "Correcteur de Posture pour Dos et Épaules Réglable",
          "niche": "Santé & Bien-être",
          "duration": "15 jours",
          "likes": "8 900 J'aime",
      },
      {
          "id": "prod_10",
          "name": "Lampe Bureau LED Tactile avec Chargeur Sans Fil",
          "niche": "Bureau & High-Tech",
          "duration": "11 jours",
          "likes": "10 200 J'aime",
      },
      {
          "id": "prod_11",
          "name": "Organisateur de Maquillage Rotatif 360°",
          "niche": "Beauté & Rangement",
          "duration": "19 jours",
          "likes": "15 400 J'aime",
      },
      {
          "id": "prod_12",
          "name": "Ceinture de Sudation Amincissante Néoprène",
          "niche": "Sport & Fitness",
          "duration": "22 jours",
          "likes": "16 000 J'aime",
      },
      {
          "id": "prod_13",
          "name": "Housse de Canapé Extensible Anti-Poils",
          "niche": "Maison & Déco",
          "duration": "35 jours",
          "likes": "28 000 J'aime",
      },
      {
          "id": "prod_14",
          "name": "Brosse de Nettoyage Électrique Sans Fil",
          "niche": "Maison & Ménage",
          "duration": "16 jours",
          "likes": "21 500 J'aime",
      },
      {
          "id": "prod_15",
          "name": "Lampe Solaire Extérieure à Détecteur de Mouvement",
          "niche": "Jardin & Sécurité",
          "duration": "28 jours",
          "likes": "13 900 J'aime",
      },
      {
          "id": "prod_16",
          "name": "Kit de Réparation de Bosses Auto Sans Peinture",
          "niche": "Auto & Bricolage",
          "duration": "17 jours",
          "likes": "14 800 J'aime",
      },
      {
          "name": "Mixeur Portable Rechargeable USB pour Smoothies",
          "id": "prod_17",
          "niche": "Cuisine & Sport",
          "duration": "20 jours",
          "likes": "22 100 J'aime",
      },
      {
          "id": "prod_18",
          "name": "Tondeuse de Précision Barbe et Cheveux Professionnelle",
          "niche": "Soins Homme",
          "duration": "40 jours",
          "likes": "35 000 J'aime",
      },
      {
          "id": "prod_19",
          "name": "Tapis Anti-Dérapant Absorbant pour Salle de Bain",
          "niche": "Maison & Déco",
          "duration": "13 jours",
          "likes": "9 800 J'aime",
      },
      {
          "id": "prod_20",
          "name": "Support Ordinateur Portable Ergonomique Pliable",
          "niche": "Bureau & High-Tech",
          "duration": "24 jours",
          "likes": "17 600 J'aime",
      },
  ]


def send_telegram(message):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": True,
  }
  requests.post(url, json=payload)


def run_bot():
  all_products = get_all_products()

  # Tirage aléatoire basé sur le temps exact
  random.seed(int(time.time() * 1000))
  shuffled = list(all_products)
  random.shuffle(shuffled)

  selected = shuffled[:10]

  # En-tête avec le nouveau design
  send_telegram(
      "⚡ **RAPPORT E-COMMERCE WINNERS DZ** 🇩🇿\n📌 *Sélection du"
      " Jour*\n═══════════════════════"
  )

  for idx, prod in enumerate(selected, 1):
    # Nouveau design compact, épuré et très clair
    msg = f"🟢 **PRODUIT #{idx} : {prod['name']}**\n"
    msg += f"├ 🏷️ **Niche :** `{prod['niche']}`\n"
    msg += f"├ ⏱️ **Ads Active :** `{prod['duration']}`\n"
    msg += f"└ ❤️ **Engagement :** `{prod['likes']}`\n"
    msg += f"───────────────────────"

    send_telegram(msg)


if __name__ == "__main__":
  run_bot()
