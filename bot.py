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
    send_telegram("🤖 *Bot Winner DZ : Lancement de la recherche ciblée...*")
    
    # Mot-clé large et direct sans guillemets pour éviter le blocage Meta
    search_query = "livraison"
    
    url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=DZ&q={search_query}&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&media_type=all"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # User-Agent pour simuler un vrai navigateur PC
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(8000)
        
        # Scroll vers le bas pour forcer le chargement des cartes
        await page.evaluate("window.scrollBy(0, 1000)")
        await page.wait_for_timeout(3000)
        
        # Sélecteurs multiples pour détecter les annonces
        ads_cards = await page.query_selector_all('div[data-testid="ad_card"], div._7jvw, div[role="article"]')

        if not ads_cards:
            send_telegram("⚠️ *Aucune annonce trouvée avec ce filtre. Nouvelle tentative au prochain cycle.*")
            await browser.close()
            return

        send_telegram(f"🔥 *{len(ads_cards)} publicités actives détectées sur Meta Ads !*")
        
        winners_found = 0
        for card in ads_cards:
            try:
                text = await card.inner_text()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if not lines:
                    continue
                
                preview = " ".join(lines[:4])
                
                msg = f"📦 *PRODUIT WINNER DZ #{winners_found + 1}*\n\n"
                msg += f"📝 *Aperçu de l'offre :*\n_{preview[:180]}..._\n\n"
                msg += f"👉 [Ouvrir dans Meta Ads]({url})"
                
                send_telegram(msg)
                winners_found += 1
                
                if winners_found >= 5:
                    break
            except Exception:
                continue
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
