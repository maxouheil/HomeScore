#!/usr/bin/env python3
"""
Téléchargement et stockage de 3-4 photos par appartement
"""

import asyncio
import json
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class ApartmentPhotoDownloader:
    """Téléchargeur de photos d'appartement"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup(self):
        """Initialise le navigateur"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
    async def close(self):
        """Ferme le navigateur"""
        if self.browser:
            await self.browser.close()
    
    async def extract_apartment_photos(self, apartment_url: str) -> list:
        """Extrait les URLs des photos d'un appartement"""
        try:
            print(f"🏠 Extraction des photos: {apartment_url}")
            await self.page.goto(apartment_url)
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(3000)
            
            # Chercher les images d'appartement avec des sélecteurs spécifiques
            selectors = [
                'img[alt*="logement"]',
                'img[alt*="appartement"]', 
                'img[alt*="intérieur"]',
                'img[alt*="salon"]',
                'img[alt*="cuisine"]',
                'img[alt*="chambre"]',
                'img[src*="loueragile-media"]',
                'img[src*="upload_pro_ad"]',
                'img[src*="media.apimo.pro"]',
                '.apartment-photo img',
                '.property-photo img',
                '.listing-photo img',
                '.swiper-slide img',
                '.carousel img'
            ]
            
            photos = []
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        src = await element.get_attribute('src')
                        alt = await element.get_attribute('alt')
                        if src and ('loueragile' in src or 'upload_pro_ad' in src or 'media.apimo.pro' in src):
                            photos.append({
                                'url': src,
                                'alt': alt or 'appartement',
                                'selector': selector
                            })
                            print(f"      📸 Photo trouvée: {src[:60]}...")
                except Exception as e:
                    continue
            
            # Si pas de photos trouvées, chercher toutes les images
            if not photos:
                print("      🔍 Recherche alternative dans toutes les images...")
                all_images = await self.page.query_selector_all('img')
                for img in all_images:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt')
                    if src and ('loueragile' in src or 'upload_pro_ad' in src or 'media.apimo.pro' in src):
                        photos.append({
                            'url': src,
                            'alt': alt or 'appartement',
                            'selector': 'all_images'
                        })
                        print(f"      📸 Photo trouvée (alt): {src[:60]}...")
            
            # Dédupliquer
            unique_photos = []
            seen_urls = set()
            for photo in photos:
                if photo['url'] not in seen_urls:
                    unique_photos.append(photo)
                    seen_urls.add(photo['url'])
            
            print(f"   ✅ {len(unique_photos)} photos d'appartement trouvées")
            return unique_photos[:4]  # Max 4 photos
            
        except Exception as e:
            print(f"   ❌ Erreur extraction photos: {e}")
            return []
    
    async def download_photos(self, photos: list, apartment_id: str) -> list:
        """Télécharge les photos d'un appartement"""
        try:
            print(f"   📥 Téléchargement de {len(photos)} photos...")
            
            # Créer le dossier
            os.makedirs(f"data/photos/{apartment_id}", exist_ok=True)
            
            downloaded_photos = []
            for i, photo in enumerate(photos):
                try:
                    print(f"      📸 Téléchargement photo {i+1}/{len(photos)}...")
                    
                    # Télécharger l'image
                    response = requests.get(photo['url'], timeout=30)
                    if response.status_code == 200:
                        # Nom du fichier
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"data/photos/{apartment_id}/photo_{i+1}_{timestamp}.jpg"
                        
                        # Sauvegarder
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        downloaded_photos.append({
                            'url': photo['url'],
                            'alt': photo['alt'],
                            'filename': filename,
                            'size': len(response.content),
                            'selector': photo['selector']
                        })
                        
                        print(f"      ✅ Photo {i+1} sauvegardée: {filename} ({len(response.content)} bytes)")
                    else:
                        print(f"      ❌ Erreur téléchargement photo {i+1}: {response.status_code}")
                        
                except Exception as e:
                    print(f"      ❌ Erreur téléchargement photo {i+1}: {e}")
                    continue
            
            print(f"   ✅ {len(downloaded_photos)} photos téléchargées avec succès")
            return downloaded_photos
                
        except Exception as e:
            print(f"   ❌ Erreur téléchargement: {e}")
            return []
    
    async def process_apartment(self, apartment_url: str):
        """Traite un appartement complet (extraction + téléchargement)"""
        try:
            # Extraire l'ID de l'appartement
            import re
            match = re.search(r'ad=(\d+)', apartment_url)
            apartment_id = match.group(1) if match else "unknown"
            
            # Extraire les photos
            photos = await self.extract_apartment_photos(apartment_url)
            
            if photos:
                # Télécharger les photos
                downloaded_photos = await self.download_photos(photos, apartment_id)
                
                # Sauvegarder les métadonnées
                metadata = {
                    'apartment_id': apartment_id,
                    'apartment_url': apartment_url,
                    'total_photos': len(photos),
                    'downloaded_photos': len(downloaded_photos),
                    'photos': downloaded_photos,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Sauvegarder les métadonnées
                os.makedirs('data/photos_metadata', exist_ok=True)
                with open(f'data/photos_metadata/{apartment_id}.json', 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Appartement {apartment_id} traité: {len(downloaded_photos)} photos téléchargées")
                return metadata
            else:
                print(f"❌ Aucune photo trouvée pour l'appartement {apartment_id}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur traitement appartement: {e}")
            return None

async def test_photo_download():
    """Test de téléchargement des photos"""
    downloader = ApartmentPhotoDownloader()
    
    try:
        await downloader.setup()
        
        # URL de l'appartement test
        apartment_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
        
        # Traiter l'appartement
        result = await downloader.process_apartment(apartment_url)
        
        if result:
            print(f"\n📊 RÉSULTATS:")
            print(f"   Appartement ID: {result['apartment_id']}")
            print(f"   Photos trouvées: {result['total_photos']}")
            print(f"   Photos téléchargées: {result['downloaded_photos']}")
            print(f"   Dossier: data/photos/{result['apartment_id']}/")
        else:
            print("❌ Échec du traitement")
    
    finally:
        await downloader.close()

async def batch_download_photos(apartment_urls: list):
    """Télécharge les photos de plusieurs appartements"""
    downloader = ApartmentPhotoDownloader()
    
    try:
        await downloader.setup()
        
        results = []
        for i, url in enumerate(apartment_urls, 1):
            print(f"\n🏠 Traitement appartement {i}/{len(apartment_urls)}")
            result = await downloader.process_apartment(url)
            if result:
                results.append(result)
            
            # Pause entre les appartements
            await asyncio.sleep(2)
        
        print(f"\n✅ BATCH TERMINÉ: {len(results)} appartements traités")
        return results
    
    finally:
        await downloader.close()

if __name__ == "__main__":
    # Test avec un appartement
    asyncio.run(test_photo_download())
