import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def run_bot():
    send_telegram("🤖 *Bot Winner DZ : Analyse des tendances en cours...*")

    # Simulation de produits gagnants détectés
    products = [
        "Mini Aspirateur Sans Fil Portable (Voiture/Maison)",
        "Pistolet de Massage Musculaire Pro",
        "Support Téléphone Magnétique avec Chargeur"
    ]

    send_telegram("🔥 *Top Produits Gagnants Détectés (Mode Simulation)* 🔥")

    for idx, prod in enumerate(products, 1):
        msg = f"🏆 *PRODUIT WINNER DZ #{idx}*\n\n"
        msg += f"📦 *Nom :* {prod}\n"
        msg += f"📈 *Statut :* En forte croissance (> 7 jours de pub)\n\n"
        msg += "🚀 _Prêt pour le test e-commerce !_"
        send_telegram(msg)

if __name__ == "__main__":
    run_bot()
