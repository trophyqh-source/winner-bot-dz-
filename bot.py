import json
import os
import random
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HISTORY_FILE = "recent_products.json"
MAX_HISTORY = 6  # Nombre de produits gardés en mémoire pour éviter les doublons


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


def select_unique_products(all_products, count=3):
  history = load_history()

  # Filtrer pour exclure les produits déjà tirés récemment
  available_products = [p for p in all_products if p not in history]

  # S'il n'y a plus assez de produits disponibles, on réinitialise l'historique
  if len(available_products) < count:
    history = []
    available_products = all_products

  # Sélection aléatoire parmi les produits disponibles
  selected = random.sample(available_products, min(count, len(all_products)))

  # Mettre à jour l'historique
  for p in selected:
    history.append(p)
    if len(history) > MAX_HISTORY:
      history.pop(0)

  save_history(history)
  return selected


def send_telegram(message):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
  requests.post(url, json=payload)


def run_bot():
  send_telegram("🤖 Bot Winner DZ : Analyse des tendances en cours...")

  # Liste élargie de produits (tu pourras en rajouter autant que tu veux ici)
  all_products = [
      "Mini Aspirateur Sans Fil Portable (Voiture/Maison)",
      "Pistolet de Massage Musculaire Pro",
      "Support Téléphone Magnétique avec Chargeur",
      "Correcteur de Posture Intelligent",
      "Diffuseur d'Huiles Essentielles Effet Flamme",
      "Gourde Motivante Dégradée avec Marqueur de Temps",
      "Épilateur à Lumière Pulsée (IPL)",
      "Lampe Bureau LED Tactile avec Chargeur Sans Fil",
      "Organisateur de Siège Arrière Voiture avec Tablette",
  ]

  # Sélection de 3 produits uniques sans répétition récente
  products = select_unique_products(all_products, 3)

  send_telegram("🔥 Top Produits Gagnants Détectés (Mode Simulation) 🔥")

  for idx, prod in enumerate(products, 1):
    msg = f"🏆 PRODUIT WINNER DZ #{idx}\n\n"
    msg += f"📦 Nom : {prod}\n"
    msg += f"📈 Statut : En forte croissance (> 7 jours de pub)\n\n"
    msg += "🚀 Prêt pour le test e-commerce !"
    send_telegram(msg)


if __name__ == "__main__":
  run_bot()
