#!/usr/bin/env python3
"""
Script de test pour la nouvelle extraction de photos v2
Teste l'extraction améliorée et sauvegarde dans data/photos_v2/
"""

import asyncio
import json
import os
import requests
from datetime import datetime
from scrape_jinka import JinkaScraper
from dotenv import load_dotenv

load_dotenv()

async def test_photo_extraction():
    """Teste l'extraction de photos avec le nouveau système"""
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        
        # Connexion
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        print("✅ Connexion réussie\n")
        
        # URL d'appartement de test
        test_apartments = [
            {
                'id': '90931157',
                'url': 'https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1'
            },
            {
                'id': '85653922',
                'url': 'https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=85653922&from=dashboard_card&from_alert_filter=all&from_alert_page=1'
            }
        ]
        
        results = []
        
        for apt in test_apartments:
            print(f"\n{'='*60}")
            print(f"🏠 Test appartement {apt['id']}")
            print(f"{'='*60}\n")
            
            # Naviguer vers l'appartement
            await scraper.page.goto(apt['url'])
            await scraper.page.wait_for_load_state('networkidle')
            await scraper.page.wait_for_timeout(2000)
            
            # Extraire les photos
            photos = await scraper.extract_photos()
            
            print(f"\n📊 RÉSULTATS:")
            print(f"   Photos trouvées: {len(photos)}")
            
            # Créer le dossier v2
            photos_dir = f"data/photos_v2/{apt['id']}"
            os.makedirs(photos_dir, exist_ok=True)
            
            downloaded_photos = []
            
            for i, photo in enumerate(photos, 1):
                try:
                    print(f"\n   📸 Photo {i}/{len(photos)}:")
                    print(f"      URL: {photo['url'][:80]}...")
                    print(f"      Sélecteur: {photo.get('selector', 'N/A')}")
                    print(f"      Dimensions: {photo.get('width', 'N/A')}x{photo.get('height', 'N/A')}")
                    
                    # Télécharger la photo
                    response = requests.get(photo['url'], timeout=30)
                    if response.status_code == 200:
                        # Sauvegarder
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"{photos_dir}/photo_{i}_{timestamp}.jpg"
                        
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        file_size = len(response.content)
                        print(f"      ✅ Téléchargée: {filename} ({file_size:,} bytes)")
                        
                        downloaded_photos.append({
                            'index': i,
                            'url': photo['url'],
                            'selector': photo.get('selector', 'N/A'),
                            'width': photo.get('width', 0),
                            'height': photo.get('height', 0),
                            'filename': filename,
                            'size': file_size
                        })
                    else:
                        print(f"      ❌ Erreur téléchargement: {response.status_code}")
                        
                except Exception as e:
                    print(f"      ❌ Erreur: {e}")
                    continue
            
            # Sauvegarder les métadonnées
            metadata = {
                'apartment_id': apt['id'],
                'apartment_url': apt['url'],
                'total_photos_found': len(photos),
                'photos_downloaded': len(downloaded_photos),
                'photos': downloaded_photos,
                'timestamp': datetime.now().isoformat()
            }
            
            metadata_file = f"{photos_dir}/metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"\n   📄 Métadonnées sauvegardées: {metadata_file}")
            
            results.append(metadata)
        
        # Rapport final
        print(f"\n\n{'='*60}")
        print("📊 RAPPORT FINAL")
        print(f"{'='*60}\n")
        
        for result in results:
            print(f"Appartement {result['apartment_id']}:")
            print(f"   Photos trouvées: {result['total_photos_found']}")
            print(f"   Photos téléchargées: {result['photos_downloaded']}")
            print(f"   Dossier: data/photos_v2/{result['apartment_id']}/")
            
            if result['photos_downloaded'] > 0:
                print(f"   Dimensions moyennes:")
                widths = [p['width'] for p in result['photos'] if p['width'] > 0]
                heights = [p['height'] for p in result['photos'] if p['height'] > 0]
                if widths and heights:
                    avg_width = sum(widths) / len(widths)
                    avg_height = sum(heights) / len(heights)
                    print(f"      Largeur moyenne: {avg_width:.0f}px")
                    print(f"      Hauteur moyenne: {avg_height:.0f}px")
            print()
        
        print("✅ Test terminé ! Vérifiez les photos dans data/photos_v2/")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper.browser:
            await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(test_photo_extraction())

