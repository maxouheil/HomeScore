#!/usr/bin/env python3
"""
Script qui détecte automatiquement la connexion
"""

import asyncio
import time
from scrape_jinka import JinkaScraper

async def auto_detect_login():
    """Détecte automatiquement la connexion"""
    print("🔍 DÉTECTION AUTOMATIQUE DE CONNEXION")
    print("=" * 50)
    print("1. Chrome va s'ouvrir")
    print("2. Connecte-toi manuellement")
    print("3. Le script détectera automatiquement quand tu es connecté")
    print()
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Chrome ouvert")
        
        # Aller au dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(3000)
        
        print("🔐 CONNEXION MANUELLE REQUISE")
        print("=" * 40)
        print("1. Connecte-toi manuellement dans le navigateur")
        print("2. Le script vérifiera toutes les 5 secondes")
        print("3. Une fois connecté, le scraping se lancera automatiquement")
        print()
        
        # Attendre la connexion (vérifier toutes les 5 secondes)
        max_wait = 300  # 5 minutes max
        wait_time = 0
        
        while wait_time < max_wait:
            current_url = scraper.page.url
            print(f"⏳ Vérification... ({wait_time}s) - URL: {current_url[:80]}...")
            
            # Vérifier si on est connecté
            if "jinka.fr" in current_url and "sign/in" not in current_url:
                print("🎉 CONNEXION DÉTECTÉE !")
                break
            
            await scraper.page.wait_for_timeout(5000)
            wait_time += 5
        
        if wait_time >= max_wait:
            print("⏰ Timeout - connexion non détectée")
            return False
        
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
            await scraper.page.screenshot(path="data/dashboard_connected.png")
            print(f"\n📸 Screenshot sauvegardé: data/dashboard_connected.png")
            
            print("\n🎉 PRÊT POUR LE SCRAPING !")
            print("Lance maintenant: python run_batch_scraper.py")
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
    asyncio.run(auto_detect_login())
