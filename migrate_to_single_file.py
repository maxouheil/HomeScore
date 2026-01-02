#!/usr/bin/env python3
"""
Script pour migrer toutes les sources d'appartements vers un fichier unique
data/all_apartments.json

Ce fichier contiendra TOUT :
- Données brutes (scraped)
- Scores
- Analyses (style, exposition, etc.)
- Toutes les métadonnées
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def load_all_sources() -> Dict[str, Dict[str, Any]]:
    """Charge tous les appartements depuis toutes les sources et les fusionne"""
    all_apartments: Dict[str, Dict[str, Any]] = {}
    
    print("=" * 80)
    print("🔄 MIGRATION VERS FICHIER UNIQUE: data/all_apartments.json")
    print("=" * 80)
    print()
    
    # 1. Charger depuis all_apartments_scores.json (contient scores + données)
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
                    all_apartments[apt_id] = apt.copy()
                    count += 1
            
            print(f"   ✅ {count} appartements chargés depuis scores")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    else:
        print(f"   ⚠️  Fichier {scores_file} non trouvé")
    
    # 2. Charger depuis scraped_apartments.json (pour compléter les données manquantes)
    scraped_file = 'data/scraped_apartments.json'
    if os.path.exists(scraped_file):
        print(f"\n📂 ÉTAPE 2: Chargement depuis {scraped_file}...")
        try:
            with open(scraped_file, 'r', encoding='utf-8') as f:
                scraped_apartments = json.load(f)
            
            updated_count = 0
            new_count = 0
            for apt in scraped_apartments:
                apt_id = str(apt.get('id', ''))
                if apt_id:
                    if apt_id in all_apartments:
                        # Fusionner: mettre à jour les champs manquants
                        existing = all_apartments[apt_id]
                        for key in ['url', 'titre', 'prix', 'surface', 'localisation', 'photos', 
                                   'description', 'caracteristiques', 'exposition', 'map_info', 
                                   'coordinates', 'transports', 'date_creation_annonce']:
                            if key in apt and apt[key]:
                                # Mettre à jour seulement si manquant ou vide
                                if key not in existing or not existing.get(key):
                                    existing[key] = apt[key]
                                    updated_count += 1
                    else:
                        # Nouvel appartement
                        all_apartments[apt_id] = apt.copy()
                        new_count += 1
            
            print(f"   ✅ {updated_count} appartements mis à jour")
            print(f"   ✅ {new_count} nouveaux appartements ajoutés")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    else:
        print(f"   ⚠️  Fichier {scraped_file} non trouvé")
    
    # 3. Charger depuis les fichiers individuels (priorité pour données brutes)
    appartements_dir = 'data/appartements'
    if os.path.exists(appartements_dir):
        print(f"\n📂 ÉTAPE 3: Chargement depuis {appartements_dir}...")
        try:
            individual_count = 0
            updated_count = 0
            for filename in os.listdir(appartements_dir):
                if filename.endswith('.json') and filename not in ['test_001.json', 'test_no_photo.json', 'unknown.json']:
                    filepath = os.path.join(appartements_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            apt_data = json.load(f)
                        
                        apt_id = str(apt_data.get('id', ''))
                        if apt_id:
                            if apt_id in all_apartments:
                                # Fusionner: mettre à jour les données brutes
                                existing = all_apartments[apt_id]
                                for key in ['url', 'titre', 'prix', 'surface', 'localisation', 'photos', 
                                           'description', 'caracteristiques', 'etage', 'agence', 
                                           'coordinates', 'map_info', 'transports']:
                                    if key in apt_data and apt_data[key]:
                                        existing[key] = apt_data[key]
                                        updated_count += 1
                            else:
                                all_apartments[apt_id] = apt_data.copy()
                                individual_count += 1
                    except Exception as e:
                        print(f"   ⚠️  Erreur lecture {filename}: {e}")
            
            print(f"   ✅ {individual_count} nouveaux appartements ajoutés")
            print(f"   ✅ {updated_count} appartements mis à jour")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    else:
        print(f"   ⚠️  Dossier {appartements_dir} non trouvé")
    
    return all_apartments

def clean_apartment_data(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """Nettoie et normalise les données d'un appartement"""
    cleaned = apartment.copy()
    
    # S'assurer que les champs essentiels existent
    if 'id' not in cleaned or not cleaned['id']:
        return None
    
    # Normaliser l'ID en string
    cleaned['id'] = str(cleaned['id'])
    
    # Supprimer les champs vides ou None
    keys_to_remove = []
    for key, value in cleaned.items():
        if value is None or value == '' or value == [] or value == {}:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del cleaned[key]
    
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
        print("❌ Aucun appartement trouvé. Impossible de créer le fichier unique.")
        return
    
    # Nettoyer les données
    print("🧹 Nettoyage et normalisation des données...")
    cleaned_apartments = []
    for apt_id, apt_data in all_apartments.items():
        cleaned = clean_apartment_data(apt_data)
        if cleaned:
            cleaned_apartments.append(cleaned)
    
    # Trier par ID pour cohérence
    cleaned_apartments.sort(key=lambda x: str(x.get('id', '')))
    
    print(f"   ✅ {len(cleaned_apartments)} appartements nettoyés")
    print()
    
    # Créer une sauvegarde si le fichier existe déjà
    output_file = Path('data/all_apartments.json')
    if output_file.exists():
        backup_file = f'data/all_apartments.json.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        print(f"💾 Création d'une sauvegarde: {backup_file}")
        import shutil
        shutil.copy2(output_file, backup_file)
        print(f"   ✅ Sauvegarde créée")
        print()
    
    # Sauvegarder dans le fichier unique
    print(f"💾 Sauvegarde dans {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_apartments, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 80)
    print("✅ MIGRATION TERMINÉE")
    print("=" * 80)
    print(f"📊 {len(cleaned_apartments)} appartements sauvegardés dans {output_file}")
    print()
    print("💡 Le fichier unique contient maintenant:")
    print("   - Toutes les données brutes (scraped)")
    print("   - Tous les scores")
    print("   - Toutes les analyses (style, exposition, etc.)")
    print("   - Toutes les métadonnées")
    print()
    print("⚠️  PROCHAINES ÉTAPES:")
    print("   1. Modifier backend/api/apartments.py pour charger depuis all_apartments.json")
    print("   2. Mettre à jour les scripts qui écrivent les données")
    print("   3. Tester que tout fonctionne correctement")
    print()

if __name__ == '__main__':
    main()
