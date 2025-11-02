#!/usr/bin/env python3
"""
Script pour re-télécharger toutes les photos depuis all_apartments_scores.json
avec numérotation correcte (photo_1.jpg, photo_2.jpg, etc.)
"""

import asyncio
import json
import os
from download_apartment_photos import ApartmentPhotoDownloader

def load_apartments():
    """Charge tous les appartements depuis all_apartments_scores.json"""
    try:
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        return apartments
    except FileNotFoundError:
        print("❌ Fichier data/scores/all_apartments_scores.json non trouvé")
        return []
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return []

def get_apartment_url(apartment):
    """Extrait l'URL de l'appartement depuis les données"""
    # Essayer différentes sources pour l'URL
    url = apartment.get('url', '')
    
    # Si pas d'URL directe, construire depuis l'ID
    if not url and apartment.get('id'):
        apartment_id = apartment.get('id')
        # Construire l'URL Jinka standard
        url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apartment_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    
    return url

async def redownload_all_photos():
    """Re-télécharge toutes les photos pour tous les appartements"""
    print("🚀 RE-TÉLÉCHARGEMENT DE TOUTES LES PHOTOS")
    print("=" * 60)
    
    # Charger les appartements
    apartments = load_apartments()
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"📊 {len(apartments)} appartements trouvés\n")
    
    # Initialiser le téléchargeur
    downloader = ApartmentPhotoDownloader()
    
    try:
        await downloader.setup()
        
        results = []
        successful = 0
        failed = 0
        total_photos = 0
        
        for i, apartment in enumerate(apartments, 1):
            apartment_id = apartment.get('id', 'unknown')
            url = get_apartment_url(apartment)
            
            if not url:
                print(f"\n⏭️  Appartement {i}/{len(apartments)} - ID: {apartment_id}")
                print(f"   ❌ Pas d'URL disponible, ignoré")
                failed += 1
                continue
            
            print(f"\n🏠 Appartement {i}/{len(apartments)} - ID: {apartment_id}")
            print(f"   🔗 URL: {url[:80]}...")
            
            try:
                # Traiter l'appartement (extraction + téléchargement)
                result = await downloader.process_apartment(url)
                
                if result:
                    photos_count = result.get('downloaded_photos', 0)
                    total_photos += photos_count
                    successful += 1
                    results.append(result)
                    print(f"   ✅ {photos_count} photos téléchargées")
                else:
                    failed += 1
                    print(f"   ❌ Aucune photo téléchargée")
                    
            except Exception as e:
                failed += 1
                print(f"   ❌ Erreur: {e}")
            
            # Pause entre les appartements pour éviter la surcharge
            if i < len(apartments):
                await asyncio.sleep(2)
        
        # Résumé final
        print(f"\n" + "=" * 60)
        print(f"🎉 RE-TÉLÉCHARGEMENT TERMINÉ !")
        print(f"   ✅ Appartements réussis: {successful}")
        print(f"   ❌ Appartements échoués: {failed}")
        print(f"   📸 Total photos téléchargées: {total_photos}")
        print(f"   📊 Moyenne: {total_photos / successful if successful > 0 else 0:.1f} photos/appartement")
        
        # Afficher le détail par appartement
        if results:
            print(f"\n📋 DÉTAIL PAR APPARTEMENT:")
            for result in results:
                apt_id = result.get('apartment_id', 'unknown')
                photos_count = result.get('downloaded_photos', 0)
                print(f"   🏠 {apt_id}: {photos_count} photos")
        
    finally:
        await downloader.close()

if __name__ == "__main__":
    asyncio.run(redownload_all_photos())

