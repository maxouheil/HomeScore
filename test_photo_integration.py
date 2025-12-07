#!/usr/bin/env python3
"""
Test de l'intégration des photos dans les scorecards
"""

import json
import os
from generate_fitscore_style_html import get_apartment_photo, format_apartment_info

def test_photo_integration():
    """Test l'intégration des photos"""
    print("🧪 TEST D'INTÉGRATION DES PHOTOS")
    print("=" * 50)
    
    # Charger les données des appartements
    appartements_dir = "data/appartements"
    if not os.path.exists(appartements_dir):
        print("❌ Dossier data/appartements non trouvé")
        return
    
    # Lister les fichiers JSON
    json_files = [f for f in os.listdir(appartements_dir) if f.endswith('.json')]
    print(f"📋 {len(json_files)} fichiers JSON trouvés")
    
    # Tester les 3 premiers appartements
    for i, json_file in enumerate(json_files[:3]):
        print(f"\n🏠 APARTEMENT {i+1}: {json_file}")
        print("-" * 30)
        
        # Charger les données
        with open(os.path.join(appartements_dir, json_file), 'r', encoding='utf-8') as f:
            apartment = json.load(f)
        
        # Tester get_apartment_photo
        photo_url = get_apartment_photo(apartment)
        print(f"📸 Photo URL: {photo_url}")
        
        # Vérifier si le fichier existe
        if photo_url and photo_url.startswith('data/photos/'):
            if os.path.exists(photo_url):
                file_size = os.path.getsize(photo_url)
                print(f"✅ Photo trouvée: {file_size} bytes")
            else:
                print(f"❌ Photo non trouvée: {photo_url}")
        elif photo_url:
            print(f"🌐 URL externe: {photo_url}")
        else:
            print("❌ Aucune photo trouvée")
        
        # Tester format_apartment_info
        apartment_info = format_apartment_info(apartment)
        print(f"📝 Titre: {apartment_info['title']}")
        print(f"📝 Sous-titre: {apartment_info['subtitle']}")
        
        # Générer le HTML de la photo
        photo_html = f'<img src="{photo_url}" alt="Photo d\'appartement" class="candidate-photo">' if photo_url else '<div class="candidate-photo" style="background: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #999; font-size: 0.8rem;">📷</div>'
        print(f"🔧 Photo HTML: {photo_html[:100]}...")

if __name__ == "__main__":
    test_photo_integration()
