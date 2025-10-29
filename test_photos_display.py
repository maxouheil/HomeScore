#!/usr/bin/env python3
"""
Test final de l'affichage des photos dans les rapports HTML
"""

import os
import webbrowser
from pathlib import Path

def test_photos_display():
    """Test l'affichage des photos dans les rapports"""
    print("🖼️ TEST D'AFFICHAGE DES PHOTOS")
    print("=" * 50)
    
    # Vérifier les rapports générés
    fitscore_report = "output/scorecard_fitscore_style.html"
    original_report = "output/scorecard_rapport.html"
    
    if not os.path.exists(fitscore_report):
        print(f"❌ Rapport Fitscore non trouvé: {fitscore_report}")
        return
    
    if not os.path.exists(original_report):
        print(f"❌ Rapport original non trouvé: {original_report}")
        return
    
    print(f"✅ Rapport Fitscore: {fitscore_report}")
    print(f"✅ Rapport original: {original_report}")
    
    # Vérifier les photos
    photos_dir = "data/photos"
    if not os.path.exists(photos_dir):
        print(f"❌ Dossier photos non trouvé: {photos_dir}")
        return
    
    # Compter les photos
    photo_count = 0
    apartment_dirs = [d for d in os.listdir(photos_dir) if os.path.isdir(os.path.join(photos_dir, d))]
    
    for apartment_dir in apartment_dirs:
        apartment_path = os.path.join(photos_dir, apartment_dir)
        photos = [f for f in os.listdir(apartment_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
        photo_count += len(photos)
        print(f"🏠 {apartment_dir}: {len(photos)} photos")
    
    print(f"📸 Total photos: {photo_count}")
    
    # Vérifier les chemins dans le HTML
    print("\n🔍 VÉRIFICATION DES CHEMINS HTML")
    print("-" * 30)
    
    with open(fitscore_report, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Chercher les chemins d'images
    import re
    img_paths = re.findall(r'src="(\.\./data/photos/[^"]+)"', content)
    print(f"📋 Chemins d'images trouvés: {len(img_paths)}")
    
    # Vérifier que les fichiers existent
    existing_photos = 0
    for img_path in img_paths[:5]:  # Vérifier les 5 premiers
        full_path = img_path.replace('../', '')
        if os.path.exists(full_path):
            existing_photos += 1
            file_size = os.path.getsize(full_path)
            print(f"✅ {img_path} ({file_size} bytes)")
        else:
            print(f"❌ {img_path} (fichier non trouvé)")
    
    print(f"📊 Photos existantes: {existing_photos}/{len(img_paths[:5])}")
    
    # Ouvrir les rapports dans le navigateur
    print("\n🌐 OUVERTURE DES RAPPORTS")
    print("-" * 30)
    
    try:
        # Chemin absolu pour éviter les problèmes de chemins relatifs
        fitscore_abs = os.path.abspath(fitscore_report)
        original_abs = os.path.abspath(original_report)
        
        print(f"🎨 Ouverture Fitscore: {fitscore_abs}")
        webbrowser.open(f"file://{fitscore_abs}")
        
        print(f"🏠 Ouverture Original: {original_abs}")
        webbrowser.open(f"file://{original_abs}")
        
        print("✅ Rapports ouverts dans le navigateur")
        
    except Exception as e:
        print(f"❌ Erreur ouverture navigateur: {e}")
        print(f"📁 Ouvrez manuellement: {os.path.abspath(fitscore_report)}")
        print(f"📁 Ouvrez manuellement: {os.path.abspath(original_report)}")

if __name__ == "__main__":
    test_photos_display()
