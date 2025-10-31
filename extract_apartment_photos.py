#!/usr/bin/env python3
"""
Extraction et analyse des photos d'appartement pour déterminer l'exposition
"""

import asyncio
import json
import os
import re
import requests
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class ApartmentPhotoExtractor:
    """Extracteur de photos d'appartement pour l'analyse d'exposition"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup(self):
        """Initialise le navigateur"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
    async def close(self):
        """Ferme le navigateur"""
        if self.browser:
            await self.browser.close()
    
    async def login_jinka(self):
        """Connexion à Jinka"""
        try:
            await self.page.goto("https://www.jinka.fr/sign/in")
            print("🔐 Connexion à Jinka...")
            
            # Cliquer sur le bouton Google
            await self.page.click('button.mt-20.flex.cursor-pointer.items-center.gap-15.rounded-\\[14px\\].border-1.border-text.bg-white.px-20.py-16')
            await self.page.wait_for_url("https://accounts.google.com/**")
            
            # Remplir l'email
            await self.page.fill('input[type="email"]', os.getenv('JINKA_EMAIL'))
            await self.page.click('div[id="identifierNext"]')
            
            # Attendre et remplir le mot de passe
            await self.page.wait_for_selector('input[type="password"]', state='visible')
            await self.page.fill('input[type="password"]', os.getenv('JINKA_PASSWORD'))
            await self.page.click('div[id="passwordNext"]')
            
            # Attendre la redirection
            await self.page.wait_for_url("https://www.jinka.fr/**")
            print("✅ Connexion réussie")
            return True
            
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    async def extract_etage(self) -> str:
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
            print(f"   ⚠️ Erreur extraction étage: {e}")
            return None
    
    async def extract_surface(self) -> str:
        """Extrait la surface de la page d'appartement"""
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
        except Exception as e:
            print(f"   ⚠️ Erreur extraction surface: {e}")
            return None
    
    async def extract_prix_m2(self) -> str:
        """Extrait le prix au m² de la page d'appartement"""
        try:
            # Chercher le prix au m²
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
        except Exception as e:
            print(f"   ⚠️ Erreur extraction prix au m²: {e}")
            return None
    
    async def extract_style(self) -> str:
        """Extrait le style de l'appartement"""
        try:
            page_content = await self.page.content()
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
            print(f"   ⚠️ Erreur extraction style: {e}")
            return "Style Inconnu"
    
    def format_photo_description(self, surface: str = None, prix_m2: str = None, etage: str = None, style: str = None) -> str:
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
    
    async def extract_apartment_photos(self, apartment_url: str) -> list:
        """Extrait les photos d'un appartement dans l'ordre de la galerie Jinka"""
        try:
            print(f"🏠 Extraction des photos: {apartment_url}")
            await self.page.goto(apartment_url)
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(3000)
            
            # Extraire les informations de l'appartement pour la description
            etage = await self.extract_etage()
            surface = await self.extract_surface()
            prix_m2 = await self.extract_prix_m2()
            style = await self.extract_style()
            
            if etage:
                print(f"   🏢 Étage trouvé: {etage}")
            if surface:
                print(f"   📐 Surface trouvée: {surface}")
            if prix_m2:
                print(f"   💰 Prix au m² trouvé: {prix_m2}")
            if style:
                print(f"   🎨 Style trouvé: {style}")
            
            # Attendre un peu plus pour le chargement des images lazy
            await asyncio.sleep(1)
            
            # Scroller un peu pour déclencher le chargement lazy si nécessaire
            await self.page.evaluate('window.scrollTo(0, 200)')
            await asyncio.sleep(0.5)
            await self.page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(0.5)
            
            photos = []
            
            # Méthode 1: Cibler la div galerie principale (sc-cJSrbW juBoVb ou sc-gPEVay jnWxBz)
            gallery_selectors = [
                'div.sc-cJSrbW.juBoVb',  # Structure actuelle
                'div.sc-gPEVay.jnWxBz',  # Ancienne structure
                '[class*="sc-cJSrbW"][class*="juBoVb"]',
                '[class*="sc-gPEVay"][class*="jnWxBz"]'
            ]
            
            for selector in gallery_selectors:
                try:
                    gallery_div = self.page.locator(selector)
                    if await gallery_div.count() > 0:
                        print(f"   🎯 Div galerie trouvée ({selector}), extraction des images dans l'ordre...")
                        
                        # Extraire les images dans l'ordre exact du DOM de la galerie
                        # Extraire d'abord toutes les images de la galerie dans l'ordre du DOM
                        gallery_element = await gallery_div.first.element_handle()
                        img_elements = await gallery_element.evaluate('''
                            el => {
                                // Obtenir toutes les images dans l'ordre exact du DOM
                                const allImgs = Array.from(el.querySelectorAll('img'));
                                
                                // Extraire les infos dans l'ordre d'apparition du DOM
                                return allImgs.map((img, domIndex) => {
                                    const rect = img.getBoundingClientRect();
                                    return {
                                        domIndex: domIndex,  // Index dans le DOM
                                        src: img.src || img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || '',
                                        alt: img.alt || '',
                                        width: img.naturalWidth || img.width || 0,
                                        height: img.naturalHeight || img.height || 0,
                                        display: window.getComputedStyle(img).display,
                                        visibility: window.getComputedStyle(img).visibility,
                                        top: rect.top,  // Position pour tri de fallback
                                        left: rect.left
                                    };
                                }).filter(img => 
                                    img.display !== 'none' && 
                                    img.visibility !== 'hidden' &&
                                    img.src &&
                                    !img.src.toLowerCase().includes('preloader') &&
                                    !img.src.toLowerCase().includes('placeholder')
                                );
                            }
                        ''')
                        
                        # Extraire les images avec leur index dans la galerie pour préserver l'ordre
                        photos_with_order = []
                        for img_data in img_elements:
                            try:
                                src_to_use = img_data.get('src')
                                if not src_to_use:
                                    continue
                                
                                # Filtrer les placeholders et preloaders
                                if 'placeholder' in src_to_use.lower() or 'preloader' in src_to_use.lower():
                                    continue
                                
                                # Vérifier que c'est une vraie photo (pas un logo)
                                if 'logo' in src_to_use.lower() or 'source_logos' in src_to_use.lower():
                                    continue
                                
                                # Accepter les URLs de vraies photos d'appartements
                                photo_patterns = ['loueragile', 'upload_pro_ad', 'media.apimo.pro', 'studio-net.fr', 'images.century21.fr', 'biens', 'apartement', 'transopera', 'staticlbi', 'uploadcaregdc', 'uploadcare', 's3.amazonaws.com', 'googleusercontent.com', 'cdn.safti.fr', 'safti.fr', 'paruvendu.fr', 'immo-facile.com', 'mms.seloger.com', 'seloger.com']
                                if not any(pattern in src_to_use.lower() for pattern in photo_patterns):
                                    continue
                                
                                # Vérifier les dimensions
                                width = img_data.get('width', 0)
                                height = img_data.get('height', 0)
                                
                                if width > 0 and height > 0 and (width < 200 or height < 200):
                                    continue
                                
                                alt_text = img_data.get('alt', '')
                                
                                # Ajouter l'étage à la description si disponible
                                if etage:
                                    if alt_text and alt_text != 'preloader' and alt_text != 'appartement':
                                        alt_text = f"{alt_text} - {etage}"
                                    else:
                                        alt_text = f"Appartement - {etage}"
                                
                                # Ajouter l'image avec position visuelle pour préserver l'ordre de Jinka
                                photos_with_order.append({
                                    'url': src_to_use,
                                    'alt': alt_text or 'appartement',
                                    'selector': 'gallery',
                                    'dom_index': img_data.get('domIndex', 0),
                                    'position_top': img_data.get('top', 0),
                                    'position_left': img_data.get('left', 0)
                                })
                            except Exception as e:
                                continue
                        
                        # Trier par position visuelle (top puis left) pour conserver l'ordre de Jinka
                        # Cela correspond à l'ordre de lecture : de haut en bas, puis de gauche à droite
                        photos_with_order.sort(key=lambda x: (x.get('position_top', 0), x.get('position_left', 0)))
                        
                        # Dédupliquer en conservant l'ordre
                        seen_urls = set()
                        for photo_with_order in photos_with_order:
                            if photo_with_order['url'] not in seen_urls:
                                photo = {
                                    'url': photo_with_order['url'],
                                    'alt': photo_with_order['alt'],
                                    'selector': photo_with_order['selector']
                                }
                                photos.append(photo)
                                seen_urls.add(photo_with_order['url'])
                                print(f"   📸 Photo trouvée (top: {photo_with_order.get('position_top', 0):.0f}, left: {photo_with_order.get('position_left', 0):.0f}): {photo_with_order['url'][:60]}...")
                        
                        if len(photos) > 0:
                            break  # On a trouvé des photos dans la galerie
                except Exception as e:
                    continue
            
            # Méthode 2: Si pas de photos dans la galerie, chercher toutes les images visibles
            if len(photos) == 0:
                print("   🔍 Recherche alternative dans toutes les images visibles...")
                all_images = await self.page.query_selector_all('img')
                
                photos_with_position = []
                for index, img in enumerate(all_images):
                    try:
                        src = await img.get_attribute('src') or await img.get_attribute('data-src') or await img.get_attribute('data-lazy-src')
                        if not src:
                            continue
                        
                        # Filtrer les vraies photos d'appartement
                        photo_patterns = ['loueragile', 'upload_pro_ad', 'jinka']
                        if not any(pattern in src.lower() for pattern in photo_patterns):
                            continue
                        
                        if 'logo' in src.lower() or 'preloader' in src.lower():
                            continue
                        
                        alt = await img.get_attribute('alt')
                        
                        # Formater la description complète avec toutes les infos
                        alt = self.format_photo_description(surface, prix_m2, etage, style)
                        
                        photos_with_position.append({
                            'url': src,
                            'alt': alt or 'appartement',
                            'selector': 'all_images',
                            'dom_index': index
                        })
                    except:
                        continue
                
                # Trier par position DOM
                photos_with_position.sort(key=lambda x: x['dom_index'])
                
                # Dédupliquer
                seen_urls = set()
                for photo_with_pos in photos_with_position:
                    if photo_with_pos['url'] not in seen_urls:
                        photo = {
                            'url': photo_with_pos['url'],
                            'alt': photo_with_pos['alt'],
                            'selector': photo_with_pos['selector']
                        }
                        photos.append(photo)
                        seen_urls.add(photo_with_pos['url'])
            
            print(f"   ✅ {len(photos)} photos uniques trouvées (ordre galerie préservé)")
            return photos
            
        except Exception as e:
            print(f"   ❌ Erreur extraction photos: {e}")
            return []
    
    async def download_first_photo(self, photo_url: str, apartment_id: str) -> str:
        """Télécharge la première photo de l'appartement"""
        try:
            print(f"   📥 Téléchargement de la première photo...")
            
            # Créer le dossier
            os.makedirs("data/photos", exist_ok=True)
            
            # Télécharger l'image
            response = requests.get(photo_url, timeout=30)
            if response.status_code == 200:
                # Nom du fichier
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"data/photos/apartment_{apartment_id}_{timestamp}.jpg"
                
                # Sauvegarder
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"   ✅ Photo sauvegardée: {filename}")
                return filename
            else:
                print(f"   ❌ Erreur téléchargement: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Erreur téléchargement: {e}")
            return None
    
    async def analyze_photo_exposition(self, photo_path: str) -> dict:
        """Analyse l'exposition d'une photo d'appartement"""
        try:
            print(f"   🧭 Analyse de l'exposition de la photo...")
            
            # Pour l'instant, on va juste identifier les éléments visuels
            # Dans une vraie implémentation, on utiliserait OpenAI Vision ou une autre IA
            
            # Analyser les éléments visuels basiques
            analysis = {
                'has_windows': False,
                'has_balcony': False,
                'lighting_quality': 'unknown',
                'window_direction': 'unknown',
                'exposition': 'unknown',
                'confidence': 0.0
            }
            
            # Ici on pourrait ajouter de l'analyse d'image réelle
            # Pour l'instant, on retourne une structure de base
            
            print(f"   📊 Analyse basique: {analysis}")
            return analysis
            
        except Exception as e:
            print(f"   ❌ Erreur analyse photo: {e}")
            return {'error': str(e)}

