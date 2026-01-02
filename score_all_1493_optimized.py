#!/usr/bin/env python3
"""
Script optimisé pour scorer les 1493 appartements
Utilise le système de scoring basé sur règles (gratuit, local)
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
    print(f"💾 Scores sauvegardés dans {scores_file}")

def score_all_1493_optimized():
    """Score tous les appartements de manière optimisée"""
    print("🚀 SCORING OPTIMISÉ DES 1493 APPARTEMENTS")
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
    print()
    
    # Charger les scores existants
    print("📂 Chargement des scores existants...")
    existing_scores = load_existing_scores()
    scored_ids = {apt.get('id') for apt in existing_scores if apt.get('id')}
    print(f"✅ {len(scored_ids)} appartements déjà scorés")
    print()
    
    # Identifier les appartements à scorer
    apartments_to_score = []
    for apt in apartments:
        apt_id = apt.get('id')
        if apt_id and apt_id not in scored_ids:
            apartments_to_score.append(apt)
    
    print(f"📊 Appartements à scorer: {len(apartments_to_score)}")
    print(f"⏭️  Appartements déjà scorés: {len(scored_ids)}")
    print()
    
    if not apartments_to_score:
        print("✅ Tous les appartements sont déjà scorés !")
        return
    
    # Créer un dict des scores existants pour fusion
    scores_dict = {apt.get('id'): apt for apt in existing_scores}
    
    # Scorer par batch avec sauvegarde progressive
    batch_size = 50
    total_batches = (len(apartments_to_score) + batch_size - 1) // batch_size
    scored_count = 0
    error_count = 0
    start_time = time.time()
    
    print(f"🔄 Traitement par batch de {batch_size} appartements")
    print(f"📦 Total: {total_batches} batches")
    print()
    
    for batch_num in range(total_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(apartments_to_score))
        batch = apartments_to_score[batch_start:batch_end]
        
        print(f"📦 Batch {batch_num + 1}/{total_batches} ({len(batch)} appartements)")
        print("-" * 80)
        
        for i, apartment in enumerate(batch, 1):
            apt_id = apartment.get('id', 'N/A')
            global_index = batch_start + i
            
            try:
                # Scorer l'appartement (système basé sur règles, gratuit)
                score_result = score_apartment(apartment, config)
                
                if score_result:
                    # Fusionner avec données originales
                    score_result.update(apartment)
                    scores_dict[apt_id] = score_result
                    scored_count += 1
                    
                    score_total = score_result.get('score_total', 0)
                    tier = score_result.get('tier', 'N/A')
                    print(f"  [{global_index}/{len(apartments_to_score)}] ✅ {apt_id}: {score_total}/100 ({tier})")
                else:
                    # Même en cas d'erreur, garder l'appartement sans score
                    scores_dict[apt_id] = apartment
                    error_count += 1
                    print(f"  [{global_index}/{len(apartments_to_score)}] ⚠️  {apt_id}: Échec scoring (conservé sans score)")
            
            except Exception as e:
                # En cas d'erreur, garder l'appartement sans score
                scores_dict[apt_id] = apartment
                error_count += 1
                print(f"  [{global_index}/{len(apartments_to_score)}] ❌ {apt_id}: Erreur - {str(e)[:50]}")
        
        # Sauvegarder après chaque batch
        scored_list = list(scores_dict.values())
        save_scores(scored_list)
        
        elapsed = time.time() - start_time
        avg_time = elapsed / (scored_count + error_count) if (scored_count + error_count) > 0 else 0
        remaining = len(apartments_to_score) - (scored_count + error_count)
        estimated_remaining = remaining * avg_time if avg_time > 0 else 0
        
        print()
        print(f"  💾 Batch sauvegardé | Scorés: {scored_count} | Erreurs: {error_count}")
        print(f"  ⏱️  Temps écoulé: {elapsed:.1f}s | Temps restant estimé: {estimated_remaining:.1f}s")
        print()
    
    # Résumé final
    total_time = time.time() - start_time
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

if __name__ == "__main__":
    score_all_1493_optimized()





