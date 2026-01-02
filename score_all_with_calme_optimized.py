#!/usr/bin/env python3
"""
Script optimisé pour scorer tous les appartements avec le nouveau critère "calme"
OPTIMISATIONS:
- Ne re-score que les appartements qui n'ont pas encore le critère calme
- Utilise le cache existant (30 jours)
- Respecte les rate limits Nominatim (1 req/sec)
- Batch processing avec sauvegarde progressive
- Évite les requêtes API inutiles
"""

import json
import os
import time
from datetime import datetime
from scoring import score_apartment, load_scoring_config


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


def has_calme_score(apartment):
    """Vérifie si l'appartement a déjà le critère calme calculé"""
    scores_detaille = apartment.get('scores_detaille', {})
    calme_score = scores_detaille.get('calme', {})
    
    # Vérifier si le score calme existe et a une structure valide
    if calme_score and isinstance(calme_score, dict):
        # Vérifier qu'il a au moins un score et un tier
        if 'score' in calme_score and 'tier' in calme_score:
            # Vérifier que les détails sont présents (nouvelle structure)
            details = calme_score.get('details', {})
            if details and ('type_rue' in details or 'bars_restos' in details or 'commerces_agites' in details):
                return True
    
    return False


def save_scores(scored_apartments):
    """Sauvegarde tous les scores"""
    os.makedirs('data/scores', exist_ok=True)
    scores_file = 'data/scores/all_apartments_scores.json'
    with open(scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, ensure_ascii=False, indent=2)
    print(f"💾 Scores sauvegardés dans {scores_file}")


