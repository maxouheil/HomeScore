#!/usr/bin/env python3
"""
Test du placeholder pour les appartements sans photo
"""

import json
import os
from generate_fitscore_style_html import generate_fitscore_style_html
from generate_scorecard_html import generate_scorecard_html

def test_placeholder():
    """Teste le placeholder avec un appartement sans photo"""
    
    # Créer un appartement de test sans photo
    test_apartment = {
        'id': 'test_no_photo',
        'titre': 'Appartement Test Sans Photo',
        'localisation': 'Paris 19e',
        'surface': '70m²',
        'pieces': '3 pièces',
        'prix': '775 000€',
        'score_total': 75,
        'scores_detaille': {
            'localisation': 15,
            'prix': 18,
            'style': 20,
            'ensoleillement': 8,
            'cuisine': 7,
            'etage': 7
        },
        'photos': []  # Pas de photos
    }
    
    # Sauvegarder l'appartement de test
    os.makedirs('data/appartements', exist_ok=True)
    with open('data/appartements/test_no_photo.json', 'w', encoding='utf-8') as f:
        json.dump(test_apartment, f, ensure_ascii=False, indent=2)
    
    print("🧪 TEST PLACEHOLDER PHOTOS")
    print("=" * 50)
    print(f"📋 Appartement de test créé: {test_apartment['titre']}")
    print(f"📸 Photos: {len(test_apartment['photos'])} (aucune)")
    
    # Charger tous les appartements existants + le test
    apartments = []
    
    # Charger les appartements existants
    if os.path.exists('data/appartements'):
        for filename in os.listdir('data/appartements'):
            if filename.endswith('.json'):
                with open(f'data/appartements/{filename}', 'r', encoding='utf-8') as f:
                    apartment = json.load(f)
                    apartments.append(apartment)
    
    # Ajouter l'appartement de test
    apartments.append(test_apartment)
    
    print(f"📋 Total: {len(apartments)} appartements (dont 1 sans photo)")
    
    # Générer les rapports
    print("\n🏠 Génération des rapports...")
    generate_fitscore_style_html(apartments)
    generate_scorecard_html(apartments)
    
    print("✅ Rapports générés avec placeholder")
    print("🌐 Ouvrez les fichiers HTML pour voir le placeholder gris clair 370x200")

if __name__ == "__main__":
    test_placeholder()
