#!/usr/bin/env python3
"""
Régénère all_apartments_scores.json depuis les fichiers individuels mis à jour
"""

import json
from pathlib import Path
from generate_scorecard_html import load_scored_apartments


def regenerate_scores_file():
    """Régénère all_apartments_scores.json depuis les fichiers individuels"""
    print("🔄 RÉGÉNÉRATION DE all_apartments_scores.json")
    print("=" * 60)
    
    # Charger depuis les fichiers individuels (qui ont les scores à jour)
    apartments_dir = Path('data/appartements')
    if not apartments_dir.exists():
        print("❌ Dossier data/appartements non trouvé")
        return
    
    apartment_files = list(apartments_dir.glob('*.json'))
    total = len(apartment_files)
    
    print(f"📋 {total} appartements trouvés")
    print()
    
    scored_apartments = []
    
    for i, apartment_file in enumerate(apartment_files, 1):
        apartment_id = apartment_file.stem
        if apartment_id in ['test_001', 'test_no_photo', 'unknown']:
            continue
        
        try:
            with open(apartment_file, 'r', encoding='utf-8') as f:
                apartment = json.load(f)
            
            # Vérifier que l'appartement a des scores
            if 'scores_detaille' in apartment:
                scored_apartments.append(apartment)
                print(f"✅ [{i}/{total}] {apartment_id} - Score: {apartment.get('score_total', 0)}")
            else:
                print(f"⚠️ [{i}/{total}] {apartment_id} - Pas de scores")
        
        except Exception as e:
            print(f"❌ [{i}/{total}] {apartment_id} - Erreur: {e}")
    
    # Sauvegarder dans all_apartments_scores.json
    scores_file = Path('data/scores/all_apartments_scores.json')
    scores_file.parent.mkdir(exist_ok=True)
    
    with open(scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 60)
    print(f"✅ Fichier régénéré: {scores_file}")
    print(f"   {len(scored_apartments)} appartements avec scores")
    
    # Vérifier l'appartement problématique
    for apt in scored_apartments:
        if str(apt.get('id')) == '93083514':
            loc_score = apt.get('scores_detaille', {}).get('localisation', {})
            print()
            print(f"✅ Appartement 93083514 vérifié:")
            print(f"   Score: {loc_score.get('score')} pts")
            print(f"   Tier: {loc_score.get('tier')}")
            print(f"   Justification: {loc_score.get('justification')}")
            break


if __name__ == "__main__":
    regenerate_scores_file()