def score_all_with_calme_optimized():
    """Score tous les appartements avec le nouveau critère calme (optimisé)"""
    print("🚀 SCORING OPTIMISÉ AVEC CRITÈRE CALME")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    
    # Séparer les appartements selon leur statut
    apartments_with_calme = []
    apartments_without_calme = []
    apartments_without_coords = []
    
    for apt in apartments:
        coordinates = apt.get('coordinates', {})
        if not coordinates.get('latitude') or not coordinates.get('longitude'):
            apartments_without_coords.append(apt)
        elif has_calme_score(apt):
            apartments_with_calme.append(apt)
        else:
            apartments_without_calme.append(apt)
    
    print("📊 ANALYSE DES APPARTEMENTS")
    print(f"   ✅ Déjà avec critère calme: {len(apartments_with_calme)}")
    print(f"   🔄 À scorer (avec coordonnées): {len(apartments_without_calme)}")
    print(f"   ⚠️  Sans coordonnées: {len(apartments_without_coords)}")
    print()
    
    if not apartments_without_calme:
        print("✅ Tous les appartements avec coordonnées ont déjà le critère calme !")
        print("💡 Aucune requête API nécessaire.")
        return
    
    # Estimer le coût/temps
    print("💰 ESTIMATION COÛTS/TEMPS")
    print(f"   📡 Requêtes API nécessaires: ~{len(apartments_without_calme) * 3}")
    print(f"      - Overpass API: Gratuit (rate limit: ~10 req/sec)")
    print(f"      - Nominatim API: Gratuit (rate limit: 1 req/sec)")
    print(f"   ⏱️  Temps estimé: ~{len(apartments_without_calme) * 2.5 / 60:.1f} minutes")
    print(f"      (avec cache et rate limits)")
    print()
    
    # Scorer par batch avec sauvegarde progressive
    batch_size = 20  # Batch plus petit pour respecter rate limits
    total_batches = (len(apartments_without_calme) + batch_size - 1) // batch_size
    scored_count = 0
    error_count = 0
    cached_count = 0
    start_time = time.time()
    
    print(f"🔄 Traitement par batch de {batch_size} appartements")
    print(f"📦 Total: {total_batches} batches")
    print("💡 Le cache sera utilisé automatiquement pour éviter les requêtes répétées")
    print()
    
    # Commencer avec les appartements qui ont déjà le critère calme
    scored_apartments = apartments_with_calme.copy()
    
    for batch_num in range(total_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(apartments_without_calme))
        batch = apartments_without_calme[batch_start:batch_end]
        
        print(f"📦 Batch {batch_num + 1}/{total_batches} ({len(batch)} appartements)")
        print("-" * 80)
        
        for i, apartment in enumerate(batch, 1):
            apt_id = apartment.get('id', 'N/A')
            global_index = batch_start + i
            
            try:
                # Scorer l'appartement (inclut maintenant le critère calme)
                # Le cache sera utilisé automatiquement dans fetch_calme_data
                score_result = score_apartment(apartment, config)
                
                if score_result:
                    # Fusionner avec données originales (préserver scores_detaille)
                    apartment_copy = apartment.copy()
                    apartment_copy.update(score_result)
                    # S'assurer que scores_detaille est bien préservé
                    if 'scores_detaille' in score_result:
                        apartment_copy['scores_detaille'] = score_result['scores_detaille']
                    scored_apartments.append(apartment_copy)
                    scored_count += 1
                    
                    score_total = score_result.get('score_total', 0)
                    tier = score_result.get('tier', 'N/A')
                    
                    # Vérifier si le critère calme a été calculé
                    calme_score = score_result.get('scores_detaille', {}).get('calme', {})
                    calme_pts = calme_score.get('score', 'N/A')
                    calme_tier = calme_score.get('tier', 'N/A')
                    
                    # Vérifier si c'était depuis le cache
                    calme_details = calme_score.get('details', {})
                    if calme_details:
                        print(f"  [{global_index}/{len(apartments_without_calme)}] ✅ {apt_id}: {score_total}/100 ({tier}) | Calme: {calme_pts}pts ({calme_tier})")
                    else:
                        cached_count += 1
                        print(f"  [{global_index}/{len(apartments_without_calme)}] ✅ {apt_id}: {score_total}/100 ({tier}) | Calme: {calme_pts}pts ({calme_tier}) [cache]")
                else:
                    # Même en cas d'erreur, garder l'appartement sans score
                    scored_apartments.append(apartment)
                    error_count += 1
                    print(f"  [{global_index}/{len(apartments_without_calme)}] ⚠️  {apt_id}: Échec scoring (conservé sans score)")
            
            except Exception as e:
                # En cas d'erreur, garder l'appartement sans score
                scored_apartments.append(apartment)
                error_count += 1
                error_msg = str(e)[:50]
                print(f"  [{global_index}/{len(apartments_without_calme)}] ❌ {apt_id}: Erreur - {error_msg}")
            
            # Petit délai pour respecter rate limits (surtout Nominatim)
            if i < len(batch):  # Pas de délai après le dernier
                time.sleep(0.2)  # 200ms entre appartements
        
        # Ajouter les appartements sans coordonnées (sans re-scoring)
        if batch_num == 0:
            print(f"\n📋 Ajout de {len(apartments_without_coords)} appartements sans coordonnées (sans critère calme)...")
            scored_apartments.extend(apartments_without_coords)
        
        # Sauvegarder après chaque batch
        save_scores(scored_apartments)
        
        elapsed = time.time() - start_time
        avg_time = elapsed / (scored_count + error_count) if (scored_count + error_count) > 0 else 0
        remaining = len(apartments_without_calme) - (scored_count + error_count)
        estimated_remaining = remaining * avg_time if avg_time > 0 else 0
        
        print()
        print(f"  💾 Batch sauvegardé | Scorés: {scored_count} | Erreurs: {error_count}")
        print(f"  ⏱️  Temps écoulé: {elapsed:.1f}s | Temps restant estimé: {estimated_remaining:.1f}s")
        
        # Pause entre batches pour respecter rate limits
        if batch_num < total_batches - 1:  # Pas de pause après le dernier batch
            print(f"  ⏸️  Pause de 2s pour respecter rate limits...")
            time.sleep(2)
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
        if calme_score and 'tier' in calme_score:
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
    print(f"💾 Requêtes évitées grâce au cache: {cached_count}")
    print(f"⚠️  Appartements avec erreurs: {error_count}")
    print(f"📦 Total traité: {scored_count + error_count}")
    print(f"⏱️  Temps total: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    if scored_count > 0:
        print(f"⚡ Vitesse moyenne: {total_time/scored_count:.2f}s par appartement")
    print()
    print("📊 STATISTIQUES CRITÈRE CALME")
    print(f"   🟢 Tier1 (très calme): {calme_stats['tier1']}")
    print(f"   🟡 Tier2 (moyen): {calme_stats['tier2']}")
    print(f"   🔴 Tier3 (animé): {calme_stats['tier3']}")
    print(f"   ⚪ Sans critère calme: {calme_stats['no_calme']}")
    print()
    print("💰 COÛT FINAL")
    print(f"   💵 Coût API: 0€ (Overpass et Nominatim sont gratuits)")
    print(f"   📡 Requêtes API réelles: ~{scored_count - cached_count} (le reste depuis cache)")
    print()
    print(f"💾 Fichier final: data/scores/all_apartments_scores.json")
    print(f"📊 Total d'appartements dans le fichier: {len(scored_apartments)}")
    print()
    print("🎉 Scoring terminé avec succès !")
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    score_all_with_calme_optimized()

