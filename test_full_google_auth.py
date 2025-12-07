#!/usr/bin/env python3
"""
Test complet de l'authentification Google avec Jinka
"""

import asyncio
import os
from scrape_jinka import JinkaScraper

async def test_full_google_auth():
    """Test complet de l'authentification Google"""
    print("🔐 TEST COMPLET AUTHENTIFICATION GOOGLE")
    print("=" * 60)
    
    scraper = JinkaScraper()
    
    try:
        # 1. Initialiser
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # 2. Aller à la page de connexion
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
        
        # 4. Vérifier la redirection vers Google
        current_url = scraper.page.url
        print(f"📍 URL après clic: {current_url}")
        
        if "accounts.google.com" not in current_url:
            print("❌ Pas de redirection vers Google")
            return False
        
        print("✅ Redirection vers Google réussie")
        
        # 5. Saisir l'email
        print("📧 Saisie de l'email...")
        await scraper.page.wait_for_timeout(3000)
        
        email_input = await scraper.page.query_selector('input[type="email"], input[name="identifier"]')
        if not email_input:
            print("❌ Champ email non trouvé")
            return False
        
        await email_input.fill("souheil.medaghri@gmail.com")
        print("✅ Email saisi")
        
        # 6. Cliquer sur Suivant
        print("➡️ Clic sur Suivant...")
        next_button = await scraper.page.query_selector('button:has-text("Suivant"), button:has-text("Next"), #identifierNext')
        if not next_button:
            print("❌ Bouton Suivant non trouvé")
            return False
        
        await next_button.click()
        await scraper.page.wait_for_timeout(5000)
        print("✅ Bouton Suivant cliqué")
        
        # 7. Saisir le mot de passe
        print("🔑 Saisie du mot de passe...")
        password_input = await scraper.page.query_selector('input[type="password"], input[name="password"]')
        if not password_input:
            print("❌ Champ mot de passe non trouvé")
            return False
        
        await password_input.fill("Lbooycz7")
        print("✅ Mot de passe saisi")
        
        # 8. Cliquer sur Suivant (mot de passe)
        print("➡️ Clic sur Suivant (mot de passe)...")
        next_button2 = await scraper.page.query_selector('button:has-text("Suivant"), button:has-text("Next"), #passwordNext')
        if not next_button2:
            print("❌ Bouton Suivant (mot de passe) non trouvé")
            return False
        
        await next_button2.click()
        await scraper.page.wait_for_timeout(10000)  # Attendre plus longtemps
        print("✅ Bouton Suivant (mot de passe) cliqué")
        
        # 9. Vérifier la connexion
        final_url = scraper.page.url
        print(f"📍 URL finale: {final_url}")
        
        if "jinka.fr" in final_url and "sign/in" not in final_url:
            print("🎉 CONNEXION JINKA RÉUSSIE !")
            
            # 10. Tester l'accès au dashboard
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
                    for i, link in enumerate(apartment_links[:3], 1):
                        href = await link.get_attribute('href')
                        print(f"   Appartement {i}: {href}")
                
                return True
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
        if hasattr(scraper, 'browser') and scraper.browser:
            await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(test_full_google_auth())
