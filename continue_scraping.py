#!/usr/bin/env python3
"""
Continue le scraping une fois connecté à Jinka
"""

import asyncio
from scrape_jinka import JinkaScraper

async def continue_scraping():
    """Continue le scraping depuis le dashboard connecté"""
    print("🏠 CONTINUATION DU SCRAPING JINKA")
    print("=" * 50)
    print("Assure-toi d'être connecté à Jinka dans le navigateur")
    print()
    
    scraper = JinkaScraper()
    
    try:
        # 1. Initialiser
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # 2. Aller au dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        print(f"🌐 Navigation vers: {dashboard_url}")
        
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(5000)
        
        # 3. Vérifier la connexion
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        if "sign/in" in current_url:
            print("❌ Tu n'es pas connecté. Lance d'abord manual_google_auth.py")
            return False
        
        print("✅ Connexion vérifiée")
        
        # 4. Chercher des appartements
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
            print("\n📋 LISTE DES APPARTEMENTS:")
            for i, apt in enumerate(unique_apartments[:10], 1):
                print(f"   {i}. {apt}")
            
            # 5. Scraper les premiers appartements
            print(f"\n🏠 SCRAPING DES PREMIERS APPARTEMENTS")
            print("-" * 50)
            
            scraped_count = 0
            for i, apt_url in enumerate(unique_apartments[:5], 1):  # Limiter à 5 pour le test
                print(f"\n🏠 Appartement {i}/{min(5, len(unique_apartments))}")
                print(f"   URL: {apt_url}")
                
                try:
                    # Construire l'URL complète si nécessaire
                    if apt_url.startswith('/'):
                        apt_url = f"https://www.jinka.fr{apt_url}"
                    elif apt_url.startswith('loueragile://'):
                        # Extraire l'ID de l'URL loueragile
                        import re
                        match = re.search(r'ad\?id=(\d+)', apt_url)
                        if match:
                            apt_id = match.group(1)
                            apt_url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apt_id}"
                    
                    # Scraper l'appartement
                    apartment_data = await scraper.scrape_apartment_details(apt_url)
                    
                    if apartment_data:
                        print(f"   ✅ Appartement scrapé: {apartment_data.get('titre', 'N/A')}")
                        scraped_count += 1
                    else:
                        print(f"   ❌ Échec du scraping")
                        
                except Exception as e:
                    print(f"   ❌ Erreur: {e}")
            
            print(f"\n📊 RÉSULTATS:")
            print(f"   Appartements trouvés: {len(unique_apartments)}")
            print(f"   Appartements scrapés: {scraped_count}")
            
            if scraped_count > 0:
                print("🎉 SCRAPING RÉUSSI !")
                return True
            else:
                print("❌ Aucun appartement n'a pu être scrapé")
                return False
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
    asyncio.run(continue_scraping())
