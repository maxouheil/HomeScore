#!/usr/bin/env python3
"""
Test de la sélection des meilleures photos d'appartement
"""

import os
import json
from generate_fitscore_style_html import get_apartment_photo

def test_photo_selection():
    """Test la sélection des photos"""
    print("🖼️ TEST DE SÉLECTION DES PHOTOS")
    print("=" * 50)
    
    # Charger les données des appartements
    appartements_dir = "data/appartements"
    if not os.path.exists(appartements_dir):
        print("❌ Dossier data/appartements non trouvé")
        return
    
    # Lister les fichiers JSON
    json_files = [f for f in os.listdir(appartements_dir) if f.endswith('.json')]
    print(f"📋 {len(json_files)} fichiers JSON trouvés")
    
    # Tester les 5 premiers appartements
    for i, json_file in enumerate(json_files[:5]):
        print(f"\n🏠 APARTEMENT {i+1}: {json_file}")
        print("-" * 40)
        
        # Charger les données
        with open(os.path.join(appartements_dir, json_file), 'r', encoding='utf-8') as f:
            apartment = json.load(f)
        
        apartment_id = apartment.get('id', 'unknown')
        photos_dir = f"data/photos/{apartment_id}"
        
        if os.path.exists(photos_dir):
            print(f"📁 Dossier photos: {photos_dir}")
            
            # Lister toutes les photos avec leur taille
            photo_files = []
            for filename in os.listdir(photos_dir):
                if filename.endswith(('.jpg', '.jpeg', '.png')):
                    file_path = os.path.join(photos_dir, filename)
                    file_size = os.path.getsize(file_path)
                    photo_files.append((filename, file_size))
            
            # Trier par taille
            photo_files.sort(key=lambda x: x[1], reverse=True)
            
            print(f"📸 {len(photo_files)} photos trouvées:")
            for j, (filename, size) in enumerate(photo_files):
                size_kb = size / 1024
                marker = "👑" if j == 0 else "  "
                print(f"   {marker} {filename}: {size_kb:.1f} KB")
            
            # Tester la fonction get_apartment_photo
            selected_photo = get_apartment_photo(apartment)
            print(f"🎯 Photo sélectionnée: {selected_photo}")
            
            # Vérifier si c'est la plus grande
            if photo_files and selected_photo:
                expected_photo = f"../data/photos/{apartment_id}/{photo_files[0][0]}"
                if selected_photo == expected_photo:
                    print("✅ Sélection correcte (plus grande photo)")
                else:
                    print("❌ Sélection incorrecte")
        else:
            print(f"❌ Dossier photos non trouvé: {photos_dir}")

if __name__ == "__main__":
    test_photo_selection()