async def test_photo_extraction():
    """Test d'extraction des photos"""
    extractor = ApartmentPhotoExtractor()
    
    try:
        await extractor.setup()
        
        # Connexion
        if not await extractor.login_jinka():
            return
        
        # URL de l'appartement test
        apartment_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
        
        # Extraire les photos
        photos = await extractor.extract_apartment_photos(apartment_url)
        
        if photos:
            print(f"\n📸 PHOTOS TROUVÉES:")
            for i, photo in enumerate(photos, 1):
                print(f"   {i}. {photo['url']}")
                print(f"      Alt: {photo['alt']}")
                print(f"      Sélecteur: {photo['selector']}")
            
            # Télécharger la première photo
            first_photo = photos[0]
            photo_path = await extractor.download_first_photo(first_photo['url'], '90931157')
            
            if photo_path:
                # Analyser l'exposition
                analysis = await extractor.analyze_photo_exposition(photo_path)
                print(f"\n🧭 ANALYSE D'EXPOSITION:")
                print(f"   Fenêtres: {analysis.get('has_windows', 'Unknown')}")
                print(f"   Balcon: {analysis.get('has_balcony', 'Unknown')}")
                print(f"   Qualité lumière: {analysis.get('lighting_quality', 'Unknown')}")
                print(f"   Direction fenêtres: {analysis.get('window_direction', 'Unknown')}")
                print(f"   Exposition: {analysis.get('exposition', 'Unknown')}")
        else:
            print("❌ Aucune photo trouvée")
    
    finally:
        await extractor.close()

if __name__ == "__main__":
    asyncio.run(test_photo_extraction())
