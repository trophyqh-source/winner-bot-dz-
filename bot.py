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
    send_telegram("🤖 *Bot Winner DZ : Analyse approfondie avec mots-clés XXL...*")
    
    # Mots-clés élargis au maximum pour le e-commerce DZ
    keywords = [
        "prix choc", "livraison gratuite", "58 wilayas", 
        "paiement a la livraison", "promotion", "offre speciale", 
        "commander maintenant", "stock limite", "meilleur prix"
    ]
    search_query = " OR ".join([f'"{kw}"' for kw in keywords])
    
    url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=DZ&q={search_query}&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&media_type=all"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(7000)
        
        # Sélecteur CSS principal + secours
        ads_cards = await page.query_selector_all('div[data-testid="ad_card"]')
        if not ads_cards:
            ads_cards = await page.query_selector_all('div._7jvw, div[role="article"]')

        send_telegram(f"🔥 *{len(ads_cards)} publicités ciblées détectées sur Meta Ads !*")
        
        winners_found = 0
        for idx, card in enumerate(ads_cards[:12]):
            try:
                text = await card.inner_text()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                preview = " ".join(lines[:3]) if lines else "Produit détecté"
                
                msg = f"📦 *PRODUIT WINNER DZ #{winners_found + 1}*\n\n"
                msg += f"📝 *Aperçu de l'offre :*\n_{preview[:160]}..._\n\n"
                msg += f"👉 [Ouvrir la bibliothèque d'annonces]({url})"
                
                send_telegram(msg)
                winners_found += 1
                
                if winners_found >= 5: # Top 5 envoyé sur Telegram
                    break
            except Exception as e:
                continue
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
