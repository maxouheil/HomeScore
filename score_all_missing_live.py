#!/usr/bin/env python3
"""
Script pour scorer tous les appartements manquants avec feedback live
"""

import json
import os
import time
import sys
from datetime import datetime
from scoring import score_apartment, load_scoring_config

def load_apartments():
    """Charge tous les appartements"""
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

def score_all_missing_live():
    """Score tous les appartements manquants avec feedback live"""
    print("=" * 80)
    print("🚀 SCORING DES APPARTEMENTS MANQUANTS")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Charger tous les appartements
    print("📂 Chargement des appartements...")
    apartments = load_apartments()
    print(f"✅ {len(apartments)} appartements chargés")
    
    # Charger les scores existants
    print("📂 Chargement des scores existants...")
    existing_scores = load_existing_scores()
    scored_ids = {apt.get('id') for apt in existing_scores if apt.get('id') and apt.get('scores_detaille')}
    print(f"✅ {len(scored_ids)} appartements déjà scorés")
    print()
    
    # Identifier les appartements à scorer
    apartments_to_score = []
    for apt in apartments:
        apt_id = apt.get('id')
        if apt_id and apt_id not in scored_ids:
            apartments_to_score.append(apt)
    
    total_to_score = len(apartments_to_score)
    print(f"📊 Appartements à scorer: {total_to_score}")
    print()
    
    if total_to_score == 0:
        print("✅ Tous les appartements sont déjà scorés !")
        return
    
    # Créer un dict des scores existants pour fusion
    scores_dict = {apt.get('id'): apt for apt in existing_scores}
    
    # Scorer avec feedback live
    scored_count = 0
    error_count = 0
    start_time = time.time()
    batch_size = 10  # Sauvegarder tous les 10 appartements
    
    print("🔄 DÉMARRAGE DU SCORING...")
    print("=" * 80)
    print()
    
    for i, apartment in enumerate(apartments_to_score, 1):
        apt_id = apartment.get('id', 'N/A')
        
        # Afficher la progression
        progress = f"[{i}/{total_to_score}]"
        percentage = (i / total_to_score * 100) if total_to_score > 0 else 0
        
        # Calculer le temps estimé
        elapsed = time.time() - start_time
        if i > 1:
            avg_time = elapsed / (i - 1)
            remaining = (total_to_score - i) * avg_time
            eta_min = int(remaining // 60)
            eta_sec = int(remaining % 60)
            eta_str = f"ETA: {eta_min}m{eta_sec}s"
        else:
            eta_str = "ETA: calcul..."
        
        # Afficher la ligne de progression
        sys.stdout.write(f"\r{progress} {percentage:5.1f}% | ✅ {scored_count} | ❌ {error_count} | {eta_str} | {apt_id}")
        sys.stdout.flush()
        
        try:
            # Scorer l'appartement (système basé sur règles, gratuit)
            score_result = score_apartment(apartment, config)
            
            if score_result:
                # Fusionner avec données originales
                score_result.update(apartment)
                scores_dict[apt_id] = score_result
                scored_count += 1
            else:
                # Même en cas d'erreur, garder l'appartement sans score
                scores_dict[apt_id] = apartment
                error_count += 1
        
        except Exception as e:
            # En cas d'erreur, garder l'appartement sans score
            scores_dict[apt_id] = apartment
            error_count += 1
        
        # Sauvegarder tous les batch_size appartements
        if i % batch_size == 0:
            scored_list = list(scores_dict.values())
            save_scores(scored_list)
            # Afficher un retour à la ligne pour le batch
            sys.stdout.write(f"\n💾 Batch sauvegardé ({i}/{total_to_score})\n")
            sys.stdout.flush()
    
    # Sauvegarde finale
    scored_list = list(scores_dict.values())
    save_scores(scored_list)
    
    # Résumé final
    total_time = time.time() - start_time
    print()
    print()
    print("=" * 80)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"✅ Appartements scorés avec succès: {scored_count}")
    print(f"⚠️  Appartements avec erreurs: {error_count}")
    print(f"📦 Total traité: {scored_count + error_count}")
    print(f"⏱️  Temps total: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    if scored_count > 0:
        print(f"⚡ Vitesse moyenne: {total_time/scored_count:.2f}s par appartement")
    print()
    print(f"💾 Fichier final: data/scores/all_apartments_scores.json")
    print(f"📊 Total d'appartements dans le fichier: {len(scores_dict)}")
    print()
    print("🎉 Scoring terminé avec succès !")
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    score_all_missing_live()





