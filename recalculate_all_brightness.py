#!/usr/bin/env python3
"""
Recalcule le brightness pour toutes les photos de tous les appartements
et met à jour le cache
"""

import json
import os
import glob
from analyze_photos import PhotoAnalyzer
from cache_api import get_cache

def recalculate_all_brightness():
    """Recalcule le brightness pour toutes les photos"""
    
    analyzer = PhotoAnalyzer()
    cache = get_cache()
    
    # Trouver tous les fichiers d'appartements
    apartment_files = glob.glob("data/appartements/*.json")
    
    print(f"🔄 RECALCUL DU BRIGHTNESS POUR TOUTES LES PHOTOS")
    print("=" * 80)
    print(f"   {len(apartment_files)} appartements trouvés")
    print()
    
    total_photos = 0
    calculated_photos = 0
    error_photos = 0
    
    for apt_file in apartment_files:
        try:
            # Charger les données de l'appartement
            with open(apt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            apt_id = data.get('id', os.path.basename(apt_file).replace('.json', ''))
            photos = data.get('photos', [])
            
            if not photos:
                continue
            
            print(f"🏠 Appartement {apt_id}: {len(photos)} photos")
            
            # Extraire les URLs des photos
            photo_urls = []
            for photo in photos:
                if isinstance(photo, dict):
                    url = photo.get('url')
                elif isinstance(photo, str):
                    url = photo
                else:
                    continue
                
                if url:
                    photo_urls.append(url)
            
            # Calculer le brightness pour chaque photo
            for i, photo_url in enumerate(photo_urls, 1):
                total_photos += 1
                
                try:
                    # Vérifier si déjà en cache
                    cached_result = cache.get('exposition_photo', photo_url)
                    
                    # Calculer le brightness même si en cache (pour le mettre à jour)
                    print(f"   📸 Photo {i}/{len(photo_urls)}: {photo_url[:60]}...")
                    
                    # Télécharger l'image
                    import requests
                    response = requests.get(photo_url, timeout=10)
                    if response.status_code != 200:
                        print(f"      ❌ Erreur téléchargement: {response.status_code}")
                        error_photos += 1
                        continue
                    
                    # Calculer le brightness
                    brightness = analyzer._calculate_photo_brightness(response.content)
                    
                    # Mettre à jour le cache
                    if cached_result:
                        # Mettre à jour l'entrée existante
                        cached_result['brightness_value'] = brightness
                        cache.set('exposition_photo', photo_url, cached_result)
                        print(f"      ✅ Brightness calculé: {brightness:.3f} (cache mis à jour)")
                    else:
                        # Créer une nouvelle entrée minimale
                        new_result = {
                            'brightness_value': brightness,
                            'luminosite_relative': 'moyen',  # Valeur par défaut
                            'score_luminosite': 5,
                            'confidence': 0.5
                        }
                        cache.set('exposition_photo', photo_url, new_result)
                        print(f"      ✅ Brightness calculé: {brightness:.3f} (nouvelle entrée)")
                    
                    calculated_photos += 1
                    
                except Exception as e:
                    print(f"      ❌ Erreur: {e}")
                    error_photos += 1
                    continue
            
            print()
            
        except Exception as e:
            print(f"❌ Erreur traitement {apt_file}: {e}")
            print()
            continue
    
    print("=" * 80)
    print("📊 RÉSUMÉ:")
    print(f"   Total photos: {total_photos}")
    print(f"   Brightness calculés: {calculated_photos}")
    print(f"   Erreurs: {error_photos}")
    print(f"   Taux de succès: {calculated_photos/total_photos*100:.1f}%" if total_photos > 0 else "   Taux de succès: 0%")
    print()

if __name__ == "__main__":
    recalculate_all_brightness()

