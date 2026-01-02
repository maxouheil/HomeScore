#!/usr/bin/env python3
"""
Script optimisé pour scorer les 43 nouveaux appartements avec Gemini Flash
- Rate limiting automatique (15 RPM pour Gemini Flash)
- Cache intelligent
- Retry automatique
- Progress bar
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List
from scoring import load_scoring_config
from scoring_optimized import score_apartment_optimized as score_apartment


def load_apartment_data(apartment_id: str) -> Dict:
    """Charge les données d'un appartement depuis data/appartements/"""
    filepath = f"data/appartements/{apartment_id}.json"
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement {apartment_id}: {e}")
        return None


def get_new_apartments() -> List[str]:
    """Identifie les nouveaux appartements qui n'ont pas encore de score"""
    apartments_dir = 'data/appartements'
    scores_dir = 'data/scores'
    
    if not os.path.exists(apartments_dir):
        return []
    
    # Trouver tous les appartements scrapés
    apartment_files = [f for f in os.listdir(apartments_dir) 
                      if f.endswith('.json') and not f.startswith('test_')]
    
    new_apartments = []
    for apartment_file in apartment_files:
        apartment_id = apartment_file.replace('.json', '')
        
        # Vérifier si déjà scoré
        score_file = f"{scores_dir}/apartment_{apartment_id}_score.json"
        if not os.path.exists(score_file):
            new_apartments.append(apartment_id)
    
    return new_apartments


