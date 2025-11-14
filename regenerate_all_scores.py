#!/usr/bin/env python3
"""
Script pour régénérer all_apartments_scores.json depuis les fichiers de scores individuels mis à jour
"""

import json
import os

def regenerate_all_scores():
    """Régénère all_apartments_scores.json depuis les fichiers individuels"""
    print("🔄 RÉGÉNÉRATION DE all_apartments_scores.json")
    print("=" * 60)
    
    scores_dir = "data/scores"
    if not os.path.exists(scores_dir):
        print(f"❌ Dossier {scores_dir} non trouvé")
        return
    
    # Lister tous les fichiers de scores individuels
    score_files = [f for f in os.listdir(scores_dir) 
                   if f.startswith('apartment_') and f.endswith('_score.json')]
    
    if not score_files:
        print("❌ Aucun fichier de score trouvé")
        return
    
    print(f"📋 {len(score_files)} fichiers de scores trouvés\n")
    
    all_apartments = []
    
    for i, score_filename in enumerate(score_files, 1):
        score_filepath = os.path.join(scores_dir, score_filename)
        
        try:
            with open(score_filepath, 'r', encoding='utf-8') as f:
                apartment_data = json.load(f)
            
            all_apartments.append(apartment_data)
            print(f"[{i}/{len(score_files)}] {apartment_data.get('id', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Erreur lecture {score_filename}: {e}")
    
    # Sauvegarder le fichier consolidé
    all_scores_file = os.path.join(scores_dir, "all_apartments_scores.json")
    with open(all_scores_file, 'w', encoding='utf-8') as f:
        json.dump(all_apartments, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ RÉGÉNÉRATION TERMINÉE")
    print("=" * 60)
    print(f"📊 {len(all_apartments)} appartements dans all_apartments_scores.json")
    print(f"💾 Fichier sauvegardé: {all_scores_file}")
    
    # Vérifier les quartiers
    avec_quartier = sum(1 for apt in all_apartments 
                       if apt.get('map_info', {}).get('quartier', '') and 
                       apt.get('map_info', {}).get('quartier', '') != 'Quartier non identifié')
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Avec quartier identifié: {avec_quartier}/{len(all_apartments)} ({avec_quartier*100//len(all_apartments) if all_apartments else 0}%)")

if __name__ == "__main__":
    regenerate_all_scores()





