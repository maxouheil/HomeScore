#!/usr/bin/env python3
"""
Script pour mettre à jour les fichiers de scores avec les quartiers mis à jour
Fusionne les données scrapées mises à jour dans les fichiers de scores
"""

import json
import os
from datetime import datetime

def update_score_file(apartment_id):
    """Met à jour un fichier de score avec les données scrapées mises à jour"""
    apartment_file = f"data/appartements/{apartment_id}.json"
    score_file = f"data/scores/apartment_{apartment_id}_score.json"
    
    if not os.path.exists(apartment_file):
        return {'status': 'error', 'error': 'Apartment file not found'}
    
    if not os.path.exists(score_file):
        return {'status': 'skipped', 'reason': 'Score file not found'}
    
    try:
        # Charger les données scrapées mises à jour
        with open(apartment_file, 'r', encoding='utf-8') as f:
            apartment_data = json.load(f)
        
        # Charger le fichier de score existant
        with open(score_file, 'r', encoding='utf-8') as f:
            score_data = json.load(f)
        
        # Mettre à jour les données importantes depuis apartment_data
        updates = {}
        
        # Mettre à jour map_info (quartier notamment)
        if 'map_info' in apartment_data:
            score_data['map_info'] = apartment_data['map_info']
            updates['map_info'] = True
        
        # Mettre à jour transports
        if 'transports' in apartment_data:
            score_data['transports'] = apartment_data['transports']
            updates['transports'] = True
        
        # Mettre à jour localisation
        if 'localisation' in apartment_data:
            score_data['localisation'] = apartment_data['localisation']
            updates['localisation'] = True
        
        # Mettre à jour l'étage si corrigé
        if 'etage' in apartment_data:
            score_data['etage'] = apartment_data['etage']
            updates['etage'] = True
        
        # Ajouter une date de mise à jour
        score_data['updated_at'] = datetime.now().isoformat()
        
        # Sauvegarder le fichier mis à jour
        with open(score_file, 'w', encoding='utf-8') as f:
            json.dump(score_data, f, ensure_ascii=False, indent=2)
        
        return {'status': 'updated', 'updates': updates}
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def main():
    """Met à jour tous les fichiers de scores"""
    print("🔄 MISE À JOUR DES FICHIERS DE SCORES")
    print("=" * 60)
    
    scores_dir = "data/scores"
    if not os.path.exists(scores_dir):
        print(f"❌ Dossier {scores_dir} non trouvé")
        return
    
    # Lister tous les fichiers de scores
    score_files = [f for f in os.listdir(scores_dir) 
                   if f.startswith('apartment_') and f.endswith('_score.json')]
    
    if not score_files:
        print("❌ Aucun fichier de score trouvé")
        return
    
    print(f"📋 {len(score_files)} fichiers de scores à vérifier\n")
    
    stats = {
        'total': len(score_files),
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    for i, score_filename in enumerate(score_files, 1):
        # Extraire l'ID de l'appartement
        apartment_id = score_filename.replace('apartment_', '').replace('_score.json', '')
        
        print(f"[{i}/{len(score_files)}] Appartement {apartment_id}...", end=' ')
        
        result = update_score_file(apartment_id)
        
        if result['status'] == 'updated':
            stats['updated'] += 1
            updates = result.get('updates', {})
            update_list = [k for k, v in updates.items() if v]
            print(f"✅ Mis à jour: {', '.join(update_list)}")
        elif result['status'] == 'skipped':
            stats['skipped'] += 1
            print(f"⏭️  {result.get('reason', 'Skipped')}")
        elif result['status'] == 'error':
            stats['errors'] += 1
            print(f"❌ Erreur: {result.get('error', 'Unknown')}")
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"Total: {stats['total']}")
    print(f"✅ Mis à jour: {stats['updated']}")
    print(f"⏭️  Ignorés: {stats['skipped']}")
    print(f"❌ Erreurs: {stats['errors']}")

if __name__ == "__main__":
    main()








