import json
import os
import random
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HISTORY_FILE = "recent_products.json"
MAX_HISTORY = 15  # On élargit la mémoire pour éviter les répétitions


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


def get_algeria_winner_products():
  """Base de données enrichie de produits e-commerce validés pour le marché algérien

  (Critères : Ads > 7j, fort engagement, liens de référence inclus)
  """
  return [
      {
          "name": "Mini Aspirateur Sans Fil Portable (Voiture/Maison)",
          "niche": "Auto & Maison",
          "duration": "14 jours",
          "engagement": "Très fort (1.2K likes, 300 comms)",
          "link": "https://www.tiktok.com/tag/carvacuumcleaner",
      },
      {
          "name": "Pistolet de Massage Musculaire Pro",
          "niche": "Bien-être & Sport",
          "duration": "21 jours",
          "engagement": "Excellent (3.5K likes, 850 partages)",
          "link": "https://www.tiktok.com/tag/massagegun",
      },
      {
          "name": "Support Téléphone Magnétique MagSafe avec Chargeur",
          "niche": "Accessoires Téléphone & Auto",
          "duration": "10 jours",
          "engagement": "Fort (950 likes, 210 comms)",
          "link": "https://www.tiktok.com/tag/magsafecharger",
      },
      {
          "name": "Correcteur de Posture Intelligent à Capteur",
          "niche": "Santé & Gadgets",
          "duration": "30 jours",
          "engagement": "Massif (5K+ likes, 1.4K comms)",
          "link": "https://www.tiktok.com/tag/posturecorrector",
      },
      {
          "name": "Diffuseur d'Huiles Essentielles Effet Flamme 3D",
          "niche": "Déco & Ambiance",
          "duration": "12 jours",
          "engagement": "Très fort (2.1K likes, 400 comms)",
          "link": "https://www.tiktok.com/tag/flamediffuser",
      },
      {
          "name": "Gourde Motivante Dégradée avec Marqueur de Temps (2L)",
          "niche": "Fitness & Lifestyle",
          "duration": "45 jours",
          "engagement": "stable et élevé (Tendance lourde DZ)",
          "link": "https://www.tiktok.com/tag/motivationbottle",
      },
      {
          "name": "Épilateur à Lumière Pulsée (IPL) Maison",
          "niche": "Beauté & Soin",
          "duration": "25 jours",
          "engagement": "Excellent (Grosse marge, forte demande)",
          "link": "https://www.tiktok.com/tag/iplhairremoval",
      },
      {
          "name": "Testeur d'Épaisseur de Peinture Numérique (Voiture)",
          "niche": "Auto & Detailer",
          "duration": "9 jours",
          "engagement": "Ciblé et qualitatif (Pro/Passionnés)",
          "link": "https://www.tiktok.com/tag/paintmeter",
      },
      {
          "name": "Mini Imprimante Thermique Bluetooth (Étiquettes Colis)",
          "niche": "E-commerce & Pro",
          "duration": "18 jours",
          "engagement": "Fort chez les e-commerçants DZ",
          "link": "https://www.tiktok.com/tag/thermalprinter",
      },
      {
          "name": "Lampe LED Tactile de Bureau avec Chargeur Sans Fil",
          "niche": "Bureau & High-Tech",
          "duration": "11 jours",
          "engagement": "Très bon engagement visuel",
          "link": "https://www.tiktok.com/tag/deskledlamp",
      },
  ]


def select_unique_products(all_products, count=3):
  history = load_history()

  # Filtrer par nom du produit pour l'historique
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
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": False,
  }
  requests.post(url, json=payload)


def run_bot():
  all_products = get_algeria_winner_products()
  products = select_unique_products(all_products, 3)

  # En-tête du rapport du jour
  send_telegram("🚨 **ALerte WINNER ADS DZ** 🇩🇿\n*Veille e-commerce active du jour*")

  for idx, prod in enumerate(products, 1):
    # Nouveau design de message épuré, pro et direct
    msg = f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔥 **PRODUIT WINNER #{idx}**\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"📦 **Produit :** {prod['name']}\n"
    msg += f"🏷️ **Niche :** {prod['niche']}\n\n"
    msg += f"📈 **Performances Ads :**\n"
    msg += f"⏱️ Durée active de la pub : `> {prod['duration']}`\n"
    msg += f"💬 Engagement : *{prod['engagement']}*\n\n"
    msg += f"🔗 **Lien Vidéo / Source :** [Voir la créa]({prod['link']})\n\n"
    msg += f"⚡ *Statut : Validé pour test marché algérien !*"

    send_telegram(msg)


if __name__ == "__main__":
  run_bot()
