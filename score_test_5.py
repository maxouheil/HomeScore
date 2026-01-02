#!/usr/bin/env python3
"""
Script de test pour scorer 5 appartements et vérifier toutes les données
"""

import json
import os
from scoring import score_apartment, load_scoring_config

def load_apartments():
    """Charge tous les appartements depuis scraped_apartments.json"""
    with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_existing_scores():
    """Charge les scores existants"""
    scores_file = 'data/scores/all_apartments_scores.json'
    if os.path.exists(scores_file):
        with open(scores_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def check_apartment_data(apartment):
    """Vérifie que toutes les données nécessaires sont présentes"""
    checks = {
        'id': apartment.get('id'),
        'titre': apartment.get('titre'),
        'prix': apartment.get('prix'),
        'surface': apartment.get('surface'),
        'localisation': apartment.get('localisation'),
        'pieces': apartment.get('pieces'),
        'photos': len(apartment.get('photos', [])),
        'map_info': apartment.get('map_info', {}),
        '_api_data': apartment.get('_api_data', {}),
        'style_analysis': apartment.get('style_analysis'),
        'exposition': apartment.get('exposition'),
    }
    return checks

def score_test_5():
    """Test avec 5 appartements"""
    print("🧪 TEST DE SCORING - 5 APPARTEMENTS")
    print("=" * 80)
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Charger tous les appartements
    apartments = load_apartments()
    print(f"📂 {len(apartments)} appartements chargés")
    
    # Charger les scores existants
    existing_scores = load_existing_scores()
    scored_ids = {apt.get('id') for apt in existing_scores if apt.get('id')}
    print(f"📊 {len(scored_ids)} appartements déjà scorés")
    print()
    
    # Prendre les 5 premiers qui ne sont pas déjà scorés
    test_apartments = []
    for apt in apartments:
        apt_id = apt.get('id')
        if apt_id and apt_id not in scored_ids:
            test_apartments.append(apt)
            if len(test_apartments) >= 5:
                break
    
    if not test_apartments:
        print("⚠️  Tous les appartements sont déjà scorés, test avec 5 premiers")
        test_apartments = apartments[:5]
    
    print(f"🎯 Test avec {len(test_apartments)} appartements")
    print()
    
    results = []
    
    for i, apartment in enumerate(test_apartments, 1):
        apt_id = apartment.get('id', 'N/A')
        print(f"\n{'='*80}")
        print(f"🏠 APPARTEMENT {i}/5: {apt_id}")
        print(f"{'='*80}")
        
        # Vérifier les données avant scoring
        print("\n📋 DONNÉES DISPONIBLES:")
        data_check = check_apartment_data(apartment)
        for key, value in data_check.items():
            if key == 'photos':
                print(f"   {key}: {value} photo(s)")
            elif isinstance(value, dict):
                print(f"   {key}: {'✅ Présent' if value else '❌ Absent'}")
                if value and len(str(value)) < 200:
                    print(f"      Contenu: {value}")
            else:
                status = "✅" if value else "❌"
                display_value = str(value)[:60] if value else "Absent"
                print(f"   {status} {key}: {display_value}")
        
        # Scorer l'appartement
        print(f"\n🤖 SCORING...")
        try:
            score_result = score_apartment(apartment, config)
            
            if score_result:
                # Fusionner avec données originales
                score_result.update(apartment)
                results.append(score_result)
                
                score_total = score_result.get('score_total', 0)
                tier = score_result.get('tier', 'N/A')
                scores_detaille = score_result.get('scores_detaille', {})
                
                print(f"✅ Score calculé: {score_total}/100 ({tier})")
                print(f"\n📊 SCORES DÉTAILLÉS:")
                for criterion, score_data in scores_detaille.items():
                    if isinstance(score_data, dict):
                        score = score_data.get('score', 0)
                        tier_crit = score_data.get('tier', 'N/A')
                        justification = score_data.get('justification', '')[:80]
                        print(f"   • {criterion}: {score} pts ({tier_crit}) - {justification}")
                    else:
                        print(f"   • {criterion}: {score_data}")
                
                # Vérifier les données après scoring
                print(f"\n📋 DONNÉES APRÈS SCORING:")
                print(f"   ✅ score_total: {score_result.get('score_total')}")
                print(f"   ✅ tier: {score_result.get('tier')}")
                print(f"   ✅ scores_detaille: {len(score_result.get('scores_detaille', {}))} critères")
                print(f"   ✅ Données originales préservées: {score_result.get('id') == apt_id}")
                
            else:
                print(f"❌ Échec du scoring")
                results.append(apartment)
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            results.append(apartment)
    
    # Résumé
    print(f"\n{'='*80}")
    print("📊 RÉSUMÉ DU TEST")
    print(f"{'='*80}")
    print(f"✅ Appartements testés: {len(test_apartments)}")
    print(f"✅ Appartements scorés avec succès: {sum(1 for r in results if 'score_total' in r)}")
    print()
    
    # Vérifier la structure complète
    print("🔍 VÉRIFICATION DE LA STRUCTURE:")
    if results:
        sample = results[0]
        required_fields = ['id', 'score_total', 'tier', 'scores_detaille', 'titre', 'prix', 'localisation']
        for field in required_fields:
            status = "✅" if field in sample else "❌"
            print(f"   {status} {field}: {'Présent' if field in sample else 'MANQUANT'}")
    
    # Sauvegarder les résultats de test
    test_file = 'data/scores/test_5_apartments.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Résultats sauvegardés dans: {test_file}")
    print()
    print("🎉 Test terminé !")

if __name__ == "__main__":
    score_test_5()





