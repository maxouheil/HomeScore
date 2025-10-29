#!/usr/bin/env python3
"""
Test simple de connexion Jinka
"""

import asyncio
from scrape_jinka import JinkaScraper

async def test_connection():
    """Test simple de connexion"""
    print("🔍 TEST DE CONNEXION JINKA")
    print("=" * 40)
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # Aller au dashboard directement
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        print(f"🌐 Navigation vers: {dashboard_url}")
        
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(5000)
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        if "sign/in" in current_url:
            print("❌ Redirection vers login - tu n'es pas connecté")
            print("💡 Connecte-toi d'abord manuellement sur Jinka")
            return False
        else:
            print("✅ Tu es connecté !")
            
            # Chercher des appartements
            apartment_links = await scraper.page.query_selector_all('a[href*="ad="], a[href*="alert_result"]')
            print(f"🏠 Appartements trouvés: {len(apartment_links)}")
            
            if apartment_links:
                print("\n📋 PREMIERS APPARTEMENTS:")
                for i, link in enumerate(apartment_links[:5], 1):
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    print(f"   {i}. {text[:50]}... -> {href}")
                return True
            else:
                print("❌ Aucun appartement trouvé")
                return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(test_connection())
