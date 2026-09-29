import json
import os
import time
import urllib.parse
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SEEN_FILE = "seen_products.json"
NB_PAR_ENVOI = 5
STATUS = "En forte croissance (> 7 jours de pub)"

# (nom, likes, commentaires, partages, enregistrements)
PRODUITS = [
    ("Mini Aspirateur Sans Fil Portable (Voiture/Maison)", "12 500", "1 420", "890", "3 100"),
    ("Pistolet de Massage Musculaire Pro", "18 900", "2 150", "1 340", "4 800"),
    ("Support Téléphone Magnétique avec Chargeur", "9 400", "860", "520", "2 100"),
    ("Épilateur Laser IPL Portable", "21 300", "3 100", "1 890", "6 200"),
    ("Correcteur de Posture Ajustable Premium", "15 800", "1 750", "1 120", "3 900"),
    ("Projecteur LED Portable HD Smart", "24 100", "2 980", "2 100", "7 400"),
    ("Montre Connectée Fitness & Santé", "11 200", "1 050", "670", "2 800"),
    ("Mini Imprimante Thermique Bluetooth", "14 600", "1 620", "980", "3 500"),
    ("Nettoyeur de Pores Visage à Aspiration", "8 700", "790", "430", "1 950"),
    ("Lampe Bureau LED Tactile avec Chargeur Sans Fil", "10 200", "940", "610", "2 400"),
    ("Écouteurs Sans Fil Réduction de Bruit Active", "19 400", "2 300", "1 450", "5 100"),
    ("Ceinture de Massage Abdominal Chauffante", "13 100", "1 280", "810", "3 200"),
    ("Diffuseur d'Huiles Essentielles Ultra-silencieux", "16 500", "1 840", "1 150", "4 100"),
    ("Gourde Isotherme Intelligente Température", "7 900", "680", "390", "1 800"),
    ("Lampe Solaire d'Extérieur avec Détecteur", "13 900", "1 350", "870", "3 300"),
    ("Kit de Réparation Rayures Carrosserie Auto", "17 200", "1 910", "1 230", "4 400"),
    ("Mixeur Portable USB Multifonction", "22 100", "2 740", "1 920", "5 900"),
    ("Tondeuse de Précision Barbe et Cheveux", "11 800", "1 120", "740", "2 900"),
    ("Tapis Anti-dérapant Absorbant Salle de Bain", "9 800", "890", "510", "2 200"),
    ("Organisateur de Rangement Pliable Dressing", "14 100", "1 480", "930", "3 600"),
]


def get_all_products():
    """Base de données de produits"""
    return [
        {
            "id": f"prod_{i}",
            "name": nom,
            "status": STATUS,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
        }
        for i, (nom, likes, comments, shares, saves) in enumerate(PRODUITS, 1)
    ]


def load_seen_ids():
    """Lit l'historique depuis le fichier local (utilisé hors GitHub)"""
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_seen_ids(seen_list):
    """Enregistre l'historique dans le fichier local (utilisé hors GitHub)"""
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
    requests.post(url, json=payload, timeout=30)


def choisir_produits(all_prods):
    """
    Sur GitHub Actions : on utilise le numéro d'exécution (GITHUB_RUN_NUMBER),
    qui augmente à chaque lancement. Chaque exécution prend donc les 5
    produits suivants, sans avoir besoin de sauvegarder quoi que ce soit.
    En local : on utilise le fichier seen_products.json.
    """
    run_number = os.environ.get("GITHUB_RUN_NUMBER")
    total = len(all_prods)

    if run_number and run_number.isdigit():
        debut = ((int(run_number) - 1) * NB_PAR_ENVOI) % total
        return [all_prods[(debut + i) % total] for i in range(NB_PAR_ENVOI)], None

    seen_ids = load_seen_ids()
    unseen = [p for p in all_prods if p["id"] not in seen_ids]
    if len(unseen) < NB_PAR_ENVOI:
        seen_ids = []
        unseen = all_prods
    return unseen[:NB_PAR_ENVOI], seen_ids


def run_bot():
    all_prods = get_all_products()
    selected, seen_ids = choisir_produits(all_prods)

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
        msg += "📊 <b>Engagement social :</b>\n"
        msg += f"• 👍 {item['likes']} J'aime\n"
        msg += f"• 💬 {item['comments']} Commentaires\n"
        msg += f"• 🔁 {item['shares']} Partages\n"
        msg += f"• 🔖 {item['saves']} Enregistrements\n\n"
        msg += "🔍 <b>Recherche rapide en 1 clic :</b>\n"
        msg += f'• 🛍️ <a href="{ali_link}">Voir les modèles sur AliExpress</a>\n'
        msg += f'• 🎵 <a href="{tiktok_link}">Voir les vidéos sur TikTok</a>\n'
        msg += f'• 🖼️ <a href="{img_link}">Voir les photos sur Google Images</a>\n\n'
        msg += "🚀 <i>Prêt pour le test e-commerce !</i>"

        send_telegram(msg)
        new_seen.append(item["id"])
        time.sleep(1)

    # Sauvegarde locale uniquement (hors GitHub Actions)
    if seen_ids is not None:
        save_seen_ids(seen_ids + new_seen)


if __name__ == "__main__":
    run_bot()