def save_individual_score(apartment_scored: Dict, apartment_id: str) -> bool:
    """Sauvegarde le score individuel d'un appartement"""
    os.makedirs('data/scores', exist_ok=True)
    score_file = f"data/scores/apartment_{apartment_id}_score.json"
    
    try:
        with open(score_file, 'w', encoding='utf-8') as f:
            json.dump(apartment_scored, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Erreur sauvegarde score {apartment_id}: {e}")
        return False


def update_all_apartments_scores(new_apartments_scored: List[Dict]) -> int:
    """Met à jour all_apartments_scores.json avec les nouveaux appartements"""
    all_scores_file = 'data/scores/all_apartments_scores.json'
    
    # Charger les scores existants
    existing_apartments = []
    if os.path.exists(all_scores_file):
        try:
            with open(all_scores_file, 'r', encoding='utf-8') as f:
                existing_apartments = json.load(f)
        except Exception as e:
            print(f"⚠️ Erreur chargement all_apartments_scores.json: {e}")
            existing_apartments = []
    
    # Créer un dict par ID pour éviter les doublons
    apartments_dict = {apt.get('id'): apt for apt in existing_apartments}
    
    # Ajouter/mettre à jour les nouveaux appartements
    for apt in new_apartments_scored:
        apt_id = apt.get('id')
        if apt_id:
            apartments_dict[apt_id] = apt
    
    # Convertir en liste et trier par score décroissant
    all_apartments = list(apartments_dict.values())
    all_apartments.sort(key=lambda x: x.get('score_global', x.get('score_total', 0)), reverse=True)
    
    # Sauvegarder
    try:
        with open(all_scores_file, 'w', encoding='utf-8') as f:
            json.dump(all_apartments, f, ensure_ascii=False, indent=2)
        return len(all_apartments)
    except Exception as e:
        print(f"❌ Erreur sauvegarde all_apartments_scores.json: {e}")
        return 0


def rate_limit_delay(rate_limit_rpm: int = 15) -> None:
    """
    Applique un délai pour respecter le rate limiting Gemini Flash (15 RPM)
    
    Args:
        rate_limit_rpm: Requêtes par minute (défaut: 15 pour Gemini Flash gratuit)
    """
    # Calculer le délai minimum entre requêtes (en secondes)
    # 60 secondes / 15 requêtes = 4 secondes entre chaque requête
    delay_seconds = 60.0 / rate_limit_rpm
    
    # Ajouter un petit buffer pour être sûr
    time.sleep(delay_seconds + 0.5)


def score_apartment_with_retry(apartment_data: Dict, config: Dict, max_retries: int = 3) -> Dict:
    """
    Score un appartement avec retry automatique en cas d'erreur
    
    Args:
        apartment_data: Données de l'appartement
        config: Configuration de scoring
        max_retries: Nombre maximum de tentatives
    
    Returns:
        Résultat du scoring ou None en cas d'échec
    """
    for attempt in range(max_retries):
        try:
            return score_apartment(apartment_data, config)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Backoff exponentiel
                print(f"   ⚠️ Erreur (tentative {attempt + 1}/{max_retries}): {e}")
                print(f"   Nouvelle tentative dans {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise


def print_progress(current: int, total: int, apartment_id: str) -> None:
    """Affiche la progression du scoring"""
    percentage = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current / total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print(f"\r   [{bar}] {current}/{total} ({percentage:.1f}%) - {apartment_id}", end='', flush=True)


def main():
    """Fonction principale"""
    print("=" * 80)
    print("🏠 SCORING OPTIMISÉ DES 43 NOUVEAUX APPARTEMENTS")
    print("=" * 80)
    print()
    
    start_time = time.time()
    
    # 1. Charger la configuration de scoring
    print("📋 ÉTAPE 1: Chargement de la configuration de scoring")
    print("-" * 80)
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return False
    
    print("✅ Configuration chargée")
    print()
    
    # 2. Identifier les nouveaux appartements
    print("🔍 ÉTAPE 2: Identification des nouveaux appartements")
    print("-" * 80)
    new_apartment_ids = get_new_apartments()
    
    if not new_apartment_ids:
        print("✅ Aucun nouvel appartement à scorer - tous sont déjà dans la base")
        return True
    
    print(f"✅ {len(new_apartment_ids)} nouveaux appartements trouvés")
    if len(new_apartment_ids) <= 10:
        print(f"   IDs: {', '.join(new_apartment_ids)}")
    else:
        print(f"   IDs: {', '.join(new_apartment_ids[:10])}... (+ {len(new_apartment_ids) - 10} autres)")
    print()
    
    # Estimation du coût et du temps
    cost_per_apartment = 0.000225  # $0.000225 pour 3 photos avec Gemini Flash
    total_cost_usd = len(new_apartment_ids) * cost_per_apartment
    estimated_time_minutes = (len(new_apartment_ids) * 4) / 60  # 4 secondes par appartement
    
    print("💰 ESTIMATION DES COÛTS ET TEMPS")
    print("-" * 80)
    print(f"   Coût estimé: ${total_cost_usd:.4f} (~€{total_cost_usd * 0.92:.4f})")
    print(f"   Temps estimé: ~{estimated_time_minutes:.1f} minutes")
    print()
    
    # 3. Scorer chaque nouvel appartement avec rate limiting
    print(f"🎯 ÉTAPE 3: Scoring des {len(new_apartment_ids)} nouveaux appartements")
    print("-" * 80)
    print("   Rate limiting: 4 secondes entre chaque appartement (15 RPM Gemini Flash)")
    print()
    
    scored_apartments = []
    errors = []
    skipped = []
    
    for i, apartment_id in enumerate(new_apartment_ids, 1):
        print_progress(i, len(new_apartment_ids), apartment_id)
        
        # Rate limiting (sauf pour le premier)
        if i > 1:
            rate_limit_delay(rate_limit_rpm=15)
        
        # Charger les données de l'appartement
        apartment_data = load_apartment_data(apartment_id)
        if not apartment_data:
            print(f"\n   ❌ Données non trouvées pour {apartment_id}")
            errors.append(apartment_id)
            continue
        
        # Vérifier si déjà analysé (cache)
        if apartment_data.get('style_analysis'):
            print(f"\n   💾 Appartement {apartment_id} déjà analysé (cache)")
            skipped.append(apartment_id)
            # Continuer quand même pour scorer si pas encore de score
        
        try:
            # Scorer l'appartement avec retry
            score_result = score_apartment_with_retry(apartment_data, config)
            
            # Fusionner avec les données originales
            apartment_scored = {**apartment_data, **score_result}
            
            # Ajouter score_global pour compatibilité (alias de score_total)
            if 'score_total' in score_result:
                apartment_scored['score_global'] = score_result['score_total']
            
            # Sauvegarder le score individuel
            if save_individual_score(apartment_scored, apartment_id):
                scored_apartments.append(apartment_scored)
            else:
                print(f"\n   ⚠️ Score calculé mais erreur sauvegarde pour {apartment_id}")
                errors.append(apartment_id)
                
        except Exception as e:
            print(f"\n   ❌ Erreur scoring {apartment_id}: {e}")
            errors.append(apartment_id)
            import traceback
            traceback.print_exc()
    
    print()  # Nouvelle ligne après la progress bar
    
    # 4. Mettre à jour all_apartments_scores.json
    print(f"\n💾 ÉTAPE 4: Mise à jour de all_apartments_scores.json")
    print("-" * 80)
    
    if scored_apartments:
        total_count = update_all_apartments_scores(scored_apartments)
        print(f"✅ {len(scored_apartments)} nouveaux appartements ajoutés")
        print(f"📊 Total dans la base: {total_count} appartements")
    else:
        print("⚠️ Aucun appartement à ajouter")
    
    # Résumé final
    elapsed_time = time.time() - start_time
    elapsed_minutes = elapsed_time / 60
    
    print(f"\n📊 RÉSULTATS FINAUX")
    print("=" * 80)
    print(f"✅ Appartements scorés avec succès: {len(scored_apartments)}")
    if skipped:
        print(f"⏭️  Appartements déjà analysés (skip): {len(skipped)}")
    if errors:
        print(f"❌ Erreurs: {len(errors)}")
        print(f"   IDs: {', '.join(errors)}")
    
    print(f"\n⏱️  Temps total: {elapsed_minutes:.1f} minutes ({elapsed_time:.1f} secondes)")
    print(f"💰 Coût estimé réel: ${len(scored_apartments) * cost_per_apartment:.4f}")
    
    print(f"\n🎉 TERMINÉ !")
    print(f"   Les nouveaux appartements sont maintenant dans la base de données")
    print(f"   avec leurs critères (prix, style, localisation, etc.)")
    
    return len(scored_apartments) > 0


if __name__ == "__main__":
    main()


