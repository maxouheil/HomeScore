#!/usr/bin/env python3
"""
Diagnostic complet pour identifier pourquoi certains appartements n'ont pas d'images
"""

import json
import os
import re
from generate_fitscore_style_html import get_all_apartment_photos

def check_apartment_photos(apartment):
    """Vérifie complètement les photos d'un appartement"""
    apt_id = apartment.get('id', 'unknown')
    
    result = {
        'id': apt_id,
        'url': apartment.get('url', 'N/A'),
        'has_json_photos': False,
        'json_photos_count': 0,
        'has_photos_v2_dir': False,
        'photos_v2_count': 0,
        'has_photos_dir': False,
        'photos_dir_count': 0,
        'detected_photos_count': 0,
        'detected_photo_paths': [],
        'issues': []
    }
    
    # 1. Vérifier les photos dans le JSON
    json_photos = apartment.get('photos', [])
    if json_photos:
        result['has_json_photos'] = True
        result['json_photos_count'] = len(json_photos)
    else:
        result['issues'].append('Aucune photo dans le JSON')
    
    # 2. Vérifier le dossier photos_v2
    photos_v2_dir = f"data/photos_v2/{apt_id}"
    if os.path.exists(photos_v2_dir):
        result['has_photos_v2_dir'] = True
        files = [f for f in os.listdir(photos_v2_dir) 
                if f.endswith(('.jpg', '.jpeg', '.png')) and f.startswith('photo_')]
        result['photos_v2_count'] = len(files)
        if len(files) == 0:
            result['issues'].append(f'Dossier photos_v2/{apt_id} existe mais vide')
    else:
        result['issues'].append(f'Dossier photos_v2/{apt_id} n\'existe pas')
    
    # 3. Vérifier le dossier photos
    photos_dir = f"data/photos/{apt_id}"
    if os.path.exists(photos_dir):
        result['has_photos_dir'] = True
        files = [f for f in os.listdir(photos_dir) 
                if f.endswith(('.jpg', '.jpeg', '.png'))]
        result['photos_dir_count'] = len(files)
        if len(files) == 0:
            result['issues'].append(f'Dossier photos/{apt_id} existe mais vide')
        
        # Vérifier les patterns exclus
        excluded_patterns = ['AppStore.png', 'GoogleStore.png', 'Logo-Jinka', 'logo-', 
                           'source_logos', 'no-picture.png', 'placeholder', 'icon', 'logo']
        excluded_files = []
        for f in files:
            if any(pattern.lower() in f.lower() for pattern in excluded_patterns):
                excluded_files.append(f)
        if excluded_files:
            result['issues'].append(f'Fichiers exclus par filtrage: {excluded_files}')
    else:
        result['issues'].append(f'Dossier photos/{apt_id} n\'existe pas')
    
    # 4. Vérifier la détection par get_all_apartment_photos
    try:
        detected_photos = get_all_apartment_photos(apartment)
        result['detected_photos_count'] = len(detected_photos)
        result['detected_photo_paths'] = detected_photos[:3]  # Premières 3
    except Exception as e:
        result['issues'].append(f'Erreur lors de la détection: {e}')
    
    # 5. Identifier les problèmes
    if result['detected_photos_count'] == 0:
        if result['photos_dir_count'] > 0:
            result['issues'].append('⚠️ Photos existent mais ne sont pas détectées par get_all_apartment_photos()')
        elif result['photos_v2_count'] > 0:
            result['issues'].append('⚠️ Photos dans photos_v2 mais ne sont pas détectées')
        elif result['json_photos_count'] > 0:
            result['issues'].append('⚠️ Photos dans JSON mais pas téléchargées localement')
        else:
            result['issues'].append('❌ AUCUNE photo trouvée nulle part')
    
    return result

def main():
    """Fonction principale"""
    print("🔍 DIAGNOSTIC COMPLET DES PHOTOS D'APPARTEMENTS")
    print("=" * 70)
    
    # Charger les appartements
    try:
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            apartments = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier all_apartments_scores.json non trouvé")
        return
    
    print(f"\n📊 Total appartements: {len(apartments)}\n")
    
    # Analyser chaque appartement
    results = []
    for apt in apartments:
        result = check_apartment_photos(apt)
        results.append(result)
    
    # Résumé
    apartments_with_photos = [r for r in results if r['detected_photos_count'] > 0]
    apartments_without_photos = [r for r in results if r['detected_photos_count'] == 0]
    
    print(f"✅ Appartements AVEC photos détectées: {len(apartments_with_photos)}/{len(results)}")
    print(f"❌ Appartements SANS photos détectées: {len(apartments_without_photos)}/{len(results)}\n")
    
    # Afficher les détails des appartements sans photos
    if apartments_without_photos:
        print("=" * 70)
        print("🔴 APPARTEMENTS SANS PHOTOS DÉTECTÉES:")
        print("=" * 70)
        for result in apartments_without_photos:
            print(f"\n🏠 Appartement {result['id']}")
            print(f"   URL: {result['url'][:60]}...")
            print(f"   Photos JSON: {result['json_photos_count']}")
            print(f"   Photos dans photos_v2/: {result['photos_v2_count']}")
            print(f"   Photos dans photos/: {result['photos_dir_count']}")
            print(f"   Photos détectées: {result['detected_photos_count']}")
            if result['issues']:
                print(f"   ⚠️  Problèmes:")
                for issue in result['issues']:
                    print(f"      - {issue}")
    
    # Vérifier les appartements avec problèmes potentiels
    apartments_with_issues = [r for r in results if r['issues'] and r['detected_photos_count'] > 0]
    if apartments_with_issues:
        print("\n" + "=" * 70)
        print("⚠️  APPARTEMENTS AVEC PROBLÈMES POTENTIELS:")
        print("=" * 70)
        for result in apartments_with_issues:
            print(f"\n🏠 Appartement {result['id']}")
            print(f"   Photos détectées: {result['detected_photos_count']}")
            for issue in result['issues']:
                print(f"   ⚠️  {issue}")
    
    # Statistiques détaillées
    print("\n" + "=" * 70)
    print("📈 STATISTIQUES DÉTAILLÉES:")
    print("=" * 70)
    
    total_json_photos = sum(r['json_photos_count'] for r in results)
    total_photos_v2 = sum(r['photos_v2_count'] for r in results)
    total_photos_dir = sum(r['photos_dir_count'] for r in results)
    total_detected = sum(r['detected_photos_count'] for r in results)
    
    print(f"📋 Photos dans JSON: {total_json_photos}")
    print(f"📁 Photos dans photos_v2/: {total_photos_v2}")
    print(f"📁 Photos dans photos/: {total_photos_dir}")
    print(f"✅ Photos détectées par get_all_apartment_photos(): {total_detected}")
    
    # Vérifier les chemins des photos détectées
    print("\n" + "=" * 70)
    print("🔗 EXEMPLES DE CHEMINS DE PHOTOS DÉTECTÉES:")
    print("=" * 70)
    for result in apartments_with_photos[:5]:
        if result['detected_photo_paths']:
            print(f"\n🏠 {result['id']}:")
            for path in result['detected_photo_paths']:
                # Vérifier si le fichier existe réellement
                if path.startswith('../'):
                    file_path = path.replace('../', '')
                    exists = os.path.exists(file_path)
                    status = "✅" if exists else "❌"
                    exists_text = "(existe)" if exists else "(N'EXISTE PAS!)"
                    print(f"   {status} {path} {exists_text}")

if __name__ == "__main__":
    main()

