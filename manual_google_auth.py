#!/usr/bin/env python3
"""
Authentification Google manuelle pour Jinka
L'utilisateur peut compléter l'authentification manuellement
"""

import asyncio
from scrape_jinka import JinkaScraper

async def manual_google_auth():
    """Authentification Google avec pause manuelle"""
    print("🔐 AUTHENTIFICATION GOOGLE MANUELLE")
    print("=" * 50)
    print("Je vais ouvrir Google et tu pourras te connecter manuellement")
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
        
        # 4. Vérifier la redirection
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        if "accounts.google.com" in current_url:
            print("✅ Redirection vers Google réussie")
            print()
            print("🔐 AUTHENTIFICATION MANUELLE REQUISE")
            print("=" * 50)
            print("1. Saisis ton email: souheil.medaghri@gmail.com")
            print("2. Saisis ton mot de passe: Lbooycz7")
            print("3. Complète toutes les étapes Google (2FA, etc.)")
            print("4. Appuie sur ENTRÉE quand tu es connecté à Jinka")
            print()
            
            # Attendre que l'utilisateur se connecte manuellement
            input("Appuie sur ENTRÉE quand tu es connecté...")
            
            # Vérifier la connexion
            final_url = scraper.page.url
            print(f"📍 URL finale: {final_url}")
            
            if "jinka.fr" in final_url and "sign/in" not in final_url:
                print("🎉 CONNEXION JINKA RÉUSSIE !")
                
                # Tester l'accès au dashboard
                print("\n🏠 TEST D'ACCÈS AU DASHBOARD")
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
                        print("\n📋 LISTE DES APPARTEMENTS:")
                        for i, link in enumerate(apartment_links[:10], 1):
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            print(f"   {i}. {text[:50]}... -> {href}")
                        
                        # Prendre un screenshot
                        await scraper.page.screenshot(path="data/dashboard_connected.png")
                        print(f"\n📸 Screenshot sauvegardé: data/dashboard_connected.png")
                        
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
        else:
            print("❌ Pas de redirection vers Google")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert pour que tu puisses voir le résultat")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(manual_google_auth())
