#!/usr/bin/env python3
"""
Script pour scorer 20 appartements avec feedback en temps réel
"""

import json
import os
import time
from datetime import datetime
from scoring import score_apartment, load_scoring_config

def load_apartments():
    """Charge tous les appartements depuis scraped_apartments.json"""
    with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_existing_scores():
    """Charge les scores existants"""
    scores_file = 'data/scores/all_apartments_scores.json'
    if os.path.exists(scores_file):
        with open(scores_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_scores(scored_apartments):
    """Sauvegarde tous les scores"""
    scores_file = 'data/scores/all_apartments_scores.json'
    with open(scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, ensure_ascii=False, indent=2)

def score_20_with_feedback():
    """Score 20 appartements avec feedback en temps réel"""
    print("🚀 SCORING DE 20 APPARTEMENTS")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Charger tous les appartements
    apartments = load_apartments()
    print(f"📂 {len(apartments)} appartements chargés")
    
    # Charger les scores existants
    existing_scores = load_existing_scores()
    scored_ids = {apt.get('id') for apt in existing_scores if apt.get('id')}
    print(f"📊 {len(scored_ids)} appartements déjà scorés")
    print()
    
    # Identifier les appartements à scorer (max 20)
    # Soit ceux sans scores, soit les 20 premiers pour re-scorer
    apartments_to_score = []
    
    # D'abord chercher ceux sans scores
    for apt in apartments:
        apt_id = apt.get('id')
        if apt_id and apt_id not in scored_ids:
            apartments_to_score.append(apt)
            if len(apartments_to_score) >= 20:
                break
    
    # Si tous ont des scores, prendre les 20 premiers pour re-scorer
    if not apartments_to_score:
        print("💡 Tous les appartements ont des scores, re-scoring des 20 premiers...")
        apartments_to_score = apartments[:20]
    
    print(f"🎯 {len(apartments_to_score)} appartements à scorer")
    print()
    print("=" * 80)
    print()
    
    # Créer un dict des scores existants pour fusion
    scores_dict = {apt.get('id'): apt for apt in existing_scores}
    
    # Scorer avec feedback en temps réel
    scored_count = 0
    error_count = 0
    start_time = time.time()
    
    for i, apartment in enumerate(apartments_to_score, 1):
        apt_id = apartment.get('id', 'N/A')
        
        # Afficher la progression
        print(f"[{i}/20] 🏠 Appartement {apt_id}")
        print(f"       {apartment.get('titre', 'N/A')[:60]}")
        print(f"       {apartment.get('prix', 'N/A')} - {apartment.get('localisation', 'N/A')[:40]}")
        
        try:
            # Scorer l'appartement
            score_result = score_apartment(apartment, config)
            
            if score_result:
                # Fusionner avec données originales
                score_result.update(apartment)
                scores_dict[apt_id] = score_result
                scored_count += 1
                
                score_total = score_result.get('score_total', 0)
                tier = score_result.get('tier', 'N/A')
                
                # Afficher le résultat
                print(f"       ✅ Score: {score_total}/100 ({tier})")
                
                # Afficher les scores détaillés
                scores_detaille = score_result.get('scores_detaille', {})
                score_summary = []
                for crit, data in scores_detaille.items():
                    if isinstance(data, dict):
                        score_val = data.get('score', 0)
                        if score_val:
                            score_summary.append(f"{crit}:{score_val}")
                
                if score_summary:
                    print(f"       📊 {' | '.join(score_summary[:4])}")
            else:
                # Même en cas d'erreur, garder l'appartement sans score
                scores_dict[apt_id] = apartment
                error_count += 1
                print(f"       ⚠️  Échec du scoring (conservé sans score)")
        
        except Exception as e:
            # En cas d'erreur, garder l'appartement sans score
            scores_dict[apt_id] = apartment
            error_count += 1
            print(f"       ❌ Erreur: {str(e)[:50]}")
        
        # Calculer le temps écoulé et estimé
        elapsed = time.time() - start_time
        avg_time = elapsed / i if i > 0 else 0
        remaining = len(apartments_to_score) - i
        estimated_remaining = remaining * avg_time if avg_time > 0 else 0
        
        # Afficher la progression
        print(f"       ⏱️  {elapsed:.1f}s écoulé | ~{estimated_remaining:.0f}s restant")
        print()
        
        # Sauvegarder après chaque appartement (pour ne pas perdre en cas d'erreur)
        scored_list = list(scores_dict.values())
        save_scores(scored_list)
    
    # Résumé final
    total_time = time.time() - start_time
    print("=" * 80)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"✅ Appartements scorés avec succès: {scored_count}/20")
    print(f"⚠️  Appartements avec erreurs: {error_count}/20")
    print(f"⏱️  Temps total: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    if scored_count > 0:
        print(f"⚡ Vitesse moyenne: {total_time/scored_count:.2f}s par appartement")
    print()
    print(f"💾 Fichier mis à jour: data/scores/all_apartments_scores.json")
    print(f"📊 Total d'appartements dans le fichier: {len(scores_dict)}")
    print()
    print("🎉 Scoring terminé !")
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    score_20_with_feedback()

