#!/usr/bin/env python3
"""
Script rapide pour ajouter detected_photos dans la structure baignoire existante
"""

import json
import os

def fix_baignoire_structure():
    """Ajoute detected_photos dans photo_validation.photo_result si manquant"""
    print("🔧 CORRECTION DE LA STRUCTURE BAIGNOIRE")
    print("=" * 60)
    
    all_scores_file = 'data/scores/all_apartments_scores.json'
    if not os.path.exists(all_scores_file):
        print(f"❌ Fichier {all_scores_file} non trouvé")
        return
    
    with open(all_scores_file, 'r', encoding='utf-8') as f:
        apartments = json.load(f)
    
    print(f"📋 {len(apartments)} appartements trouvés")
    print()
    
    fixed_count = 0
    
    for i, apartment in enumerate(apartments, 1):
        apartment_id = apartment.get('id', 'unknown')
        baignoire_score = apartment.get('scores_detaille', {}).get('baignoire', {})
        
        if not baignoire_score:
            continue
        
        details = baignoire_score.get('details', {})
        photo_validation = details.get('photo_validation', {})
        photo_result = photo_validation.get('photo_result', {})
        
        # Si photo_result existe mais n'a pas detected_photos, l'ajouter
        if photo_result and 'detected_photos' not in photo_result:
            # Essayer de récupérer depuis baignoire root si disponible
            baignoire_root = apartment.get('baignoire', {})
            detected_photos = baignoire_root.get('detected_photos', [])
            
            # Si toujours vide, utiliser une liste vide (structure correcte mais pas de photos détectées)
            photo_result['detected_photos'] = detected_photos if detected_photos else []
            
            # S'assurer que photo_validation existe
            if not photo_validation:
                details['photo_validation'] = {'photo_result': photo_result}
            else:
                photo_validation['photo_result'] = photo_result
            
            # S'assurer que details existe
            if not details:
                baignoire_score['details'] = {'photo_validation': photo_validation}
            else:
                details['photo_validation'] = photo_validation
            
            fixed_count += 1
            print(f"[{i}/{len(apartments)}] ✅ {apartment_id}: Structure corrigée")
    
    # Sauvegarder
    with open(all_scores_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 60)
    print(f"✅ {fixed_count} appartements corrigés")
    print(f"💾 Fichier sauvegardé: {all_scores_file}")
    print()
    print("🔄 Relancez le serveur backend pour voir les changements !")

if __name__ == "__main__":
    fix_baignoire_structure()



