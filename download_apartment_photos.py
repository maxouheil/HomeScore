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
        """Extrait les URLs des photos d'un appartement depuis la div galerie spécifique"""
        try:
            print(f"🏠 Extraction des photos: {apartment_url}")
            await self.page.goto(apartment_url)
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(3000)
            
            photos = []
            
            # Attendre un peu plus longtemps pour le chargement des images lazy
            await asyncio.sleep(1)
            
            # Scroller un peu pour déclencher le chargement lazy si nécessaire
            await self.page.evaluate('window.scrollTo(0, 200)')
            await asyncio.sleep(0.5)
            await self.page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(0.5)
            
            # Méthode 1: Cibler la div galerie principale (structure actuelle)
            gallery_selectors = [
                'div.sc-cJSrbW.juBoVb',  # Structure actuelle visible
                'div.sc-gPEVay.jnWxBz',  # Ancienne structure
                '[class*="sc-cJSrbW"][class*="juBoVb"]',
                '[class*="sc-gPEVay"][class*="jnWxBz"]'
            ]
            
            for selector in gallery_selectors:
                try:
                    gallery_div = self.page.locator(selector)
                    if await gallery_div.count() > 0:
                        print(f"      🎯 Div galerie trouvée ({selector}), extraction des images visibles...")
                        
                        # PRIORITÉ 1: Chercher dans les divs visibles avec classes "col" (première, middle, last)
                        # Ces divs contiennent les photos réellement affichées
                        col_selectors = [
                            '[class*="col"][class*="first"] img',
                            '[class*="col"][class*="middle"] img',
                            '[class*="col"][class*="last"] img',
                            '[class*="cyvIwy"] img',
                            '.col img'
                        ]
                        
                        visible_images = []
                        seen_srcs = set()  # Pour dédupliquer par URL
                        for col_selector in col_selectors:
                            try:
                                col_images = await gallery_div.locator(col_selector).all()
                                if col_images:
                                    print(f"      🔍 {len(col_images)} images trouvées dans les divs 'col' ({col_selector})")
                                    # Ajouter toutes les images trouvées (ne pas break pour accumuler)
                                    for img in col_images:
                                        try:
                                            # Vérifier si on a déjà vu cette URL
                                            src = await img.get_attribute('src') or await img.get_attribute('data-src')
                                            if src and src not in seen_srcs:
                                                visible_images.append(img)
                                                seen_srcs.add(src)
                                        except:
                                            # Si on ne peut pas vérifier l'URL, on ajoute quand même
                                            visible_images.append(img)
                            except:
                                continue
                        
                        # Si on a trouvé des images dans les divs col, on les garde
                        if len(visible_images) > 0:
                            print(f"      ✅ {len(visible_images)} images uniques trouvées dans toutes les divs 'col'")
                        
                        # PRIORITÉ 2: Si pas trouvé dans les divs col, chercher toutes les images visibles
                        if len(visible_images) == 0:
                            visible_images = await gallery_div.locator('img:visible').all()
                            print(f"      🔍 {len(visible_images)} images VISIBLES trouvées dans la div galerie")
                        
                        # Exclure les images avec alt="preloader" SAUF si l'URL correspond à un pattern valide
                        # (car certaines images visibles ont alt="preloader" mais sont de vraies photos)
                        if len(visible_images) > 0:
                            filtered_images = []
                            photo_patterns = ['loueragile', 'upload_pro_ad', 'media.apimo.pro', 'studio-net.fr', 'images.century21.fr', 'biens', 'apartement', 'transopera', 'staticlbi', 'uploadcaregdc', 'uploadcare', 's3.amazonaws.com', 'googleusercontent.com', 'cdn.safti.fr', 'safti.fr', 'paruvendu.fr', 'immo-facile.com', 'mms.seloger.com', 'seloger.com']
                            for img in visible_images:
                                try:
                                    alt = await img.get_attribute('alt')
                                    src = await img.get_attribute('src') or await img.get_attribute('data-src')
                                    # Si alt="preloader" mais URL valide, on garde quand même
                                    if alt and 'preloader' in alt.lower() and src:
                                        if any(pattern in src.lower() for pattern in photo_patterns):
                                            # URL valide malgré alt="preloader", on garde
                                            filtered_images.append(img)
                                        else:
                                            # alt="preloader" et URL non valide, on skip
                                            continue
                                    else:
                                        # Pas de alt="preloader" ou pas d'URL, on garde
                                        filtered_images.append(img)
                                except:
                                    filtered_images.append(img)
                            visible_images = filtered_images
                            print(f"      🔍 {len(visible_images)} images après filtrage (sans preloader)")
                        
                        # Extraire les photos avec leur position DOM pour préserver l'ordre
                        photos_with_position = []
                        for img in visible_images:
                            try:
                                # Vérifier que l'image n'est pas cachée
                                display = await img.evaluate('el => window.getComputedStyle(el).display')
                                if display == 'none':
                                    continue
                                
                                # Obtenir la position visuelle (top, left) pour préserver l'ordre de Jinka
                                position = await img.evaluate('''
                                    el => {
                                        const rect = el.getBoundingClientRect();
                                        return { top: rect.top, left: rect.left };
                                    }
                                ''')
                                
                                # Obtenir aussi l'index DOM pour ordre de fallback
                                dom_index = await img.evaluate('''
                                    el => {
                                        const allImgs = document.querySelectorAll('img');
                                        return Array.from(allImgs).indexOf(el);
                                    }
                                ''')
                                
                                # Vérifier les dimensions de l'image (exclure les très petites comme les logos)
                                width = await img.evaluate('el => el.naturalWidth || el.width || 0')
                                height = await img.evaluate('el => el.naturalHeight || el.height || 0')
                                
                                # Les logos font généralement ~128x128px, les vraies photos sont beaucoup plus grandes
                                # On exclut seulement les images très petites (< 200px)
                                if width > 0 and height > 0:
                                    if width < 200 or height < 200:
                                        # Probablement un logo ou icône (ex: logo immobilier 128x128), on skip
                                        continue
                                
                                # Récupérer src et data-src (lazy loading)
                                src = await img.get_attribute('src')
                                data_src = await img.get_attribute('data-src')
                                data_lazy = await img.get_attribute('data-lazy-src')
                                srcset = await img.get_attribute('srcset')
                                
                                # Utiliser src, data-src ou extraire de srcset
                                src_to_use = src
                                if not src_to_use or 'placeholder' in src_to_use.lower() or 'preloader' in src_to_use.lower():
                                    src_to_use = data_src or data_lazy
                                
                                # Si srcset, extraire la première URL
                                if not src_to_use and srcset:
                                    srcset_urls = srcset.split(',')
                                    if srcset_urls:
                                        src_to_use = srcset_urls[0].strip().split(' ')[0]
                                
                                if not src_to_use:
                                    continue
                                
                                alt = await img.get_attribute('alt')
                                
                                # Vérifier que c'est une vraie photo (pas un logo)
                                if 'logo' in src_to_use.lower() or 'source_logos' in src_to_use.lower() or 'preloader' in src_to_use.lower():
                                    continue
                                
                                # Accepter les URLs de vraies photos d'appartements (patterns étendus)
                                photo_patterns = ['loueragile', 'upload_pro_ad', 'media.apimo.pro', 'studio-net.fr', 'images.century21.fr', 'biens', 'apartement', 'transopera', 'staticlbi', 'uploadcaregdc', 'uploadcare', 's3.amazonaws.com', 'googleusercontent.com', 'cdn.safti.fr', 'safti.fr', 'paruvendu.fr', 'immo-facile.com', 'mms.seloger.com', 'seloger.com']
                                if not any(pattern in src_to_use.lower() for pattern in photo_patterns):
                                    continue
                                
                                # Si l'image n'est pas encore chargée, essayer de la charger
                                if width == 0 or height == 0:
                                    await asyncio.sleep(0.5)
                                    width = await img.evaluate('el => el.naturalWidth || el.width || 0')
                                    height = await img.evaluate('el => el.naturalHeight || el.height || 0')
                                
                                photos_with_position.append({
                                    'url': src_to_use,
                                    'alt': alt or 'appartement',
                                    'selector': 'gallery_div_visible',
                                    'width': width,
                                    'height': height,
                                    'dom_index': dom_index,
                                    'position_top': position['top'],
                                    'position_left': position['left']
                                })
                            except Exception as e:
                                continue
                        
                        # Trier par position visuelle (top puis left) pour conserver l'ordre de Jinka
                        # Cela correspond à l'ordre de lecture : de haut en bas, puis de gauche à droite
                        photos_with_position.sort(key=lambda x: (x.get('position_top', 0), x.get('position_left', 0)))
                        
                        # Ajouter les photos dans l'ordre correct (ordre visuel de Jinka)
                        for photo_with_pos in photos_with_position:
                            photo = {k: v for k, v in photo_with_pos.items() if k not in ['dom_index', 'position_top', 'position_left']}
                            photos.append(photo)
                            print(f"      📸 Photo galerie visible ({photo_with_pos['width']}x{photo_with_pos['height']}): {photo_with_pos['url'][:60]}...")
                        
                        if len(photos) > 0:
                            break  # On a trouvé des photos, pas besoin d'essayer les autres sélecteurs
                except Exception as e:
                    continue
            
            # Méthode 2: Si pas de photos dans la galerie, chercher les images visibles avec URLs d'appartement
            if not photos:
                print("      🔍 Recherche alternative dans les images visibles...")
                all_visible_images = await self.page.locator('img:visible').all()
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
                        
                        # Récupérer src et data-src (lazy loading)
                        src = await img.get_attribute('src')
                        data_src = await img.get_attribute('data-src')
                        data_lazy = await img.get_attribute('data-lazy-src')
                        srcset = await img.get_attribute('srcset')
                        
                        # Utiliser src, data-src ou extraire de srcset
                        src_to_use = src
                        if not src_to_use or 'placeholder' in src_to_use.lower() or 'preloader' in src_to_use.lower():
                            src_to_use = data_src or data_lazy
                        
                        # Si srcset, extraire la première URL
                        if not src_to_use and srcset:
                            srcset_urls = srcset.split(',')
                            if srcset_urls:
                                src_to_use = srcset_urls[0].strip().split(' ')[0]
                        
                        if not src_to_use:
                            continue
                        
                        alt = await img.get_attribute('alt')
                        
                        # Vérifier que c'est une vraie photo (pas un logo)
                        if 'logo' in src_to_use.lower() or 'source_logos' in src_to_use.lower() or 'preloader' in src_to_use.lower():
                            continue
                        
                        # Accepter les URLs de vraies photos d'appartements (patterns étendus)
                        photo_patterns = ['loueragile', 'upload_pro_ad', 'media.apimo.pro', 'studio-net.fr', 'images.century21.fr', 'biens', 'apartement', 'transopera', 'staticlbi', 'uploadcaregdc', 'uploadcare', 's3.amazonaws.com', 'googleusercontent.com', 'cdn.safti.fr', 'safti.fr', 'paruvendu.fr', 'immo-facile.com', 'mms.seloger.com', 'seloger.com']
                        if not any(pattern in src_to_use.lower() for pattern in photo_patterns):
                            continue
                        
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
