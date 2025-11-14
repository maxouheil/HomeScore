#!/usr/bin/env python3
"""
Script pour mettre à jour all_apartments_scores.json avec la nouvelle structure baignoire
Utilise scoring_optimized pour re-scorer tous les appartements
"""

import json
import os
from scoring_optimized import score_apartment_optimized
from scoring import load_scoring_config

def update_all_scores():
    """Met à jour all_apartments_scores.json avec la nouvelle structure"""
    print("🔄 MISE À JOUR DE all_apartments_scores.json")
    print("=" * 60)
    
    # Charger la config de scoring
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Charger all_apartments_scores.json
    all_scores_file = 'data/scores/all_apartments_scores.json'
    if not os.path.exists(all_scores_file):
        print(f"❌ Fichier {all_scores_file} non trouvé")
        return
    
    with open(all_scores_file, 'r', encoding='utf-8') as f:
        apartments = json.load(f)
    
    print(f"📋 {len(apartments)} appartements trouvés")
    print()
    
    updated_count = 0
    
    for i, apartment in enumerate(apartments, 1):
        apartment_id = apartment.get('id', 'unknown')
        print(f"🏠 [{i}/{len(apartments)}] Appartement {apartment_id}")
        
        try:
            # Re-scorer l'appartement avec la logique optimisée
            score_result = score_apartment_optimized(apartment, config)
            
            if not score_result:
                print(f"   ❌ Échec du scoring")
                continue
            
            # Mettre à jour scores_detaille dans l'appartement
            apartment['scores_detaille'] = score_result.get('scores_detaille', {})
            apartment['score_total'] = score_result.get('score_total', apartment.get('score_total', 0))
            apartment['tier'] = score_result.get('tier', apartment.get('tier', 'tier3'))
            
            # Vérifier si baignoire a detected_photos (nouvelle structure)
            baignoire_score = apartment['scores_detaille'].get('baignoire', {})
            baignoire_details = baignoire_score.get('details', {})
            photo_validation = baignoire_details.get('photo_validation', {})
            photo_result = photo_validation.get('photo_result', {})
            detected_photos = photo_result.get('detected_photos', [])
            
            if detected_photos:
                print(f"   ✅ Baignoire: {len(detected_photos)} photo(s) détectée(s) - {detected_photos}")
            elif photo_result.get('has_baignoire') is not None or photo_result.get('has_douche') is not None:
                print(f"   ✅ Baignoire: Score mis à jour (photos analysées)")
            else:
                print(f"   ✅ Score mis à jour")
            
            updated_count += 1
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Sauvegarder le fichier mis à jour
    with open(all_scores_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print(f"✅ Appartements mis à jour: {updated_count}/{len(apartments)}")
    print(f"💾 Fichier sauvegardé: {all_scores_file}")
    print()
    print("💡 La nouvelle structure avec detected_photos est maintenant disponible !")
    print("🔄 N'oubliez pas de relancer le serveur backend pour voir les changements !")

if __name__ == "__main__":
    update_all_scores()



