#!/usr/bin/env python3
"""
Version rapide : Affiche juste les résultats du critère calme pour les 12 appartements
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scoring import score_apartment, load_scoring_config
from alert_scoring import filter_apartments_by_alert
from backend.api.apartments import load_apartments_data


def load_alert_by_name(alert_name):
    """Charge une alerte par son nom"""
    alerts_dir = "data/alerts"
    for filename in os.listdir(alerts_dir):
        if filename.endswith('.json'):
            alert_path = os.path.join(alerts_dir, filename)
            with open(alert_path, 'r', encoding='utf-8') as f:
                alert = json.load(f)
                if alert.get('name') == alert_name:
                    return alert
    return None


def test_alert_calme_quick():
    """Version rapide - juste le critère calme"""
    print("🧪 RÉSULTATS CRITÈRE CALME - ALERTE 'Sou & Delphine Apparte'")
    print("=" * 80)
    
    config = load_scoring_config()
    alert = load_alert_by_name("Sou & Delphine Apparte")
    
    if not alert:
        print("❌ Alerte non trouvée")
        return
    
    all_apartments = load_apartments_data()
    filtered_apartments = filter_apartments_by_alert(all_apartments, alert)
    
    print(f"📋 {len(filtered_apartments)} appartements trouvés\n")
    print("🏠 RÉSULTATS PAR APPARTEMENT")
    print("=" * 80)
    
    results = []
    
    for i, apartment in enumerate(filtered_apartments, 1):
        apt_id = apartment.get('id', 'N/A')
        localisation = apartment.get('localisation', 'N/A')
        prix = apartment.get('prix', 'N/A')
        surface = apartment.get('surface', 'N/A')
        
        try:
            # Scorer juste pour obtenir le critère calme
            score_result = score_apartment(apartment, config)
            
            if score_result:
                calme_score = score_result.get('scores_detaille', {}).get('calme', {})
                score_total = score_result.get('score_total', 0)
                tier = score_result.get('tier', 'N/A')
                
                calme_pts = calme_score.get('score', 'N/A') if calme_score else 'N/A'
                calme_tier = calme_score.get('tier', 'N/A') if calme_score else 'N/A'
                calme_justification = calme_score.get('justification', 'N/A')[:100] if calme_score else 'N/A'
                
                calme_details = calme_score.get('details', {}) if calme_score else {}
                type_rue = calme_details.get('type_rue', {}).get('details', 'N/A') if calme_details else 'N/A'
                bars_restos = calme_details.get('bars_restos', {}).get('count', 'N/A') if calme_details else 'N/A'
                commerces = calme_details.get('commerces_agites', {}).get('count', 'N/A') if calme_details else 'N/A'
                
                results.append({
                    'id': apt_id,
                    'localisation': localisation,
                    'prix': prix,
                    'surface': surface,
                    'score_total': score_total,
                    'tier': tier,
                    'calme_pts': calme_pts,
                    'calme_tier': calme_tier,
                    'calme_justification': calme_justification,
                    'type_rue': type_rue,
                    'bars_restos': bars_restos,
                    'commerces': commerces
                })
                
                print(f"[{i}/{len(filtered_apartments)}] {apt_id}")
                print(f"   📍 {localisation}")
                print(f"   💰 {prix} | 📐 {surface}")
                print(f"   🎯 Score total: {score_total}/100 ({tier})")
                print(f"   🔇 Calme: {calme_pts}pts ({calme_tier})")
                print(f"      - Type rue: {type_rue}")
                print(f"      - Bars/restos (100m): {bars_restos}")
                print(f"      - Commerces agités (100m): {commerces}")
                print(f"      - {calme_justification}")
                print()
        
        except Exception as e:
            print(f"[{i}/{len(filtered_apartments)}] ❌ {apt_id}: Erreur - {str(e)[:50]}")
            print()
    
    # Statistiques
    print("=" * 80)
    print("📊 STATISTIQUES CALME")
    print("=" * 80)
    
    calme_stats = {'tier1': 0, 'tier2': 0, 'tier3': 0, 'no_calme': 0}
    for r in results:
        if r['calme_tier'] == 'tier1':
            calme_stats['tier1'] += 1
        elif r['calme_tier'] == 'tier2':
            calme_stats['tier2'] += 1
        elif r['calme_tier'] == 'tier3':
            calme_stats['tier3'] += 1
        else:
            calme_stats['no_calme'] += 1
    
    print(f"🟢 Tier1 (très calme): {calme_stats['tier1']}")
    print(f"🟡 Tier2 (moyen): {calme_stats['tier2']}")
    print(f"🔴 Tier3 (animé): {calme_stats['tier3']}")
    print(f"⚪ Sans calme: {calme_stats['no_calme']}")
    print()
    
    # Top 5 par calme
    print("🏆 TOP 5 PAR CALME")
    print("=" * 80)
    
    def calme_sort_key(r):
        tier_order = {'tier1': 0, 'tier2': 1, 'tier3': 2}.get(r['calme_tier'], 3)
        pts = r['calme_pts'] if isinstance(r['calme_pts'], (int, float)) else 0
        return (tier_order, -pts)
    
    sorted_results = sorted(results, key=calme_sort_key)
    
    for i, r in enumerate(sorted_results[:5], 1):
        print(f"{i}. {r['id']}")
        print(f"   📍 {r['localisation']}")
        print(f"   💰 {r['prix']} | 📐 {r['surface']}")
        print(f"   🎯 Score: {r['score_total']}/100 | 🔇 Calme: {r['calme_pts']}pts ({r['calme_tier']})")
        print(f"   {r['calme_justification']}")
        print()


if __name__ == "__main__":
    test_alert_calme_quick()


