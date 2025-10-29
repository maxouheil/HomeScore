#!/usr/bin/env python3
"""
Test avec une URL spécifique
"""

import asyncio
from scrape_jinka import JinkaScraper

async def test_specific_url():
    """Test avec une URL spécifique"""
    print("🏠 TEST AVEC URL SPÉCIFIQUE")
    print("=" * 40)
    print("Donne-moi l'URL de ton dashboard connecté")
    print()
    
    # URL par défaut
    dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
    
    print(f"🌐 Test avec l'URL: {dashboard_url}")
    print("Si tu as une autre URL, modifie-la dans le script")
    print()
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Chrome ouvert")
        
        # Aller au dashboard
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(5000)
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        if "sign/in" in current_url:
            print("❌ Redirection vers login")
            print("💡 Tu dois te connecter dans ce navigateur")
            return False
        else:
            print("✅ Accès au dashboard réussi !")
            
            # Chercher des appartements
            print("\n🔍 RECHERCHE D'APPARTEMENTS")
            print("-" * 40)
            
            # Essayer différents sélecteurs
            selectors = [
                'a[href*="ad="]',
                'a[href*="alert_result"]',
                'a.sc-bdVaJa',
                '[data-testid*="apartment"]',
                '.apartment-card',
                '.property-card'
            ]
            
            all_apartments = []
            for selector in selectors:
                try:
                    elements = await scraper.page.query_selector_all(selector)
                    print(f"   Sélecteur '{selector}': {len(elements)} éléments")
                    
                    for element in elements:
                        href = await element.get_attribute('href')
                        if href and ('ad=' in href or 'alert_result' in href):
                            all_apartments.append(href)
                            
                except Exception as e:
                    print(f"   Erreur avec '{selector}': {e}")
            
            # Dédupliquer
            unique_apartments = list(set(all_apartments))
            print(f"\n🏠 Total d'appartements uniques: {len(unique_apartments)}")
            
            if unique_apartments:
                print("\n📋 PREMIERS APPARTEMENTS:")
                for i, apt in enumerate(unique_apartments[:10], 1):
                    print(f"   {i}. {apt}")
                
                # Prendre un screenshot
                await scraper.page.screenshot(path="data/dashboard_test.png")
                print(f"\n📸 Screenshot sauvegardé: data/dashboard_test.png")
                
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
    asyncio.run(test_specific_url())
