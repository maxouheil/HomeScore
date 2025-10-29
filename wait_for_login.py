#!/usr/bin/env python3
"""
Script qui ouvre Chrome et attend que tu te connectes
"""

import asyncio
from scrape_jinka import JinkaScraper

async def wait_for_login():
    """Ouvre Chrome et attend la connexion"""
    print("🔐 CONNEXION MANUELLE JINKA")
    print("=" * 50)
    print("1. Chrome va s'ouvrir")
    print("2. Connecte-toi manuellement à Google")
    print("3. Une fois connecté à Jinka, appuie sur ENTRÉE")
    print()
    
    scraper = JinkaScraper()
    
    try:
        # 1. Initialiser
        await scraper.setup()
        print("✅ Chrome ouvert")
        
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
        
        print("✅ Redirection vers Google réussie")
        print()
        print("🔐 CONNEXION MANUELLE REQUISE")
        print("=" * 40)
        print("1. Saisis ton email: souheil.medaghri@gmail.com")
        print("2. Saisis ton mot de passe: Lbooycz7")
        print("3. Complète toutes les étapes Google (2FA, etc.)")
        print("4. Attends d'être redirigé vers Jinka")
        print("5. Appuie sur ENTRÉE quand tu es sur Jinka")
        print()
        
        # Attendre que l'utilisateur se connecte
        input("Appuie sur ENTRÉE quand tu es connecté à Jinka...")
        
        # Vérifier la connexion
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        if "jinka.fr" in current_url and "sign/in" not in current_url:
            print("🎉 CONNEXION JINKA RÉUSSIE !")
            
            # Aller au dashboard
            print("\n🏠 ACCÈS AU DASHBOARD")
            print("-" * 40)
            
            dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
            await scraper.page.goto(dashboard_url)
            await scraper.page.wait_for_timeout(5000)
            
            dashboard_url_final = scraper.page.url
            print(f"📍 URL dashboard: {dashboard_url_final}")
            
            if "sign/in" not in dashboard_url_final:
                print("✅ Accès au dashboard réussi !")
                
                # Chercher des appartements
                apartment_links = await scraper.page.query_selector_all('a[href*="ad="], a[href*="alert_result"]')
                print(f"🏠 Appartements trouvés: {len(apartment_links)}")
                
                if apartment_links:
                    print("\n📋 PREMIERS APPARTEMENTS:")
                    for i, link in enumerate(apartment_links[:5], 1):
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        print(f"   {i}. {text[:50]}... -> {href}")
                    
                    print("\n🎉 PRÊT POUR LE SCRAPING !")
                    print("Lance maintenant: python run_batch_scraper.py")
                    return True
                else:
                    print("❌ Aucun appartement trouvé")
                    return False
            else:
                print("❌ Redirection vers login détectée")
                return False
        else:
            print("❌ Connexion Jinka échouée")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Chrome restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(wait_for_login())
