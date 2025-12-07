#!/usr/bin/env python3
"""
Test du dashboard d'alertes Jinka
"""

import asyncio
from scrape_jinka import JinkaScraper

async def test_dashboard():
    """Test du dashboard d'alertes"""
    print("🔍 TEST DU DASHBOARD D'ALERTES JINKA")
    print("=" * 50)
    
    scraper = JinkaScraper()
    
    try:
        # 1. Initialiser
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # 2. Se connecter
        if await scraper.login():
            print("✅ Connexion réussie")
        else:
            print("❌ Échec de connexion")
            return
        
        # 3. Aller au dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        print(f"🌐 Navigation vers: {dashboard_url}")
        
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(5000)
        
        # 4. Vérifier l'URL actuelle
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        # 5. Vérifier si on est connecté
        if "sign/in" in current_url or "auth" in current_url:
            print("⚠️ Redirection vers authentification détectée")
            
            # Essayer de se connecter via Google
            try:
                print("🔐 Tentative de connexion Google...")
                await scraper.page.goto("https://pro.jinka.fr/auth/signin")
                await scraper.page.wait_for_timeout(3000)
                
                # Chercher le bouton Google
                google_selectors = [
                    'button[data-testid="google-signin-button"]',
                    'a[href*="google"]',
                    'button:has-text("Google")',
                    'a:has-text("Google")',
                    'button:has-text("Se connecter avec Google")'
                ]
                
                google_button = None
                for selector in google_selectors:
                    try:
                        google_button = await scraper.page.query_selector(selector)
                        if google_button:
                            print(f"✅ Bouton Google trouvé avec: {selector}")
                            break
                    except:
                        continue
                
                if google_button:
                    await google_button.click()
                    await scraper.page.wait_for_timeout(5000)
                    print("✅ Clic sur Google effectué")
                    
                    # Retourner au dashboard
                    await scraper.page.goto(dashboard_url)
                    await scraper.page.wait_for_timeout(5000)
                    print("🔄 Retour au dashboard")
                    
                else:
                    print("❌ Bouton Google non trouvé")
                    
            except Exception as e:
                print(f"❌ Erreur connexion Google: {e}")
        
        # 6. Analyser la page du dashboard
        print("\n📊 ANALYSE DE LA PAGE DASHBOARD")
        print("-" * 40)
        
        # Vérifier le contenu de la page
        page_content = await scraper.page.content()
        print(f"📄 Taille de la page: {len(page_content)} caractères")
        
        # Chercher des liens d'appartements
        apartment_links = await scraper.page.query_selector_all('a[href*="ad="], a[href*="alert_result"]')
        print(f"🔗 Liens d'appartements trouvés: {len(apartment_links)}")
        
        for i, link in enumerate(apartment_links[:5], 1):
            href = await link.get_attribute('href')
            text = await link.inner_text()
            print(f"   Lien {i}: {href} - {text[:50]}...")
        
        # Chercher des cartes d'appartements
        apartment_cards = await scraper.page.query_selector_all('[data-testid*="apartment"], .apartment-card, .property-card')
        print(f"🏠 Cartes d'appartements trouvées: {len(apartment_cards)}")
        
        # Prendre un screenshot
        await scraper.page.screenshot(path="data/dashboard_screenshot.png")
        print("📸 Screenshot sauvegardé: data/dashboard_screenshot.png")
        
        # 7. Essayer de scraper les appartements
        print("\n🏠 TENTATIVE DE SCRAPING DES APPARTEMENTS")
        print("-" * 50)
        
        apartments = await scraper.scrape_alert_page(dashboard_url)
        if apartments:
            print(f"✅ {len(apartments)} appartements trouvés")
            for i, apt in enumerate(apartments[:3], 1):
                print(f"   Appartement {i}: {apt}")
        else:
            print("❌ Aucun appartement trouvé")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        if hasattr(scraper, 'browser') and scraper.browser:
            await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(test_dashboard())
