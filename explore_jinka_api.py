#!/usr/bin/env python3
"""
Script d'exploration des APIs Jinka pour identifier les endpoints disponibles
"""

import asyncio
import json
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def explore_jinka_apis():
    """Explore les APIs Jinka en analysant les requêtes réseau"""
    
    print("🔍 Exploration des APIs Jinka...")
    
    async with async_playwright() as p:
        # Lancer le navigateur
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Intercepter les requêtes réseau
        api_requests = []
        
        async def handle_request(request):
            url = request.url
            if any(keyword in url.lower() for keyword in ['api', 'json', 'data', 'alert', 'property', 'ad']):
                api_requests.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers)
                })
                print(f"🌐 API détectée: {request.method} {url}")
        
        async def handle_response(response):
            url = response.url
            if any(keyword in url.lower() for keyword in ['api', 'json', 'data', 'alert', 'property', 'ad']):
                try:
                    content = await response.text()
                    if content and len(content) > 10:  # Éviter les réponses vides
                        print(f"📦 Réponse API: {url}")
                        print(f"   Taille: {len(content)} caractères")
                        if content.startswith('{') or content.startswith('['):
                            try:
                                data = json.loads(content)
                                print(f"   JSON valide avec {len(data) if isinstance(data, (list, dict)) else 'N/A'} éléments")
                            except:
                                print(f"   Contenu non-JSON")
                        print()
                except Exception as e:
                    print(f"   Erreur lecture réponse: {e}")
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        try:
            # Aller sur la page de connexion
            print("🔐 Connexion à Jinka...")
            await page.goto('https://www.jinka.fr/sign/in')
            await page.wait_for_load_state('networkidle')
            
            # Se connecter avec Google
            print("🔑 Connexion Google...")
            google_button = page.locator('button:has-text("Continuer avec Google")')
            if await google_button.count() > 0:
                await google_button.click()
                await page.wait_for_load_state('networkidle')
                
                # Attendre la redirection et saisir les identifiants
                await page.wait_for_timeout(2000)
                
                # Saisir l'email
                email_input = page.locator('input[type="email"]')
                if await email_input.count() > 0:
                    await email_input.fill(os.getenv('JINKA_EMAIL'))
                    await page.keyboard.press('Enter')
                    await page.wait_for_timeout(2000)
                
                # Saisir le mot de passe
                password_input = page.locator('input[type="password"]')
                if await password_input.count() > 0:
                    await password_input.fill(os.getenv('JINKA_PASSWORD'))
                    await page.keyboard.press('Enter')
                    await page.wait_for_load_state('networkidle')
            
            # Aller sur la page d'alerte
            print("🏠 Navigation vers l'alerte...")
            alert_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
            await page.goto(alert_url)
            await page.wait_for_load_state('networkidle')
            
            # Attendre que les données se chargent
            await page.wait_for_timeout(3000)
            
            # Cliquer sur une annonce pour voir les requêtes de détail
            print("🔍 Analyse des requêtes de détail...")
            apartment_links = page.locator('a[href*="alert_result"]')
            if await apartment_links.count() > 0:
                await apartment_links.first.click()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(2000)
            
            print(f"\n📊 Résumé de l'exploration:")
            print(f"   {len(api_requests)} requêtes API détectées")
            
            # Sauvegarder les résultats
            with open('data/api_exploration.json', 'w', encoding='utf-8') as f:
                json.dump(api_requests, f, ensure_ascii=False, indent=2)
            
            print("💾 Résultats sauvegardés dans data/api_exploration.json")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_jinka_apis())
