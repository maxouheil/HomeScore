#!/usr/bin/env python3
"""
Test du calcul des scores d'alerte avec la nouvelle logique
"""

import json
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alert_scoring import score_apartment_for_alert, get_score_from_tier
from backend.api.apartments import load_apartments_data

def test_score_from_tier():
    """Test de la fonction get_score_from_tier"""
    print("🧪 Test de get_score_from_tier:")
    print("=" * 60)
    
    # Test critères principaux (30pts)
    print("\n📊 Critères principaux (30 pts max):")
    print(f"  tier1 (good) = {get_score_from_tier('tier1', 30)} pts (attendu: 30)")
    print(f"  tier2 (moyen) = {get_score_from_tier('tier2', 30)} pts (attendu: 15)")
    print(f"  tier3 (bad) = {get_score_from_tier('tier3', 30)} pts (attendu: 0)")
    
    # Test critères secondaires (20pts)
    print("\n📊 Critères secondaires (20 pts max):")
    print(f"  tier1 (good) = {get_score_from_tier('tier1', 20)} pts (attendu: 20)")
    print(f"  tier2 (moyen) = {get_score_from_tier('tier2', 20)} pts (attendu: 10)")
    print(f"  tier3 (bad) = {get_score_from_tier('tier3', 20)} pts (attendu: 0)")
    
    print("\n✅ Test terminé\n")

def test_real_alert():
    """Test avec une vraie alerte"""
    print("🏠 Test avec une vraie alerte:")
    print("=" * 60)
    
    # Charger les alertes
    alerts_dir = "data/alerts"
    if not os.path.exists(alerts_dir):
        print("❌ Dossier data/alerts non trouvé")
        return
    
    alert_files = [f for f in os.listdir(alerts_dir) if f.endswith('.json')]
    if not alert_files:
        print("❌ Aucune alerte trouvée")
        return
    
    # Charger la première alerte
    alert_file = os.path.join(alerts_dir, alert_files[0])
    with open(alert_file, 'r', encoding='utf-8') as f:
        alert = json.load(f)
    
    print(f"\n📋 Alerte: {alert.get('name', 'Sans nom')}")
    print(f"   ID: {alert.get('id', 'N/A')}")
    
    criteria = alert.get('criteria', {})
    primary = criteria.get('primary', [])
    secondary = criteria.get('secondary', [])
    
    print(f"\n📊 Critères:")
    print(f"   Principaux: {primary}")
    print(f"   Secondaires: {secondary}")
    print(f"\n   Structure attendue:")
    print(f"   - {primary[0] if len(primary) > 0 else 'N/A'}: 30 pts max")
    print(f"   - {primary[1] if len(primary) > 1 else 'N/A'}: 30 pts max")
    print(f"   - {primary[2] if len(primary) > 2 else 'N/A'}: 20 pts max")
    print(f"   - {secondary[0] if len(secondary) > 0 else 'N/A'}: 20 pts max")
    
    # Charger un appartement
    print("\n🏠 Chargement d'un appartement...")
    apartments = load_apartments_data()
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    # Prendre le premier appartement
    apartment = apartments[0]
    print(f"   ID: {apartment.get('id', 'N/A')}")
    print(f"   Prix: {apartment.get('prix', 'N/A')}")
    
    # Scorer l'appartement
    print("\n🎯 Calcul du score...")
    try:
        score_result = score_apartment_for_alert(apartment, alert)
        
        print(f"\n✅ Score total: {score_result['score']}/100")
        print(f"   Tier: {score_result['tier']}")
        
        print(f"\n📊 Scores par critère:")
        criteria_scores = score_result.get('criteria_scores', {})
        
        for i, criterion_name in enumerate(primary[:2]):
            criterion_score = criteria_scores.get(criterion_name, {})
            expected_max = 30
            actual_score = criterion_score.get('score', 0)
            tier = criterion_score.get('tier', 'tier3')
            print(f"   {i+1}. {criterion_name}:")
            print(f"      Score: {actual_score}/{expected_max} (tier: {tier})")
            print(f"      Attendu pour tier1: {expected_max}, tier2: {expected_max*0.5}")
        
        if len(primary) > 2:
            criterion_name = primary[2]
            criterion_score = criteria_scores.get(criterion_name, {})
            expected_max = 20
            actual_score = criterion_score.get('score', 0)
            tier = criterion_score.get('tier', 'tier3')
            print(f"   3. {criterion_name}:")
            print(f"      Score: {actual_score}/{expected_max} (tier: {tier})")
            print(f"      Attendu pour tier1: {expected_max}, tier2: {expected_max*0.5}")
        
        if len(secondary) > 0:
            criterion_name = secondary[0]
            criterion_score = criteria_scores.get(criterion_name, {})
            expected_max = 20
            actual_score = criterion_score.get('score', 0)
            tier = criterion_score.get('tier', 'tier3')
            print(f"   4. {criterion_name}:")
            print(f"      Score: {actual_score}/{expected_max} (tier: {tier})")
            print(f"      Attendu pour tier1: {expected_max}, tier2: {expected_max*0.5}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_score_from_tier()
    test_real_alert()



