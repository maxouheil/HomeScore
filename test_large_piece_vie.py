#!/usr/bin/env python3
"""
Test du critère "large pièce de vie"
Vérifie que l'analyse de la taille du salon fonctionne correctement
"""

import json
import os
from scoring import score_large_piece_vie, load_scoring_config
from data_loader import load_apartments

def test_large_piece_vie():
    """Test le scoring de large pièce de vie"""
    print("🧪 TEST CRITÈRE 'LARGE PIÈCE DE VIE'")
    print("=" * 60)
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger la config")
        return
    
    # Charger un appartement de test
    apartments = load_apartments(prefer_api=True)
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    # Prendre le premier appartement avec des photos
    test_apartment = None
    for apt in apartments:
        photos = apt.get('photos', [])
        if photos and len(photos) > 0:
            test_apartment = apt
            break
    
    if not test_apartment:
        print("❌ Aucun appartement avec photos trouvé")
        return
    
    print(f"\n🏠 Appartement de test:")
    print(f"   ID: {test_apartment.get('id')}")
    print(f"   Surface: {test_apartment.get('surface')}")
    print(f"   Photos: {len(test_apartment.get('photos', []))}")
    
    # Tester le scoring
    print(f"\n📊 Analyse de la taille du salon...")
    result = score_large_piece_vie(test_apartment, config)
    
    print(f"\n✅ RÉSULTAT:")
    print(f"   Score: {result.get('score')}/10")
    print(f"   Tier: {result.get('tier')}")
    print(f"   Justification: {result.get('justification')}")
    
    details = result.get('details', {})
    if details:
        print(f"\n📋 DÉTAILS:")
        if 'salon_size_estimate' in details:
            print(f"   Taille salon estimée: {details['salon_size_estimate']}m²")
        if 'surface_totale' in details:
            print(f"   Surface totale: {details['surface_totale']}m²")
        if 'pourcentage_salon' in details:
            print(f"   Pourcentage salon: {details['pourcentage_salon']}%")
        if 'salon_category' in details:
            print(f"   Catégorie salon: {details['salon_category']}")
        if 'confidence' in details:
            print(f"   Confiance: {details['confidence']:.2f}")
    
    print(f"\n✅ Test terminé!")

if __name__ == "__main__":
    test_large_piece_vie()



