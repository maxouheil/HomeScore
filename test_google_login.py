#!/usr/bin/env python3
"""
Test spécifique du bouton Google sur la page de login Jinka
"""

import asyncio
from scrape_jinka import JinkaScraper

async def test_google_login():
    """Test du bouton Google sur la page de login"""
    print("🔍 TEST DU BOUTON GOOGLE JINKA")
    print("=" * 50)
    
    scraper = JinkaScraper()
    
    try:
        # 1. Initialiser
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # 2. Aller directement à la page de login
        login_url = "https://www.jinka.fr/sign/in"
        print(f"🌐 Navigation vers: {login_url}")
        
        await scraper.page.goto(login_url)
        await scraper.page.wait_for_timeout(3000)
        
        # 3. Analyser la page de login
        print("\n📊 ANALYSE DE LA PAGE DE LOGIN")
        print("-" * 40)
        
        # Vérifier l'URL actuelle
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        # Chercher tous les boutons sur la page
        all_buttons = await scraper.page.query_selector_all('button, a, [role="button"]')
        print(f"🔘 Total de boutons/liens: {len(all_buttons)}")
        
        # Chercher spécifiquement le bouton Google
        google_selectors = [
            'button:has-text("Google")',
            'button:has-text("Continuer avec Google")',
            'a:has-text("Google")',
            'a:has-text("Continuer avec Google")',
            '[data-testid*="google"]',
            'button[aria-label*="Google"]',
            'a[href*="google"]',
            'button img[alt*="Google"]',
            'button svg[aria-label*="Google"]'
        ]
        
        print("\n🔍 RECHERCHE DU BOUTON GOOGLE")
        print("-" * 40)
        
        google_button = None
        for i, selector in enumerate(google_selectors, 1):
            try:
                elements = await scraper.page.query_selector_all(selector)
                print(f"   Sélecteur {i} '{selector}': {len(elements)} éléments")
                
                for j, element in enumerate(elements):
                    text = await element.inner_text()
                    href = await element.get_attribute('href')
                    print(f"      Élément {j+1}: '{text[:50]}...' (href: {href})")
                    
                    if 'google' in text.lower() or 'google' in (href or '').lower():
                        google_button = element
                        print(f"      ✅ BOUTON GOOGLE TROUVÉ !")
                        break
                
                if google_button:
                    break
                    
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
        
        if google_button:
            print(f"\n✅ BOUTON GOOGLE TROUVÉ !")
            print(f"   Texte: {await google_button.inner_text()}")
            print(f"   Tag: {await google_button.evaluate('el => el.tagName')}")
            
            # Essayer de cliquer
            try:
                print("\n🖱️ TENTATIVE DE CLIC")
                print("-" * 30)
                await google_button.click()
                await scraper.page.wait_for_timeout(5000)
                
                # Vérifier l'URL après le clic
                new_url = scraper.page.url
                print(f"📍 URL après clic: {new_url}")
                
                if "google" in new_url.lower() or "accounts.google" in new_url.lower():
                    print("✅ Redirection vers Google réussie !")
                else:
                    print("⚠️ Pas de redirection vers Google détectée")
                    
            except Exception as e:
                print(f"❌ Erreur lors du clic: {e}")
        else:
            print("\n❌ BOUTON GOOGLE NON TROUVÉ")
            
            # Afficher tous les textes de boutons pour debug
            print("\n🔍 TOUS LES BOUTONS TROUVÉS:")
            print("-" * 40)
            for i, button in enumerate(all_buttons[:10], 1):
                try:
                    text = await button.inner_text()
                    tag = await button.evaluate('el => el.tagName')
                    print(f"   Bouton {i} ({tag}): '{text[:100]}...'")
                except:
                    print(f"   Bouton {i}: (erreur lecture)")
        
        # Prendre un screenshot
        await scraper.page.screenshot(path="data/login_page_debug.png")
        print(f"\n📸 Screenshot sauvegardé: data/login_page_debug.png")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        if hasattr(scraper, 'browser') and scraper.browser:
            await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(test_google_login())
