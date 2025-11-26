#!/usr/bin/env python3
"""
Script pour tester l'extraction de photos d'un appartement spécifique
Usage: python test_single_apartment.py <apartment_id>
"""

import asyncio
import sys
import json
import os
import requests
from datetime import datetime
from scrape_jinka import JinkaScraper
from dotenv import load_dotenv

load_dotenv()

async def test_single_apartment(apartment_id):
    """Teste l'extraction de photos pour un appartement spécifique"""
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        
        # Connexion
        print("🔐 Connexion à Jinka...")
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        print("✅ Connexion réussie\n")
        
        # Charger les appartements pour trouver l'URL
        try:
            with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
                apartments = json.load(f)
            
            apartment = next((apt for apt in apartments if apt.get('id') == apartment_id), None)
            if not apartment:
                print(f"❌ Appartement {apartment_id} non trouvé dans all_apartments_scores.json")
                return
            
            apartment_url = apartment.get('url', '')
            if not apartment_url:
                print(f"❌ Pas d'URL pour l'appartement {apartment_id}")
                return
        except FileNotFoundError:
            print("❌ Fichier all_apartments_scores.json non trouvé")
            return
        
        print(f"\n{'='*60}")
        print(f"🏠 Test appartement {apartment_id}")
        print(f"{'='*60}\n")
        print(f"📍 URL: {apartment_url}\n")
        
        # Naviguer vers l'appartement
        await scraper.page.goto(apartment_url)
        await scraper.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Extraire les photos
        photos = await scraper.extract_photos()
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   Photos trouvées: {len(photos)}")
        
        if len(photos) == 0:
            print("\n⚠️  Aucune photo trouvée. Causes possibles:")
            print("   - Images en lazy loading non chargées")
            print("   - Structure HTML différente")
            print("   - Images seulement visibles au survol/clic")
            print("   - URLs d'images dans un format différent")
        else:
            # Créer le dossier v2
            photos_dir = f"data/photos_v2/{apartment_id}"
            os.makedirs(photos_dir, exist_ok=True)
            
            downloaded_photos = []
            
            for i, photo in enumerate(photos[:5], 1):  # Limiter à 5 photos
                try:
                    print(f"\n   📸 Photo {i}/{len(photos)}:")
                    print(f"      URL: {photo.get('url', 'N/A')[:80]}...")
                    print(f"      Sélecteur: {photo.get('selector', 'N/A')}")
                    print(f"      Dimensions: {photo.get('width', 'N/A')}x{photo.get('height', 'N/A')}")
                    
                    # Télécharger la photo
                    photo_url = photo.get('url', '')
                    if photo_url:
                        response = requests.get(photo_url, timeout=30)
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
                                'url': photo_url,
                                'selector': photo.get('selector', 'N/A'),
                                'width': photo.get('width', 0),
                                'height': photo.get('height', 0),
                                'filename': filename,
                                'size': file_size
                            })
                        else:
                            print(f"      ❌ Erreur téléchargement: {response.status_code}")
                    else:
                        print(f"      ❌ Pas d'URL pour cette photo")
                        
                except Exception as e:
                    print(f"      ❌ Erreur: {e}")
                    continue
            
            # Sauvegarder les métadonnées
            metadata = {
                'apartment_id': apartment_id,
                'apartment_url': apartment_url,
                'total_photos_found': len(photos),
                'photos_downloaded': len(downloaded_photos),
                'photos': downloaded_photos,
                'timestamp': datetime.now().isoformat()
            }
            
            metadata_file = f"{photos_dir}/metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 Métadonnées sauvegardées: {metadata_file}")
            print(f"\n✅ {len(downloaded_photos)} photos téléchargées dans {photos_dir}/")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper.browser:
            await scraper.browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_single_apartment.py <apartment_id>")
        print("\nExemples d'appartements sans photos détectées précédemment:")
        print("  92125826, 92274287, 88404156, 92075365, 92008125, 91908884, 91658092, 89473319, 84210379")
        sys.exit(1)
    
    apartment_id = sys.argv[1]
    asyncio.run(test_single_apartment(apartment_id))











