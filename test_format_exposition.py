#!/usr/bin/env python3
"""
Test du formatage des indices d'exposition
"""

import json
from criteria.exposition import format_exposition

def test_format():
    """Test le formatage avec les données réelles"""
    
    # Charger un appartement avec méthode voting
    with open('data/appartements/90931157.json', 'r', encoding='utf-8') as f:
        apt = json.load(f)
    
    # Simuler les données de la méthode voting
    apt['exposition'] = {
        'exposition': 'sud',
        'score': 20,
        'tier': 'tier1',
        'confidence': 85,
        'details': {
            'method': 'voting',
            'etage_num': 5,
            'image_brightness': 0.716,
            'final_class': 'Lumineux'
        }
    }
    
    result = format_exposition(apt)
    
    print("📊 RÉSULTAT FORMATAGE:")
    print(f"   Main value: {result.get('main_value')}")
    print(f"   Confidence: {result.get('confidence')}%")
    print(f"   Indices: {result.get('indices')}")
    print()
    
    # Test avec autre appartement
    with open('data/appartements/90129925.json', 'r', encoding='utf-8') as f:
        apt2 = json.load(f)
    
    # Simuler données voting
    apt2['exposition'] = {
        'exposition': 'est',
        'score': 10,
        'tier': 'tier2',
        'confidence': 75,
        'details': {
            'method': 'voting',
            'etage_num': 1,
            'image_brightness': 0.650,
            'final_class': 'Moyen'
        }
    }
    
    result2 = format_exposition(apt2)
    
    print("📊 RÉSULTAT FORMATAGE (appartement 2):")
    print(f"   Main value: {result2.get('main_value')}")
    print(f"   Confidence: {result2.get('confidence')}%")
    print(f"   Indices: {result2.get('indices')}")

if __name__ == "__main__":
    test_format()

