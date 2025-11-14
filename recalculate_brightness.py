#!/usr/bin/env python3
"""
Script pour recalculer brightness_value pour tous les appartements existants
et l'ajouter aux détails de l'exposition
"""

import json
import os
from extract_exposition import ExpositionExtractor

def recalculate_brightness_for_apartments(input_file="data/scraped_apartments.json", output_file=None):
    """Recalcule brightness_value pour tous les appartements"""
    
    if output_file is None:
        output_file = input_file
    
    print("🔄 RECALCUL DE LA LUMINOSITÉ IMAGE POUR TOUS LES APPARTEMENTS")
    print("=" * 70)
    
    # Charger les appartements
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {input_file}")
        return
    
    print(f"📊 {len(apartments)} appartements à traiter")
    print()
    
    extractor = ExpositionExtractor()
    updated_count = 0
    
    for i, apt in enumerate(apartments, 1):
        apt_id = apt.get('id', 'N/A')
        print(f"[{i}/{len(apartments)}] Appartement {apt_id}")
        
        # Vérifier si brightness_value existe déjà
        expo = apt.get('exposition', {})
        details = expo.get('details', {})
        
        if details.get('brightness_value') is not None:
            print(f"   ⏭️  Brightness déjà présent: {details.get('brightness_value'):.2f}")
            continue
        
        # Extraire les URLs des photos
        photos = apt.get('photos', [])
        photos_urls = []
        
        if photos:
            for photo in photos:
                if isinstance(photo, str):
                    photos_urls.append(photo)
                elif isinstance(photo, dict):
                    photos_urls.append(photo.get('url', ''))
        
        if not photos_urls:
            print(f"   ⚠️  Pas de photos disponibles")
            continue
        
        print(f"   📸 {len(photos_urls)} photos disponibles")
        
        # Analyser les photos pour obtenir brightness_value
        try:
            photo_result = extractor.extract_exposition_photos(photos_urls[:5])  # Analyser max 5 photos
            
            if photo_result and photo_result.get('photos_analyzed', 0) > 0:
                photo_details = photo_result.get('details', {})
                brightness_value = photo_details.get('brightness_value')
                
                if brightness_value is not None:
                    # Ajouter brightness_value aux détails de l'exposition
                    if 'exposition' not in apt:
                        apt['exposition'] = {}
                    if 'details' not in apt['exposition']:
                        apt['exposition']['details'] = {}
                    
                    apt['exposition']['details']['brightness_value'] = brightness_value
                    apt['exposition']['details']['image_brightness'] = brightness_value
                    
                    print(f"   ✅ Brightness ajouté: {brightness_value:.2f}")
                    updated_count += 1
                else:
                    print(f"   ⚠️  Brightness non calculé")
            else:
                print(f"   ⚠️  Photos non analysées")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print()
    
    # Sauvegarder les modifications
    print(f"💾 Sauvegarde dans {output_file}...")
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    
    print()
    print("📊 RÉSULTATS")
    print("=" * 70)
    print(f"✅ Appartements mis à jour: {updated_count}/{len(apartments)}")
    print(f"💾 Fichier sauvegardé: {output_file}")

if __name__ == "__main__":
    recalculate_brightness_for_apartments()






