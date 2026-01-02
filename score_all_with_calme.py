#!/usr/bin/env python3
"""
Script pour scorer tous les appartements avec le nouveau critère "calme"
Met à jour les scores existants en ajoutant le critère calme
"""

import json
import os
import time
from datetime import datetime
from scoring import score_apartment, load_scoring_config
from openai_cost_monitor import get_cost_monitor, CostLimitExceeded


def load_apartments():
    """Charge tous les appartements depuis scraped_apartments.json ou all_apartments_scores.json"""
    # Priorité 1: all_apartments_scores.json (contient déjà les scores)
    scores_file = 'data/scores/all_apartments_scores.json'
    if os.path.exists(scores_file):
        print(f"📂 Chargement depuis {scores_file}...")
        with open(scores_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        print(f"✅ {len(apartments)} appartements chargés depuis scores existants")
        return apartments
    
    # Priorité 2: scraped_apartments.json
    scraped_file = 'data/scraped_apartments.json'
    if os.path.exists(scraped_file):
        print(f"📂 Chargement depuis {scraped_file}...")
        with open(scraped_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        print(f"✅ {len(apartments)} appartements chargés depuis données scrapées")
        return apartments
    
    # Priorité 3: data/appartements/ (fichiers individuels)
    apartments_dir = 'data/appartements'
    if os.path.exists(apartments_dir):
        apartment_files = [f for f in os.listdir(apartments_dir) if f.endswith('.json')]
        apartments = []
        for apt_file in apartment_files:
            apt_path = os.path.join(apartments_dir, apt_file)
            try:
                with open(apt_path, 'r', encoding='utf-8') as f:
                    apartments.append(json.load(f))
            except Exception as e:
                print(f"⚠️ Erreur chargement {apt_file}: {e}")
        if apartments:
            print(f"✅ {len(apartments)} appartements chargés depuis data/appartements/")
            return apartments
    
    print("❌ Aucun fichier d'appartements trouvé")
    return []


def save_scores(scored_apartments):
    """Sauvegarde tous les scores"""
    os.makedirs('data/scores', exist_ok=True)
    scores_file = 'data/scores/all_apartments_scores.json'
    with open(scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, ensure_ascii=False, indent=2)
    print(f"💾 Scores sauvegardés dans {scores_file}")


def score_all_with_calme():
    """Score tous les appartements avec le nouveau critère calme"""
    print("🚀 SCORING DE TOUS LES APPARTEMENTS AVEC CRITÈRE CALME")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialiser le monitor de coûts
    monitor = get_cost_monitor()
    monitor.reset()  # Nouvelle session
    monitor.print_status()
    print()
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Vérifier que le critère calme est dans la config
    if 'calme' not in config.get('axes', {}):
        print("⚠️ Le critère 'calme' n'est pas dans scoring_config.json")
        print("   Le scoring continuera mais sans le critère calme")
    
    # Charger tous les appartements
    print("📂 Chargement des appartements...")
    apartments = load_apartments()
    
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"✅ {len(apartments)} appartements chargés")
    print()
    
    # Filtrer les appartements qui ont des coordonnées (nécessaires pour calme)
    apartments_with_coords = []
    apartments_without_coords = []
    
    for apt in apartments:
        coordinates = apt.get('coordinates', {})
        if coordinates.get('latitude') and coordinates.get('longitude'):
            apartments_with_coords.append(apt)
        else:
            apartments_without_coords.append(apt)
    
    print(f"📍 Appartements avec coordonnées: {len(apartments_with_coords)}")
    print(f"⚠️  Appartements sans coordonnées: {len(apartments_without_coords)}")
    if apartments_without_coords:
        print(f"   (Le critère calme ne pourra pas être calculé pour ces appartements)")
    print()
    
    # Scorer par batch avec sauvegarde progressive
    batch_size = 50
    total_batches = (len(apartments_with_coords) + batch_size - 1) // batch_size
    scored_count = 0
    error_count = 0
    start_time = time.time()
    
    print(f"🔄 Traitement par batch de {batch_size} appartements")
    print(f"📦 Total: {total_batches} batches")
    print()
    
    scored_apartments = []
    
    for batch_num in range(total_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(apartments_with_coords))
        batch = apartments_with_coords[batch_start:batch_end]
        
        print(f"📦 Batch {batch_num + 1}/{total_batches} ({len(batch)} appartements)")
        print("-" * 80)
        
        for i, apartment in enumerate(batch, 1):
            apt_id = apartment.get('id', 'N/A')
            global_index = batch_start + i
            
            try:
                # Vérifier la limite de coût avant de scorer
                try:
                    monitor.print_status()
                except:
                    pass
                
                # Scorer l'appartement (inclut maintenant le critère calme)
                score_result = score_apartment(apartment, config)
                
                if score_result:
                    # Fusionner avec données originales
                    score_result.update(apartment)
                    scored_apartments.append(score_result)
                    scored_count += 1
                    
                    score_total = score_result.get('score_total', 0)
                    tier = score_result.get('tier', 'N/A')
                    
                    # Vérifier si le critère calme a été calculé
                    calme_score = score_result.get('scores_detaille', {}).get('calme', {})
                    calme_pts = calme_score.get('score', 'N/A')
                    calme_tier = calme_score.get('tier', 'N/A')
                    
                    print(f"  [{global_index}/{len(apartments_with_coords)}] ✅ {apt_id}: {score_total}/100 ({tier}) | Calme: {calme_pts}pts ({calme_tier})")
                else:
                    # Même en cas d'erreur, garder l'appartement sans score
                    scored_apartments.append(apartment)
                    error_count += 1
                    print(f"  [{global_index}/{len(apartments_with_coords)}] ⚠️  {apt_id}: Échec scoring (conservé sans score)")
            
            except CostLimitExceeded as e:
                # Limite de coût atteinte - arrêter le traitement
                print(f"\n🚨 LIMITE DE COÛT ATTEINTE - ARRÊT DU TRAITEMENT")
                print(f"   Appartements traités: {scored_count}")
                print(f"   Appartements restants: {len(apartments_with_coords) - (scored_count + error_count)}")
                monitor.print_status()
                break
            except Exception as e:
                # En cas d'erreur, garder l'appartement sans score
                scored_apartments.append(apartment)
                error_count += 1
                error_msg = str(e)[:50]
                print(f"  [{global_index}/{len(apartments_with_coords)}] ❌ {apt_id}: Erreur - {error_msg}")
        
        # Ajouter les appartements sans coordonnées (sans re-scoring)
        if batch_num == 0:
            print(f"\n📋 Ajout de {len(apartments_without_coords)} appartements sans coordonnées (sans critère calme)...")
            scored_apartments.extend(apartments_without_coords)
        
        # Sauvegarder après chaque batch
        save_scores(scored_apartments)
        
        elapsed = time.time() - start_time
        avg_time = elapsed / (scored_count + error_count) if (scored_count + error_count) > 0 else 0
        remaining = len(apartments_with_coords) - (scored_count + error_count)
        estimated_remaining = remaining * avg_time if avg_time > 0 else 0
        
        print()
        print(f"  💾 Batch sauvegardé | Scorés: {scored_count} | Erreurs: {error_count}")
        print(f"  ⏱️  Temps écoulé: {elapsed:.1f}s | Temps restant estimé: {estimated_remaining:.1f}s")
        print()
    
    # Statistiques sur le critère calme
    calme_stats = {
        'tier1': 0,
        'tier2': 0,
        'tier3': 0,
        'no_calme': 0
    }
    
    for apt in scored_apartments:
        calme_score = apt.get('scores_detaille', {}).get('calme', {})
        if calme_score:
            tier = calme_score.get('tier', '')
            if tier == 'tier1':
                calme_stats['tier1'] += 1
            elif tier == 'tier2':
                calme_stats['tier2'] += 1
            elif tier == 'tier3':
                calme_stats['tier3'] += 1
        else:
            calme_stats['no_calme'] += 1
    
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
    
    # Afficher le résumé des coûts
    monitor.print_status()
    monitor.reset()  # Sauvegarder l'historique
    print()
    print("📊 STATISTIQUES CRITÈRE CALME")
    print(f"   🟢 Tier1 (très calme): {calme_stats['tier1']}")
    print(f"   🟡 Tier2 (moyen): {calme_stats['tier2']}")
    print(f"   🔴 Tier3 (animé): {calme_stats['tier3']}")
    print(f"   ⚪ Sans critère calme: {calme_stats['no_calme']}")
    print()
    print(f"💾 Fichier final: data/scores/all_apartments_scores.json")
    print(f"📊 Total d'appartements dans le fichier: {len(scored_apartments)}")
    print()
    print("🎉 Scoring terminé avec succès !")
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    score_all_with_calme()

