#!/usr/bin/env python3
"""
Module pour extraire les données des appartements depuis Jinka
Utilise l'API en priorité, avec fallback sur le scraping HTML si nécessaire
"""

import json
import re
import time
from typing import List, Dict, Optional
from datetime import datetime
from jinka_api import JinkaAPIClient
from config_jinka import JINKA_DASHBOARD_URL
from cookie_manager import CookieManager


class JinkaScraper:
    """Scraper pour extraire les données des appartements Jinka"""
    
    def __init__(self):
        self.api_client = JinkaAPIClient()
        self.cookie_manager = CookieManager()
    
    def _extract_apartment_id_from_url(self, url: str) -> Optional[str]:
        """Extrait l'ID de l'appartement depuis une URL"""
        if not url:
            return None
        
        # Format: https://www.jinka.fr/alert_result?token=...&ad=93828578
        match = re.search(r'[?&]ad=(\d+)', url)
        if match:
            return match.group(1)
        
        # Format alternatif
        match = re.search(r'/ad/(\d+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def _normalize_apartment_data(self, raw_data: Dict) -> Dict:
        """
        Normalise les données d'un appartement au format standard
        
        Args:
            raw_data: Données brutes de l'appartement
            
        Returns:
            Dictionnaire normalisé
        """
        apartment_id = str(raw_data.get('id', raw_data.get('ad_id', raw_data.get('apartment_id', ''))))
        
        # Extraire l'ID depuis l'URL si nécessaire
        if not apartment_id or apartment_id == 'None':
            url = raw_data.get('url', raw_data.get('link', ''))
            apartment_id = self._extract_apartment_id_from_url(url) or 'unknown'
        
        # Construire l'URL si elle n'existe pas
        url = raw_data.get('url', raw_data.get('link', ''))
        if not url and apartment_id != 'unknown':
            # Construire l'URL depuis le token et l'ID
            from config_jinka import JINKA_ALERT_TOKEN
            url = f"https://www.jinka.fr/alert_result?token={JINKA_ALERT_TOKEN}&ad={apartment_id}"
        
        # Extraire le titre
        titre = raw_data.get('titre', raw_data.get('title', raw_data.get('name', '')))
        
        # Extraire le prix
        prix = raw_data.get('prix', raw_data.get('price', raw_data.get('rent', '')))
        if isinstance(prix, (int, float)):
            prix = f"{prix:,.0f} €".replace(',', ' ')
        
        # Extraire la surface
        surface = raw_data.get('surface', raw_data.get('area', raw_data.get('size', '')))
        if isinstance(surface, (int, float)):
            surface = f"{surface} m²"
        
        # Extraire la localisation
        localisation = raw_data.get('localisation', raw_data.get('location', raw_data.get('address', '')))
        
        # Extraire les photos
        photos = raw_data.get('photos', raw_data.get('images', raw_data.get('pictures', [])))
        if isinstance(photos, str):
            photos = [photos]
        elif not isinstance(photos, list):
            photos = []
        
        # Normaliser les photos
        normalized_photos = []
        for photo in photos:
            if isinstance(photo, dict):
                normalized_photos.append(photo)
            elif isinstance(photo, str) and photo:
                normalized_photos.append({'url': photo})
        
        # Extraire la date de création de l'annonce depuis les données brutes
        # Chercher dans plusieurs champs possibles
        date_creation_annonce = None
        date_fields = [
            'created_at', 'date_creation', 'published_at', 'date_publication',
            'created', 'date', 'creation_date', 'publication_date',
            'date_created', 'date_published', 'posted_at', 'date_posted',
            'annonce_date', 'ad_created_at', 'ad_date'
        ]
        for field in date_fields:
            if field in raw_data and raw_data[field]:
                date_creation_annonce = raw_data[field]
                break
        
        # Normaliser le format de date si nécessaire
        if date_creation_annonce:
            # Si c'est un timestamp Unix
            if isinstance(date_creation_annonce, (int, float)):
                try:
                    date_creation_annonce = datetime.fromtimestamp(date_creation_annonce).isoformat()
                except (ValueError, OSError):
                    pass
            # Si c'est déjà une chaîne ISO, la garder telle quelle
            elif isinstance(date_creation_annonce, str):
                # Essayer de parser et reformater si nécessaire
                try:
                    # Formats communs
                    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                        try:
                            dt = datetime.strptime(date_creation_annonce, fmt)
                            date_creation_annonce = dt.isoformat()
                            break
                        except ValueError:
                            continue
                except:
                    pass
        
        result = {
            'id': apartment_id,
            'titre': titre,
            'url': url,
            'prix': prix,
            'surface': surface,
            'localisation': localisation,
            'photos': normalized_photos,
            'date_ajout': datetime.now().isoformat(),  # Date d'ajout dans notre système
            'source': 'jinka_alert',
            'raw_data': raw_data  # Garder les données brutes pour référence
        }
        
        # Ajouter la date de création de l'annonce si disponible
        if date_creation_annonce:
            result['date_creation_annonce'] = date_creation_annonce
        
        return result
    
    def extract_apartments_from_api(self, filter_type: str = "all", max_pages: int = 50) -> List[Dict]:
        """
        Extrait les appartements depuis l'API (endpoint dashboard)
        
        Args:
            filter_type: Type de filtre ("all", "seen", "unseen", etc.)
            max_pages: Nombre maximum de pages à récupérer (défaut: 10)
        
        Returns:
            Liste des appartements normalisés
        """
        print("🔍 Extraction des appartements depuis l'API...")
        
        all_apartments = []
        page = 1
        rrkey = ""
        
        while page <= max_pages:
            # Récupérer les résultats de la page actuelle
            results = self.api_client.get_alert_results(filter_type=filter_type, page=page, rrkey=rrkey)
            
            if not results:
                if page == 1:
                    print("⚠️  Aucun résultat trouvé via l'API")
                    return []
                else:
                    # Plus de pages disponibles
                    break
            
            # L'endpoint dashboard retourne les appartements dans 'ads'
            if 'ads' in results and isinstance(results['ads'], list):
                ads = results['ads']
                print(f"✅ Page {page}: {len(ads)} appartement(s) trouvé(s)")
                
                # Si aucune annonce sur cette page, on a fini
                if len(ads) == 0:
                    break
                
                for ad in ads:
                    if isinstance(ad, dict):
                        normalized = self._normalize_apartment_data(ad)
                        all_apartments.append(normalized)
                
                # Vérifier s'il y a une page suivante
                pagination = results.get('pagination', {})
                
                # La pagination peut utiliser soit 'has_more'/'next_rrkey', soit 'nbPages'
                nb_pages = pagination.get('nbPages', 0)
                has_more = pagination.get('has_more', False)
                next_rrkey = pagination.get('next_rrkey', '')
                
                # Si on connaît le nombre total de pages, vérifier si on a atteint la dernière
                if nb_pages > 0:
                    print(f"   📄 Pagination: {page}/{nb_pages} pages (total: {pagination.get('totals', {}).get('all', 'N/A')} appartements)")
                    if page >= nb_pages:
                        print(f"   ✅ Dernière page atteinte")
                        break
                    # Continuer à la page suivante
                    page += 1
                    if next_rrkey:
                        rrkey = next_rrkey
                    else:
                        rrkey = ""  # Réinitialiser si pas de rrkey
                    continue
                
                # Sinon, utiliser has_more/next_rrkey (méthode alternative)
                if not has_more and not next_rrkey:
                    # Plus de pages
                    break
                
                # Préparer la page suivante
                page += 1
                if next_rrkey:
                    rrkey = next_rrkey
                else:
                    rrkey = ""  # Réinitialiser si pas de rrkey
            else:
                # Structure inattendue
                print(f"⚠️  Structure de réponse inattendue. Clés: {list(results.keys())[:10]}")
                break
        
        print(f"✅ {len(all_apartments)} appartement(s) extrait(s) depuis l'API ({page} page(s))")
        return all_apartments
    
    def extract_apartments_from_html(self, html_content: str) -> List[Dict]:
        """
        Extrait les appartements depuis du HTML (fallback)
        
        Args:
            html_content: Contenu HTML de la page
            
        Returns:
            Liste des appartements normalisés
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("❌ beautifulsoup4 n'est pas installé. Impossible de faire du scraping HTML.")
            return []
        
        print("🔍 Extraction des appartements depuis le HTML...")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        apartments = []
        
        # Chercher des scripts JSON qui pourraient contenir les données
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Chercher récursivement des appartements dans les données
                apartments.extend(self._find_apartments_in_data(data))
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Chercher des éléments avec des attributs data-*
        data_elements = soup.find_all(attrs={'data-ad-id': True})
        for element in data_elements:
            apartment_id = element.get('data-ad-id')
            # Extraire d'autres données depuis les attributs ou le contenu
            # (à adapter selon la structure HTML réelle)
            pass
        
        print(f"✅ {len(apartments)} appartement(s) extrait(s) depuis le HTML")
        return apartments
    
    def extract_apartments_with_selenium(self) -> List[Dict]:
        """
        Extrait les appartements depuis le dashboard en utilisant Selenium
        
        Returns:
            Liste des appartements normalisés
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
        except ImportError:
            print("❌ Selenium n'est pas installé. Impossible de faire du scraping avec navigateur.")
            return []
        
        print("🌐 Ouverture du navigateur avec Selenium...")
        
        # Configuration Chrome (sans headless pour mieux charger les données)
        chrome_options = Options()
        # Ne pas utiliser headless pour mieux charger les données dynamiques
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        # Garder le navigateur ouvert en cas d'erreur
        chrome_options.add_experimental_option("detach", True)
        
        driver = None
        apartments = []
        network_logs = []
        
        try:
            # Créer le driver Chrome
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            
            # Activer le logging réseau
            driver.execute_cdp_cmd('Network.enable', {})
            
            # Accéder au dashboard
            from config_jinka import JINKA_DASHBOARD_URL
            print(f"📡 Accès à {JINKA_DASHBOARD_URL}")
            driver.get(JINKA_DASHBOARD_URL)
            
            # Attendre que la page charge et que les données soient disponibles
            print("⏳ Attente du chargement des données...")
            
            # Attendre que React charge
            try:
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                # Attendre que React soit monté
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return typeof window.__NEXT_DATA__ !== 'undefined' || document.getElementById('root').children.length > 0")
                )
            except Exception:
                pass
            
            # Vérifier qu'on est bien connecté (pas redirigé vers login)
            current_url = driver.current_url
            print(f"   📍 URL actuelle: {current_url[:80]}...")
            
            if '/sign/in' in current_url:
                print("   ⚠️  Redirection vers la page de connexion détectée")
                print("   🔄 Rechargement de la page avec les cookies...")
                # Recharger avec les cookies
                saved_cookies = self.cookie_manager.load_cookies()
                if saved_cookies:
                    self.cookie_manager.add_cookies_to_driver(driver, saved_cookies)
                driver.get(JINKA_DASHBOARD_URL)
                time.sleep(5)
            
            # Attendre un peu plus pour que les données se chargent
            print("⏳ Attente du chargement complet des données (30 secondes)...")
            time.sleep(30)  # Attendre plus longtemps pour que React charge tout
            
            # Vérifier à nouveau l'URL
            final_url = driver.current_url
            print(f"   📍 URL finale: {final_url[:80]}...")
            if '/sign/in' in final_url:
                print("   ❌ Toujours sur la page de connexion - les cookies ne fonctionnent pas")
                return []
            
            # Essayer de faire défiler la page pour déclencher le chargement lazy
            try:
                print("   📜 Défilement pour déclencher le chargement lazy...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(3)
                # Re-défiler pour être sûr
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
            except:
                pass
            
            # Sauvegarder les cookies après chargement (au cas où ils auraient été mis à jour)
            try:
                current_cookies = driver.get_cookies()
                if current_cookies:
                    self.cookie_manager.save_cookies(current_cookies, source='selenium')
            except Exception:
                pass
            
            # Méthode alternative: Appeler directement l'API avec les cookies de session
            print("🍪 Récupération des cookies de session...")
            try:
                cookies = driver.get_cookies()
                cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                
                # Appeler directement l'API avec les cookies
                import requests
                session = requests.Session()
                session.cookies.update(cookie_dict)
                session.headers.update({
                    'User-Agent': driver.execute_script("return navigator.userAgent;"),
                    'Referer': JINKA_DASHBOARD_URL
                })
                
                # Essayer d'appeler l'API directement
                api_url = f"https://api.jinka.fr/apiv2/alert/{self.api_client.alert_token}"
                print(f"   📡 Appel direct de l'API avec cookies: {api_url}")
                response = session.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Données récupérées de l'API")
                    print(f"      Structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    
                    # Vérifier si l'alerte a des résultats non lus
                    if isinstance(data, dict) and data.get('has_unread_result'):
                        print(f"      ℹ️  L'alerte a des résultats non lus (has_unread_result: true)")
                    
                    # Chercher des appartements dans les données
                    found = self._find_apartments_in_data(data)
                    if found:
                        apartments.extend(found)
                        print(f"      ✅ Trouvé {len(found)} appartement(s)")
                    
                    # Essayer différents endpoints pour récupérer les résultats
                    if isinstance(data, dict):
                        print(f"      🔍 Recherche d'endpoints pour les résultats...")
                        # Essayer différents endpoints possibles
                        possible_endpoints = [
                            'results', 'ads', 'matches', 'listings', 
                            'apartments', 'properties', 'annonces',
                            'unread', 'new', 'latest'
                        ]
                        for endpoint in possible_endpoints:
                            try:
                                result_url = f"{api_url}/{endpoint}"
                                result_response = session.get(result_url, timeout=10)
                                if result_response.status_code == 200:
                                    result_data = result_response.json()
                                    print(f"         ✅ Endpoint /{endpoint} accessible")
                                    found = self._find_apartments_in_data(result_data)
                                    if found:
                                        apartments.extend(found)
                                        print(f"         ✅ Trouvé {len(found)} appartement(s) dans /{endpoint}")
                                        break
                                    else:
                                        print(f"         ℹ️  Pas d'appartements dans /{endpoint}, structure: {type(result_data)}")
                                elif result_response.status_code != 404:
                                    print(f"         ⚠️  Endpoint /{endpoint} retourne {result_response.status_code}")
                            except Exception as e:
                                pass
                        
                        # Essayer aussi avec des paramètres de pagination
                        try:
                            result_url = f"{api_url}/results?page=1&limit=100"
                            result_response = session.get(result_url, timeout=10)
                            if result_response.status_code == 200:
                                result_data = result_response.json()
                                found = self._find_apartments_in_data(result_data)
                                if found:
                                    apartments.extend(found)
                                    print(f"      ✅ Trouvé {len(found)} appartement(s) avec pagination")
                        except Exception:
                            pass
                else:
                    print(f"   ⚠️  API retourne status {response.status_code}")
            except Exception as e:
                print(f"   ⚠️  Erreur lors de l'appel API avec cookies: {e}")
                import traceback
                traceback.print_exc()
            
            # Récupérer les logs de performance (requêtes réseau) pour debug
            print("📡 Récupération des logs réseau (debug)...")
            try:
                logs = driver.get_log('performance')
                for log in logs:
                    message = json.loads(log['message'])
                    msg = message.get('message', {})
                    method = msg.get('method')
                    params = msg.get('params', {})
                    
                    if method == 'Network.responseReceived':
                        response = params.get('response', {})
                        url = response.get('url', '')
                        
                        if 'api.jinka.fr' in url and 'alert' in url:
                            network_logs.append({
                                'url': url,
                                'status': response.get('status'),
                                'mimeType': response.get('mimeType', '')
                            })
                            print(f"   📡 Requête détectée: {url[:80]}... (status: {response.get('status')})")
            except Exception as e:
                print(f"   ⚠️  Erreur lors de la récupération des logs: {e}")
            
            # Chercher les données JSON dans les scripts
            print("🔍 Recherche des données dans la page...")
            
            # Méthode 1: Utiliser Chrome DevTools Protocol pour récupérer les réponses
            try:
                # Récupérer les réponses depuis les logs de performance
                if network_logs:
                    print(f"   🔍 Analyse de {len(network_logs)} requête(s) réseau...")
                    for i, log_entry in enumerate(network_logs):
                        url = log_entry.get('url', '')
                        request_id = log_entry.get('requestId')
                        status = log_entry.get('status', 0)
                        
                        if 'api.jinka.fr' in url and request_id and status == 200:
                            try:
                                # Récupérer le body de la réponse via CDP
                                response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                body_text = response_body.get('body', '')
                                
                                if body_text:
                                    # Décode base64 si nécessaire
                                    if response_body.get('base64Encoded'):
                                        import base64
                                        body_text = base64.b64decode(body_text).decode('utf-8')
                                    
                                    try:
                                        data = json.loads(body_text)
                                        print(f"      📦 Données récupérées de {url[:60]}...")
                                        
                                        # Chercher des appartements dans les données
                                        found = self._find_apartments_in_data(data)
                                        if found:
                                            apartments.extend(found)
                                            print(f"      ✅ Trouvé {len(found)} appartement(s) dans {url[:60]}...")
                                        else:
                                            # Si pas d'appartements directs, peut-être que les données contiennent des références
                                            print(f"      ℹ️  Données récupérées mais pas d'appartements trouvés directement")
                                            print(f"         Structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                                    except json.JSONDecodeError as e:
                                        print(f"      ⚠️  Erreur JSON pour {url[:60]}: {e}")
                            except Exception as e:
                                print(f"      ⚠️  Erreur pour {url[:60]}: {e}")
            except Exception as e:
                print(f"   ⚠️  Erreur lors de l'analyse des logs réseau: {e}")
                import traceback
                traceback.print_exc()
            
            # Méthode 1b: Essayer de récupérer les données depuis React/Redux/Next.js
            try:
                print("   🔍 Recherche des données dans React/Redux/Next.js...")
                
                # Chercher dans __NEXT_DATA__
                next_data = driver.execute_script("""
                    if (window.__NEXT_DATA__) {
                        return window.__NEXT_DATA__.props || window.__NEXT_DATA__.pageProps || window.__NEXT_DATA__;
                    }
                    return null;
                """)
                if next_data:
                    found = self._find_apartments_in_data(next_data)
                    if found:
                        apartments.extend(found)
                        print(f"      ✅ Trouvé {len(found)} appartement(s) dans __NEXT_DATA__")
                
                # Chercher dans le state React via React DevTools
                react_data = driver.execute_script("""
                    // Essayer de trouver les composants React montés
                    const results = [];
                    
                    // Chercher dans window.__REACT_DEVTOOLS_GLOBAL_HOOK__
                    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
                        try {
                            const hook = window.__REACT_DEVTOOLS_GLOBAL_HOOK__;
                            if (hook.renderers) {
                                for (let id in hook.renderers) {
                                    const renderer = hook.renderers[id];
                                    if (renderer && renderer.findFiberByHostInstance) {
                                        // Essayer d'accéder au fiber root
                                        const roots = hook.getFiberRoots(id);
                                        if (roots) {
                                            results.push({source: 'react_devtools', data: Array.from(roots)});
                                        }
                                    }
                                }
                            }
                        } catch(e) {}
                    }
                    
                    // Chercher dans toutes les variables window
                    const windowVars = {};
                    for (let key in window) {
                        try {
                            if (key.startsWith('__') || key.includes('REACT') || key.includes('REDUX') || key.includes('STATE')) {
                                const value = window[key];
                                if (value && typeof value === 'object') {
                                    const str = JSON.stringify(value).substring(0, 1000);
                                    if (str.includes('apartment') || str.includes('ad') || str.includes('listing') || str.includes('result')) {
                                        windowVars[key] = typeof value;
                                    }
                                }
                            }
                        } catch(e) {}
                    }
                    
                    return {react: results, windowVars: windowVars};
                """)
                
                if react_data.get('windowVars'):
                    print(f"      ℹ️  Variables window trouvées: {list(react_data['windowVars'].keys())}")
                
                # Chercher dans le DOM pour des données JSON cachées
                json_data = driver.execute_script("""
                    const results = [];
                    // Chercher tous les scripts avec type="application/json"
                    const scripts = document.querySelectorAll('script[type="application/json"]');
                    scripts.forEach(script => {
                        try {
                            const data = JSON.parse(script.textContent);
                            results.push(data);
                        } catch(e) {}
                    });
                    
                    // Chercher des attributs data-* qui pourraient contenir des IDs
                    const dataElements = document.querySelectorAll('[data-id], [data-ad-id], [data-apartment-id]');
                    const ids = [];
                    dataElements.forEach(el => {
                        const id = el.getAttribute('data-id') || el.getAttribute('data-ad-id') || el.getAttribute('data-apartment-id');
                        if (id && id.length > 5 && !isNaN(id)) {
                            ids.push(id);
                        }
                    });
                    
                    return {scripts: results, ids: ids};
                """)
                
                if json_data.get('scripts'):
                    for script_data in json_data['scripts']:
                        found = self._find_apartments_in_data(script_data)
                        if found:
                            apartments.extend(found)
                            print(f"      ✅ Trouvé {len(found)} appartement(s) dans un script JSON")
                
                if json_data.get('ids'):
                    print(f"      ℹ️  {len(json_data['ids'])} ID(s) trouvé(s) dans les attributs data-*")
                    # Créer des appartements basiques depuis les IDs
                    for apt_id in json_data['ids'][:20]:  # Limiter à 20 pour éviter trop de faux positifs
                        if apt_id not in {apt.get('id') for apt in apartments}:
                            apt_data = {
                                'id': apt_id,
                                'url': f"https://www.jinka.fr/alert_result?token={self.api_client.alert_token}&ad={apt_id}"
                            }
                            normalized = self._normalize_apartment_data(apt_data)
                            apartments.append(normalized)
                            print(f"      ✅ Appartement {apt_id} trouvé via attribut data-*")
                
            except Exception as e:
                print(f"      ⚠️  Erreur lors de la recherche React: {e}")
            
            # Méthode 2: Chercher dans les scripts avec type="application/json"
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                script_type = script.get_attribute("type")
                if script_type == "application/json":
                    try:
                        script_content = script.get_attribute("innerHTML")
                        if script_content:
                            data = json.loads(script_content)
                            found = self._find_apartments_in_data(data)
                            if found:
                                apartments.extend(found)
                                print(f"   ✅ Trouvé {len(found)} appartement(s) dans un script JSON")
                    except (json.JSONDecodeError, Exception) as e:
                        continue
            
            # Méthode 3: Chercher dans window.__NEXT_DATA__ ou autres variables globales
            try:
                next_data = driver.execute_script("""
                    return window.__NEXT_DATA__ || 
                           window.__INITIAL_STATE__ || 
                           window.__APOLLO_STATE__ ||
                           window.__REDUX_STATE__ ||
                           null;
                """)
                if next_data:
                    found = self._find_apartments_in_data(next_data)
                    if found:
                        apartments.extend(found)
                        print(f"   ✅ Trouvé {len(found)} appartement(s) dans les données globales")
            except Exception as e:
                pass
            
            # Méthode 4: Chercher dans le localStorage/sessionStorage
            try:
                storage_data = driver.execute_script("""
                    const data = {};
                    try { data.localStorage = JSON.parse(JSON.stringify(localStorage)); } catch(e) {}
                    try { data.sessionStorage = JSON.parse(JSON.stringify(sessionStorage)); } catch(e) {}
                    return data;
                """)
                for storage_type, storage in storage_data.items():
                    for key, value in storage.items():
                        try:
                            if isinstance(value, str):
                                parsed = json.loads(value)
                                found = self._find_apartments_in_data(parsed)
                                if found:
                                    apartments.extend(found)
                                    print(f"   ✅ Trouvé {len(found)} appartement(s) dans {storage_type}.{key}")
                        except:
                            pass
            except Exception as e:
                pass
            
            # Méthode 3: Chercher des éléments HTML avec des attributs data-*
            try:
                ad_elements = driver.find_elements(By.CSS_SELECTOR, "[data-ad-id], [data-id], [data-apartment-id]")
                for element in ad_elements:
                    apartment_id = element.get_attribute("data-ad-id") or element.get_attribute("data-id") or element.get_attribute("data-apartment-id")
                    if apartment_id:
                        # Extraire d'autres informations depuis l'élément
                        try:
                            title = element.find_element(By.CSS_SELECTOR, ".title, h2, h3, [class*='title']").text
                            price = element.find_element(By.CSS_SELECTOR, ".price, [class*='price']").text
                            # Construire un objet appartement basique
                            apt_data = {
                                'id': apartment_id,
                                'titre': title,
                                'prix': price,
                                'url': f"https://www.jinka.fr/alert_result?token={self.api_client.alert_token}&ad={apartment_id}"
                            }
                            normalized = self._normalize_apartment_data(apt_data)
                            apartments.append(normalized)
                        except Exception:
                            pass
            except Exception as e:
                pass
            
            # Méthode 5: Chercher dans le HTML avec BeautifulSoup
            html_content = driver.page_source
            soup_apartments = self.extract_apartments_from_html(html_content)
            if soup_apartments:
                # Éviter les doublons
                existing_ids = {apt.get('id') for apt in apartments}
                for apt in soup_apartments:
                    if apt.get('id') not in existing_ids:
                        apartments.append(apt)
            
            # Méthode 6: Chercher des liens vers les annonces dans le HTML avec Selenium
            try:
                print("   🔍 Recherche d'appartements dans le DOM...")
                
                # Attendre que les éléments se chargent
                try:
                    WebDriverWait(driver, 15).until(
                        lambda d: len(d.find_elements(By.TAG_NAME, "a")) > 10
                    )
                except:
                    pass
                
                # Chercher des liens avec pattern /alert_result?token=...&ad=
                links = driver.find_elements(By.CSS_SELECTOR, "a[href*='alert_result'], a[href*='ad='], a[href*='/ad/']")
                print(f"      📋 {len(links)} lien(s) trouvé(s) avec alert_result ou ad=")
                
                # Extraire les IDs depuis le HTML source (méthode la plus fiable)
                # Récupérer le HTML après avoir attendu
                print("      📄 Récupération du HTML source...")
                html_content = driver.page_source
                html_length = len(html_content)
                print(f"      📏 Taille du HTML: {html_length:,} caractères")
                
                import re
                
                # Chercher tous les IDs dans les URLs (plusieurs patterns)
                # Pattern 1: ad=12345678
                ad_ids_pattern1 = re.findall(r'[?&]ad=(\d{6,})', html_content)
                # Pattern 2: ad=12345678 dans les href
                ad_ids_pattern2 = re.findall(r'href=["\'].*?[?&]ad=(\d{6,})', html_content)
                # Pattern 3: ad= suivi de chiffres (plus permissif)
                ad_ids_pattern3 = re.findall(r'ad=(\d{5,})', html_content)
                
                # Combiner tous les patterns
                all_ad_ids = ad_ids_pattern1 + ad_ids_pattern2 + ad_ids_pattern3
                ad_ids_in_html = list(set(all_ad_ids))  # Dédupliquer
                
                print(f"      🔍 Recherche de pattern ad= dans le HTML...")
                print(f"         Pattern 1: {len(ad_ids_pattern1)} IDs")
                print(f"         Pattern 2: {len(ad_ids_pattern2)} IDs")
                print(f"         Pattern 3: {len(ad_ids_pattern3)} IDs")
                print(f"         Total unique: {len(ad_ids_in_html)} IDs")
                
                if ad_ids_in_html:
                    unique_ids = list(set(ad_ids_in_html))
                    print(f"      📋 {len(unique_ids)} ID(s) unique(s) trouvé(s) dans le HTML")
                    
                    # Créer des appartements depuis ces IDs
                    for apt_id in unique_ids:
                        # Ignorer le token de l'alerte lui-même
                        if apt_id == self.api_client.alert_token:
                            continue
                        
                        if apt_id not in {apt.get('id') for apt in apartments}:
                            # Essayer d'extraire plus d'infos depuis le HTML autour de cet ID
                            # Chercher le contexte autour de l'ID dans le HTML (titre, prix, etc.)
                            context_pattern = f'ad={re.escape(apt_id)}[^>]*>([^<]{10,200})'
                            matches = re.findall(context_pattern, html_content, re.IGNORECASE | re.DOTALL)
                            
                            title = ""
                            if matches:
                                # Prendre le premier match et nettoyer
                                title = re.sub(r'\s+', ' ', matches[0]).strip()[:100]
                            
                            # Chercher aussi dans un contexte plus large
                            if not title:
                                wide_pattern = f'(.{0,200})ad={re.escape(apt_id)}(.{0,200})'
                                wide_matches = re.findall(wide_pattern, html_content, re.IGNORECASE | re.DOTALL)
                                if wide_matches:
                                    context = wide_matches[0][0] + wide_matches[0][1]
                                    # Chercher des patterns de titre (Paris, m², pièces, etc.)
                                    title_match = re.search(r'(Paris\s+\d+e[^<]{0,50})', context, re.IGNORECASE)
                                    if title_match:
                                        title = title_match.group(1).strip()
                            
                            apt_data = {
                                'id': apt_id,
                                'titre': title or f"Appartement {apt_id}",
                                'url': f"https://www.jinka.fr/alert_result?token={self.api_client.alert_token}&ad={apt_id}",
                            }
                            normalized = self._normalize_apartment_data(apt_data)
                            apartments.append(normalized)
                            print(f"      ✅ Appartement {apt_id} trouvé: {title[:50] if title else 'N/A'}")
                
                # Chercher aussi dans tous les liens pour trouver des patterns d'ID
                all_links = driver.find_elements(By.TAG_NAME, "a")
                print(f"      📋 {len(all_links)} lien(s) total trouvé(s)")
                
                # Chercher des éléments qui pourraient contenir des IDs d'appartements
                # (cards, items, listings, etc.)
                potential_containers = driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='card'], [class*='item'], [class*='listing'], [class*='apartment'], [class*='ad'], [data-id], [data-ad-id]")
                print(f"      📋 {len(potential_containers)} conteneur(s) potentiel(s) trouvé(s)")
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if not href:
                            continue
                        
                        apt_id = self._extract_apartment_id_from_url(href)
                        if apt_id and apt_id != self.api_client.alert_token:  # Exclure le token de l'alerte
                            # Essayer d'extraire le titre depuis le lien ou son parent
                            title = link.text.strip()
                            if not title or len(title) < 5:
                                try:
                                    parent = link.find_element(By.XPATH, "./ancestor::*[contains(@class, 'card') or contains(@class, 'item') or contains(@class, 'listing')][1]")
                                    title_elem = parent.find_elements(By.CSS_SELECTOR, "h2, h3, h4, [class*='title'], [class*='Title']")
                                    if title_elem:
                                        title = title_elem[0].text.strip()
                                except:
                                    pass
                            
                            if title and apt_id not in {apt.get('id') for apt in apartments}:
                                # Essayer d'extraire d'autres infos (prix, surface, etc.)
                                try:
                                    parent = link.find_element(By.XPATH, "./ancestor::*[contains(@class, 'card') or contains(@class, 'item')][1]")
                                    price_elem = parent.find_elements(By.CSS_SELECTOR, "[class*='price'], [class*='Price']")
                                    price = price_elem[0].text.strip() if price_elem else ""
                                    
                                    surface_elem = parent.find_elements(By.CSS_SELECTOR, "[class*='surface'], [class*='area'], [class*='size']")
                                    surface = surface_elem[0].text.strip() if surface_elem else ""
                                except:
                                    price = ""
                                    surface = ""
                                
                                apt_data = {
                                    'id': apt_id,
                                    'titre': title,
                                    'prix': price,
                                    'surface': surface,
                                    'url': href if href.startswith('http') else f"https://www.jinka.fr{href}",
                                }
                                normalized = self._normalize_apartment_data(apt_data)
                                apartments.append(normalized)
                                print(f"      ✅ Trouvé appartement {apt_id}: {title[:50]}")
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"   ⚠️  Erreur lors de la recherche dans le DOM: {e}")
            
            # Méthode 7: Chercher dans le HTML avec BeautifulSoup (fallback)
            try:
                from bs4 import BeautifulSoup
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Chercher des liens avec pattern /alert_result?token=...&ad=
                links = soup.find_all('a', href=re.compile(r'alert_result.*ad=\d+'))
                for link in links:
                    href = link.get('href', '')
                    apt_id = self._extract_apartment_id_from_url(href)
                    if apt_id and apt_id != self.api_client.alert_token and apt_id not in {apt.get('id') for apt in apartments}:
                        title = link.get_text(strip=True)
                        if not title or len(title) < 5:
                            parent = link.find_parent(['div', 'article', 'section'])
                            if parent:
                                title_elem = parent.find(['h2', 'h3', 'h4'], class_=re.compile('title', re.I))
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                        
                        if title:
                            apt_data = {
                                'id': apt_id,
                                'titre': title,
                                'url': href if href.startswith('http') else f"https://www.jinka.fr{href}",
                            }
                            normalized = self._normalize_apartment_data(apt_data)
                            apartments.append(normalized)
                            print(f"   ✅ Trouvé appartement {apt_id} depuis un lien HTML (BeautifulSoup)")
            except Exception as e:
                print(f"   ⚠️  Erreur lors de la recherche de liens BeautifulSoup: {e}")
            
            # Dédupliquer par ID
            seen_ids = set()
            unique_apartments = []
            for apt in apartments:
                apt_id = str(apt.get('id', ''))
                if apt_id and apt_id not in seen_ids:
                    seen_ids.add(apt_id)
                    unique_apartments.append(apt)
            
            apartments = unique_apartments
            
            print(f"✅ {len(apartments)} appartement(s) unique(s) extrait(s) avec Selenium")
            
        except Exception as e:
            print(f"❌ Erreur lors du scraping avec Selenium: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if driver:
                driver.quit()
                print("🔒 Navigateur fermé")
        
        return apartments
    
    def _find_apartments_in_data(self, data, depth=0) -> List[Dict]:
        """
        Cherche récursivement des appartements dans une structure de données
        
        Args:
            data: Structure de données (dict, list, etc.)
            depth: Profondeur de récursion (pour éviter les boucles infinies)
            
        Returns:
            Liste des appartements trouvés
        """
        if depth > 5:  # Limiter la profondeur
            return []
        
        apartments = []
        
        if isinstance(data, dict):
            # Vérifier si c'est un appartement (pas une alerte)
            # Les alertes ont des champs comme 'token', 'search_type', 'stops', etc.
            # Les appartements ont des champs comme 'ad_id', 'apartment_id', ou sont dans une liste de résultats
            is_alert = any(key in data for key in ['token', 'search_type', 'stops', 'line_stations', 'notification_channels'])
            
            # Vérifier si c'est un appartement réel
            has_apartment_id = any(key in data for key in ['ad_id', 'apartment_id', 'property_id', 'listing_id'])
            has_apartment_fields = any(key in data for key in ['titre', 'title', 'price', 'prix', 'surface', 'area', 'address', 'adresse'])
            
            # Si c'est un appartement (pas une alerte) et qu'il a des identifiants ou champs d'appartement
            if not is_alert and (has_apartment_id or (has_apartment_fields and ('id' in data or 'ad_id' in data))):
                normalized = self._normalize_apartment_data(data)
                apartments.append(normalized)
            else:
                # Chercher récursivement
                for value in data.values():
                    apartments.extend(self._find_apartments_in_data(value, depth + 1))
        
        elif isinstance(data, list):
            for item in data:
                apartments.extend(self._find_apartments_in_data(item, depth + 1))
        
        return apartments
    
    def get_all_apartments(self) -> List[Dict]:
        """
        Récupère tous les appartements (API en priorité, Selenium en fallback)
        
        Returns:
            Liste des appartements normalisés
        """
        # Essayer d'abord l'API
        apartments = self.extract_apartments_from_api()
        
        # Si aucun appartement trouvé, essayer le scraping avec Selenium
        if len(apartments) == 0:
            print("⚠️  Aucun appartement trouvé via l'API, tentative de scraping avec Selenium...")
            apartments = self.extract_apartments_with_selenium()
        
        return apartments
    
    def debug_raw_data_fields(self, apartment: Dict) -> None:
        """
        Affiche les champs disponibles dans les données brutes d'un appartement
        Utile pour déboguer et voir quelles données sont disponibles via l'API
        
        Args:
            apartment: Dictionnaire d'appartement normalisé
        """
        raw_data = apartment.get('raw_data', {})
        if raw_data:
            print("\n📋 Champs disponibles dans les données brutes:")
            print(f"   Clés: {list(raw_data.keys())}")
            
            # Chercher spécifiquement les champs liés aux dates
            date_fields = [k for k in raw_data.keys() if 'date' in k.lower() or 'created' in k.lower() or 'published' in k.lower()]
            if date_fields:
                print(f"\n📅 Champs de date trouvés:")
                for field in date_fields:
                    print(f"   - {field}: {raw_data.get(field)}")
            else:
                print("\n⚠️  Aucun champ de date trouvé dans les données brutes")
        else:
            print("\n⚠️  Aucune donnée brute disponible")


def main():
    """Test du scraper"""
    scraper = JinkaScraper()
    
    print("=" * 80)
    print("🔍 TEST DU SCRAPER JINKA")
    print("=" * 80)
    print()
    
    apartments = scraper.get_all_apartments()
    
    print()
    print(f"📊 Résultat: {len(apartments)} appartement(s) trouvé(s)")
    print()
    
    if apartments:
        print("Aperçu du premier appartement:")
        apt = apartments[0]
        print(f"  ID: {apt.get('id')}")
        print(f"  Titre: {apt.get('titre')}")
        print(f"  Prix: {apt.get('prix')}")
        print(f"  Surface: {apt.get('surface')}")
        print(f"  Localisation: {apt.get('localisation')}")
        print(f"  Photos: {len(apt.get('photos', []))}")
        print(f"  Date d'ajout (système): {apt.get('date_ajout', 'N/A')}")
        print(f"  Date création annonce: {apt.get('date_creation_annonce', 'Non disponible')}")
        
        # Afficher les champs disponibles dans les données brutes pour debug
        scraper.debug_raw_data_fields(apt)


if __name__ == "__main__":
    main()

