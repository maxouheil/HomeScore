#!/usr/bin/env python3
"""
Test du scoring avec critère calme sur tous les appartements de l'alerte "Sou & Delphine Apparte"
"""

import json
import os
import sys
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scoring import score_apartment, load_scoring_config
from alert_scoring import filter_apartments_by_alert
from backend.api.apartments import load_apartments_data


def load_alert_by_name(alert_name):
    """Charge une alerte par son nom"""
    alerts_dir = "data/alerts"
    if not os.path.exists(alerts_dir):
        print(f"❌ Dossier {alerts_dir} non trouvé")
        return None
    
    for filename in os.listdir(alerts_dir):
        if filename.endswith('.json'):
            alert_path = os.path.join(alerts_dir, filename)
            try:
                with open(alert_path, 'r', encoding='utf-8') as f:
                    alert = json.load(f)
                    if alert.get('name') == alert_name:
                        return alert
            except Exception as e:
                print(f"⚠️ Erreur chargement {filename}: {e}")
    
    return None


def test_alert_calme():
    """Test le scoring avec critère calme sur tous les appartements de l'alerte"""
    print("🧪 TEST DU CRITÈRE CALME SUR L'ALERTE 'Sou & Delphine Apparte'")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Charger la config de scoring
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Charger l'alerte
    alert_name = "Sou & Delphine Apparte"
    print(f"📋 Recherche de l'alerte: {alert_name}...")
    alert = load_alert_by_name(alert_name)
    
    if not alert:
        print(f"❌ Alerte '{alert_name}' non trouvée")
        return
    
    print(f"✅ Alerte trouvée: {alert.get('name')}")
    print(f"   ID: {alert.get('id')}")
    print()
    
    # Afficher les critères de l'alerte
    criteria = alert.get('criteria', {})
    primary = criteria.get('primary', [])
    secondary = criteria.get('secondary', [])
    all_criteria = criteria.get('all', [])
    
    print("📊 Critères de l'alerte:")
    if all_criteria:
        print(f"   Tous les critères (5): {all_criteria}")
    else:
        print(f"   Principaux: {primary}")
        print(f"   Secondaires: {secondary}")
    print()
    
    # Charger tous les appartements
    print("📂 Chargement de tous les appartements...")
    try:
        all_apartments = load_apartments_data()
        print(f"✅ {len(all_apartments)} appartements chargés")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Filtrer selon les critères de l'alerte
    print("\n🔍 Filtrage des appartements selon l'alerte...")
    try:
        filtered_apartments = filter_apartments_by_alert(all_apartments, alert)
        print(f"✅ {len(filtered_apartments)} appartements correspondent aux critères")
    except Exception as e:
        print(f"❌ Erreur lors du filtrage: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not filtered_apartments:
        print("⚠️ Aucun appartement ne correspond aux critères de l'alerte")
        return
    
    print()
    print("🏠 SCORING DES APPARTEMENTS AVEC CRITÈRE CALME")
    print("=" * 80)
    
    # Scorer chaque appartement avec le critère calme
    scored_results = []
    apartments_with_coords = 0
    apartments_without_coords = 0
    apartments_with_calme = 0
    apartments_without_calme = 0
    
    for i, apartment in enumerate(filtered_apartments, 1):
        apt_id = apartment.get('id', 'N/A')
        localisation = apartment.get('localisation', 'N/A')
        
        # Vérifier les coordonnées
        coordinates = apartment.get('coordinates', {})
        has_coords = bool(coordinates.get('latitude') and coordinates.get('longitude'))
        
        if has_coords:
            apartments_with_coords += 1
        else:
            apartments_without_coords += 1
        
        try:
            # Scorer l'appartement (inclut maintenant le critère calme)
            score_result = score_apartment(apartment, config)
            
            if score_result:
                # Vérifier si le critère calme a été calculé
                calme_score = score_result.get('scores_detaille', {}).get('calme', {})
                has_calme = bool(calme_score and calme_score.get('score') is not None)
                
                if has_calme:
                    apartments_with_calme += 1
                else:
                    apartments_without_calme += 1
                
                score_total = score_result.get('score_total', 0)
                tier = score_result.get('tier', 'N/A')
                calme_pts = calme_score.get('score', 'N/A') if calme_score else 'N/A'
                calme_tier = calme_score.get('tier', 'N/A') if calme_score else 'N/A'
                calme_justification = calme_score.get('justification', 'N/A')[:80] if calme_score else 'N/A'
                
                result = {
                    'apartment': apartment,
                    'score_result': score_result,
                    'calme_score': calme_score,
                    'has_coords': has_coords,
                    'has_calme': has_calme
                }
                scored_results.append(result)
                
                print(f"[{i}/{len(filtered_apartments)}] ✅ {apt_id}")
                print(f"   Localisation: {localisation}")
                print(f"   Score total: {score_total}/100 ({tier})")
                print(f"   Calme: {calme_pts}pts ({calme_tier})")
                print(f"   Justification: {calme_justification}")
                print()
            else:
                print(f"[{i}/{len(filtered_apartments)}] ⚠️  {apt_id}: Échec scoring")
                print()
        
        except Exception as e:
            print(f"[{i}/{len(filtered_apartments)}] ❌ {apt_id}: Erreur - {str(e)[:50]}")
            print()
    
    # Statistiques finales
    print("=" * 80)
    print("📊 STATISTIQUES FINALES")
    print("=" * 80)
    print(f"📋 Total appartements filtrés: {len(filtered_apartments)}")
    print(f"📍 Avec coordonnées: {apartments_with_coords}")
    print(f"⚠️  Sans coordonnées: {apartments_without_coords}")
    print()
    print(f"✅ Avec critère calme calculé: {apartments_with_calme}")
    print(f"⚠️  Sans critère calme: {apartments_without_calme}")
    print()
    
    # Statistiques sur les scores calme
    calme_stats = {
        'tier1': 0,
        'tier2': 0,
        'tier3': 0
    }
    
    for result in scored_results:
        if result['has_calme']:
            calme_score = result['calme_score']
            tier = calme_score.get('tier', '')
            if tier == 'tier1':
                calme_stats['tier1'] += 1
            elif tier == 'tier2':
                calme_stats['tier2'] += 1
            elif tier == 'tier3':
                calme_stats['tier3'] += 1
    
    print("📊 DISTRIBUTION DES SCORES CALME")
    print(f"   🟢 Tier1 (très calme): {calme_stats['tier1']}")
    print(f"   🟡 Tier2 (moyen): {calme_stats['tier2']}")
    print(f"   🔴 Tier3 (animé): {calme_stats['tier3']}")
    print()
    
    # Top 5 appartements par score calme
    print("🏆 TOP 5 APPARTEMENTS PAR SCORE CALME")
    print("-" * 80)
    
    # Trier par score calme (tier1 > tier2 > tier3)
    def calme_sort_key(result):
        if not result['has_calme']:
            return (3, 0)  # Sans calme en dernier
        tier = result['calme_score'].get('tier', 'tier3')
        score = result['calme_score'].get('score', 0)
        tier_order = {'tier1': 0, 'tier2': 1, 'tier3': 2}.get(tier, 2)
        return (tier_order, -score)  # Négatif pour tri décroissant
    
    sorted_results = sorted(scored_results, key=calme_sort_key)
    
    for i, result in enumerate(sorted_results[:5], 1):
        apt = result['apartment']
        calme_score = result['calme_score']
        apt_id = apt.get('id', 'N/A')
        localisation = apt.get('localisation', 'N/A')
        score_total = result['score_result'].get('score_total', 0)
        calme_pts = calme_score.get('score', 'N/A') if result['has_calme'] else 'N/A'
        calme_tier = calme_score.get('tier', 'N/A') if result['has_calme'] else 'N/A'
        calme_justification = calme_score.get('justification', 'N/A')[:100] if result['has_calme'] else 'N/A'
        
        print(f"{i}. {apt_id}")
        print(f"   Localisation: {localisation}")
        print(f"   Score total: {score_total}/100")
        print(f"   Calme: {calme_pts}pts ({calme_tier})")
        print(f"   {calme_justification}")
        print()
    
    print("=" * 80)
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ Test terminé avec succès !")


if __name__ == "__main__":
    test_alert_calme()


