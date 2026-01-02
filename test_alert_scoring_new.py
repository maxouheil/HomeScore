#!/usr/bin/env python3
"""
Test du nouveau système de scoring sur 5
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alert_scoring import score_apartment_for_alert, load_scoring_config
from backend.api.apartments import load_apartments_data

def test_scoring():
    """Test le scoring sur un appartement réel"""
    print("🧪 Test du nouveau système de scoring sur 5")
    print("=" * 60)
    
    # Charger un appartement
    apartments = load_apartments_data()
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    # Prendre le premier appartement
    apartment = apartments[0]
    print(f"📋 Appartement test: {apartment.get('id')} - {apartment.get('localisation', 'N/A')}")
    
    # Créer une alerte de test avec 5 critères
    test_alert = {
        'criteria': {
            'all': ['quartier', 'prix', 'luminosite', 'cuisine_ouverte', 'haussmanien']
        }
    }
    
    # Calculer le score
    config = load_scoring_config()
    result = score_apartment_for_alert(apartment, test_alert, config)
    
    print(f"\n📊 Résultats du scoring:")
    print(f"   Score total: {result['score']}/5")
    print(f"   Tier: {result['tier']}")
    print(f"   Max score: {result['max_score']}")
    
    print(f"\n📋 Scores par critère:")
    for criterion_name, criterion_result in result['criteria_scores'].items():
        score = criterion_result.get('score', 0)
        tier = criterion_result.get('tier', 'tier3')
        print(f"   {criterion_name}: {score}pt (tier: {tier})")
    
    # Vérifier que le score est bien sur 5
    if result['score'] > 5:
        print(f"\n❌ ERREUR: Score {result['score']} > 5!")
        return False
    else:
        print(f"\n✅ Score correct: {result['score']}/5")
        return True

if __name__ == "__main__":
    success = test_scoring()
    sys.exit(0 if success else 1)


