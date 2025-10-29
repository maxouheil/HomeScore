#!/usr/bin/env python3
"""
Analyse des photos d'appartement pour déterminer l'exposition
"""

import json
import os
import requests
from datetime import datetime

def download_apartment_photos(apartment_data):
    """Télécharge les photos d'appartement"""
    photos = apartment_data.get('photos', [])
    if not photos:
        print("❌ Aucune photo trouvée")
        return []
    
    print(f"📸 Téléchargement de {len(photos)} photos d'appartement...")
    
    # Créer le dossier
    os.makedirs("data/photos", exist_ok=True)
    
    downloaded_photos = []
    apartment_id = apartment_data.get('id', 'unknown')
    
    for i, photo in enumerate(photos[:5], 1):  # Limiter à 5 photos
        try:
            if isinstance(photo, dict):
                url = photo.get('url')
                alt = photo.get('alt', 'appartement')
            else:
                url = photo
                alt = 'appartement'
            
            if not url:
                continue
            
            print(f"   📥 Téléchargement photo {i}: {url[:60]}...")
            
            # Télécharger l'image
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Nom du fichier
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"data/photos/apartment_{apartment_id}_photo_{i}_{timestamp}.jpg"
                
                # Sauvegarder
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                downloaded_photos.append({
                    'filename': filename,
                    'url': url,
                    'alt': alt,
                    'size': len(response.content)
                })
                
                print(f"   ✅ Photo {i} sauvegardée: {filename}")
            else:
                print(f"   ❌ Erreur téléchargement photo {i}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur photo {i}: {e}")
            continue
    
    return downloaded_photos

def analyze_photo_exposition(photo_path):
    """Analyse l'exposition d'une photo d'appartement"""
    try:
        print(f"   🧭 Analyse de l'exposition: {photo_path}")
        
        # Pour l'instant, on va faire une analyse basique
        # Dans une vraie implémentation, on utiliserait OpenAI Vision ou une autre IA
        
        # Analyser les éléments visuels basiques
        analysis = {
            'has_windows': False,
            'has_balcony': False,
            'lighting_quality': 'unknown',
            'window_direction': 'unknown',
            'exposition': 'unknown',
            'confidence': 0.0,
            'file_size': os.path.getsize(photo_path) if os.path.exists(photo_path) else 0
        }
        
        # Ici on pourrait ajouter de l'analyse d'image réelle
        # Pour l'instant, on retourne une structure de base
        
        print(f"   📊 Analyse basique: {analysis}")
        return analysis
        
    except Exception as e:
        print(f"   ❌ Erreur analyse photo: {e}")
        return {'error': str(e)}

def main():
    """Fonction principale"""
    print("📸 ANALYSE DES PHOTOS D'APPARTEMENT POUR L'EXPOSITION")
    print("=" * 70)
    
    # Charger les données de l'appartement
    try:
        with open('data/appartements/90931157.json', 'r') as f:
            apartment_data = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier de données non trouvé")
        return
    
    print(f"🏠 Appartement: {apartment_data.get('id', 'N/A')}")
    print(f"   Prix: {apartment_data.get('prix', 'N/A')}€")
    print(f"   Surface: {apartment_data.get('surface', 'N/A')}")
    print()
    
    # Télécharger les photos
    downloaded_photos = download_apartment_photos(apartment_data)
    
    if not downloaded_photos:
        print("❌ Aucune photo téléchargée")
        return
    
    print(f"\n✅ {len(downloaded_photos)} photos téléchargées")
    print()
    
    # Analyser chaque photo
    print("🧭 ANALYSE DE L'EXPOSITION:")
    print("-" * 40)
    
    all_analyses = []
    for i, photo in enumerate(downloaded_photos, 1):
        print(f"\n📸 Photo {i}:")
        print(f"   Fichier: {photo['filename']}")
        print(f"   URL: {photo['url']}")
        print(f"   Alt: {photo['alt']}")
        print(f"   Taille: {photo['size']} bytes")
        
        # Analyser l'exposition
        analysis = analyze_photo_exposition(photo['filename'])
        all_analyses.append(analysis)
    
    # Résumé des analyses
    print(f"\n📊 RÉSUMÉ DES ANALYSES:")
    print("-" * 40)
    
    for i, analysis in enumerate(all_analyses, 1):
        print(f"Photo {i}: {analysis}")
    
    print(f"\n💡 PROCHAINES ÉTAPES:")
    print("1. Configurer OpenAI Vision API pour analyser les photos")
    print("2. Implémenter l'analyse d'orientation des fenêtres")
    print("3. Détecter la direction de la lumière naturelle")
    print("4. Déterminer l'exposition basée sur l'analyse visuelle")
    
    print(f"\n✅ Analyse terminée ! {len(downloaded_photos)} photos prêtes pour l'analyse d'exposition.")

if __name__ == "__main__":
    main()
