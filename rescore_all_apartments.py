#!/usr/bin/env python3
"""
Script pour re-scorer tous les appartements existants
Met à jour scores_detaille avec la nouvelle structure (notamment baignoire avec detected_photos)
"""

import json
import os
from scoring_optimized import score_apartment_optimized
from scoring import load_scoring_config

def load_apartment(apartment_id):
    """Charge un appartement depuis data/appartements/"""
    apartment_file = f"data/appartements/{apartment_id}.json"
    if not os.path.exists(apartment_file):
        return None
    
    try:
        with open(apartment_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"   ❌ Erreur chargement {apartment_id}: {e}")
        return None

def save_apartment(apartment_data):
    """Sauvegarde un appartement mis à jour"""
    apartment_id = apartment_data.get('id')
    if not apartment_id:
        print(f"   ⚠️ Pas d'ID pour l'appartement, skip")
        return False
    
    apartment_file = f"data/appartements/{apartment_id}.json"
    try:
        with open(apartment_file, 'w', encoding='utf-8') as f:
            json.dump(apartment_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"   ❌ Erreur sauvegarde {apartment_id}: {e}")
        return False

def rescore_all_apartments():
    """Re-score tous les appartements existants"""
    print("🔄 RE-SCORING DE TOUS LES APPARTEMENTS")
    print("=" * 60)
    
    # Charger la config de scoring
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Trouver tous les appartements
    apartments_dir = "data/appartements"
    if not os.path.exists(apartments_dir):
        print(f"❌ Dossier {apartments_dir} non trouvé")
        return
    
    apartment_files = [f for f in os.listdir(apartments_dir) if f.endswith('.json')]
    total = len(apartment_files)
    
    if total == 0:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"📋 {total} appartements trouvés")
    print()
    
    updated_count = 0
    error_count = 0
    
    for i, apartment_file in enumerate(apartment_files, 1):
        apartment_id = apartment_file.replace('.json', '')
        print(f"🏠 [{i}/{total}] Appartement {apartment_id}")
        
        # Charger l'appartement
        apartment = load_apartment(apartment_id)
        if not apartment:
            error_count += 1
            continue
        
        try:
            # Re-scorer l'appartement avec la logique optimisée (nouvelle structure cuisine/baignoire)
            score_result = score_apartment_optimized(apartment, config)
            
            if not score_result:
                print(f"   ❌ Échec du scoring")
                error_count += 1
                continue
            
            # Mettre à jour scores_detaille dans l'appartement
            apartment['scores_detaille'] = score_result.get('scores_detaille', {})
            apartment['score_total'] = score_result.get('score_total', 0)
            apartment['tier'] = score_result.get('tier', 'tier3')
            apartment['recommandation'] = score_result.get('recommandation', '')
            
            # Vérifier si baignoire a detected_photos (nouvelle structure)
            baignoire_score = apartment['scores_detaille'].get('baignoire', {})
            baignoire_details = baignoire_score.get('details', {})
            photo_validation = baignoire_details.get('photo_validation', {})
            photo_result = photo_validation.get('photo_result', {})
            detected_photos = photo_result.get('detected_photos', [])
            
            if detected_photos:
                print(f"   ✅ Baignoire: {len(detected_photos)} photo(s) détectée(s) - {detected_photos}")
            else:
                print(f"   ✅ Baignoire: Score mis à jour (pas de photos détectées)")
            
            # Sauvegarder l'appartement mis à jour
            if save_apartment(apartment):
                updated_count += 1
                print(f"   💾 Sauvegardé - Score: {apartment['score_total']}/100")
            else:
                error_count += 1
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
        
        print()
    
    # Résumé
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print(f"✅ Appartements mis à jour: {updated_count}/{total}")
    if error_count > 0:
        print(f"❌ Erreurs: {error_count}")
    print()
    print("💡 Les nouvelles structures avec detected_photos sont maintenant disponibles !")

if __name__ == "__main__":
    rescore_all_apartments()



