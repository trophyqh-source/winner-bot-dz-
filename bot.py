import asyncio
import os
import random
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
    send_telegram("🤖 *Bot Winner DZ : Tentative en mode furtif...*")
    
    url = "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=DZ&q=Prix%20choc&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&media_type=all"

    async with async_playwright() as p:
        # Lancement avec arguments d'évitement avancés
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security'
            ]
        )
        
        # Simulation complète d'un navigateur réel avec en-têtes
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768},
            extra_http_headers={
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Sec-Ch-Ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            }
        )

        page = await context.new_page()

        try:
            # Navigation avec pause aléatoire
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(random.randint(4000, 7000))

            # Simulation d'un comportement humain (scroll lent)
            for _ in range(4):
                await page.evaluate(f"window.scrollBy(0, {random.randint(500, 900)})")
                await page.wait_for_timeout(random.randint(1500, 3000))

            # Récupération des cartes d'annonces
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
