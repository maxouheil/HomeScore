#!/usr/bin/env python3
"""
Script de test pour extraire les photos de TOUS les appartements avec le nouveau système v2
"""

import asyncio
import json
import os
import requests
from datetime import datetime
from scrape_jinka import JinkaScraper
from dotenv import load_dotenv

load_dotenv()

async def extract_all_photos():
    """Extrait les photos de tous les appartements"""
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        
        # Connexion
        print("🔐 Connexion à Jinka...")
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        print("✅ Connexion réussie\n")
        
        # Charger tous les appartements depuis les scores
        print("📋 Chargement des appartements...")
        try:
            with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
                apartments = json.load(f)
            print(f"✅ {len(apartments)} appartements trouvés\n")
        except FileNotFoundError:
            print("❌ Fichier all_apartments_scores.json non trouvé")
            return
        
        results = []
        success_count = 0
        error_count = 0
        
        for i, apartment in enumerate(apartments, 1):
            apartment_id = apartment.get('id', 'unknown')
            apartment_url = apartment.get('url', '')
            
            if not apartment_url:
                print(f"\n{'='*60}")
                print(f"⚠️  Appartement {i}/{len(apartments)}: {apartment_id} - Pas d'URL")
                print(f"{'='*60}")
                error_count += 1
                continue
            
            print(f"\n{'='*60}")
            print(f"🏠 Appartement {i}/{len(apartments)}: {apartment_id}")
            print(f"{'='*60}\n")
            
            try:
                # Naviguer vers l'appartement
                await scraper.page.goto(apartment_url)
                await scraper.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)  # Attendre le chargement
                
                # Extraire les photos
                photos = await scraper.extract_photos()
                
                print(f"📊 Photos trouvées: {len(photos)}")
                
                # Créer le dossier v2
                photos_dir = f"data/photos_v2/{apartment_id}"
                os.makedirs(photos_dir, exist_ok=True)
                
                downloaded_photos = []
                
                for j, photo in enumerate(photos[:5], 1):  # Limiter à 5 photos max
                    try:
                        # Télécharger la photo
                        response = requests.get(photo['url'], timeout=30)
                        if response.status_code == 200:
                            # Sauvegarder
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = f"{photos_dir}/photo_{j}_{timestamp}.jpg"
                            
                            with open(filename, 'wb') as f:
                                f.write(response.content)
                            
                            file_size = len(response.content)
                            print(f"   ✅ Photo {j}/{len(photos[:5])} téléchargée ({photo.get('width', '?')}x{photo.get('height', '?')}, {file_size:,} bytes)")
                            
                            downloaded_photos.append({
                                'index': j,
                                'url': photo['url'],
                                'selector': photo.get('selector', 'N/A'),
                                'width': photo.get('width', 0),
                                'height': photo.get('height', 0),
                                'filename': filename,
                                'size': file_size
                            })
                        else:
                            print(f"   ❌ Erreur téléchargement photo {j}: {response.status_code}")
                            
                    except Exception as e:
                        print(f"   ❌ Erreur photo {j}: {e}")
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
                
                print(f"📄 Métadonnées sauvegardées\n")
                
                results.append(metadata)
                success_count += 1
                
                # Pause entre les appartements pour éviter de surcharger
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Erreur traitement appartement {apartment_id}: {e}")
                error_count += 1
                continue
        
        # Rapport final
        print(f"\n\n{'='*60}")
        print("📊 RAPPORT FINAL")
        print(f"{'='*60}\n")
        
        print(f"Total appartements: {len(apartments)}")
        print(f"✅ Succès: {success_count}")
        print(f"❌ Erreurs: {error_count}\n")
        
        if results:
            total_photos_found = sum(r['total_photos_found'] for r in results)
            total_photos_downloaded = sum(r['photos_downloaded'] for r in results)
            
            print(f"📸 Photos trouvées au total: {total_photos_found}")
            print(f"📥 Photos téléchargées au total: {total_photos_downloaded}\n")
            
            # Statistiques par appartement
            print("📊 Détails par appartement:")
            for result in results:
                print(f"   {result['apartment_id']}: {result['photos_downloaded']}/{result['total_photos_found']} photos")
                
                if result['photos_downloaded'] > 0:
                    widths = [p['width'] for p in result['photos'] if p['width'] > 0]
                    if widths:
                        avg_width = sum(widths) / len(widths)
                        print(f"      Dimensions moyennes: {avg_width:.0f}px de large")
        
        print(f"\n✅ Extraction terminée ! Vérifiez les photos dans data/photos_v2/")
        
        # Sauvegarder le rapport global
        global_report = {
            'total_apartments': len(apartments),
            'success_count': success_count,
            'error_count': error_count,
            'total_photos_found': sum(r['total_photos_found'] for r in results),
            'total_photos_downloaded': sum(r['photos_downloaded'] for r in results),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        report_file = 'data/photos_v2/global_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(global_report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Rapport global sauvegardé: {report_file}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper.browser:
            await scraper.browser.close()

if __name__ == "__main__":
    asyncio.run(extract_all_photos())

