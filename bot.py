import os
import requests

# Récupération des secrets GitHub
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise ValueError("Variables d'environnement TELEGRAM manquantes dans GitHub Secrets !")

def test_telegram_connection():
    print("[INFO] Test de connexion à Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🤖 <b>Test de connexion réussi !</b>\nLe bot Telegram fonctionne parfaitement.",
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"[STATUS CODE] {response.status_code}")
        print(f"[REPONSE TELEGRAM] {response.text}")
        response.raise_for_status()
        print("[SUCCESS] Le message de test a été envoyé sur Telegram !")
    except Exception as e:
        print(f"[ERROR] Échec d'envoi Telegram : {e}")

if __name__ == "__main__":
    test_telegram_connection()
