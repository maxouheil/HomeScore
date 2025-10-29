#!/usr/bin/env python3
"""
Authentification Google automatique pour Jinka
"""

import asyncio
import time
from scrape_jinka import JinkaScraper

async def auto_google_auth():
    """Authentification Google automatique"""
    print("🤖 AUTHENTIFICATION GOOGLE AUTOMATIQUE")
    print("=" * 50)
    
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
        
        if "accounts.google.com" not in current_url:
            print("❌ Pas de redirection vers Google")
            return False
        
        print("✅ Redirection vers Google réussie")
        
        # 5. Attendre que la page Google se charge complètement
        print("⏳ Attente du chargement de Google...")
        await scraper.page.wait_for_timeout(5000)
        
        # 6. Saisir l'email
        print("📧 Recherche du champ email...")
        
        # Essayer plusieurs sélecteurs pour l'email
        email_selectors = [
            'input[type="email"]',
            'input[name="identifier"]',
            'input[aria-label*="email"]',
            'input[aria-label*="Email"]',
            '#identifierId',
            'input[autocomplete="username"]'
        ]
        
        email_input = None
        for selector in email_selectors:
            try:
                email_input = await scraper.page.query_selector(selector)
                if email_input:
                    print(f"✅ Champ email trouvé avec: {selector}")
                    break
            except:
                continue
        
        if not email_input:
            print("❌ Champ email non trouvé")
            return False
        
        # Saisir l'email
        await email_input.fill("souheil.medaghri@gmail.com")
        print("✅ Email saisi")
        
        # 7. Cliquer sur Suivant
        print("➡️ Recherche du bouton Suivant...")
        
        next_selectors = [
            'button:has-text("Suivant")',
            'button:has-text("Next")',
            '#identifierNext',
            'button[type="submit"]',
            'button[aria-label*="Suivant"]',
            'button[aria-label*="Next"]'
        ]
        
        next_button = None
        for selector in next_selectors:
            try:
                next_button = await scraper.page.query_selector(selector)
                if next_button:
                    print(f"✅ Bouton Suivant trouvé avec: {selector}")
                    break
            except:
                continue
        
        if not next_button:
            print("❌ Bouton Suivant non trouvé")
            return False
        
        await next_button.click()
        print("✅ Bouton Suivant cliqué")
        await scraper.page.wait_for_timeout(5000)
        
        # 8. Saisir le mot de passe
        print("🔑 Recherche du champ mot de passe...")
        
        # Attendre que le champ mot de passe apparaisse
        await scraper.page.wait_for_timeout(3000)
        
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[aria-label*="password"]',
            'input[aria-label*="Password"]',
            '#password',
            'input[autocomplete="current-password"]'
        ]
        
        password_input = None
        for selector in password_selectors:
            try:
                password_input = await scraper.page.query_selector(selector)
                if password_input:
                    print(f"✅ Champ mot de passe trouvé avec: {selector}")
                    break
            except:
                continue
        
        if not password_input:
            print("❌ Champ mot de passe non trouvé")
            print("⚠️ Google peut demander une vérification supplémentaire")
            return False
        
        # Saisir le mot de passe
        await password_input.fill("Lbooycz7")
        print("✅ Mot de passe saisi")
        
        # 9. Cliquer sur Suivant (mot de passe)
        print("➡️ Recherche du bouton Suivant (mot de passe)...")
        
        next_password_selectors = [
            'button:has-text("Suivant")',
            'button:has-text("Next")',
            '#passwordNext',
            'button[type="submit"]',
            'button[aria-label*="Suivant"]',
            'button[aria-label*="Next"]'
        ]
        
        next_password_button = None
        for selector in next_password_selectors:
            try:
                next_password_button = await scraper.page.query_selector(selector)
                if next_password_button:
                    print(f"✅ Bouton Suivant (mot de passe) trouvé avec: {selector}")
                    break
            except:
                continue
        
        if not next_password_button:
            print("❌ Bouton Suivant (mot de passe) non trouvé")
            return False
        
        await next_password_button.click()
        print("✅ Bouton Suivant (mot de passe) cliqué")
        
        # 10. Attendre la redirection vers Jinka
        print("⏳ Attente de la redirection vers Jinka...")
        await scraper.page.wait_for_timeout(10000)
        
        # 11. Vérifier la connexion
        final_url = scraper.page.url
        print(f"📍 URL finale: {final_url}")
        
        if "jinka.fr" in final_url and "sign/in" not in final_url:
            print("🎉 CONNEXION JINKA RÉUSSIE !")
            
            # 12. Tester l'accès au dashboard
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
                    print("\n📋 PREMIERS APPARTEMENTS:")
                    for i, link in enumerate(apartment_links[:5], 1):
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        print(f"   {i}. {text[:50]}... -> {href}")
                    
                    # Prendre un screenshot
                    await scraper.page.screenshot(path="data/dashboard_auto_connected.png")
                    print(f"\n📸 Screenshot sauvegardé: data/dashboard_auto_connected.png")
                    
                    return True
                else:
                    print("❌ Aucun appartement trouvé")
                    return False
            else:
                print("❌ Redirection vers login détectée")
                return False
        else:
            print("❌ Connexion Jinka échouée")
            print("⚠️ Google peut avoir demandé une vérification supplémentaire")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert pour que tu puisses voir le résultat")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(auto_google_auth())
