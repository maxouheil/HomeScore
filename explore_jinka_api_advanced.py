#!/usr/bin/env python3
"""
Script d'exploration avancée des APIs Jinka pour reverse engineer l'API privée
Capture TOUTES les requêtes réseau avec détails complets
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from scrape_jinka import JinkaScraper

load_dotenv()

class JinkaAPIExplorer:
    """Explorateur avancé de l'API Jinka"""
    
    def __init__(self):
        self.all_requests = []
        self.all_responses = []
        self.cookies = []
        self.api_endpoints = []
        self.auth_tokens = {}
        self.start_time = None
        
    async def setup(self):
        """Initialise le navigateur avec interception complète"""
        print("🔧 Initialisation du navigateur...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)  # Visible pour debug
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='fr-FR',
            timezone_id='Europe/Paris'
        )
        
        self.page = await self.context.new_page()
        self.start_time = datetime.now()
        
        # Intercepter TOUTES les requêtes
        self.page.on('request', self._handle_request)
        self.page.on('response', self._handle_response)
        
        print("✅ Navigateur initialisé avec interception complète")
    
    async def _handle_request(self, request):
        """Capture toutes les requêtes avec détails complets"""
        url = request.url
        method = request.method
        headers = dict(request.headers)
        
        # Extraire le body si présent
        post_data = None
        try:
            post_data = request.post_data
        except:
            pass
        
        # Vérifier si c'est une requête API
        is_api = any(keyword in url.lower() for keyword in [
            'api', 'json', 'graphql', 'rest', 'v1', 'v2', 'v3',
            'alert', 'property', 'ad', 'auth', 'login', 'user',
            'dashboard', 'search', 'photo', 'media'
        ])
        
        request_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'method': method,
            'headers': headers,
            'post_data': post_data,
            'resource_type': request.resource_type,
            'is_api': is_api,
            'frame_url': request.frame.url if request.frame else None,
        }
        
        self.all_requests.append(request_data)
        
        if is_api:
            print(f"🌐 API REQUEST: {method} {url[:100]}")
            if post_data:
                print(f"   Body: {post_data[:200]}")
            
            # Extraire les tokens d'authentification
            auth_header = headers.get('Authorization', '')
            if auth_header:
                self.auth_tokens['Authorization'] = auth_header
                print(f"   🔑 Token trouvé: {auth_header[:50]}...")
            
            # Extraire les cookies de la requête
            cookie_header = headers.get('Cookie', '')
            if cookie_header:
                print(f"   🍪 Cookies: {cookie_header[:100]}...")
    
    async def _handle_response(self, response):
        """Capture toutes les réponses avec détails complets"""
        url = response.url
        status = response.status
        headers = dict(response.headers)
        
        # Vérifier si c'est une réponse API
        is_api = any(keyword in url.lower() for keyword in [
            'api', 'json', 'graphql', 'rest', 'v1', 'v2', 'v3',
            'alert', 'property', 'ad', 'auth', 'login', 'user',
            'dashboard', 'search', 'photo', 'media'
        ])
        
        # Capturer le body de la réponse
        response_body = None
        response_json = None
        try:
            if 'application/json' in headers.get('Content-Type', ''):
                response_body = await response.text()
                try:
                    response_json = json.loads(response_body)
                except:
                    pass
            elif 'text/' in headers.get('Content-Type', ''):
                response_body = await response.text()
        except Exception as e:
            response_body = f"<Error reading response: {e}>"
        
        response_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'status': status,
            'status_text': response.status_text,
            'headers': headers,
            'body': response_body,
            'json': response_json,
            'is_api': is_api,
            'request_url': response.request.url if response.request else None,
        }
        
        self.all_responses.append(response_data)
        
        if is_api:
            print(f"📦 API RESPONSE: {status} {url[:100]}")
            if response_json:
                if isinstance(response_json, dict):
                    print(f"   JSON keys: {list(response_json.keys())[:10]}")
                elif isinstance(response_json, list):
                    print(f"   JSON array length: {len(response_json)}")
            elif response_body:
                print(f"   Body preview: {response_body[:200]}")
            
            # Identifier les endpoints
            endpoint_info = {
                'url': url,
                'method': response.request.method if response.request else 'UNKNOWN',
                'status': status,
                'has_json': response_json is not None,
            }
            self.api_endpoints.append(endpoint_info)
    
    async def explore_authentication(self):
        """Explore le processus d'authentification"""
        print("\n" + "="*60)
        print("🔐 PHASE 1: EXPLORATION DE L'AUTHENTIFICATION")
        print("="*60)
        
        # Utiliser le scraper existant pour la connexion
        scraper = JinkaScraper()
        scraper.browser = self.browser
        scraper.context = self.context
        scraper.page = self.page
        scraper.rate_limit_count = 0  # Initialiser l'attribut manquant
        
        print("📧 Connexion via email (code d'activation)...")
        success = await scraper.login()
        
        if success:
            print("✅ Connexion réussie")
            
            # Capturer les cookies après connexion
            cookies = await self.context.cookies()
            self.cookies = cookies
            print(f"🍪 {len(cookies)} cookies capturés")
            
            # Afficher les cookies importants
            for cookie in cookies:
                if any(key in cookie['name'].lower() for key in ['session', 'token', 'auth', 'jwt', 'access']):
                    print(f"   🔑 {cookie['name']}: {cookie['value'][:50]}...")
        else:
            print("❌ Échec de la connexion")
            return False
        
        return True
    
    async def explore_dashboard(self):
        """Explore le dashboard et les alertes"""
        print("\n" + "="*60)
        print("🏠 PHASE 2: EXPLORATION DU DASHBOARD")
        print("="*60)
        
        # Aller sur le dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        print(f"📍 Navigation vers: {dashboard_url}")
        await self.page.goto(dashboard_url)
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        print("✅ Dashboard chargé")
        
        # Essayer de faire défiler pour charger plus de données
        print("📜 Scroll pour charger plus de données...")
        for i in range(3):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
        
        print("✅ Scroll terminé")
    
    async def explore_alert_page(self):
        """Explore une page d'alerte"""
        print("\n" + "="*60)
        print("📋 PHASE 3: EXPLORATION DE LA PAGE D'ALERTE")
        print("="*60)
        
        alert_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
        print(f"📍 Navigation vers: {alert_url}")
        await self.page.goto(alert_url)
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        print("✅ Page d'alerte chargée")
        
        # Essayer de faire défiler pour charger plus d'appartements
        print("📜 Scroll pour charger plus d'appartements...")
        for i in range(5):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
        
        print("✅ Scroll terminé")
    
    async def explore_property_details(self):
        """Explore les détails d'un appartement"""
        print("\n" + "="*60)
        print("🏢 PHASE 4: EXPLORATION DES DÉTAILS D'APPARTEMENT")
        print("="*60)
        
        # Chercher un lien d'appartement
        apartment_links = self.page.locator('a[href*="alert_result"][href*="ad="]')
        count = await apartment_links.count()
        
        if count > 0:
            print(f"📋 {count} liens d'appartements trouvés")
            print("🖱️ Clic sur le premier appartement...")
            
            # Cliquer sur le premier appartement
            await apartment_links.first.click()
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            print("✅ Détails de l'appartement chargés")
            
            # Essayer de charger les photos
            print("📸 Tentative de chargement des photos...")
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
            print("✅ Photos chargées")
        else:
            print("⚠️  Aucun lien d'appartement trouvé")
    
    async def save_results(self):
        """Sauvegarde tous les résultats"""
        print("\n" + "="*60)
        print("💾 SAUVEGARDE DES RÉSULTATS")
        print("="*60)
        
        os.makedirs('data/api_exploration', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Résumé
        summary = {
            'timestamp': timestamp,
            'total_requests': len(self.all_requests),
            'total_responses': len(self.all_responses),
            'api_requests': len([r for r in self.all_requests if r['is_api']]),
            'api_responses': len([r for r in self.all_responses if r['is_api']]),
            'api_endpoints': len(self.api_endpoints),
            'cookies_count': len(self.cookies),
            'auth_tokens': list(self.auth_tokens.keys()),
        }
        
        # Sauvegarder le résumé
        summary_path = f'data/api_exploration/summary_{timestamp}.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"✅ Résumé sauvegardé: {summary_path}")
        
        # Sauvegarder toutes les requêtes
        requests_path = f'data/api_exploration/requests_{timestamp}.json'
        with open(requests_path, 'w', encoding='utf-8') as f:
            json.dump(self.all_requests, f, ensure_ascii=False, indent=2)
        print(f"✅ Requêtes sauvegardées: {requests_path}")
        
        # Sauvegarder toutes les réponses
        responses_path = f'data/api_exploration/responses_{timestamp}.json'
        # Filtrer les réponses trop grandes (limiter à 10KB par réponse)
        filtered_responses = []
        for resp in self.all_responses:
            filtered_resp = resp.copy()
            if filtered_resp.get('body') and len(str(filtered_resp['body'])) > 10000:
                filtered_resp['body'] = str(filtered_resp['body'])[:10000] + "... [TRUNCATED]"
            filtered_responses.append(filtered_resp)
        
        with open(responses_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_responses, f, ensure_ascii=False, indent=2)
        print(f"✅ Réponses sauvegardées: {responses_path}")
        
        # Sauvegarder les endpoints API identifiés
        endpoints_path = f'data/api_exploration/endpoints_{timestamp}.json'
        with open(endpoints_path, 'w', encoding='utf-8') as f:
            json.dump(self.api_endpoints, f, ensure_ascii=False, indent=2)
        print(f"✅ Endpoints sauvegardés: {endpoints_path}")
        
        # Sauvegarder les cookies
        cookies_path = f'data/api_exploration/cookies_{timestamp}.json'
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(self.cookies, f, ensure_ascii=False, indent=2)
        print(f"✅ Cookies sauvegardés: {cookies_path}")
        
        # Sauvegarder les tokens d'authentification
        tokens_path = f'data/api_exploration/tokens_{timestamp}.json'
        with open(tokens_path, 'w', encoding='utf-8') as f:
            json.dump(self.auth_tokens, f, ensure_ascii=False, indent=2)
        print(f"✅ Tokens sauvegardés: {tokens_path}")
        
        # Créer un rapport textuel
        report_path = f'data/api_exploration/report_{timestamp}.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("RAPPORT D'EXPLORATION API JINKA\n")
            f.write("="*60 + "\n\n")
            f.write(f"Date: {datetime.now().isoformat()}\n")
            f.write(f"Total requêtes: {len(self.all_requests)}\n")
            f.write(f"Total réponses: {len(self.all_responses)}\n")
            f.write(f"Requêtes API: {summary['api_requests']}\n")
            f.write(f"Réponses API: {summary['api_responses']}\n")
            f.write(f"Endpoints identifiés: {len(self.api_endpoints)}\n")
            f.write(f"Cookies capturés: {len(self.cookies)}\n\n")
            
            f.write("="*60 + "\n")
            f.write("ENDPOINTS API IDENTIFIÉS\n")
            f.write("="*60 + "\n\n")
            for endpoint in self.api_endpoints:
                f.write(f"{endpoint['method']} {endpoint['url']}\n")
                f.write(f"  Status: {endpoint['status']}\n")
                f.write(f"  JSON: {endpoint['has_json']}\n\n")
            
            f.write("="*60 + "\n")
            f.write("TOKENS D'AUTHENTIFICATION\n")
            f.write("="*60 + "\n\n")
            for key, value in self.auth_tokens.items():
                f.write(f"{key}: {value[:100]}...\n\n")
            
            f.write("="*60 + "\n")
            f.write("COOKIES IMPORTANTS\n")
            f.write("="*60 + "\n\n")
            for cookie in self.cookies:
                if any(key in cookie['name'].lower() for key in ['session', 'token', 'auth', 'jwt', 'access']):
                    f.write(f"{cookie['name']}: {cookie['value'][:50]}...\n")
                    f.write(f"  Domain: {cookie.get('domain', 'N/A')}\n")
                    f.write(f"  Path: {cookie.get('path', 'N/A')}\n")
                    f.write(f"  HttpOnly: {cookie.get('httpOnly', False)}\n")
                    f.write(f"  Secure: {cookie.get('secure', False)}\n\n")
        
        print(f"✅ Rapport sauvegardé: {report_path}")
        
        # Afficher le résumé
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DE L'EXPLORATION")
        print("="*60)
        print(f"Total requêtes capturées: {len(self.all_requests)}")
        print(f"Total réponses capturées: {len(self.all_responses)}")
        print(f"Requêtes API identifiées: {summary['api_requests']}")
        print(f"Réponses API identifiées: {summary['api_responses']}")
        print(f"Endpoints uniques: {len(self.api_endpoints)}")
        print(f"Cookies capturés: {len(self.cookies)}")
        print(f"Tokens d'authentification: {len(self.auth_tokens)}")
        print("\n✅ Tous les résultats ont été sauvegardés dans data/api_exploration/")
    
    async def cleanup(self):
        """Ferme le navigateur"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def main():
    """Fonction principale"""
    print("🚀 EXPLORATION AVANCÉE DE L'API JINKA")
    print("="*60)
    print("Ce script va capturer TOUTES les requêtes réseau")
    print("pendant la connexion et la navigation sur Jinka")
    print("="*60)
    
    explorer = JinkaAPIExplorer()
    
    try:
        await explorer.setup()
        
        # Phase 1: Authentification
        auth_success = await explorer.explore_authentication()
        if not auth_success:
            print("❌ Échec de l'authentification, arrêt de l'exploration")
            return
        
        # Phase 2: Dashboard
        await explorer.explore_dashboard()
        
        # Phase 3: Page d'alerte
        await explorer.explore_alert_page()
        
        # Phase 4: Détails d'appartement
        await explorer.explore_property_details()
        
        # Sauvegarder tous les résultats
        await explorer.save_results()
        
        print("\n✅ Exploration terminée avec succès!")
        print("📁 Consultez les fichiers dans data/api_exploration/ pour analyser les résultats")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exploration: {e}")
        import traceback
        traceback.print_exc()
        
        # Sauvegarder quand même ce qui a été capturé
        try:
            await explorer.save_results()
        except:
            pass
    
    finally:
        print("\n⏳ Fermeture du navigateur dans 5 secondes...")
        print("   (Laissez le temps de vérifier les requêtes dans DevTools si besoin)")
        await asyncio.sleep(5)
        await explorer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

