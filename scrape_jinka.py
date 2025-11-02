#!/usr/bin/env python3
"""
Scraper Jinka pour extraire les données des appartements
"""

import asyncio
import json
import math
import os
import re
import aiohttp
import sys
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from extract_exposition import ExpositionExtractor

load_dotenv()

class JinkaScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.apartments = []
        self.exposition_extractor = ExpositionExtractor()
        
    async def setup(self):
        """Initialise le navigateur et la page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)  # Mode visible
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
    async def login(self):
        """Se connecte à Jinka via Google"""
        print("🔐 Connexion à Jinka...")
        
        try:
            await self.page.goto('https://www.jinka.fr/sign/in')
            await self.page.wait_for_load_state('networkidle')
            
            # Cliquer sur "Continuer avec Google"
            google_button = self.page.locator('button:has-text("Continuer avec Google")')
            if await google_button.count() > 0:
                await google_button.click()
                await self.page.wait_for_load_state('networkidle')
                await self.page.wait_for_timeout(2000)
                
                # Saisir l'email
                email_input = self.page.locator('input[type="email"]')
                if await email_input.count() > 0:
                    await email_input.fill(os.getenv('JINKA_EMAIL'))
                    await self.page.keyboard.press('Enter')
                    await self.page.wait_for_timeout(2000)
                
                # Saisir le mot de passe
                password_input = self.page.locator('input[type="password"]')
                if await password_input.count() > 0:
                    await password_input.fill(os.getenv('JINKA_PASSWORD'))
                    await self.page.keyboard.press('Enter')
                    await self.page.wait_for_load_state('networkidle')
                    
                print("✅ Connexion réussie")
                return True
            else:
                print("❌ Bouton Google non trouvé")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    async def scrape_alert_page(self, alert_url):
        """Scrape une page d'alerte Jinka"""
        print(f"🏠 Scraping de l'alerte: {alert_url}")
        
        try:
            await self.page.goto(alert_url)
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(2000)
            
            # Attendre que la page se charge complètement
            await self.page.wait_for_timeout(3000)
            
            # Essayer différents sélecteurs pour les cartes d'appartements
            selectors = [
                'a[href*="alert_result"][href*="ad="]',  # Liens avec alert_result ET ad=
                'a[href*="alert_result"]',
                'a[href*="ad="]',
                'a.sc-bdVaJa.csp.sc-cJSrbW.doPXAe',  # Sélecteur exact d'après l'image
                'a.sc-bdVaJa',  # Sélecteur plus large
                '.apartment-card',
                '[data-testid="apartment-card"]',
                'a[href*="/alert_result"]'
            ]
            
            apartment_links = None
            count = 0
            
            for selector in selectors:
                try:
                    apartment_links = self.page.locator(selector)
                    count = await apartment_links.count()
                    if count > 0:
                        print(f"📋 {count} appartements trouvés avec sélecteur: {selector}")
                        break
                except:
                    continue
            
            if count == 0:
                print("🔍 Aucun appartement trouvé, debug de la page...")
                # Debug: afficher le contenu de la page
                page_content = await self.page.content()
                print(f"📄 Taille de la page: {len(page_content)} caractères")
                
                # Chercher tous les liens
                all_links = self.page.locator('a')
                all_links_count = await all_links.count()
                print(f"🔗 Total de liens sur la page: {all_links_count}")
                
                # Afficher les premiers liens trouvés
                for i in range(min(5, all_links_count)):
                    href = await all_links.nth(i).get_attribute('href')
                    print(f"   Lien {i+1}: {href}")
                
                return False
            
            # Extraire les URLs des appartements
            apartment_urls = []
            for i in range(count):
                href = await apartment_links.nth(i).get_attribute('href')
                print(f"   Lien {i+1}: href='{href}'")
                
                # Chercher les liens avec id= (format loueragile://) ou ad=
                if href and ('id=' in href or 'ad=' in href):
                    # Extraire l'ID de l'appartement
                    apartment_id = None
                    if 'id=' in href:
                        import re
                        match = re.search(r'id=(\d+)', href)
                        if match:
                            apartment_id = match.group(1)
                    elif 'ad=' in href:
                        import re
                        match = re.search(r'ad=(\d+)', href)
                        if match:
                            apartment_id = match.group(1)
                    
                    if apartment_id:
                        # Construire l'URL standard Jinka
                        full_url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apartment_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
                        apartment_urls.append(full_url)
                        print(f"   ✅ Appartement {i+1} (ID: {apartment_id}): {full_url}")
                    else:
                        print(f"   ❌ Lien {i+1} ignoré: impossible d'extraire l'ID")
                else:
                    print(f"   ❌ Lien {i+1} ignoré: pas de paramètre 'id=' ou 'ad='")
            
            print(f"🔗 {len(apartment_urls)} URLs d'appartements extraites")
            
            # Scraper chaque appartement
            for i, url in enumerate(apartment_urls):
                print(f"🏠 Scraping appartement {i+1}/{len(apartment_urls)}")
                apartment_data = await self.scrape_apartment(url)
                if apartment_data:
                    self.apartments.append(apartment_data)
                    await self.save_apartment(apartment_data)
                
                # Pause entre les requêtes
                await self.page.wait_for_timeout(1000)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur scraping alerte: {e}")
            return False
    
    async def scrape_apartment(self, url):
        """Scrape les détails d'un appartement"""
        try:
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(2000)
            
            # Extraire l'ID de l'appartement
            apartment_id = self.extract_apartment_id(url)
            
            # Extraire les données
            description = await self.extract_description()
            caracteristiques = await self.extract_caracteristiques()
            photos = await self.extract_photos()
            
            # Télécharger les photos localement
            await self.download_apartment_photos(apartment_id, photos)
            
            data = {
                'id': apartment_id,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'titre': await self.extract_titre(),
                'prix': await self.extract_prix(),
                'prix_m2': await self.extract_prix_m2(),
                'localisation': await self.extract_localisation(),
                'coordinates': await self.extract_coordinates(),
                'map_info': await self.extract_map_info(apartment_id),
                'surface': await self.extract_surface(),
                'pieces': await self.extract_pieces(),
                'date': await self.extract_date(),
                'transports': await self.extract_transports(),
                'description': description,
                'photos': photos,
                'caracteristiques': caracteristiques,
                'agence': await self.extract_agence(),
                'style_haussmannien': await self.extract_style_haussmannien()
            }
            
            # Ajouter l'analyse d'exposition contextuelle
            data['exposition'] = self.exposition_extractor.extract_exposition_ultimate(data)
            
            print(f"✅ Appartement {apartment_id} scrapé")
            return data
            
        except Exception as e:
            print(f"❌ Erreur scraping appartement {url}: {e}")
            return None
    
    def extract_apartment_id(self, url):
        """Extrait l'ID de l'appartement depuis l'URL"""
        match = re.search(r'ad=(\d+)', url)
        return match.group(1) if match else "unknown"
    
    async def extract_titre(self):
        """Extrait le titre de l'appartement"""
        try:
            # Chercher le titre dans différents sélecteurs possibles
            selectors = ['h1', '.title', '[data-testid="title"]', 'h2']
            for selector in selectors:
                element = self.page.locator(selector).first
                if await element.count() > 0:
                    text = await element.text_content()
                    if text and len(text.strip()) > 5:
                        return text.strip()
            return "Titre non trouvé"
        except:
            return "Titre non trouvé"
    
    async def extract_prix(self):
        """Extrait le prix principal"""
        try:
            # Sélecteur pour le prix principal
            price_element = self.page.locator('.hmmXKG, [class*="price"], .price').first
            if await price_element.count() > 0:
                text = await price_element.text_content()
                # Nettoyer le prix
                price = re.search(r'[\d\s]+€', text or '')
                return price.group(0).strip() if price else "Prix non trouvé"
            return "Prix non trouvé"
        except:
            return "Prix non trouvé"
    
    async def extract_prix_m2(self):
        """Extrait le prix au m²"""
        try:
            # Chercher le prix au m² près du prix principal
            price_elements = self.page.locator('text=/€\/m²/')
            if await price_elements.count() > 0:
                text = await price_elements.first.text_content()
                if text:
                    # Extraire et formater le prix au m²
                    match = re.search(r'([\d\s]+)\s*€\s*/?\s*m²', text, re.IGNORECASE)
                    if match:
                        prix_clean = match.group(1).strip().replace(' ', ' ')
                        return f"{prix_clean} € / m²"
            return None
        except:
            return None
    
    async def extract_etage(self):
        """Extrait l'étage de la page d'appartement"""
        try:
            page_content = await self.page.content()
            
            # Patterns pour trouver l'étage
            etage_patterns = [
                r'(\d+)(?:er?|e|ème?)\s*étage',
                r'étage\s*(\d+)',
                r'(\d+)(?:er?|e|ème?)\s*ét\.',
            ]
            
            for pattern in etage_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    etage_num = matches[0]
                    # Formater comme "4e étage" ou "1er étage"
                    if etage_num == '1':
                        return "1er étage"
                    else:
                        return f"{etage_num}e étage"
            
            # Chercher RDC
            if re.search(r'RDC|rez-de-chaussée|rez de chaussée', page_content, re.IGNORECASE):
                return "RDC"
            
            return None
        except Exception as e:
            print(f"  ⚠️ Erreur extraction étage: {e}")
            return None
    
    async def extract_style_for_photo(self):
        """Extrait le style de l'appartement pour la description de photo"""
        try:
            page_text = await self.page.text_content('body') or ""
            
            # Chercher des indices de style haussmannien
            style_keywords = {
                'haussmannien': 'Haussmannien',
                'haussmann': 'Haussmannien',
                'moulures': 'Haussmannien',
                'parquet': 'Haussmannien',
                'cheminée': 'Haussmannien',
                'restauré': 'Haussmannien',
                'contemporain': 'Contemporain',
                'moderne': 'Moderne',
                'ancien': 'Ancien',
                'neuf': 'Neuf'
            }
            
            for keyword, style in style_keywords.items():
                if re.search(keyword, page_text, re.IGNORECASE):
                    return style
            
            return "Style Inconnu"
        except Exception as e:
            print(f"  ⚠️ Erreur extraction style: {e}")
            return "Style Inconnu"
    
    def format_photo_description(self, surface=None, prix_m2=None, etage=None, style=None):
        """Formate la description de photo au format: 70 m² · 3e étage · Style Inconnu"""
        parts = []
        
        if surface:
            parts.append(surface)
        # Prix au m² masqué pour simplifier
        # if prix_m2:
        #     parts.append(prix_m2)
        if etage:
            parts.append(etage)
        if style:
            parts.append(style)
        
        return " · ".join(parts) if parts else "Appartement"
    
    async def extract_localisation(self):
        """Extrait la localisation (adresse exacte si possible)"""
        try:
            # Récupérer tout le contenu de la page
            page_text = await self.page.text_content('body')
            
            # Chercher l'adresse exacte avec différents patterns
            address_patterns = [
                r'(\d+[,\s]*[a-zA-Z\s]*[Rr]ue[^,\n]*)',
                r'(\d+[,\s]*[a-zA-Z\s]*[Aa]venue[^,\n]*)',
                r'(\d+[,\s]*[a-zA-Z\s]*[Bb]oulevard[^,\n]*)',
                r'(\d+[,\s]*[a-zA-Z\s]*[Pp]lace[^,\n]*)',
                r'(\d+[,\s]*[a-zA-Z\s]*[Cc]ours[^,\n]*)',
                r'(\d+[,\s]*[a-zA-Z\s]*[Vv]illa[^,\n]*)',
                r'(\d+[,\s]*[a-zA-Z\s]*[Ii]mpasse[^,\n]*)',
                r'(\d+[,\s]*[a-zA-Z\s]*[Aa]llée[^,\n]*)',
                r'(\d+[,\s]*[a-zA-Z\s]*[Pp]assage[^,\n]*)',
                r'(\d+[,\s]*[a-zA-Z\s]*[Cc]hemin[^,\n]*)'
            ]
            
            adresses_trouvees = []
            for pattern in address_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    # Nettoyer l'adresse
                    clean_addr = re.sub(r'\s+', ' ', match.strip())
                    if len(clean_addr) > 5 and clean_addr not in adresses_trouvees:
                        adresses_trouvees.append(clean_addr)
            
            if adresses_trouvees:
                return adresses_trouvees[0]  # Retourner la première adresse trouvée
            
            # Fallback 1: chercher juste l'arrondissement
            selectors = ['text=/Paris \d+e/', 'text=/750\d+/', '[class*="location"]']
            for selector in selectors:
                element = self.page.locator(selector).first
                if await element.count() > 0:
                    text = await element.text_content()
                    if text and 'Paris' in text:
                        return text.strip()
            
            # Fallback 2: utiliser les stations de métro comme localisation
            try:
                transports = await self.extract_transports()
                if transports:
                    # Prendre les 2 premières stations comme localisation
                    stations_str = ", ".join(transports[:2])
                    return f"Proche de {stations_str}"
            except Exception as e:
                print(f"  ⚠️ Erreur fallback stations: {e}")
            
            return "Localisation non trouvée"
        except:
            return "Localisation non trouvée"
    
    async def extract_surface(self):
        """Extrait la surface"""
        try:
            # Chercher la surface dans différents formats
            surface_elements = self.page.locator('text=/\\d+\\s*m²/')
            if await surface_elements.count() > 0:
                text = await surface_elements.first.text_content()
                if text:
                    # Extraire juste la partie "XX m²"
                    match = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', text, re.IGNORECASE)
                    if match:
                        # Arrondir si décimal et formater
                        surface_val = match.group(1).replace(',', '.')
                        try:
                            surface_num = float(surface_val)
                            return f"{int(surface_num)} m²" if surface_num == int(surface_num) else f"{surface_num:.1f} m²"
                        except:
                            return f"{match.group(1)} m²"
            return None
        except:
            return None
    
    async def extract_pieces(self):
        """Extrait le nombre de pièces"""
        try:
            # Chercher les pièces dans différents formats
            pieces_elements = self.page.locator('text=/\d+\s*pièces?/')
            if await pieces_elements.count() > 0:
                text = await pieces_elements.first.text_content()
                return text.strip() if text else "Pièces non trouvées"
            return "Pièces non trouvées"
        except:
            return "Pièces non trouvées"
    
    async def extract_date(self):
        """Extrait la date de publication"""
        try:
            # Chercher la date
            date_elements = self.page.locator('text=/le \d+ \w+ à/')
            if await date_elements.count() > 0:
                text = await date_elements.first.text_content()
                return text.strip() if text else "Date non trouvée"
            return "Date non trouvée"
        except:
            return "Date non trouvée"
    
    async def extract_transports(self):
        """Extrait les transports proches (stations de métro)"""
        try:
            transports = []
            
            # Méthode 1: Chercher la section "Proche des stations"
            try:
                # Chercher la div qui contient "Proche des stations"
                stations_div = self.page.locator('div.fz-16.sc-bdVaJa.bDXQKW:has(h3:has-text("Proche des stations"))')
                if await stations_div.count() > 0:
                    # Chercher tous les spans dans les li de la liste ul
                    station_spans = stations_div.locator('ul li span')
                    station_count = await station_spans.count()
                    
                    if station_count > 0:
                        for i in range(station_count):
                            station_text = await station_spans.nth(i).text_content()
                            if station_text and len(station_text.strip()) > 2:
                                transports.append(station_text.strip())
                    else:
                        # Fallback: utiliser les li directement
                        station_lis = stations_div.locator('ul li')
                        li_count = await station_lis.count()
                        for i in range(li_count):
                            station_text = await station_lis.nth(i).text_content()
                            if station_text:
                                # Nettoyer le texte (enlever les numéros de ligne)
                                station_name = re.sub(r'\s+\d+\s*$', '', station_text.strip())
                                if station_name and len(station_name) > 2:
                                    transports.append(station_name)
            except Exception as e:
                print(f"  ⚠️ Erreur extraction section stations: {e}")
            
            # Méthode 2: Chercher les images de métro et extraire les noms
            try:
                metro_images = await self.page.locator('img[src*="subway"], img[alt*="metro"]').all()
                for img in metro_images:
                    # Chercher le texte de la station dans le même conteneur
                    parent = img.locator('..')
                    station_text = await parent.text_content()
                    if station_text:
                        # Extraire le nom de la station (avant les icônes)
                        station_name = re.split(r'\s+\d+\s*', station_text)[0].strip()
                        if station_name and len(station_name) > 2 and station_name not in transports:
                            transports.append(station_name)
            except Exception as e:
                print(f"  ⚠️ Erreur extraction images métro: {e}")
            
            # Méthode 3: Fallback - chercher les patterns de stations
            if not transports:
                try:
                    transport_elements = self.page.locator('text=/[A-Za-z]+\s+\d+/')
                    for i in range(await transport_elements.count()):
                        text = await transport_elements.nth(i).text_content()
                        if text and re.match(r'[A-Za-z]+\s+\d+', text.strip()):
                            transports.append(text.strip())
                except Exception as e:
                    print(f"  ⚠️ Erreur extraction fallback: {e}")
            
            # Nettoyer et dédupliquer
            transports = list(dict.fromkeys(transports))  # Supprimer les doublons
            return transports[:10]  # Limiter à 10 transports
            
        except Exception as e:
            print(f"  ⚠️ Erreur extraction transports: {e}")
            return []
    
    async def extract_description(self):
        """Extrait la description détaillée"""
        try:
            # Essayer différents sélecteurs pour la description
            description_selectors = [
                '.fz-16.sc-bxivhb.fcnykg',
                '[class*="description"]',
                'p:has-text("Globalstone")',
                'text=/Globalstone/',
                'div:has-text("Globalstone")',
                'section:has-text("Globalstone")'
            ]
            
            for selector in description_selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.count() > 0:
                        text = await element.text_content()
                        if text and len(text.strip()) > 50:  # S'assurer qu'on a une vraie description
                            return text.strip()
                except:
                    continue
            
            return "Description non trouvée"
        except:
            return "Description non trouvée"
    
    async def extract_map_info(self, apartment_id=None):
        """Extrait les informations de la carte (rues, quartier, métros)"""
        try:
            print("   🗺️ Analyse de la carte...")
            
            # Initialiser screenshot_path
            screenshot_path = None
            
            # Prendre un screenshot de la carte pour analyse
            map_element = self.page.locator('.leaflet-container, [class*="map"], [class*="carte"]').first
            if await map_element.count() > 0:
                # Attendre que la carte se charge complètement pour cet appartement
                # Attendre que les tuiles de la carte soient chargées
                await self.page.wait_for_timeout(1000)
                
                # Attendre que la carte soit visible et chargée
                try:
                    await map_element.wait_for(state='visible', timeout=5000)
                except:
                    pass
                
                # Attendre un peu plus pour que la carte se centre sur l'appartement
                await self.page.wait_for_timeout(2000)
                
                # Scroller vers la carte pour s'assurer qu'elle est visible
                try:
                    await map_element.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(1000)
                except:
                    pass
                
                # Prendre un screenshot de la carte avec l'ID de l'appartement dans le nom
                if apartment_id:
                    screenshot_path = f"data/screenshots/map_{apartment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                else:
                    screenshot_path = f"data/screenshots/map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                os.makedirs("data/screenshots", exist_ok=True)
                await map_element.screenshot(path=screenshot_path)
                print(f"   📸 Screenshot de la carte sauvegardé: {screenshot_path}")
            
            # Extraire le texte visible sur la carte
            map_text = ""
            try:
                map_text = await map_element.text_content()
            except:
                pass
            
            # Chercher des noms de rues dans le contenu de la page
            page_content = await self.page.text_content('body')
            
            # Patterns pour identifier les rues et quartiers
            street_patterns = [
                r'Rue\s+[A-Za-z\s\-\']+',
                r'Avenue\s+[A-Za-z\s\-\']+',
                r'Boulevard\s+[A-Za-z\s\-\']+',
                r'Place\s+[A-Za-z\s\-\']+',
                r'Cours\s+[A-Za-z\s\-\']+',
                r'Villa\s+[A-Za-z\s\-\']+',
                r'Impasse\s+[A-Za-z\s\-\']+',
                r'Allée\s+[A-Za-z\s\-\']+',
                r'Passage\s+[A-Za-z\s\-\']+',
                r'Chemin\s+[A-Za-z\s\-\']+'
            ]
            
            metro_patterns = [
                r'[A-Za-z\s\-\']+\s*\(métro\)',
                r'Station\s+[A-Za-z\s\-\']+',
                r'Métro\s+[A-Za-z\s\-\']+'
            ]
            
            # Extraire les rues
            streets_found = []
            for pattern in street_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    clean_street = re.sub(r'\s+', ' ', match.strip())
                    if len(clean_street) > 5 and clean_street not in streets_found:
                        streets_found.append(clean_street)
            
            # Extraire les métros
            metros_found = []
            for pattern in metro_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    clean_metro = re.sub(r'\s+', ' ', match.strip())
                    if len(clean_metro) > 3 and clean_metro not in metros_found:
                        metros_found.append(clean_metro)
            
            # Identifier le quartier basé sur les rues trouvées
            quartier = self.identify_quartier(streets_found, metros_found)
            
            map_info = {
                "streets": streets_found[:10],  # Limiter à 10 rues
                "metros": metros_found[:5],     # Limiter à 5 métros
                "quartier": quartier,
                "screenshot": screenshot_path if 'screenshot_path' in locals() else None
            }
            
            print(f"   🏘️ Quartier identifié: {quartier}")
            print(f"   🛣️ Rues trouvées: {len(streets_found)}")
            print(f"   🚇 Métros trouvés: {len(metros_found)}")
            
            return map_info
            
        except Exception as e:
            print(f"   ❌ Erreur analyse carte: {e}")
            return {"streets": [], "metros": [], "quartier": "Non identifié", "error": str(e)}
    
    def identify_quartier(self, streets, metros):
        """Identifie le quartier basé sur les rues et métros trouvés"""
        # Quartiers du 19e avec leurs rues caractéristiques
        quartiers_19e = {
            "Buttes-Chaumont": ["Rue Botzaris", "Avenue Secrétan", "Rue Manin", "Rue de Crimée", "Botzaris", "Secrétan", "Manin", "Crimée"],
            "Place des Fêtes": ["Rue Carducci", "Rue Mélingue", "Rue des Alouettes", "Rue de la Villette", "Carducci", "Mélingue", "Alouettes", "Villette"],
            "Jourdain": ["Rue de Belleville", "Rue Pelleport", "Rue de Mouzaïa", "Rue Compans", "Belleville", "Pelleport", "Mouzaïa", "Compans"],
            "Pyrénées": ["Rue Pradier", "Rue Clavel", "Rue Rébeval", "Rue Levert", "Pradier", "Clavel", "Rébeval", "Levert"],
            "Belleville": ["Rue de Belleville", "Rue du Faubourg du Temple", "Boulevard de la Villette", "Belleville", "Faubourg du Temple", "Villette"],
            "Canal de l'Ourcq": ["Quai de la Loire", "Quai de la Seine", "Rue de l'Ourcq", "Loire", "Seine", "Ourcq"]
        }
        
        # Métros caractéristiques
        metros_quartiers = {
            "Place des Fêtes": ["Place des Fêtes", "Place des Fetes"],
            "Jourdain": ["Jourdain"],
            "Pyrénées": ["Pyrénées", "Pyrenees"],
            "Buttes-Chaumont": ["Botzaris", "Crimée", "Crimée"],
            "Belleville": ["Belleville", "Couronnes"]
        }
        
        # Compter les correspondances
        quartier_scores = {}
        
        for quartier, rues_quartier in quartiers_19e.items():
            score = 0
            for rue in streets:
                for rue_quartier in rues_quartier:
                    if rue_quartier.lower() in rue.lower():
                        score += 1
            quartier_scores[quartier] = score
        
        # Ajouter les scores des métros
        for quartier, metros_quartier in metros_quartiers.items():
            for metro in metros:
                for metro_quartier in metros_quartier:
                    if metro_quartier.lower() in metro.lower():
                        quartier_scores[quartier] = quartier_scores.get(quartier, 0) + 2
        
        # Retourner le quartier avec le plus haut score
        if quartier_scores:
            best_quartier = max(quartier_scores, key=quartier_scores.get)
            if quartier_scores[best_quartier] > 0:
                return f"{best_quartier} (score: {quartier_scores[best_quartier]})"
        
        return "Quartier non identifié"
    
    def analyze_screenshot_for_quartier(self, screenshot_path):
        """Analyse le screenshot pour identifier le quartier (méthode basique)"""
        try:
            if not os.path.exists(screenshot_path):
                return "Screenshot non trouvé"
            
            # Pour l'instant, on retourne une analyse basée sur la description
            # Dans une version avancée, on pourrait utiliser OCR ou vision par ordinateur
            return "Analyse manuelle requise - voir screenshot"
            
        except Exception as e:
            return f"Erreur analyse: {e}"
    
    async def extract_coordinates(self):
        """Extrait les coordonnées GPS depuis la carte Leaflet"""
        try:
            # Chercher les éléments de la carte Leaflet avec différents sélecteurs
            leaflet_selectors = [
                '.leaflet-proxy',
                '.leaflet-map-pane', 
                '.leaflet-container',
                '[class*="leaflet"]'
            ]
            
            coordinates = None
            for selector in leaflet_selectors:
                elements = self.page.locator(selector)
                count = await elements.count()
                
                for i in range(count):
                    element = elements.nth(i)
                    style = await element.get_attribute('style')
                    
                    if style and 'translate3d' in style:
                        print(f"   🔍 Style trouvé: {style[:100]}...")
                        
                        # Extraire les coordonnées du transform avec regex plus robuste
                        import re
                        patterns = [
                            r'translate3d\(([^,]+),\s*([^,]+),\s*([^)]+)\)',
                            r'translate3d\(([^,]+),\s*([^,]+),\s*([^)]+)\)',
                            r'transform:\s*translate3d\(([^,]+),\s*([^,]+),\s*([^)]+)\)'
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, style)
                            if match:
                                try:
                                    x_str = match.group(1).strip()
                                    y_str = match.group(2).strip()
                                    scale_str = match.group(3).strip()
                                    
                                    print(f"   📍 Coordonnées brutes: x={x_str}, y={y_str}, scale={scale_str}")
                                    
                                    # Nettoyer et convertir les valeurs
                                    x = float(x_str.replace('px', '').replace('e+', 'e'))
                                    y = float(y_str.replace('px', '').replace('e+', 'e'))
                                    scale = float(scale_str.replace('px', '')) if scale_str != '0px' else 1.0
                                    
                                    # Vérifier que les valeurs sont valides (pas 0)
                                    if abs(x) > 1000 and abs(y) > 1000:  # Coordonnées Web Mercator valides
                                        # Convertir les coordonnées Web Mercator en lat/lng
                                        lon = (x / 20037508.34) * 180
                                        lat = (y / 20037508.34) * 180
                                        lat = 180 / 3.14159265359 * (2 * math.atan(math.exp(lat * 3.14159265359 / 180)) - 3.14159265359 / 2)
                                        
                                        coordinates = {
                                            "latitude": round(lat, 6),
                                            "longitude": round(lon, 6),
                                            "raw_x": x,
                                            "raw_y": y,
                                            "scale": scale
                                        }
                                        print(f"   ✅ Coordonnées converties: {lat:.6f}, {lon:.6f}")
                                        break
                                    else:
                                        print(f"   ⚠️ Coordonnées invalides (trop petites): x={x}, y={y}")
                                        
                                except ValueError as ve:
                                    print(f"   ❌ Erreur de conversion: {ve}")
                                    continue
                        
                        if coordinates:
                            break
                
                if coordinates:
                    break
            
            if not coordinates:
                print("   ❌ Aucune coordonnée valide trouvée")
                return {"latitude": None, "longitude": None, "error": "No valid coordinates found"}
            
            return coordinates
            
        except Exception as e:
            print(f"   ❌ Erreur générale: {e}")
            return {"latitude": None, "longitude": None, "error": str(e)}
    
    async def extract_style_haussmannien(self):
        """Extrait les éléments de style haussmannien"""
        try:
            # Récupérer la description
            description = await self.extract_description()
            if description == "Description non trouvée":
                return {"score": 0, "elements": [], "keywords": []}
            
            # Mots-clés haussmanniens étendus
            haussmann_keywords = {
                'architectural': [
                    'haussmannien', 'haussmannienne', 'haussmann',
                    'moulures', 'moulure', 'mouluré', 'moulurée',
                    'cheminée', 'cheminées', 'cheminée de marbre',
                    'parquet', 'parquets', 'parquet d\'origine', 'parquet ancien',
                    'corniches', 'corniche', 'corniche moulurée',
                    'rosaces', 'rosace', 'rosace de plafond',
                    'balcon', 'balcons', 'balcon en fer forgé', 'balcon forgé',
                    'fer forgé', 'fer forgée', 'grille en fer forgé',
                    'hauteur sous plafond', 'haut plafond', 'plafond haut',
                    'escalier', 'escaliers', 'escalier d\'honneur'
                ],
                'caractère': [
                    'caractère', 'caractères', 'caractéristique',
                    'restauré', 'restaurée', 'rénové', 'rénovée',
                    'authentique', 'authentiques', 'original', 'originale',
                    'époque', 'période', 'époque haussmannienne',
                    'ancien', 'ancienne', 'ancien immeuble',
                    'vieux', 'vieille', 'vieux immeuble',
                    'charme', 'charmant', 'charmante',
                    'prestige', 'prestigieux', 'prestigieuse',
                    'noble', 'noblesse', 'noblesse des matériaux'
                ],
                'matériaux': [
                    'marbre', 'marbres', 'marbre de carrare',
                    'bois', 'bois noble', 'bois précieux',
                    'pierre', 'pierres', 'pierre de taille',
                    'stuc', 'stucs', 'stuc décoratif',
                    'plâtre', 'plâtres', 'plâtre moulé',
                    'métal', 'métaux', 'métal forgé'
                ],
                'détails': [
                    'moulure', 'moulures', 'moulure de plafond',
                    'décoration', 'décoratif', 'décorative',
                    'ornement', 'ornements', 'ornemental',
                    'détail', 'détails', 'détail architectural',
                    'finesse', 'finesses', 'finitions',
                    'élégance', 'élégant', 'élégante'
                ]
            }
            
            # Chercher les mots-clés par catégorie
            found_by_category = {}
            total_found = 0
            all_keywords = []
            
            for category, keywords in haussmann_keywords.items():
                found_in_category = []
                for keyword in keywords:
                    if keyword.lower() in description.lower():
                        found_in_category.append(keyword)
                        all_keywords.append(keyword)
                        total_found += 1
                
                if found_in_category:
                    found_by_category[category] = found_in_category
            
            # Calculer un score de style
            style_score = min(100, (total_found * 10) + 20)  # 10 points par mot-clé + 20 de base
            
            return {
                "score": style_score,
                "elements": found_by_category,
                "keywords": all_keywords,
                "total_found": total_found
            }
            
        except Exception as e:
            return {"score": 0, "elements": [], "keywords": [], "error": str(e)}
    
    async def extract_photos(self):
        """Extrait les URLs des photos d'appartement depuis la div spécifique"""
        try:
            print("   📸 Extraction des photos d'appartement...")
            
            # Extraire les informations pour la description des photos
            etage = await self.extract_etage()
            surface = await self.extract_surface()
            prix_m2 = await self.extract_prix_m2()
            style = await self.extract_style_for_photo()
            
            if etage:
                print(f"      🏢 Étage trouvé: {etage}")
            if surface:
                print(f"      📐 Surface trouvée: {surface}")
            if prix_m2:
                print(f"      💰 Prix au m² trouvé: {prix_m2}")
            if style:
                print(f"      🎨 Style trouvé: {style}")
            
            photos = []
            
            # Attendre un peu plus longtemps pour le chargement des images lazy
            await asyncio.sleep(1)
            
            # Scroller un peu pour déclencher le chargement lazy si nécessaire
            await self.page.evaluate('window.scrollTo(0, 200)')
            await asyncio.sleep(0.5)
            await self.page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(0.5)
            
            # Méthode 1: Cibler la div galerie principale (sc-cJSrbW juBoVb ou sc-gPEVay jnWxBz)
            # Aussi chercher dans les divs cachées avec display="none" qui contiennent toutes les photos
            gallery_selectors = [
                'div.sc-cJSrbW.juBoVb',  # Structure actuelle visible dans l'image
                'div.sc-gPEVay.jnWxBz',  # Ancienne structure
                '[class*="sc-cJSrbW"][class*="juBoVb"]',  # Sélecteurs partiels
                '[class*="sc-gPEVay"][class*="jnWxBz"]',
                'div.sc-bdVaJa.InsofV',  # Div cachée avec toutes les photos (display="none")
                '[class*="sc-bdVaJa"][class*="InsofV"]',  # Sélecteur partiel
                'div[style*="display: none"]',  # Toute div cachée
            ]
            
            gallery_found = False
            for selector in gallery_selectors:
                try:
                    gallery_div = self.page.locator(selector)
                    if await gallery_div.count() > 0:
                        print(f"      🎯 Div galerie trouvée ({selector}), extraction des images visibles...")
                        gallery_found = True
                        
                        # Extraire toutes les images de la galerie (visibles ET cachées avec preloader)
                        gallery_element = await gallery_div.first.element_handle()
                        img_elements = await gallery_element.evaluate('''
                            el => {
                                // Obtenir toutes les images dans l'ordre exact du DOM (même cachées)
                                const allImgs = Array.from(el.querySelectorAll('img'));
                                
                                // Extraire les infos avec position visuelle pour tri correct
                                return allImgs.map((img, domIndex) => {
                                    const rect = img.getBoundingClientRect();
                                    const computedStyle = window.getComputedStyle(img);
                                    return {
                                        domIndex: domIndex,  // Index dans le DOM
                                        src: img.src || img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || '',
                                        alt: img.alt || '',
                                        width: img.naturalWidth || img.width || 0,
                                        height: img.naturalHeight || img.height || 0,
                                        display: computedStyle.display,
                                        visibility: computedStyle.visibility,
                                        top: rect.top,  // Position top pour tri visuel
                                        left: rect.left  // Position left pour tri visuel
                                    };
                                }).filter(img => {
                                    // Garder toutes les images avec une URL valide
                                    // Y compris celles avec display="none" et alt="preloader" si elles ont une URL de photo valide
                                    if (!img.src) return false;
                                    if (img.src.toLowerCase().includes('placeholder')) return false;
                                    
                                    // Patterns de vraies photos d'appartements
                                    const photoPatterns = ['loueragile', 'upload_pro_ad', 'media.apimo.pro', 'studio-net.fr', 'images.century21.fr', 'biens', 'apartement', 'transopera', 'staticlbi', 'uploadcaregdc', 'uploadcare', 's3.amazonaws.com', 'googleusercontent.com', 'cdn.safti.fr', 'safti.fr', 'paruvendu.fr', 'immo-facile.com', 'mms.seloger.com', 'seloger.com'];
                                    const hasValidPhotoPattern = photoPatterns.some(pattern => img.src.toLowerCase().includes(pattern));
                                    
                                    // Si c'est une vraie photo, on la garde même si cachée ou avec alt="preloader"
                                    return hasValidPhotoPattern;
                                });
                            }
                        ''')
                        
                        # Extraire les photos avec leur index DOM pour préserver l'ordre de Jinka
                        photos_with_position = []
                        for img_data in img_elements:
                            try:
                                src_to_use = img_data.get('src', '')
                                if not src_to_use:
                                    continue
                                
                                # Vérifier que c'est une vraie photo (pas un logo)
                                if 'logo' in src_to_use.lower() or 'source_logos' in src_to_use.lower():
                                    continue
                                
                                # Accepter les URLs de vraies photos d'appartements (patterns étendus)
                                photo_patterns = ['loueragile', 'upload_pro_ad', 'media.apimo.pro', 'studio-net.fr', 'images.century21.fr', 'biens', 'apartement', 'transopera', 'staticlbi', 'uploadcaregdc', 'uploadcare', 's3.amazonaws.com', 'googleusercontent.com', 'cdn.safti.fr', 'safti.fr', 'paruvendu.fr', 'immo-facile.com', 'mms.seloger.com', 'seloger.com']
                                if not any(pattern in src_to_use.lower() for pattern in photo_patterns):
                                    continue
                                
                                # Vérifier les dimensions de l'image (exclure les très petites comme les logos)
                                width = img_data.get('width', 0)
                                height = img_data.get('height', 0)
                                
                                # Les logos font généralement ~128x128px, les vraies photos sont beaucoup plus grandes
                                # On exclut seulement les images très petites (< 200px)
                                if width > 0 and height > 0:
                                    if width < 200 or height < 200:
                                        # Probablement un logo ou icône (ex: logo immobilier 128x128), on skip
                                        continue
                                
                                # Formater la description complète avec toutes les infos
                                alt = self.format_photo_description(surface, prix_m2, etage, style)
                                
                                position_top = img_data.get('top', 0)
                                position_left = img_data.get('left', 0)
                                
                                # Garder toutes les photos valides, même si cachées (display="none")
                                # Les photos avec alt="preloader" dans des divs cachées sont souvent les vraies photos
                                
                                photos_with_position.append({
                                    'url': src_to_use,
                                    'alt': alt or 'appartement',
                                    'selector': 'gallery_div_visible',
                                    'width': width,
                                    'height': height,
                                    'dom_index': img_data.get('domIndex', 0),
                                    'position_top': position_top,
                                    'position_left': position_left
                                })
                            except Exception as e:
                                continue
                        
                        # Dédupliquer par URL, en gardant la photo avec la meilleure position (visible de préférence)
                        url_to_photo = {}
                        for photo in photos_with_position:
                            url = photo['url']
                            top = photo.get('position_top', 0)
                            left = photo.get('position_left', 0)
                            
                            # Si on a déjà cette URL
                            if url in url_to_photo:
                                existing_top = url_to_photo[url].get('position_top', 0)
                                existing_left = url_to_photo[url].get('position_left', 0)
                                
                                # Préférer la photo avec position non-0,0 (visible)
                                if (top != 0 or left != 0) and (existing_top == 0 and existing_left == 0):
                                    # Nouvelle photo est visible, remplacer
                                    url_to_photo[url] = photo
                                elif (top == 0 and left == 0) and (existing_top != 0 or existing_left != 0):
                                    # Photo existante est visible, garder celle-là
                                    pass
                                else:
                                    # Les deux ont même type de position, garder la première
                                    pass
                            else:
                                # Première occurrence de cette URL
                                url_to_photo[url] = photo
                        
                        photos_with_position = list(url_to_photo.values())
                        
                        # Séparer les photos visibles (position != 0,0) des photos cachées (0,0)
                        visible_photos = [p for p in photos_with_position if p.get('position_top', 0) != 0 or p.get('position_left', 0) != 0]
                        hidden_photos = [p for p in photos_with_position if p.get('position_top', 0) == 0 and p.get('position_left', 0) == 0]
                        
                        # Trier les photos visibles par position (top puis left) pour l'ordre visuel
                        visible_photos.sort(key=lambda x: (x.get('position_top', 0), x.get('position_left', 0)))
                        
                        # Trier les photos cachées par index DOM pour préserver l'ordre de Jinka
                        hidden_photos.sort(key=lambda x: x.get('dom_index', 0))
                        
                        # Combiner : photos visibles d'abord, puis photos cachées dans l'ordre DOM
                        photos_with_position = visible_photos + hidden_photos
                        print(f"      ✅ {len(visible_photos)} photos visibles + {len(hidden_photos)} photos cachées = {len(photos_with_position)} photos au total")
                        
                        # Ajouter les photos dans l'ordre correct (ordre visuel de Jinka)
                        for photo_with_pos in photos_with_position:
                            photo = {k: v for k, v in photo_with_pos.items() if k not in ['dom_index', 'position_top', 'position_left']}
                            photos.append(photo)
                            print(f"      📸 Photo galerie (top: {photo_with_pos.get('position_top', 0):.0f}, left: {photo_with_pos.get('position_left', 0):.0f}, {photo_with_pos['width']}x{photo_with_pos['height']}): {photo_with_pos['url'][:60]}...")
                        
                        if len(photos) > 0:
                            # Ne pas break, continuer à chercher dans d'autres sélecteurs pour accumuler toutes les photos
                            pass
                except Exception as e:
                    continue
            
            # Après avoir cherché dans toutes les galeries, dédupliquer
            if len(photos) > 0:
                unique_photos_temp = []
                seen_urls_temp = set()
                for photo in photos:
                    if photo['url'] not in seen_urls_temp:
                        unique_photos_temp.append(photo)
                        seen_urls_temp.add(photo['url'])
                photos = unique_photos_temp
                print(f"      ✅ {len(photos)} photos uniques trouvées après déduplication")
            
            # Méthode 2: Si pas de photos dans la galerie, chercher les images visibles avec URLs d'appartement
            if len(photos) == 0:
                print("      ⚠️ Aucune photo dans la galerie, recherche d'images visibles...")
                
                # Attendre un peu pour que les images lazy-loaded se chargent
                await asyncio.sleep(2)
                
                # Chercher UNIQUEMENT les images visibles avec URLs d'appartement
                all_visible_images = await self.page.locator('img:visible').all()
                print(f"      🔍 {len(all_visible_images)} images visibles totales sur la page")
                
                # Méthode 2a: Chercher dans les images visibles
                for img in all_visible_images:
                    try:
                        # Vérifier que l'image est vraiment visible
                        display = await img.evaluate('el => window.getComputedStyle(el).display')
                        if display == 'none':
                            continue
                        
                        # Vérifier les dimensions de l'image (exclure les très petites comme les logos)
                        width = await img.evaluate('el => el.naturalWidth || el.width || 0')
                        height = await img.evaluate('el => el.naturalHeight || el.height || 0')
                        
                        # Les logos font généralement ~128x128px, les vraies photos sont beaucoup plus grandes
                        # On exclut seulement les images très petites (< 200px)
                        if width > 0 and height > 0:
                            if width < 200 or height < 200:
                                # Probablement un logo ou icône (ex: logo immobilier 128x128), on skip
                                continue
                        
                        src = await img.get_attribute('src')
                        # Chercher aussi dans data-src (lazy loading)
                        data_src = await img.get_attribute('data-src')
                        src_to_use = src or data_src
                        
                        # Accepter les URLs de vraies photos d'appartements (patterns étendus)
                        photo_patterns = ['loueragile', 'upload_pro_ad', 'media.apimo.pro', 'studio-net.fr', 'images.century21.fr', 'biens', 'apartement', 'transopera', 'staticlbi', 'uploadcaregdc', 'uploadcare', 's3.amazonaws.com', 'googleusercontent.com', 'cdn.safti.fr', 'safti.fr', 'paruvendu.fr', 'immo-facile.com', 'mms.seloger.com', 'seloger.com']
                        if src_to_use and any(pattern in src_to_use.lower() for pattern in photo_patterns):
                            # Exclure les logos
                            if 'logo' in src_to_use.lower() or 'source_logos' in src_to_use.lower() or 'preloader' in src_to_use.lower():
                                continue
                            
                            # Formater la description complète avec toutes les infos
                            alt = self.format_photo_description(surface, prix_m2, etage, style)
                            
                            photos.append({
                                'url': src_to_use,
                                'alt': alt or 'appartement',
                                'selector': 'global_search_visible',
                                'width': width,
                                'height': height
                            })
                            print(f"      📸 Photo visible ({width}x{height}): {src_to_use[:60]}...")
                    except Exception as e:
                        continue
                
                # Méthode 2b: Si toujours rien, chercher dans toutes les images (même cachées, au cas où)
                if len(photos) == 0:
                    print("      🔍 Recherche alternative dans toutes les images (y compris lazy-loaded)...")
                    all_images = await self.page.locator('img').all()
                    
                    for img in all_images:
                        try:
                            # Récupérer src et data-src (pour lazy loading)
                            src = await img.get_attribute('src')
                            data_src = await img.get_attribute('data-src')
                            data_lazy = await img.get_attribute('data-lazy-src')
                            src_to_use = src or data_src or data_lazy
                            
                            if not src_to_use:
                                continue
                            
                            # Filtrer par URL (patterns étendus)
                            photo_patterns = ['loueragile', 'upload_pro_ad', 'media.apimo.pro', 'studio-net.fr', 'images.century21.fr', 'biens', 'apartement', 'transopera', 'staticlbi', 'uploadcaregdc', 'uploadcare', 's3.amazonaws.com', 'googleusercontent.com', 'cdn.safti.fr', 'safti.fr', 'paruvendu.fr', 'immo-facile.com', 'mms.seloger.com', 'seloger.com']
                            if not any(pattern in src_to_use.lower() for pattern in photo_patterns):
                                continue
                            
                            # Exclure les logos et preloaders
                            if 'logo' in src_to_use.lower() or 'source_logos' in src_to_use.lower() or 'preloader' in src_to_use.lower():
                                continue
                            
                            # Vérifier les dimensions si l'image est chargée
                            width = 0
                            height = 0
                            try:
                                width = await img.evaluate('el => el.naturalWidth || el.width || 0')
                                height = await img.evaluate('el => el.naturalHeight || el.height || 0')
                                
                                if width > 0 and height > 0 and (width < 200 or height < 200):
                                    continue
                            except:
                                pass  # Si l'image n'est pas encore chargée, on garde quand même
                            
                            photos.append({
                                'url': src_to_use,
                                'alt': await img.get_attribute('alt') or 'appartement',
                                'selector': 'global_search_all',
                                'width': width,
                                'height': height
                            })
                            print(f"      📸 Photo trouvée (lazy-loaded?): {src_to_use[:60]}...")
                        except Exception as e:
                            continue
            
            # Dédupliquer
            unique_photos = []
            seen_urls = set()
            for photo in photos:
                if photo['url'] not in seen_urls:
                    unique_photos.append(photo)
                    seen_urls.add(photo['url'])
            
            print(f"   ✅ {len(unique_photos)} photos d'appartement trouvées")
            return unique_photos  # Retourner toutes les photos disponibles
            
        except Exception as e:
            print(f"   ❌ Erreur extraction photos: {e}")
            return []
    
    async def extract_caracteristiques(self):
        """Extrait les caractéristiques"""
        try:
            # Chercher la section caractéristiques
            char_elements = self.page.locator('h3:has-text("Caractéristiques") + *')
            if await char_elements.count() > 0:
                text = await char_elements.first.text_content()
                return text.strip() if text else "Caractéristiques non trouvées"
            return "Caractéristiques non trouvées"
        except:
            return "Caractéristiques non trouvées"
    
    async def extract_agence(self):
        """Extrait les informations de l'agence"""
        try:
            # Chercher le nom de l'agence
            agence_elements = self.page.locator('text=/[A-Z][A-Z\s]+/')
            for i in range(await agence_elements.count()):
                text = await agence_elements.nth(i).text_content()
                if text and len(text.strip()) > 3 and text.isupper():
                    return text.strip()
            return "Agence non trouvée"
        except:
            return "Agence non trouvée"
    
    async def save_apartment(self, apartment_data):
        """Sauvegarde les données d'un appartement"""
        try:
            os.makedirs('data/appartements', exist_ok=True)
            filename = f"data/appartements/{apartment_data['id']}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(apartment_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Appartement {apartment_data['id']} sauvegardé")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
    
    async def download_apartment_photos(self, apartment_id, photos):
        """Télécharge les photos d'un appartement localement avec filtrage par taille"""
        try:
            if not photos:
                return
                
            # Créer le dossier pour les photos
            photos_dir = f"data/photos/{apartment_id}"
            os.makedirs(photos_dir, exist_ok=True)
            
            # Supprimer toutes les photos existantes
            if os.path.exists(photos_dir):
                existing_files = [f for f in os.listdir(photos_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
                for existing_file in existing_files:
                    file_path = os.path.join(photos_dir, existing_file)
                    try:
                        os.remove(file_path)
                        print(f"      🗑️ Photo existante supprimée: {existing_file}")
                    except Exception as e:
                        print(f"      ⚠️ Erreur suppression {existing_file}: {e}")
            
            # Télécharger et filtrer les photos
            valid_photos = []
            async with aiohttp.ClientSession() as session:
                for i, photo in enumerate(photos):  # Télécharger toutes les photos disponibles
                    url = photo['url']
                    temp_filename = f"{photos_dir}/temp_photo_{i+1}.jpg"
                    
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                content = await response.read()
                                
                                # Sauvegarder temporairement pour analyser
                                with open(temp_filename, 'wb') as f:
                                    f.write(content)
                                
                                # Vérifier si c'est une vraie photo d'appartement
                                if self.is_valid_apartment_photo(temp_filename, content):
                                    # Renommer avec format simple: photo1.jpg, photo2.jpg, etc.
                                    photo_number = len(valid_photos) + 1
                                    final_filename = f"{photos_dir}/photo{photo_number}.jpg"
                                    os.rename(temp_filename, final_filename)
                                    valid_photos.append(final_filename)
                                    print(f"      📸 Photo {photo_number} téléchargée: {final_filename} ({len(content)} bytes)")
                                else:
                                    # Supprimer la photo invalide
                                    os.remove(temp_filename)
                                    print(f"      ❌ Photo {i+1} rejetée: {len(content)} bytes (logo/icône)")
                            else:
                                print(f"      ❌ Erreur photo {i+1}: HTTP {response.status}")
                    except Exception as e:
                        print(f"      ❌ Erreur téléchargement photo {i+1}: {e}")
                        if os.path.exists(temp_filename):
                            os.remove(temp_filename)
            
            print(f"      ✅ {len(valid_photos)} photos d'appartement téléchargées dans {photos_dir}/")
                        
        except Exception as e:
            print(f"❌ Erreur téléchargement photos: {e}")
    
    def is_valid_apartment_photo(self, filepath, content):
        """Vérifie si une photo est une vraie photo d'appartement"""
        try:
            # Vérifier la taille du fichier (pas trop petit, pas trop grand)
            if len(content) < 20000 or len(content) > 500000:  # 20KB - 500KB
                return False
            
            # Vérifier le type de fichier
            if not (content.startswith(b'\xff\xd8\xff') or  # JPEG
                    content.startswith(b'\x89PNG')):  # PNG
                return False
            
            # Pour les PNG, vérifier qu'ils ne sont pas des logos (carrés petits)
            if content.startswith(b'\x89PNG'):
                # Lire les dimensions PNG
                if len(content) >= 24:
                    width = int.from_bytes(content[16:20], 'big')
                    height = int.from_bytes(content[20:24], 'big')
                    # Rejeter les images carrées petites (logos)
                    if width == height and width < 600:
                        return False
                    # Rejeter les images trop petites
                    if width < 400 or height < 300:
                        return False
            
            return True
            
        except Exception as e:
            return False
    
    async def cleanup(self):
        """Ferme le navigateur"""
        if self.browser:
            await self.browser.close()

async def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage: python scrape_jinka.py <URL_ALERTE>")
        print("Exemple: python scrape_jinka.py 'https://www.jinka.fr/alert_result?token=...'")
        return
    
    alert_url = sys.argv[1]
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        
        if await scraper.login():
            await scraper.scrape_alert_page(alert_url)
            print(f"✅ Scraping terminé: {len(scraper.apartments)} appartements")
        else:
            print("❌ Échec de la connexion")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
