#!/usr/bin/env python3
"""
Test rapide du mega score corrigé
"""

import json
from generate_scorecard_html import load_scored_apartments


def test_mega_score_calculation():
    """Test le calcul du mega score sur quelques appartements"""
    apartments = load_scored_apartments()
    
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"✅ {len(apartments)} appartements chargés\n")
    print("🔍 Test du calcul du mega score:\n")
    
    # Tester les 3 premiers appartements
    for apt in apartments[:3]:
        apt_id = apt.get('id', 'Unknown')
        score_total = apt.get('score_total', None)
        scores_detaille = apt.get('scores_detaille', {})
        
        # Calculer comme dans generate_scorecard_html.py
        mega_score = score_total if score_total is not None else 0
        
        if mega_score == 0:
            # Recalculer depuis scores_detaille
            for key, criterion in scores_detaille.items():
                if isinstance(criterion, dict):
                    mega_score += criterion.get('score', 0)
            
            bonus = apt.get('bonus', 0)
            malus = apt.get('malus', 0)
            mega_score += bonus - malus
        
        print(f"📌 Appartement {apt_id}:")
        print(f"   Score total (stored): {score_total}")
        print(f"   Mega score calculé: {mega_score}")
        print(f"   Critères dans scores_detaille: {list(scores_detaille.keys())}")
        
        # Calculer la somme manuelle pour vérification
        manual_sum = sum(
            c.get('score', 0) for c in scores_detaille.values() 
            if isinstance(c, dict)
        )
        bonus = apt.get('bonus', 0)
        malus = apt.get('malus', 0)
        manual_total = manual_sum + bonus - malus
        
        print(f"   Somme manuelle (scores + bonus - malus): {manual_total}")
        print(f"   Bonus: {bonus}, Malus: {malus}")
        print()


if __name__ == "__main__":
    test_mega_score_calculation()







