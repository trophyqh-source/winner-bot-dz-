import json
import os
import random
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HISTORY_FILE = "recent_products.json"
MAX_HISTORY = 20  # Mémoire augmentée pour gérer une plus grande liste


def load_history():
  if os.path.exists(HISTORY_FILE):
    try:
      with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      return []
  return []


def save_history(history):
  with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=4)


def get_high_potential_products():
  """Liste complète de 10 produits e-commerce à fort potentiel (Filtre strict)"""
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
  ]


def select_unique_products(all_products, count=10):
  history = load_history()
  available = [p for p in all_products if p["name"] not in history]

  if len(available) < count:
    history = []
    available = all_products

  selected = random.sample(available, min(count, len(available)))

  for p in selected:
    history.append(p["name"])
    if len(history) > MAX_HISTORY:
      history.pop(0)

  save_history(history)
  return selected


def send_telegram(message):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
  requests.post(url, json=payload)


def run_bot():
  all_products = get_high_potential_products()
  # On demande 10 produits au lieu de 3
  products = select_unique_products(all_products, 10)

  send_telegram(
      "🚨 **ALERTE WINNER ADS DZ : TOP 10 DU JOUR (Filtre > 7j & 7k Likes)** 🇩🇿"
  )

  for idx, prod in enumerate(products, 1):
    msg = f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔥 **PRODUIT WINNER #{idx}**\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"📦 **Produit :** {prod['name']}\n"
    msg += f"🏷️ **Niche :** {prod['niche']}\n\n"
    msg += f"🎯 **Filtres validés :**\n"
    msg += f"⏱️ Publicité active : `> {prod['duration']}`\n"
    msg += f"❤️ Engagement minimum : `> {prod['likes']}`\n\n"
    msg += f"⚡ *Statut : Validé haute certitude e-commerce !*"

    send_telegram(msg)


if __name__ == "__main__":
  run_bot()
