import asyncio
import os
import requests
from playwright.async_api import async_playwright

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

async def run_scraper():
    send_telegram("🤖 *Bot Winner DZ : Analyse avec contournement amélioré...*")
    
    # URL de recherche Meta Ads Library
    url = "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=DZ&q=Prix%20choc&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&media_type=all"

    async with async_playwright() as p:
        # Lancement de Chromium avec options anti-détection
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Simulation d'un vrai navigateur utilisateur (User-Agent récent)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )

        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            # Défilement progressif pour charger les annonces
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await page.wait_for_timeout(2000)

            # Récupération du contenu
            ads_cards = await page.query_selector_all('div[role="article"], div[data-testid="ad_card"]')

            if not ads_cards:
                send_telegram("⚠️ *Meta a bloqué l'accès automatisé. Réessayez plus tard.*")
                await browser.close()
                return

            send_telegram(f"🔥 *{len(ads_cards)} publicités détectées sur Meta Ads !*")

            winners_found = 0
            for card in ads_cards[:5]:
                text = await card.inner_text()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                preview = " - ".join(lines[:3]) if lines else "Offre détectée"

                msg = f"🔥 *PRODUIT WINNER DZ #{winners_found + 1}*\n\n"
                msg += f"📝 *Aperçu :* {preview[:150]}...\n\n"
                msg += f"🔗 [Voir sur Meta Ads]({url})"

                send_telegram(msg)
                winners_found += 1

        except Exception as e:
            send_telegram(f"❌ *Erreur lors du traitement :* {str(e)[:100]}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
