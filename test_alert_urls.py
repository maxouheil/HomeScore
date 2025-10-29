#!/usr/bin/env python3
"""
Test de différentes URLs d'alertes Jinka
"""

import asyncio
from scrape_jinka import JinkaScraper

async def test_alert_urls():
    """Test différentes URLs d'alertes"""
    print("🔍 TEST DES URLS D'ALERTES JINKA")
    print("=" * 50)
    
    # URLs à tester
    test_urls = [
        "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&filter=all",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&from_alert_filter=all",
    ]
    
    scraper = JinkaScraper()
    
    try:
        # 1. Initialiser et se connecter
        await scraper.setup()
        if not await scraper.login():
            print("❌ Échec de connexion")
            return
        
        print("✅ Connexion réussie")
        
        # 2. Tester chaque URL
        for i, url in enumerate(test_urls, 1):
            print(f"\n🌐 TEST URL {i}: {url}")
            print("-" * 60)
            
            try:
                await scraper.page.goto(url)
                await scraper.page.wait_for_timeout(3000)
                
                # Vérifier l'URL actuelle
                current_url = scraper.page.url
                print(f"📍 URL actuelle: {current_url}")
                
                # Chercher des appartements
                apartment_links = await scraper.page.query_selector_all('a[href*="ad="], a[href*="alert_result"]')
                print(f"🔗 Liens d'appartements: {len(apartment_links)}")
                
                if apartment_links:
                    for j, link in enumerate(apartment_links[:3], 1):
                        href = await link.get_attribute('href')
                        print(f"   Appartement {j}: {href}")
                
                # Chercher des cartes d'appartements
                apartment_cards = await scraper.page.query_selector_all('[data-testid*="apartment"], .apartment-card, .property-card, a.sc-bdVaJa')
                print(f"🏠 Cartes d'appartements: {len(apartment_cards)}")
                
                # Prendre un screenshot
                screenshot_path = f"data/test_url_{i}.png"
                await scraper.page.screenshot(path=screenshot_path)
                print(f"📸 Screenshot: {screenshot_path}")
                
                # Essayer de scraper
                apartments = await scraper.scrape_alert_page(url)
                if apartments:
                    print(f"✅ {len(apartments)} appartements scrapés")
                    for j, apt in enumerate(apartments[:2], 1):
                        print(f"   Appartement {j}: {apt}")
                else:
                    print("❌ Aucun appartement scrapé")
                
            except Exception as e:
                print(f"❌ Erreur avec URL {i}: {e}")
            
            print()
        
    except Exception as e:
        print(f"❌ Erreur globale: {e}")
    finally:
        if hasattr(scraper, 'browser') and scraper.browser:
            await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(test_alert_urls())
