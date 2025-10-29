#!/usr/bin/env python3
"""
Extraction et analyse des photos d'appartement pour déterminer l'exposition
"""

import asyncio
import json
import os
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
    
    async def extract_apartment_photos(self, apartment_url: str) -> list:
        """Extrait les photos d'un appartement"""
        try:
            print(f"🏠 Extraction des photos: {apartment_url}")
            await self.page.goto(apartment_url)
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(3000)
            
            # Chercher les images d'appartement
            photo_urls = []
            
            # Méthode 1: Chercher les images avec des sélecteurs spécifiques
            selectors = [
                'img[alt*="logement"]',
                'img[alt*="appartement"]',
                'img[alt*="intérieur"]',
                'img[alt*="salon"]',
                'img[alt*="cuisine"]',
                'img[alt*="chambre"]',
                'img[src*="loueragile-media"]',
                'img[src*="upload_pro_ad"]',
                '.apartment-photo img',
                '.property-photo img',
                '.listing-photo img'
            ]
            
            for selector in selectors:
                try:
                    images = await self.page.query_selector_all(selector)
                    for img in images:
                        src = await img.get_attribute('src')
                        alt = await img.get_attribute('alt')
                        if src and ('loueragile' in src or 'upload_pro_ad' in src):
                            photo_urls.append({
                                'url': src,
                                'alt': alt,
                                'selector': selector
                            })
                            print(f"   📸 Photo trouvée: {src[:80]}...")
                except:
                    continue
            
            # Méthode 2: Chercher toutes les images et filtrer
            if not photo_urls:
                print("   🔍 Recherche alternative...")
                all_images = await self.page.query_selector_all('img')
                for img in all_images:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt')
                    if src and ('loueragile' in src or 'upload_pro_ad' in src or 'jinka' in src):
                        photo_urls.append({
                            'url': src,
                            'alt': alt or 'appartement',
                            'selector': 'all_images'
                        })
                        print(f"   📸 Photo trouvée (alt): {src[:80]}...")
            
            # Dédupliquer
            unique_photos = []
            seen_urls = set()
            for photo in photo_urls:
                if photo['url'] not in seen_urls:
                    unique_photos.append(photo)
                    seen_urls.add(photo['url'])
            
            print(f"   ✅ {len(unique_photos)} photos uniques trouvées")
            return unique_photos
            
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
