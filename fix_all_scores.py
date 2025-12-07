#!/usr/bin/env python3
"""
Script pour recalculer tous les scores avec scoring.py et corriger les incohérences
"""

import json
import os
from scoring import load_scoring_config, score_apartment, round_to_nearest_5

def fix_all_scores():
    """Recalcule tous les scores avec scoring.py"""
    
    print("🔧 Correction de tous les scores d'appartements")
    print("=" * 70)
    print()
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return False
    
    # Charger tous les appartements scorés
    all_scores_file = 'data/scores/all_apartments_scores.json'
    if not os.path.exists(all_scores_file):
        print(f"❌ Fichier {all_scores_file} non trouvé")
        return False
    
    with open(all_scores_file, 'r', encoding='utf-8') as f:
        scored_apartments = json.load(f)
    
    # Charger les données scrapées
    scraped_file = 'data/scraped_apartments.json'
    if not os.path.exists(scraped_file):
        print(f"❌ Fichier {scraped_file} non trouvé")
        return False
    
    with open(scraped_file, 'r', encoding='utf-8') as f:
        scraped_apartments = json.load(f)
    
    # Créer un dictionnaire pour accès rapide
    scraped_dict = {apt['id']: apt for apt in scraped_apartments}
    
    print(f"📊 Traitement de {len(scored_apartments)} appartements\n")
    
    fixed_count = 0
    missing_data_count = 0
    errors = []
    
    scored_criteria = ['localisation', 'prix', 'style', 'ensoleillement', 'cuisine']
    
    for i, apt_scored in enumerate(scored_apartments, 1):
        apt_id = apt_scored.get('id')
        if not apt_id:
            continue
        
        print(f"[{i}/{len(scored_apartments)}] Appartement {apt_id}...", end=' ')
        
        # Charger les données scrapées complètes
        apt_scraped = scraped_dict.get(apt_id)
        if not apt_scraped:
            print("⚠️  Données scrapées non trouvées")
            missing_data_count += 1
            continue
        
        try:
            # Recalculer avec scoring.py
            new_score = score_apartment(apt_scraped, config)
            
            # Mettre à jour les scores détaillés
            apt_scored['scores_detaille'] = new_score['scores_detaille']
            
            # Recalculer le score total (seulement les 5 critères à 20pts chacun, pas de bonus/malus)
            mega_score = sum(
                new_score['scores_detaille'].get(key, {}).get('score', 0)
                for key in scored_criteria
            )
            # Pas de bonus/malus (supprimés - jamais validés)
            # Arrondir au multiple de 5 le plus proche
            apt_scored['score_total'] = round_to_nearest_5(mega_score)
            
            # Déterminer tier global
            if apt_scored['score_total'] >= 80:
                apt_scored['tier'] = 'tier1'
            elif apt_scored['score_total'] >= 60:
                apt_scored['tier'] = 'tier2'
            else:
                apt_scored['tier'] = 'tier3'
            
            # Bonus/malus supprimés (jamais validés)
            apt_scored['bonus'] = 0
            apt_scored['malus'] = 0
            
            # Mettre à jour model_used
            apt_scored['model_used'] = 'rules_based'
            
            # Sauvegarder le fichier individuel
            individual_file = f"data/scores/apartment_{apt_id}_score.json"
            with open(individual_file, 'w', encoding='utf-8') as f:
                json.dump(apt_scored, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Corrigé (score: {apt_scored['score_total']})")
            fixed_count += 1
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            errors.append({'id': apt_id, 'error': str(e)})
    
    # Sauvegarder le fichier global mis à jour
    with open(all_scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 70)
    print("📊 RÉSULTATS")
    print("=" * 70)
    print(f"✅ Appartements corrigés: {fixed_count}")
    print(f"⚠️  Données scrapées manquantes: {missing_data_count}")
    if errors:
        print(f"❌ Erreurs: {len(errors)}")
        for err in errors:
            print(f"   - {err['id']}: {err['error']}")
    
    return True


if __name__ == "__main__":
    fix_all_scores()

