import os
import requests

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")

def test_apify():
    print(f"--- TEST APIFY ---")
    if not APIFY_TOKEN:
        print("❌ ERREUR: APIFY_TOKEN est introuvable !")
        return

    url = f"https://api.apify.com/v2/acts/curious_coder~facebook-ads-library-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    payload = {
        "searchTerms": ["livraison 58 wilayas"],
        "countryCode": "DZ",
        "limit": 5
    }

    try:
        print("Envoi de la requête à Apify...")
        res = requests.post(url, json=payload, timeout=120)
        print(f"Statut HTTP : {res.status_code}")
        
        data = res.json()
        print("Réponse brute reçue :")
        print(data)
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")

if __name__ == "__main__":
    test_apify()
