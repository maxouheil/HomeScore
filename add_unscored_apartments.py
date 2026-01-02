#!/usr/bin/env python3
"""
Script pour ajouter les appartements sans score à all_apartments_scores.json
Ces appartements seront visibles dans l'UI avec le message "Appartement sans score"
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Set

def load_scraped_apartments() -> List[Dict[str, Any]]:
    """Charge tous les appartements depuis scraped_apartments.json"""
    scraped_file = Path('data/scraped_apartments.json')
    if not scraped_file.exists():
        print(f"⚠️  Fichier {scraped_file} non trouvé")
        return []
    
    try:
        with open(scraped_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        print(f"✅ {len(apartments)} appartements chargés depuis {scraped_file.name}")
        return apartments
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {scraped_file}: {e}")
        return []

def load_individual_apartments() -> List[Dict[str, Any]]:
    """Charge tous les appartements depuis data/appartements/ (fichiers individuels)"""
    apartments_dir = Path('data/appartements')
    if not apartments_dir.exists():
        print(f"⚠️  Dossier {apartments_dir} n'existe pas")
        return []
    
    apartments = []
    apartment_files = [
        f for f in apartments_dir.glob('*.json')
        if f.stem not in ['test_001', 'test_no_photo', 'unknown']
    ]
    
    print(f"📂 Chargement depuis {apartments_dir} ({len(apartment_files)} fichiers)...")
    
    for apt_file in apartment_files:
        try:
            with open(apt_file, 'r', encoding='utf-8') as f:
                apt_data = json.load(f)
                apt_id = apt_data.get('id')
                if apt_id:
                    apartments.append(apt_data)
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement de {apt_file.name}: {e}")
            continue
    
    print(f"✅ {len(apartments)} appartements chargés depuis {apartments_dir}")
    return apartments

def load_existing_scored_apartments() -> List[Dict[str, Any]]:
    """Charge les appartements existants depuis all_apartments_scores.json"""
    scores_file = Path('data/scores/all_apartments_scores.json')
    if not scores_file.exists():
        print(f"⚠️  Fichier {scores_file} n'existe pas, création d'un nouveau fichier")
        return []
    
    try:
        with open(scores_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        print(f"✅ {len(apartments)} appartements existants chargés depuis {scores_file.name}")
        return apartments
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {scores_file}: {e}")
        return []

def clean_apartment_data(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nettoie les données d'un appartement pour l'ajouter sans score
    Supprime tous les champs de score mais préserve toutes les autres données
    """
    cleaned = {}
    
    # Liste des champs à exclure (champs de score)
    score_fields = [
        'scores_detaille',
        'score_total',
        'score_global',
        'alert_score',
        'alert_criteria_scores',
        'alert_tier',
        'megaScore',
        'score'
    ]
    
    # Copier tous les champs sauf les champs de score
    for key, value in apartment.items():
        if key not in score_fields:
            cleaned[key] = value
    
    # S'assurer que les photos sont préservées
    if 'photos' not in cleaned and 'photos' in apartment:
        cleaned['photos'] = apartment['photos']
    
    return cleaned

