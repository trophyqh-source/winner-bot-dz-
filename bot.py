import json
import os
import random
import time
import urllib.parse
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SEEN_FILE = "seen_products.json"


def get_all_products():
    """Base de données de produits"""
    return [
        {
            "id": "prod_1",
            "name": "Mini Aspirateur Sans Fil Portable (Voiture/Maison)",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "12 500",
            "comments": "1 420",
            "shares": "890",
            "saves": "3 100",
        },
        {
            "id": "prod_2",
            "name": "Pistolet de Massage Musculaire Pro",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "18 900",
            "comments": "2 150",
            "shares": "1 340",
            "saves": "4 800",
        },
        {
            "id": "prod_3",
            "name": "Support Téléphone Magnétique avec Chargeur",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "9 400",
            "comments": "860",
            "shares": "520",
            "saves": "2 100",
        },
        {
            "id": "prod_4",
            "name": "Épilateur Laser IPL Portable",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "21 300",
            "comments": "3 100",
            "shares": "1 890",
            "saves": "6 200",
        },
        {
            "id": "prod_5",
            "name": "Correcteur de Posture Ajustable Premium",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "15 800",
            "comments": "1 750",
            "shares": "1 120",
            "saves": "3 900",
        },
        {
            "id": "prod_6",
            "name": "Projecteur LED Portable HD Smart",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "24 100",
            "comments": "2 980",
            "shares": "2 100",
            "saves": "7 400",
        },
        {
            "id": "prod_7",
            "name": "Montre Connectée Fitness & Santé",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "11 200",
            "comments": "1 050",
            "shares": "670",
            "saves": "2 800",
        },
        {
            "id": "prod_8",
            "name": "Mini Imprimante Thermique Bluetooth",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "14 600",
            "comments": "1 620",
            "shares": "980",
            "saves": "3 500",
        },
        {
            "id": "prod_9",
            "name": "Nettoyeur de Pores Visage à Aspiration",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "8 700",
            "comments": "790",
            "shares": "430",
            "saves": "1 950",
        },
        {
            "id": "prod_10",
            "name": "Lampe Bureau LED Tactile avec Chargeur Sans Fil",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "10 200",
            "comments": "940",
            "shares": "610",
            "saves": "2 400",
        },
        {
            "id": "prod_11",
            "name": "Écouteurs Sans Fil Réduction de Bruit Active",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "19 400",
            "comments": "2 300",
            "shares": "1 450",
            "saves": "5 100",
        },
        {
            "id": "prod_12",
            "name": "Ceinture de Massage Abdominal Chauffante",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "13 100",
            "comments": "1 280",
            "shares": "810",
            "saves": "3 200",
        },
        {
            "id": "prod_13",
            "name": "Diffuseur d'Huiles Essentielles Ultra-silencieux",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "16 500",
            "comments": "1 840",
            "shares": "1 150",
            "saves": "4 100",
        },
        {
            "id": "prod_14",
            "name": "Gourde Isotherme Intelligente Température",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "7 900",
            "comments": "680",
            "shares": "390",
            "saves": "1 800",
        },
        {
            "id": "prod_15",
            "name": "Lampe Solaire d'Extérieur avec Détecteur",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "13 900",
            "comments": "1 350",
            "shares": "870",
            "saves": "3 300",
        },
        {
            "id": "prod_16",
            "name": "Kit de Réparation Rayures Carrosserie Auto",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "17 200",
            "comments": "1 910",
            "shares": "1 230",
            "saves": "4 400",
        },
        {
            "id": "prod_17",
            "name": "Mixeur Portable USB Multifonction",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "22 100",
            "comments": "2 740",
            "shares": "1 920",
            "saves": "5 900",
        },
        {
            "id": "prod_18",
            "name": "Tondeuse de Précision Barbe et Cheveux",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "11 800",
            "comments": "1 120",
            "shares": "740",
            "saves": "2 900",
        },
        {
            "id": "prod_19",
            "name": "Tapis Anti-dérapant Absorbant Salle de Bain",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "9 800",
            "comments": "890",
            "shares": "510",
            "saves": "2 200",
        },
        {
            "id": "prod_20",
            "name": "Organisateur de Rangement Pliable Dressing",
            "status": "En forte croissance (> 7 jours de pub)",
            "likes": "14 100",
            "comments": "1 480",
            "shares": "930",
            "saves": "3 600",
        },
    ]


def load_seen_ids():
    """Lit l'historique depuis le fichier local"""
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_seen_ids(seen_list):
    """Enregistre l'historique dans le fichier local"""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen_list, f, ensure_ascii=False, indent=2)


def send_telegram(text):
    """Envoie un message textuel à Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    requests.post(url, json=payload)


def run_bot():
    all_prods = get_all_products()
    seen_ids = load_seen_ids()

    # On ne prend QUE les produits qui n'ont jamais été envoyés
    unseen = [p for p in all_prods if p["id"] not in seen_ids]

    # Si tous les produits ont été envoyés, on réinitialise pour refaire un cycle complet
    if len(unseen) < 5:
        seen_ids = []
        unseen = all_prods

    # Sélection des 5 prochains produits DANS L'ORDRE exact
    selected = unseen[:5]

    send_telegram("🤖 <b>Bot Winner DZ : Analyse des tendances en cours...</b>")
    time.sleep(1)
    send_telegram("🔥 <b>Top 5 Produits Gagnants Détectés</b> 🔥")
    time.sleep(1)

    new_seen = []
    for idx, item in enumerate(selected, 1):
        query_encoded = urllib.parse.quote(item["name"])
        ali_link = f"https://www.aliexpress.com/wholesale?SearchText={query_encoded}"
        tiktok_link = f"https://www.tiktok.com/search?q={query_encoded}"
        img_link = f"https://www.google.com/search?tbm=isch&q={query_encoded}"

        msg = f"🏆 <b>PRODUIT WINNER DZ #{idx}</b>\n\n"
        msg += f"📦 <b>Nom :</b> {item['name']}\n"
        msg += f"📈 <b>Statut :</b> {item['status']}\n\n"
        msg += f"📊 <b>Engagement social :</b>\n"
        msg += f"• 👍 {item['likes']} J'aime\n"
        msg += f"• 💬 {item['comments']} Commentaires\n"
        msg += f"• 🔁 {item['shares']} Partages\n"
        msg += f"• 🔖 {item['saves']} Enregistrements\n\n"
        msg += f"🔍 <b>Recherche rapide en 1 clic :</b>\n"
        msg += f'• 🛍️ <a href="{ali_link}">Voir les modèles sur AliExpress</a>\n'
        msg += f'• 🎵 <a href="{tiktok_link}">Voir les vidéos sur TikTok</a>\n'
        msg += f'• 🖼️ <a href="{img_link}">Voir les photos sur Google Images</a>\n\n'
        msg += f"🚀 <i>Prêt pour le test e-commerce !</i>"

        send_telegram(msg)
        new_seen.append(item["id"])
        time.sleep(1)

    # Sauvegarde locale
    save_seen_ids(seen_ids + new_seen)


if __name__ == "__main__":
    run_bot()
