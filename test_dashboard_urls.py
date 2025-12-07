#!/usr/bin/env python3
"""
Test de différentes URLs de dashboard
"""

import asyncio
from scrape_jinka import JinkaScraper

async def test_dashboard_urls():
    """Test différentes URLs de dashboard"""
    print("🏠 TEST DIFFÉRENTES URLs DASHBOARD")
    print("=" * 50)
    
    # URLs à tester
    test_urls = [
        "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&filter=all",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&page=1",
    ]
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Chrome ouvert")
        
        for i, url in enumerate(test_urls, 1):
            print(f"\n🌐 TEST URL {i}: {url}")
            print("-" * 60)
            
            try:
                await scraper.page.goto(url)
                await scraper.page.wait_for_timeout(5000)
                
                current_url = scraper.page.url
                print(f"📍 URL actuelle: {current_url}")
                
                if "sign/in" in current_url:
                    print("❌ Redirection vers login")
                    continue
                
                print("✅ Accès réussi !")
                
                # Chercher des appartements
                apartment_links = await scraper.page.query_selector_all('a[href*="ad="], a[href*="alert_result"]')
                print(f"🏠 Appartements trouvés: {len(apartment_links)}")
                
                if apartment_links:
                    print("\n📋 PREMIERS APPARTEMENTS:")
                    for j, link in enumerate(apartment_links[:5], 1):
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        print(f"   {j}. {text[:50]}... -> {href}")
                    
                    # Prendre un screenshot
                    await scraper.page.screenshot(path=f"data/dashboard_test_{i}.png")
                    print(f"📸 Screenshot: data/dashboard_test_{i}.png")
                    
                    print(f"\n🎉 SUCCÈS AVEC URL {i} !")
                    return True
                else:
                    print("❌ Aucun appartement trouvé")
                    
            except Exception as e:
                print(f"❌ Erreur avec URL {i}: {e}")
        
        print("\n❌ Aucune URL n'a fonctionné")
        return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(test_dashboard_urls())
