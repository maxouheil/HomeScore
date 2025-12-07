#!/usr/bin/env python3
"""
Test de l'extraction des photos depuis la div galerie spécifique
"""

import asyncio
from scrape_jinka import JinkaScraper

async def test_gallery_photos():
    """Test l'extraction des photos depuis la div galerie"""
    print("🖼️ TEST EXTRACTION PHOTOS GALERIE")
    print("=" * 50)
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        
        # URL d'un appartement test
        test_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
        
        print(f"🏠 Test avec: {test_url}")
        
        # Naviguer vers la page
        await scraper.page.goto(test_url)
        await scraper.page.wait_for_timeout(3000)
        
        # Extraire les photos
        photos = await scraper.extract_photos()
        
        print(f"\n📸 RÉSULTATS:")
        print(f"   Total photos trouvées: {len(photos)}")
        
        for i, photo in enumerate(photos):
            print(f"   {i+1}. {photo['url'][:80]}...")
            print(f"      Alt: {photo.get('alt', 'N/A')}")
            print(f"      Selector: {photo.get('selector', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(test_gallery_photos())
