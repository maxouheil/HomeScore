#!/usr/bin/env python3
"""
Script pour reconstruire scraped_apartments.json à partir de toutes les sources disponibles
- all_apartments_scores.json (1400 appartements)
- data/appartements/*.json (fichiers individuels)
- scraped_apartments.json actuel (pour récupérer les données manquantes)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime

def load_all_sources() -> Dict[str, Dict[str, Any]]:
    """Charge tous les appartements depuis toutes les sources disponibles"""
    all_apartments: Dict[str, Dict[str, Any]] = {}
    
    print("=" * 80)
    print("🔄 RECONSTRUCTION DE scraped_apartments.json")
    print("=" * 80)
    print()
    
    # 1. Charger depuis all_apartments_scores.json (source principale)
    scores_file = 'data/scores/all_apartments_scores.json'
    if os.path.exists(scores_file):
        print(f"📂 ÉTAPE 1: Chargement depuis {scores_file}...")
        try:
            with open(scores_file, 'r', encoding='utf-8') as f:
                scored_apartments = json.load(f)
            
            count = 0
            for apt in scored_apartments:
                apt_id = str(apt.get('id', ''))
                if apt_id:
                    # Les scores ont priorité car ils contiennent toutes les données enrichies
                    all_apartments[apt_id] = apt
                    count += 1
            
            print(f"   ✅ {count} appartements chargés depuis scores")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    else:
        print(f"   ⚠️  Fichier {scores_file} non trouvé")
    
    # 2. Charger depuis les fichiers individuels (priorité sur scores pour données brutes)
    appartements_dir = 'data/appartements'
    if os.path.exists(appartements_dir):
        print(f"\n📂 ÉTAPE 2: Chargement depuis {appartements_dir}...")
        try:
            individual_count = 0
            for filename in os.listdir(appartements_dir):
                if filename.endswith('.json') and filename not in ['test_001.json', 'test_no_photo.json', 'unknown.json']:
                    filepath = os.path.join(appartements_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            apt_data = json.load(f)
                        
                        apt_id = str(apt_data.get('id', ''))
                        if apt_id:
                            # Fusionner avec les données existantes (fichiers individuels ont priorité pour données brutes)
                            if apt_id in all_apartments:
                                # Fusionner: garder les scores mais mettre à jour les données brutes
                                existing = all_apartments[apt_id]
                                # Mettre à jour les champs de base depuis le fichier individuel
                                for key in ['url', 'titre', 'prix', 'surface', 'localisation', 'photos', 'description', 'caracteristiques']:
                                    if key in apt_data and apt_data[key]:
                                        existing[key] = apt_data[key]
                                # Préserver les scores et analyses
                                all_apartments[apt_id] = existing
                            else:
                                all_apartments[apt_id] = apt_data
                            individual_count += 1
                    except Exception as e:
                        print(f"   ⚠️  Erreur lecture {filename}: {e}")
            
            print(f"   ✅ {individual_count} appartements chargés depuis fichiers individuels")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    else:
        print(f"   ⚠️  Dossier {appartements_dir} non trouvé")
    
    # 3. Charger depuis scraped_apartments.json actuel (pour récupérer les données manquantes)
    scraped_file = 'data/scraped_apartments.json'
    if os.path.exists(scraped_file):
        print(f"\n📂 ÉTAPE 3: Chargement depuis {scraped_file}...")
        try:
            with open(scraped_file, 'r', encoding='utf-8') as f:
                scraped_apartments = json.load(f)
            
            scraped_count = 0
            for apt in scraped_apartments:
                apt_id = str(apt.get('id', ''))
                if apt_id:
                    if apt_id not in all_apartments:
                        # Ajouter les appartements qui ne sont pas dans les scores
                        all_apartments[apt_id] = apt
                        scraped_count += 1
                    else:
                        # Fusionner: préserver les données depuis scraped si elles sont plus complètes
                        existing = all_apartments[apt_id]
                        # Mettre à jour les champs manquants
                        for key in ['exposition', 'visavis', 'map_info', 'coordinates']:
                            if key in apt and apt[key] and (key not in existing or not existing.get(key)):
                                existing[key] = apt[key]
            
            print(f"   ✅ {scraped_count} nouveaux appartements ajoutés depuis scraped_apartments.json")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    else:
        print(f"   ⚠️  Fichier {scraped_file} non trouvé")
    
    return all_apartments

def clean_apartment_for_scraped(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """Nettoie un appartement pour le format scraped_apartments.json"""
    cleaned = {}
    
    # Champs de base
    base_fields = [
        'id', 'url', 'titre', 'prix', 'surface', 'localisation', 'pieces',
        'prix_m2', 'date', 'transports', 'description', 'caracteristiques',
        'etage', 'agence', 'coordinates', 'map_info', 'photos',
        'scraped_at', 'date_creation_annonce'
    ]
    
    for field in base_fields:
        if field in apartment and apartment[field]:
            cleaned[field] = apartment[field]
    
    # Champs d'analyse (garder seulement les plus importants)
    analysis_fields = ['exposition', 'style_analysis', 'visavis']
    for field in analysis_fields:
        if field in apartment and apartment[field]:
            cleaned[field] = apartment[field]
    
    # Ne pas inclure les scores dans scraped_apartments.json (ils sont dans all_apartments_scores.json)
    # Mais garder les données brutes nécessaires
    
    return cleaned

def main():
    """Fonction principale"""
    print()
    
    # Charger tous les appartements depuis toutes les sources
    all_apartments = load_all_sources()
    
    print()
    print("=" * 80)
    print(f"📊 TOTAL: {len(all_apartments)} appartements trouvés dans toutes les sources")
    print("=" * 80)
    print()
    
    if not all_apartments:
        print("❌ Aucun appartement trouvé. Impossible de reconstruire le fichier.")
        return
    
    # Créer une sauvegarde de l'ancien fichier
    scraped_file = Path('data/scraped_apartments.json')
    if scraped_file.exists():
        backup_file = f'data/scraped_apartments.json.backup_rebuild_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        print(f"💾 Création d'une sauvegarde: {backup_file}")
        import shutil
        shutil.copy2(scraped_file, backup_file)
        print(f"   ✅ Sauvegarde créée")
        print()
    
    # Nettoyer et préparer les appartements
    print("🧹 Nettoyage des données...")
    cleaned_apartments = []
    for apt_id, apt_data in all_apartments.items():
        cleaned = clean_apartment_for_scraped(apt_data)
        cleaned_apartments.append(cleaned)
    
    # Trier par ID pour cohérence
    cleaned_apartments.sort(key=lambda x: str(x.get('id', '')))
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde dans {scraped_file}...")
    scraped_file.parent.mkdir(parents=True, exist_ok=True)
    with open(scraped_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_apartments, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 80)
    print("✅ RECONSTRUCTION TERMINÉE")
    print("=" * 80)
    print(f"📊 {len(cleaned_apartments)} appartements sauvegardés dans {scraped_file}")
    print()
    print("💡 Le fichier scraped_apartments.json a été reconstruit à partir de:")
    print("   - all_apartments_scores.json (1400 appartements)")
    print("   - data/appartements/*.json (fichiers individuels)")
    print("   - scraped_apartments.json (ancien fichier)")
    print()

if __name__ == '__main__':
    main()