def add_unscored_apartments():
    """Ajoute les appartements sans score à all_apartments_scores.json"""
    print("=" * 80)
    print("🏠 AJOUT DES APPARTEMENTS SANS SCORE À LA BASE DE DONNÉES")
    print("=" * 80)
    
    # 1. Charger tous les appartements scrapés
    print("\n📋 ÉTAPE 1: Chargement des appartements scrapés")
    print("-" * 80)
    
    scraped_apartments = load_scraped_apartments()
    individual_apartments = load_individual_apartments()
    
    # Créer un dictionnaire par ID pour éviter les doublons (priorité aux fichiers individuels)
    all_scraped_dict: Dict[str, Dict[str, Any]] = {}
    
    # D'abord ajouter depuis scraped_apartments.json
    for apt in scraped_apartments:
        apt_id = str(apt.get('id', ''))
        if apt_id:
            all_scraped_dict[apt_id] = apt
    
    # Ensuite ajouter depuis les fichiers individuels (priorité)
    for apt in individual_apartments:
        apt_id = str(apt.get('id', ''))
        if apt_id:
            all_scraped_dict[apt_id] = apt
    
    print(f"\n📊 Total appartements scrapés (dédupliqués): {len(all_scraped_dict)}")
    
    # 2. Charger les appartements existants dans all_apartments_scores.json
    print("\n📋 ÉTAPE 2: Chargement des appartements existants")
    print("-" * 80)
    
    existing_apartments = load_existing_scored_apartments()
    existing_ids: Set[str] = {str(apt.get('id', '')) for apt in existing_apartments if apt.get('id')}
    
    print(f"📊 Appartements déjà dans all_apartments_scores.json: {len(existing_ids)}")
    
    # 3. Identifier les nouveaux appartements (ceux sans score)
    print("\n📋 ÉTAPE 3: Identification des nouveaux appartements")
    print("-" * 80)
    
    new_apartments = []
    for apt_id, apt_data in all_scraped_dict.items():
        if apt_id not in existing_ids:
            # Nettoyer les données (supprimer les scores s'il y en a)
            cleaned_apt = clean_apartment_data(apt_data)
            new_apartments.append(cleaned_apt)
    
    print(f"📊 Nouveaux appartements à ajouter: {len(new_apartments)}")
    
    if not new_apartments:
        print("\n✅ Aucun nouvel appartement à ajouter - tous sont déjà dans la base")
        return
    
    # Afficher quelques exemples
    print(f"\n📋 Exemples d'IDs à ajouter:")
    for i, apt in enumerate(new_apartments[:10], 1):
        apt_id = apt.get('id', 'N/A')
        titre = apt.get('titre', 'N/A')[:50]
        photos_count = len(apt.get('photos', []))
        print(f"   {i}. {apt_id}: {titre}... ({photos_count} photos)")
    
    if len(new_apartments) > 10:
        print(f"   ... et {len(new_apartments) - 10} autres")
    
    # 4. Vérifier que les photos sont préservées
    print("\n📋 ÉTAPE 4: Vérification des photos")
    print("-" * 80)
    
    apartments_with_photos = sum(1 for apt in new_apartments if apt.get('photos'))
    print(f"📊 Appartements avec photos: {apartments_with_photos}/{len(new_apartments)}")
    
    if apartments_with_photos < len(new_apartments):
        print(f"⚠️  {len(new_apartments) - apartments_with_photos} appartements sans photos")
    
    # 5. Ajouter les nouveaux appartements à all_apartments_scores.json
    print("\n📋 ÉTAPE 5: Ajout à all_apartments_scores.json")
    print("-" * 80)
    
    # Créer un dictionnaire pour éviter les doublons
    all_apartments_dict: Dict[str, Dict[str, Any]] = {}
    
    # D'abord ajouter les appartements existants (avec leurs scores)
    for apt in existing_apartments:
        apt_id = str(apt.get('id', ''))
        if apt_id:
            all_apartments_dict[apt_id] = apt
    
    # Ensuite ajouter les nouveaux appartements (sans score)
    for apt in new_apartments:
        apt_id = str(apt.get('id', ''))
        if apt_id:
            all_apartments_dict[apt_id] = apt
    
    # Convertir en liste
    all_apartments = list(all_apartments_dict.values())
    
    # Trier: d'abord ceux avec score (par score décroissant), puis ceux sans score (par ID)
    def sort_key(apt):
        # Si l'appartement a un score, utiliser le score (négatif pour tri décroissant)
        score = apt.get('score_global') or apt.get('score_total') or apt.get('score')
        if score is not None:
            return (-score, 0)  # Score négatif pour tri décroissant
        # Sinon, utiliser l'ID pour trier
        return (1, str(apt.get('id', '')))
    
    all_apartments.sort(key=sort_key)
    
    # Sauvegarder
    scores_file = Path('data/scores/all_apartments_scores.json')
    scores_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(scores_file, 'w', encoding='utf-8') as f:
            json.dump(all_apartments, f, ensure_ascii=False, indent=2)
        print(f"✅ {len(new_apartments)} nouveaux appartements ajoutés")
        print(f"📊 Total dans la base: {len(all_apartments)} appartements")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. Résumé final
    print("\n📊 RÉSULTATS FINAUX")
    print("=" * 80)
    print(f"✅ Appartements ajoutés sans score: {len(new_apartments)}")
    print(f"📊 Total dans all_apartments_scores.json: {len(all_apartments)}")
    print(f"   - Appartements avec score: {len(existing_ids)}")
    print(f"   - Appartements sans score: {len(new_apartments)}")
    print(f"📸 Appartements avec photos: {apartments_with_photos}/{len(new_apartments)}")
    
    print("\n🎉 TERMINÉ !")
    print("   Les nouveaux appartements sont maintenant dans la base de données")
    print("   Ils seront affichés dans l'UI avec le message 'Appartement sans score'")
    print("   et leurs photos seront visibles dans le carousel")

if __name__ == "__main__":
    add_unscored_apartments()
