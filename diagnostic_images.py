#!/usr/bin/env python3
"""
Diagnostic des images - Vérifie que les images téléchargées sont bien référencées dans le HTML
"""

import os
import json
import re
from pathlib import Path

def check_photo_files():
    """Vérifie les fichiers photos réels"""
    photos_dir = Path("data/photos")
    if not photos_dir.exists():
        print("❌ Répertoire data/photos n'existe pas")
        return {}
    
    apartments_photos = {}
    for apt_dir in photos_dir.iterdir():
        if apt_dir.is_dir():
            apt_id = apt_dir.name
            photos = []
            for photo_file in sorted(apt_dir.glob("*.jpg")):
                photos.append(photo_file.name)
            if photos:
                apartments_photos[apt_id] = photos
    
    return apartments_photos

def check_html_references():
    """Vérifie les références aux images dans le HTML"""
    # Vérifier d'abord homepage.html (fichier principal), puis scorecard_rapport.html comme fallback
    html_file = Path("output/homepage.html")
    if not html_file.exists():
        html_file = Path("output/scorecard_rapport.html")
        if not html_file.exists():
            print("❌ Fichier HTML non trouvé (homepage.html ou scorecard_rapport.html)")
            return {}
    
    html_content = html_file.read_text(encoding='utf-8')
    
    # Extraire toutes les références aux images
    pattern = r'data/photos/(\d+)/([^"]+\.jpg)'
    matches = re.findall(pattern, html_content)
    
    html_references = {}
    for apt_id, filename in matches:
        if apt_id not in html_references:
            html_references[apt_id] = []
        if filename not in html_references[apt_id]:
            html_references[apt_id].append(filename)
    
    return html_references

def check_apartment_photos_in_data():
    """Vérifie les photos depuis les données JSON"""
    try:
        with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        
        apartments_photos_data = {}
        for apt in apartments:
            apt_id = apt.get('id')
            if apt_id:
                photos = apt.get('photos', [])
                photo_urls = []
                for photo in photos:
                    if isinstance(photo, dict):
                        url = photo.get('url', '')
                    elif isinstance(photo, str):
                        url = photo
                    if url:
                        photo_urls.append(url)
                if photo_urls:
                    apartments_photos_data[str(apt_id)] = photo_urls
        
        return apartments_photos_data
    except FileNotFoundError:
        return {}

def main():
    """Fonction principale de diagnostic"""
    print("🔍 Diagnostic des Images")
    print("=" * 60)
    
    # 1. Vérifier les fichiers photos réels
    print("\n1️⃣  Vérification des fichiers photos réels...")
    real_photos = check_photo_files()
    print(f"   ✅ {len(real_photos)} appartements avec photos téléchargées")
    
    total_photos = sum(len(photos) for photos in real_photos.values())
    print(f"   📸 {total_photos} photos au total")
    
    # 2. Vérifier les références dans le HTML
    print("\n2️⃣  Vérification des références dans le HTML...")
    html_refs = check_html_references()
    print(f"   ✅ {len(html_refs)} appartements référencés dans le HTML")
    
    total_html_refs = sum(len(refs) for refs in html_refs.values())
    print(f"   📸 {total_html_refs} références d'images dans le HTML")
    
    # 3. Comparer fichiers réels vs références HTML
    print("\n3️⃣  Comparaison fichiers réels vs références HTML...")
    mismatches = []
    missing_files = []
    
    for apt_id in set(list(real_photos.keys()) + list(html_refs.keys())):
        real_files = set(real_photos.get(apt_id, []))
        html_files = set(html_refs.get(apt_id, []))
        
        if real_files != html_files:
            if apt_id in real_photos and apt_id in html_refs:
                mismatches.append({
                    'apt_id': apt_id,
                    'real_files': sorted(real_files),
                    'html_files': sorted(html_files),
                    'missing': sorted(html_files - real_files),
                    'extra': sorted(real_files - html_files)
                })
            elif apt_id in html_refs and apt_id not in real_photos:
                missing_files.append({
                    'apt_id': apt_id,
                    'html_files': sorted(html_files)
                })
    
    if mismatches:
        print(f"\n   ⚠️  {len(mismatches)} appartements avec des incohérences:")
        for mismatch in mismatches[:5]:
            print(f"\n   📌 Appartement {mismatch['apt_id']}:")
            print(f"      Fichiers réels: {mismatch['real_files']}")
            print(f"      Références HTML: {mismatch['html_files']}")
            if mismatch['missing']:
                print(f"      ❌ Fichiers manquants: {mismatch['missing']}")
            if mismatch['extra']:
                print(f"      ✅ Fichiers supplémentaires: {mismatch['extra']}")
        
        if len(mismatches) > 5:
            print(f"\n   ... et {len(mismatches) - 5} autres appartements")
    else:
        print("   ✅ Aucune incohérence détectée!")
    
    if missing_files:
        print(f"\n   ⚠️  {len(missing_files)} appartements référencés dans HTML mais sans photos:")
        for missing in missing_files[:3]:
            print(f"      - {missing['apt_id']}: {len(missing['html_files'])} références")
    
    # 4. Vérifier les photos dans les données JSON
    print("\n4️⃣  Vérification des photos dans les données JSON...")
    json_photos = check_apartment_photos_in_data()
    print(f"   ✅ {len(json_photos)} appartements avec URLs de photos dans JSON")
    
    # 5. Résumé et recommandations
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    apartments_with_both = len(set(real_photos.keys()) & set(html_refs.keys()))
    apartments_only_real = len(set(real_photos.keys()) - set(html_refs.keys()))
    apartments_only_html = len(set(html_refs.keys()) - set(real_photos.keys()))
    
    print(f"\n✅ Appartements avec photos ET références HTML: {apartments_with_both}")
    print(f"📸 Appartements avec photos mais SANS références HTML: {apartments_only_real}")
    print(f"🔗 Appartements avec références HTML mais SANS photos: {apartments_only_html}")
    
    if mismatches or missing_files:
        print("\n⚠️  RECOMMANDATION: Régénérer le HTML pour corriger les références")
        print("   Commande: python generate_scorecard_html.py")
    else:
        print("\n✅ Tout semble correct!")

if __name__ == "__main__":
    main()

