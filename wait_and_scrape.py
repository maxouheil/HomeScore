#!/usr/bin/env python3
"""
Script qui attend que tu sois connecté puis lance le scraping
"""

import asyncio
import time
from scrape_jinka import JinkaScraper

async def wait_and_scrape():
    """Attend la connexion puis lance le scraping"""
    print("⏳ ATTENTE DE CONNEXION + SCRAPING AUTOMATIQUE")
    print("=" * 60)
    print("1. Connecte-toi manuellement à Google dans le navigateur")
    print("2. Une fois connecté à Jinka, le scraping se lancera automatiquement")
    print()
    
    scraper = JinkaScraper()
    
    try:
        # 1. Initialiser
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # 2. Aller à Jinka
        print("🌐 Navigation vers Jinka...")
        await scraper.page.goto("https://www.jinka.fr/sign/in")
        await scraper.page.wait_for_timeout(3000)
        
        # 3. Cliquer sur Google
        print("🔍 Recherche du bouton Google...")
        google_button = await scraper.page.query_selector('button:has-text("Continuer avec Google")')
        if not google_button:
            print("❌ Bouton Google non trouvé")
            return False
        
        print("🖱️ Clic sur Google...")
        await google_button.click()
        await scraper.page.wait_for_timeout(5000)
        
        # 4. Attendre que tu te connectes manuellement
        print("🔐 CONNEXION MANUELLE REQUISE")
        print("=" * 40)
        print("Connecte-toi manuellement à Google dans le navigateur")
        print("Le script attendra que tu sois connecté à Jinka...")
        print()
        
        # Attendre la connexion (vérifier toutes les 5 secondes)
        max_wait = 300  # 5 minutes max
        wait_time = 0
        
        while wait_time < max_wait:
            current_url = scraper.page.url
            print(f"⏳ Attente... ({wait_time}s) - URL: {current_url[:80]}...")
            
            # Vérifier si on est connecté à Jinka
            if "jinka.fr" in current_url and "sign/in" not in current_url:
                print("🎉 CONNEXION JINKA DÉTECTÉE !")
                break
            
            await scraper.page.wait_for_timeout(5000)
            wait_time += 5
        
        if wait_time >= max_wait:
            print("⏰ Timeout - connexion non détectée")
            return False
        
        # 5. Aller au dashboard
        print("\n🏠 ACCÈS AU DASHBOARD")
        print("-" * 40)
        
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(5000)
        
        dashboard_url_final = scraper.page.url
        print(f"📍 URL dashboard: {dashboard_url_final}")
        
        if "sign/in" in dashboard_url_final:
            print("❌ Redirection vers login détectée")
            return False
        
        print("✅ Accès au dashboard réussi !")
        
        # 6. Chercher des appartements
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
        
        if not unique_apartments:
            print("❌ Aucun appartement trouvé")
            return False
        
        print("\n📋 LISTE DES APPARTEMENTS:")
        for i, apt in enumerate(unique_apartments[:10], 1):
            print(f"   {i}. {apt}")
        
        # 7. Scraper les appartements
        print(f"\n🏠 SCRAPING DE {min(10, len(unique_apartments))} APPARTEMENTS")
        print("-" * 50)
        
        scraped_count = 0
        for i, apt_url in enumerate(unique_apartments[:10], 1):  # Limiter à 10 pour le test
            print(f"\n🏠 Appartement {i}/{min(10, len(unique_apartments))}")
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
        
        print(f"\n📊 RÉSULTATS FINAUX:")
        print(f"   Appartements trouvés: {len(unique_apartments)}")
        print(f"   Appartements scrapés: {scraped_count}")
        
        if scraped_count > 0:
            print("🎉 SCRAPING RÉUSSI !")
            return True
        else:
            print("❌ Aucun appartement n'a pu être scrapé")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(wait_and_scrape())
