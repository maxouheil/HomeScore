#!/usr/bin/env python3
"""
Test de l'extraction des stations de métro
"""

import asyncio
from scrape_jinka import JinkaScraper

async def test_metro_extraction():
    """Test l'extraction des stations de métro"""
    print("🚇 TEST EXTRACTION STATIONS DE MÉTRO")
    print("=" * 50)
    
    # URL d'un appartement avec des stations visibles
    test_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=78267327&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # Naviguer vers l'appartement
        await scraper.page.goto(test_url)
        await scraper.page.wait_for_timeout(3000)
        print("✅ Page chargée")
        
        # Tester l'extraction des transports
        print("\n🚇 EXTRACTION DES STATIONS DE MÉTRO")
        print("-" * 40)
        
        transports = await scraper.extract_transports()
        print(f"Stations trouvées: {len(transports)}")
        for i, station in enumerate(transports, 1):
            print(f"  {i}. {station}")
        
        # Tester l'extraction de localisation avec fallback
        print("\n📍 EXTRACTION DE LOCALISATION")
        print("-" * 40)
        
        localisation = await scraper.extract_localisation()
        print(f"Localisation: {localisation}")
        
        print("\n✅ Test terminé")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(test_metro_extraction())
