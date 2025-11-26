#!/usr/bin/env python3
"""
Script d'exploration avancée des APIs SeLoger pour reverse engineer l'API privée
Capture TOUTES les requêtes réseau avec détails complets
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class SeLogerAPIExplorer:
    """Explorateur avancé de l'API SeLoger"""
    
    def __init__(self):
        self.all_requests = []
        self.all_responses = []
        self.cookies = []
        self.api_endpoints = []
        self.auth_tokens = {}
        self.start_time = None
        
    async def setup(self):
        """Initialise le navigateur avec interception complète et comportement humain"""
        print("🔧 Initialisation du navigateur...")
        self.playwright = await async_playwright().start()
        
        # Lancer avec des options pour être moins détectable comme bot
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Visible pour debug
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        # Créer un contexte avec des caractéristiques humaines
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='fr-FR',
            timezone_id='Europe/Paris',
            permissions=['geolocation'],
            geolocation={'latitude': 48.8566, 'longitude': 2.3522},  # Paris
            color_scheme='light',
        )
        
        # Masquer les indicateurs de bot - VERSION AMÉLIORÉE
        await self.context.add_init_script("""
            // Masquer webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Masquer les propriétés de Playwright
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Masquer les propriétés d'automation
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-FR', 'fr', 'en-US', 'en']
            });
            
            // Masquer les traces de Playwright
            delete window.__playwright;
            delete window.__pw_manual;
            delete window.__PW_inspect;
            
            // Override getBattery si disponible
            if (navigator.getBattery) {
                navigator.getBattery = undefined;
            }
        """)
        
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
        
        # Vérifier si c'est une requête API (SeLoger spécifique)
        is_api = any(keyword in url.lower() for keyword in [
            'api', 'json', 'graphql', 'rest', 'v1', 'v2', 'v3',
            'search', 'annonce', 'property', 'ad', 'auth', 'login', 'user',
            'dashboard', 'photo', 'media', 'seloger.com/api',
            'ws.seloger.com', 'api.seloger.com'
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
        
        # Vérifier si c'est une réponse API (SeLoger spécifique)
        is_api = any(keyword in url.lower() for keyword in [
            'api', 'json', 'graphql', 'rest', 'v1', 'v2', 'v3',
            'search', 'annonce', 'property', 'ad', 'auth', 'login', 'user',
            'dashboard', 'photo', 'media', 'seloger.com/api',
            'ws.seloger.com', 'api.seloger.com'
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
    
    async def _human_delay(self, min_seconds=0, max_seconds=0):
        """Délai désactivé pour vitesse maximale"""
        pass
    
    async def _human_scroll(self):
        """Scroll rapide sans pauses"""
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    async def _simulate_human_reading(self, min_seconds=0, max_seconds=0):
        """Lecture désactivée pour vitesse maximale"""
        pass
    
    async def _move_mouse_randomly(self):
        """Mouvements de souris désactivés pour vitesse maximale"""
        pass
    
    async def explore_homepage(self):
        """Explore la page d'accueil SeLoger"""
        print("\n" + "="*60)
        print("🏠 PHASE 1: EXPLORATION DE LA PAGE D'ACCUEIL")
        print("="*60)
        
        homepage_url = "https://www.seloger.com/"
        print(f"📍 Navigation vers: {homepage_url}")
        
        # Navigation rapide
        print("⏳ Navigation en cours...")
        await self.page.goto(homepage_url, wait_until='domcontentloaded', timeout=10000)
        
        # Attendre que la page se charge
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
        except:
            pass
        
        print("✅ Page d'accueil chargée")
        
        # Capturer les cookies initiaux
        cookies = await self.context.cookies()
        self.cookies = cookies
        print(f"🍪 {len(cookies)} cookies capturés")
    
    async def explore_search(self, location: str = "Paris", property_type: str = "appartement"):
        """Explore la recherche d'annonces"""
        print("\n" + "="*60)
        print("🔍 PHASE 2: EXPLORATION DE LA RECHERCHE")
        print("="*60)
        
        # Construire l'URL de recherche
        search_url = f"https://www.seloger.com/list.htm?types=2&projects=2&rooms=2,3,4&price=NaN/NaN&surface=NaN/NaN&mandatorycommodities=0&enterprise=0&qsVersion=1.0&LISTING-LISTpg=1"
        print(f"📍 Navigation vers: {search_url}")
        
        # Navigation rapide
        print("⏳ Navigation vers la recherche...")
        await self.page.goto(search_url, wait_until='domcontentloaded', timeout=10000)
        
        # Attendre que la page se charge
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
        except:
            pass
        
        # Chercher le bouton "custom-primary-button" sur la page de recherche
        try:
            button = await self.page.query_selector('button.custom-primary-button, .custom-primary-button')
            if button:
                print("🔘 Bouton 'custom-primary-button' trouvé sur la page de recherche!")
                await button.scroll_into_view_if_needed()
                await button.click()
                print("✅ Clic sur le bouton effectué")
                
                # Attendre que la page se charge après le clic
                try:
                    await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
                except:
                    pass
        except Exception as e:
            print(f"ℹ️  Bouton non trouvé ou erreur: {e}")
        
        print("✅ Page de recherche chargée")
        
        # Vérifier s'il y a un CAPTCHA
        captcha_indicators = [
            'captcha',
            'challenge',
            'verification',
            'robot',
            'human verification'
        ]
        
        page_content = await self.page.content()
        has_captcha = any(indicator in page_content.lower() for indicator in captcha_indicators)
        
        if has_captcha:
            print("\n" + "⚠️" * 30)
            print("🤖 CAPTCHA DÉTECTÉ!")
            print("=" * 60)
            print("Veuillez résoudre le CAPTCHA manuellement dans le navigateur.")
            print("Le script attendra que vous ayez terminé...")
            print("=" * 60)
            
            # Attendre que l'utilisateur résolve le CAPTCHA (rapide)
            max_wait_time = 10  # 10 secondes max
            wait_interval = 1  # Vérifier toutes les secondes
            waited = 0
            
            while waited < max_wait_time:
                await asyncio.sleep(wait_interval)
                waited += wait_interval
                
                # Vérifier si le CAPTCHA est toujours là
                current_content = await self.page.content()
                still_has_captcha = any(indicator in current_content.lower() for indicator in captcha_indicators)
                
                if not still_has_captcha:
                    print("✅ CAPTCHA résolu! Continuation...")
                    break
                
                if waited % 5 == 0:  # Afficher un message toutes les 5 secondes
                    print(f"⏳ Attente... ({waited}s / {max_wait_time}s)")
            
            if waited >= max_wait_time:
                print("⚠️  Timeout d'attente du CAPTCHA. Continuation quand même...")
        
        # Scroll rapide pour charger plus de résultats
        print("📜 Scroll pour charger plus de résultats...")
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        print("✅ Scroll terminé")
    
    async def explore_property_details(self):
        """Explore les détails d'une annonce"""
        print("\n" + "="*60)
        print("🏢 PHASE 3: EXPLORATION DES DÉTAILS D'ANNONCE")
        print("="*60)
        
        # Chercher un lien d'annonce avec plusieurs sélecteurs possibles
        property_selectors = [
            'a[href*="/annonces/"]',
            'a[href*="/annonce/"]',
            'a[href*="/detail/"]',
            '[data-testid*="property"] a',
            '.c-pa-link',
            '[class*="property"] a',
            '[class*="listing"] a',
        ]
        
        property_links = None
        count = 0
        
        for selector in property_selectors:
            try:
                property_links = self.page.locator(selector)
                count = await property_links.count()
                if count > 0:
                    print(f"✅ Sélecteur trouvé: {selector}")
                    break
            except:
                continue
        
        if count > 0:
            print(f"📋 {count} liens d'annonces trouvés")
            print("🖱️ Clic sur la première annonce...")
            
            # Cliquer sur la première annonce rapidement
            await property_links.first.scroll_into_view_if_needed()
            await property_links.first.click()
            
            # Attendre le chargement
            await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
            
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
            except:
                pass
            
            print("✅ Détails de l'annonce chargés")
            
            # Scroll rapide pour charger les photos
            print("📸 Tentative de chargement des photos...")
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            print("✅ Photos chargées")
        else:
            print("⚠️  Aucun lien d'annonce trouvé")
            print("   La page peut encore être en cours de chargement ou bloquée par CAPTCHA")
    
    async def explore_authentication(self):
        """Explore le processus d'authentification (si nécessaire)"""
        print("\n" + "="*60)
        print("🔐 PHASE 4: EXPLORATION DE L'AUTHENTIFICATION")
        print("="*60)
        
        # Aller sur la page de connexion (lien spécifique fourni)
        login_url = "https://signin.seloger.com/u/login?state=hKFo2SA5enk2U0hKY2N5SHM0VWQ4dVVBQ3ZBNWQ4d1otZURCVqFur3VuaXZlcnNhbC1sb2dpbqN0aWTZIC1pYmRtRWpEd0x0UGRSODRpWUNCeFpCZFJPYURFYjd5o2NpZNkgVDFWSmlHUXJtVUlvVjM5bnNmZnR5RHlyTG9yVkR3UDI&ui_locales=fr"
        print(f"📍 Navigation vers: {login_url}")
        
        await self.page.goto(login_url, wait_until='domcontentloaded', timeout=10000)
        
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
        except:
            pass
        
        print("✅ Page de connexion chargée")
        print("🔐 Tentative de connexion automatique...")
        
        # Attendre que les champs soient chargés (un peu plus de temps)
        try:
            await self.page.wait_for_selector('input[name="username"], input[type="email"]', timeout=10000)
        except:
            print("⚠️  Les champs ne sont pas encore chargés, continuation...")
        
        try:
            # D'ABORD: Chercher et cliquer sur le bouton "Se connecter avec email" si présent
            email_button_selectors = [
                # Par ID
                'button#login-with-email-button',
                '#login-with-email-button',
                'button[id="login-with-email-button"]',
                'button[id*="email" i]',
                'button[id*="connecter" i]',
                '#login-with-email',
                '#email-login',
                '#connect-email',
                
                # Par classe
                'button.custom-primary-button',
                '.custom-primary-button',
                'button[class*="email" i]',
                'button[class*="connecter" i]',
                'button[class*="login" i]',
                '.email-button',
                '.email-login',
                '.connect-email',
                
                # Par texte (Playwright)
                'button:has-text("Se connecter avec email")',
                'button:has-text("se connecter avec email")',
                'button:has-text("Connexion avec email")',
                'button:has-text("Email")',
                'a:has-text("Se connecter avec email")',
                'a:has-text("Email")',
                
                # Par attributs
                '[data-testid*="email" i]',
                '[aria-label*="email" i]',
                '[aria-label*="connecter" i]',
                'button[type="button"]:has-text("email" i)',
                
                # Sélecteurs génériques
                'button[id*="email"]',
                'a[id*="email"]',
                'div[role="button"][id*="email"]',
                'div[role="button"][class*="email" i]',
            ]
            
            email_button = None
            
            # Chercher aussi par texte, classe et ID dans le DOM
            try:
                page_text = await self.page.content()
                if 'se connecter avec email' in page_text.lower() or 'connexion avec email' in page_text.lower() or 'email' in page_text.lower():
                    print("ℹ️  Texte 'email' trouvé dans la page, recherche approfondie...")
                    # Essayer de trouver tous les boutons et vérifier leur texte, classe et ID
                    all_buttons = await self.page.query_selector_all('button, a, div[role="button"]')
                    for btn in all_buttons:
                        try:
                            # Vérifier le texte
                            text = await btn.inner_text()
                            # Vérifier l'ID
                            btn_id = await btn.get_attribute('id') or ''
                            # Vérifier la classe
                            btn_class = await btn.get_attribute('class') or ''
                            
                            # Vérifier si c'est le bon bouton
                            text_match = text and ('email' in text.lower() and ('connecter' in text.lower() or 'login' in text.lower()))
                            id_match = btn_id and ('email' in btn_id.lower() or 'login-with-email' in btn_id.lower())
                            class_match = btn_class and ('email' in btn_class.lower() or 'custom-primary-button' in btn_class.lower())
                            
                            if text_match or id_match or class_match:
                                print(f"✅ Bouton trouvé - Texte: '{text}', ID: '{btn_id}', Class: '{btn_class}'")
                                await btn.scroll_into_view_if_needed()
                                await btn.click()
                                print("✅ Clic sur le bouton effectué")
                                await asyncio.sleep(1)
                                email_button = btn
                                break
                        except:
                            continue
            except Exception as e:
                print(f"⚠️  Erreur lors de la recherche approfondie: {e}")
            
            # Si pas trouvé par texte, chercher avec les sélecteurs
            if not email_button:
                for selector in email_button_selectors:
                    try:
                        email_button = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                        if email_button:
                            print(f"✅ Bouton 'Se connecter avec email' trouvé avec: {selector}")
                            await email_button.scroll_into_view_if_needed()
                            await email_button.click()
                            print("✅ Clic sur 'Se connecter avec email' effectué")
                            await asyncio.sleep(1)  # Attendre que le formulaire apparaisse
                            break
                    except:
                        continue
            
            # Chercher le champ email avec plusieurs sélecteurs possibles
            email_selectors = [
                'input[type="email"]',
                'input[name="username"]',
                'input[name="email"]',
                'input[id*="email"]',
                'input[id*="username"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="Email" i]',
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = await self.page.query_selector(selector)
                    if email_field:
                        print(f"✅ Champ email trouvé avec: {selector}")
                        break
                except:
                    continue
            
            if email_field:
                await email_field.scroll_into_view_if_needed()
                await email_field.click()
                await email_field.fill('souheil.medaghri@gmail.com')
                print("✅ Email saisi")
                # Attendre un peu pour que le champ mot de passe apparaisse
                await asyncio.sleep(0.5)
            else:
                print("⚠️  Champ email non trouvé, tentative manuelle nécessaire")
            
            # Chercher le champ mot de passe (il apparaît après avoir rempli l'email)
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id*="password"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="Password" i]',
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    # Attendre que le champ soit visible (il apparaît dynamiquement)
                    password_field = await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                    if password_field:
                        print(f"✅ Champ mot de passe trouvé avec: {selector}")
                        break
                except:
                    continue
            
            if password_field:
                await password_field.scroll_into_view_if_needed()
                await password_field.click()
                await password_field.fill('Lbooycz7!')
                print("✅ Mot de passe saisi")
            else:
                print("⚠️  Champ mot de passe non trouvé")
            
            # Chercher et cliquer sur le bouton "Se connecter" final (formulaire email)
            # Sélecteur exact: button[type="submit"][name="action"]
            button_selectors = [
                # Sélecteur exact du bouton
                'button[type="submit"][name="action"]',
                
                # Par attributs spécifiques vus dans DevTools (formulaire email)
                'button[data-action-button-primary="true"]:not(:has-text("Google")):not(:has-text("Apple"))',
                'button[type="submit"]:has-text("Se connecter"):not(:has-text("Google")):not(:has-text("Apple"))',
                'button[type="submit"]:has-text("se connecter"):not(:has-text("Google")):not(:has-text("Apple"))',
                
                # Par classes spécifiques vues dans DevTools
                'button.c779d66dd.c737b527e.c4d92db71.cdeb183b6.c996d9041',
                'button.c779d66dd',
                'button[class*="c779d66dd"]',
                'button[class*="c737b527e"]',
                
                # Sélecteurs génériques (mais exclure Google/Apple)
                'button[type="submit"]:not([id*="google"]):not([id*="apple"]):not([class*="google"]):not([class*="apple"])',
                'button:has-text("Se connecter"):not(:has-text("Google")):not(:has-text("Apple"))',
                'button:has-text("se connecter"):not(:has-text("Google")):not(:has-text("Apple"))',
                'input[type="submit"]',
            ]
            
            submit_button = None
            
            # Attendre un peu que le formulaire soit complètement chargé après avoir rempli le mot de passe
            await asyncio.sleep(0.5)
            
            # D'abord, chercher par texte dans tous les boutons (plus fiable)
            # IMPORTANT: Exclure les boutons Google/Apple
            try:
                all_buttons = await self.page.query_selector_all('button[type="submit"], button')
                for btn in all_buttons:
                    try:
                        text = await btn.inner_text()
                        btn_id = await btn.get_attribute('id') or ''
                        btn_class = await btn.get_attribute('class') or ''
                        btn_type = await btn.get_attribute('type') or ''
                        data_attr = await btn.get_attribute('data-action-button-primary') or ''
                        
                        # EXCLURE les boutons Google/Apple
                        is_google = 'google' in text.lower() or 'google' in btn_id.lower() or 'google' in btn_class.lower()
                        is_apple = 'apple' in text.lower() or 'apple' in btn_id.lower() or 'apple' in btn_class.lower()
                        
                        if is_google or is_apple:
                            continue  # Ignorer les boutons sociaux
                        
                        # Vérifier si c'est le bouton "Se connecter" du formulaire email
                        text_match = text and ('se connecter' in text.lower() or 'connexion' in text.lower())
                        is_submit = btn_type == 'submit'
                        has_primary_attr = data_attr == 'true'
                        
                        # Le bouton doit être dans le formulaire email (pas les boutons sociaux)
                        # Il doit avoir "Se connecter" sans mentionner Google/Apple
                        if text_match and (is_submit or has_primary_attr) and not is_google and not is_apple:
                            print(f"✅ Bouton 'Se connecter' trouvé - Texte: '{text}', ID: '{btn_id}', Class: '{btn_class}', Type: '{btn_type}'")
                            submit_button = btn
                            break
                    except:
                        continue
            except Exception as e:
                print(f"⚠️  Erreur lors de la recherche approfondie du bouton: {e}")
            
            # Si pas trouvé par texte, utiliser les sélecteurs CSS
            if not submit_button:
                for selector in button_selectors:
                    try:
                        # Attendre que le bouton soit visible
                        submit_button = await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                        if submit_button:
                            print(f"✅ Bouton de connexion trouvé avec: {selector}")
                            break
                    except:
                        continue
            
            if submit_button:
                await submit_button.scroll_into_view_if_needed()
                await submit_button.click()
                print("✅ Clic sur le bouton de connexion effectué")
                
                # Attendre que la page se charge après la connexion
                try:
                    await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                except:
                    pass
                
                # Vérifier si on est toujours sur la page de connexion (échec) ou si on a été redirigé (succès)
                current_url = self.page.url
                if 'login' in current_url.lower() or 'signin' in current_url.lower():
                    print("⚠️  Toujours sur la page de connexion - peut-être un CAPTCHA à résoudre")
                    print("💡 Le script attendra 10 secondes pour que vous résolviez le CAPTCHA si nécessaire...")
                    await asyncio.sleep(10)
                else:
                    print("✅ Connexion réussie! Redirection détectée")
            else:
                print("⚠️  Bouton de connexion non trouvé")
                print("💡 Le script attendra 10 secondes pour une connexion manuelle...")
                await asyncio.sleep(10)
                
        except Exception as e:
            print(f"⚠️  Erreur lors de la connexion automatique: {e}")
            print("💡 Le script attendra 10 secondes pour une connexion manuelle...")
            await asyncio.sleep(10)
        
        # Capturer les cookies après navigation/connexion
        cookies = await self.context.cookies()
        self.cookies = cookies
        print(f"🍪 {len(cookies)} cookies capturés")
        
        # Afficher les cookies importants
        important_cookies = [c for c in cookies if any(key in c['name'].lower() for key in ['session', 'token', 'auth', 'jwt', 'access'])]
        if important_cookies:
            print("🔑 Cookies importants trouvés:")
            for cookie in important_cookies:
                print(f"   - {cookie['name']}: {cookie['value'][:50]}...")
        else:
            print("   Aucun cookie d'authentification trouvé")
    
    async def save_results(self):
        """Sauvegarde tous les résultats"""
        print("\n" + "="*60)
        print("💾 SAUVEGARDE DES RÉSULTATS")
        print("="*60)
        
        os.makedirs('data/api_exploration/seloger', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Résumé
        summary = {
            'timestamp': timestamp,
            'site': 'seloger',
            'total_requests': len(self.all_requests),
            'total_responses': len(self.all_responses),
            'api_requests': len([r for r in self.all_requests if r['is_api']]),
            'api_responses': len([r for r in self.all_responses if r['is_api']]),
            'api_endpoints': len(self.api_endpoints),
            'cookies_count': len(self.cookies),
            'auth_tokens': list(self.auth_tokens.keys()),
        }
        
        # Sauvegarder le résumé
        summary_path = f'data/api_exploration/seloger/summary_{timestamp}.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"✅ Résumé sauvegardé: {summary_path}")
        
        # Sauvegarder toutes les requêtes
        requests_path = f'data/api_exploration/seloger/requests_{timestamp}.json'
        with open(requests_path, 'w', encoding='utf-8') as f:
            json.dump(self.all_requests, f, ensure_ascii=False, indent=2)
        print(f"✅ Requêtes sauvegardées: {requests_path}")
        
        # Sauvegarder toutes les réponses
        responses_path = f'data/api_exploration/seloger/responses_{timestamp}.json'
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
        endpoints_path = f'data/api_exploration/seloger/endpoints_{timestamp}.json'
        with open(endpoints_path, 'w', encoding='utf-8') as f:
            json.dump(self.api_endpoints, f, ensure_ascii=False, indent=2)
        print(f"✅ Endpoints sauvegardés: {endpoints_path}")
        
        # Sauvegarder les cookies
        cookies_path = f'data/api_exploration/seloger/cookies_{timestamp}.json'
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(self.cookies, f, ensure_ascii=False, indent=2)
        print(f"✅ Cookies sauvegardés: {cookies_path}")
        
        # Sauvegarder les tokens d'authentification
        tokens_path = f'data/api_exploration/seloger/tokens_{timestamp}.json'
        with open(tokens_path, 'w', encoding='utf-8') as f:
            json.dump(self.auth_tokens, f, ensure_ascii=False, indent=2)
        print(f"✅ Tokens sauvegardés: {tokens_path}")
        
        # Créer un rapport textuel
        report_path = f'data/api_exploration/seloger/report_{timestamp}.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("RAPPORT D'EXPLORATION API SELOGER\n")
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
        print("\n✅ Tous les résultats ont été sauvegardés dans data/api_exploration/seloger/")
    
    async def cleanup(self):
        """Ferme le navigateur"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def main():
    """Fonction principale"""
    print("🚀 EXPLORATION AVANCÉE DE L'API SELOGER")
    print("="*60)
    print("Ce script va capturer TOUTES les requêtes réseau")
    print("pendant la navigation sur SeLoger")
    print("="*60)
    
    explorer = SeLogerAPIExplorer()
    
    try:
        await explorer.setup()
        
        # Phase 1: Page d'accueil
        await explorer.explore_homepage()
        
        # Phase 2: Authentification (AVANT la recherche pour éviter CAPTCHA)
        await explorer.explore_authentication()
        
        # Phase 3: Recherche (après connexion)
        await explorer.explore_search()
        
        # Phase 4: Détails d'annonce
        await explorer.explore_property_details()
        
        # Sauvegarder tous les résultats
        await explorer.save_results()
        
        print("\n✅ Exploration terminée avec succès!")
        print("📁 Consultez les fichiers dans data/api_exploration/seloger/ pour analyser les résultats")
        
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
        await explorer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

