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
    send_telegram("🔍 *Bot Winner DZ en cours de recherche sur Meta Ads...*")
    
    # Recherche ciblée e-commerce Algérie
    search_query = "58 wilayas"
    url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=DZ&q={search_query}&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&media_type=all"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(5000)

        ads_cards = await page.query_selector_all('div._7jvw')
        
        send_telegram(f"🔥 *{len(ads_cards)} publicités actives détectées aujourd'hui !*")

        for idx, card in enumerate(ads_cards[:5]): # Top 5 des pubs
            try:
                text_element = await card.query_selector('div._7jvc')
                text = await text_element.inner_text() if text_element else "Produit détecté"
                
                msg = f"📦 *PRODUIT WINNER DZ #{idx+1}*\n\n"
                msg += f"📝 *Aperçu de l'offre :*\n_{text[:150]}..._\n\n"
                msg += f"👉 [Ouvrir la publicité originale]({url})"
                
                send_telegram(msg)
            except Exception as e:
                continue

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
