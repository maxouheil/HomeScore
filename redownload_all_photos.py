#!/usr/bin/env python3
"""
Retélécharge toutes les photos pour tous les appartements avec le nouveau système
"""

import asyncio
import json
import os
from download_apartment_photos import ApartmentPhotoDownloader

def get_all_apartment_urls():
    """Récupère toutes les URLs d'appartements depuis scores.json ou data/appartements"""
    apartment_urls = []
    
    # Méthode 1: Depuis scores.json
    if os.path.exists('data/scores.json'):
        try:
            with open('data/scores.json', 'r', encoding='utf-8') as f:
                apartments = json.load(f)
            
            base_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
            
            for apt in apartments:
                apt_id = apt.get('id')
                apt_url = apt.get('url')
                
                if apt_url:
                    apartment_urls.append(apt_url)
                elif apt_id:
                    apartment_urls.append(base_url.format(apt_id))
            
            print(f"✅ {len(apartment_urls)} URLs trouvées depuis scores.json")
        except Exception as e:
            print(f"⚠️ Erreur lecture scores.json: {e}")
    
    # Méthode 2: Depuis data/appartements/*.json
    if not apartment_urls and os.path.exists('data/appartements'):
        try:
            base_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
            
            for filename in os.listdir('data/appartements'):
                if filename.endswith('.json'):
                    apt_id = filename.replace('.json', '')
                    apartment_urls.append(base_url.format(apt_id))
            
            print(f"✅ {len(apartment_urls)} URLs trouvées depuis data/appartements/")
        except Exception as e:
            print(f"⚠️ Erreur lecture data/appartements: {e}")
    
    return apartment_urls

async def main():
    """Fonction principale"""
    print("🚀 RETÉLÉCHARGEMENT DE TOUTES LES PHOTOS")
    print("=" * 60)
    
    # Récupérer toutes les URLs
    apartment_urls = get_all_apartment_urls()
    
    if not apartment_urls:
        print("❌ Aucune URL d'appartement trouvée")
        return
    
    print(f"📊 {len(apartment_urls)} appartements à traiter")
    print(f"📸 Nouveau système: extraction de TOUTES les photos (visibles + cachées)")
    print(f"💾 Nommage: photo1.jpg, photo2.jpg, etc.")
    print(f"🗑️ Suppression automatique des anciennes photos")
    print()
    
    downloader = ApartmentPhotoDownloader()
    
    try:
        await downloader.setup()
        
        results = []
        total_photos = 0
        
        for i, url in enumerate(apartment_urls, 1):
            print(f"\n{'='*60}")
            print(f"🏠 Appartement {i}/{len(apartment_urls)}")
            print(f"{'='*60}")
            
            result = await downloader.process_apartment(url)
            if result:
                results.append(result)
                total_photos += result['downloaded_photos']
                print(f"✅ {result['downloaded_photos']} photos téléchargées")
            else:
                print(f"❌ Échec du traitement")
            
            # Pause entre les appartements
            if i < len(apartment_urls):
                await asyncio.sleep(2)
        
        # Résumé final
        print(f"\n{'='*60}")
        print(f"🎉 RETÉLÉCHARGEMENT TERMINÉ !")
        print(f"{'='*60}")
        print(f"✅ {len(results)} appartements traités avec succès")
        print(f"📸 {total_photos} photos téléchargées au total")
        
        if len(results) > 0:
            avg_photos = total_photos / len(results)
            print(f"📊 Moyenne: {avg_photos:.2f} photos/appartement")
            
            print(f"\n📋 DÉTAIL PAR APPARTEMENT:")
            for result in results:
                print(f"   🏠 {result['apartment_id']}: {result['downloaded_photos']} photos")
    
    finally:
        await downloader.close()

if __name__ == "__main__":
    asyncio.run(main())
