#!/usr/bin/env python3
"""
Script pour ajouter les nouveaux appartements à la base de données avec scoring
"""

import json
import os
from datetime import datetime
from scoring import load_scoring_config
from scoring_optimized import score_apartment_optimized as score_apartment

def load_apartment_data(apartment_id):
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

def get_new_apartments():
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

def save_individual_score(apartment_scored, apartment_id):
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

def update_all_apartments_scores(new_apartments_scored):
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
    all_apartments.sort(key=lambda x: x.get('score_global', 0), reverse=True)
    
    # Sauvegarder
    try:
        with open(all_scores_file, 'w', encoding='utf-8') as f:
            json.dump(all_apartments, f, ensure_ascii=False, indent=2)
        return len(all_apartments)
    except Exception as e:
        print(f"❌ Erreur sauvegarde all_apartments_scores.json: {e}")
        return 0

def main():
    """Fonction principale"""
    print("🏠 AJOUT DES NOUVEAUX APPARTEMENTS À LA BASE DE DONNÉES")
    print("=" * 60)
    
    # 1. Charger la configuration de scoring
    print("\n📋 ÉTAPE 1: Chargement de la configuration de scoring")
    print("-" * 40)
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return False
    
    print("✅ Configuration chargée")
    
    # 2. Identifier les nouveaux appartements
    print("\n🔍 ÉTAPE 2: Identification des nouveaux appartements")
    print("-" * 40)
    new_apartment_ids = get_new_apartments()
    
    if not new_apartment_ids:
        print("✅ Aucun nouvel appartement à scorer - tous sont déjà dans la base")
        return True
    
    print(f"✅ {len(new_apartment_ids)} nouveaux appartements trouvés")
    print(f"   IDs: {', '.join(new_apartment_ids[:10])}{'...' if len(new_apartment_ids) > 10 else ''}")
    
    # 3. Scorer chaque nouvel appartement
    print(f"\n🎯 ÉTAPE 3: Scoring des {len(new_apartment_ids)} nouveaux appartements")
    print("-" * 40)
    
    scored_apartments = []
    errors = []
    
    for i, apartment_id in enumerate(new_apartment_ids, 1):
        print(f"\n🏠 Scoring {i}/{len(new_apartment_ids)}: Appartement {apartment_id}")
        
        # Charger les données de l'appartement
        apartment_data = load_apartment_data(apartment_id)
        if not apartment_data:
            print(f"   ❌ Données non trouvées")
            errors.append(apartment_id)
            continue
        
        print(f"   📍 {apartment_data.get('localisation', 'N/A')}")
        print(f"   💰 {apartment_data.get('prix', 'N/A')}")
        print(f"   📐 {apartment_data.get('surface', 'N/A')}")
        
        try:
            # Scorer l'appartement
            score_result = score_apartment(apartment_data, config)
            
            # Fusionner avec les données originales
            apartment_scored = {**apartment_data, **score_result}
            
            # Ajouter score_global pour compatibilité (alias de score_total)
            if 'score_total' in score_result:
                apartment_scored['score_global'] = score_result['score_total']
            
            # Sauvegarder le score individuel
            if save_individual_score(apartment_scored, apartment_id):
                print(f"   ✅ Score: {score_result.get('score_total', 0)}/100")
                print(f"   💾 Score sauvegardé")
                scored_apartments.append(apartment_scored)
            else:
                print(f"   ⚠️ Score calculé mais erreur sauvegarde")
                errors.append(apartment_id)
                
        except Exception as e:
            print(f"   ❌ Erreur scoring: {e}")
            errors.append(apartment_id)
            import traceback
            traceback.print_exc()
    
    # 4. Mettre à jour all_apartments_scores.json
    print(f"\n💾 ÉTAPE 4: Mise à jour de all_apartments_scores.json")
    print("-" * 40)
    
    if scored_apartments:
        total_count = update_all_apartments_scores(scored_apartments)
        print(f"✅ {len(scored_apartments)} nouveaux appartements ajoutés")
        print(f"📊 Total dans la base: {total_count} appartements")
    else:
        print("⚠️ Aucun appartement à ajouter")
    
    # Résumé final
    print(f"\n📊 RÉSULTATS FINAUX")
    print("=" * 60)
    print(f"✅ Appartements scorés avec succès: {len(scored_apartments)}")
    if errors:
        print(f"❌ Erreurs: {len(errors)}")
        print(f"   IDs: {', '.join(errors)}")
    
    print(f"\n🎉 TERMINÉ !")
    print(f"   Les nouveaux appartements sont maintenant dans la base de données")
    print(f"   avec leurs critères (prix, style, localisation, etc.)")
    
    return len(scored_apartments) > 0

if __name__ == "__main__":
    main()

