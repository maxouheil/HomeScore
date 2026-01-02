#!/usr/bin/env python3
"""
Script pour tester le nouveau système batch sur 20 appartements du 20e arrondissement
Écrase les scores précédents pour forcer la ré-analyse avec le nouveau système
"""

import json
import os
from datetime import datetime
from analyze_apartment_style import ApartmentStyleAnalyzer
from scoring import score_apartment, load_scoring_config


def load_apartments():
    """Charge tous les appartements depuis scraped_apartments.json ou all_apartments_scores.json"""
    # Priorité 1: all_apartments_scores.json (contient déjà les scores)
    scores_file = 'data/scores/all_apartments_scores.json'
    if os.path.exists(scores_file):
        print(f"📂 Chargement depuis {scores_file}...")
        with open(scores_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        print(f"✅ {len(apartments)} appartements chargés depuis scores existants")
        return apartments
    
    # Priorité 2: scraped_apartments.json
    scraped_file = 'data/scraped_apartments.json'
    if os.path.exists(scraped_file):
        print(f"📂 Chargement depuis {scraped_file}...")
        with open(scraped_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        print(f"✅ {len(apartments)} appartements chargés depuis données scrapées")
        return apartments
    
    print("❌ Aucun fichier d'appartements trouvé")
    return []


def filter_20e_arrondissement(apartments):
    """Filtre les appartements du 20e arrondissement"""
    filtered = []
    
    for apt in apartments:
        localisation = str(apt.get('localisation', '')).lower()
        map_info = apt.get('map_info', {}) or {}
        quartier = str(map_info.get('quartier', '')).lower()
        
        # Chercher des indices du 20e arrondissement
        indicators = ['20e', '20ème', '75020', '20e arrondissement', '20ème arrondissement']
        
        found = False
        for indicator in indicators:
            if indicator in localisation or indicator in quartier:
                found = True
                break
        
        # Vérifier aussi dans les métros (certains appartements peuvent être près de métros du 20e)
        metros = map_info.get('metros', []) or []
        for metro in metros:
            metro_str = str(metro).lower()
            # Métros typiques du 20e
            if any(m in metro_str for m in ['gambetta', 'père lachaise', 'ménilmontant', 'belleville', 'nation']):
                found = True
                break
        
        if found:
            filtered.append(apt)
    
    return filtered


def save_scores(scored_apartments, all_apartments):
    """Sauvegarde les scores en écrasant les anciens scores pour ces appartements"""
    os.makedirs('data/scores', exist_ok=True)
    scores_file = 'data/scores/all_apartments_scores.json'
    
    # Créer un dictionnaire pour faciliter la mise à jour
    scored_dict = {apt['id']: apt for apt in scored_apartments}
    
    # Charger tous les scores existants
    if os.path.exists(scores_file):
        with open(scores_file, 'r', encoding='utf-8') as f:
            all_scores = json.load(f)
    else:
        all_scores = []
    
    # Créer un dictionnaire des scores existants
    existing_scores_dict = {apt['id']: apt for apt in all_scores}
    
    # Mettre à jour ou ajouter les nouveaux scores
    for apt_id, scored_apt in scored_dict.items():
        existing_scores_dict[apt_id] = scored_apt
    
    # Reconvertir en liste
    updated_scores = list(existing_scores_dict.values())
    
    # Sauvegarder
    with open(scores_file, 'w', encoding='utf-8') as f:
        json.dump(updated_scores, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Scores sauvegardés dans {scores_file}")
    print(f"   {len(scored_apartments)} appartements mis à jour")


def test_batch_20e():
    """Teste le nouveau système batch sur 20 appartements du 20e"""
    print("🚀 TEST DU NOUVEAU SYSTÈME BATCH SUR 20 APPARTEMENTS DU 20E")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Charger tous les appartements
    print("📂 Chargement des appartements...")
    all_apartments = load_apartments()
    
    if not all_apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"✅ {len(all_apartments)} appartements chargés")
    print()
    
    # Filtrer les appartements du 20e
    print("🔍 Filtrage des appartements du 20e arrondissement...")
    apartments_20e = filter_20e_arrondissement(all_apartments)
    
    if not apartments_20e:
        print("❌ Aucun appartement du 20e trouvé")
        return
    
    print(f"✅ {len(apartments_20e)} appartements du 20e trouvés")
    
    # Prendre les 20 premiers
    apartments_to_test = apartments_20e[:20]
    print(f"📋 Test sur {len(apartments_to_test)} appartements")
    print()
    
    # Initialiser l'analyseur de style
    style_analyzer = ApartmentStyleAnalyzer()
    
    scored_apartments = []
    
    for i, apartment in enumerate(apartments_to_test, 1):
        apt_id = apartment.get('id', 'N/A')
        localisation = apartment.get('localisation', 'N/A')
        prix = apartment.get('prix', 'N/A')
        
        print(f"🏠 APPARTEMENT {i}/{len(apartments_to_test)}")
        print(f"   ID: {apt_id}")
        print(f"   Localisation: {localisation}")
        print(f"   Prix: {prix}")
        print("   " + "-" * 70)
        
        try:
            # SUPPRIMER style_analysis pour forcer la ré-analyse avec le nouveau système batch
            if 'style_analysis' in apartment:
                del apartment['style_analysis']
                print("   🗑️  style_analysis supprimé (forçage ré-analyse)")
            
            # Analyser avec le nouveau système batch (va analyser tous les critères en une fois)
            print("   📸 Analyse batch des photos (style, cuisine, luminosité, baignoire, vis-à-vis, taille salon)...")
            style_analysis = style_analyzer.analyze_apartment_photos_from_data(apartment)
            
            if style_analysis:
                apartment['style_analysis'] = style_analysis
                print(f"   ✅ Analyse batch réussie")
                print(f"      Style: {style_analysis.get('style', {}).get('type', 'N/A')}")
                print(f"      Cuisine: {'Ouverte' if style_analysis.get('cuisine', {}).get('ouverte') else 'Fermée'}")
                print(f"      Luminosité: {style_analysis.get('luminosite', {}).get('type', 'N/A')}")
                
                # Afficher les nouveaux critères si présents
                if style_analysis.get('baignoire'):
                    baignoire_data = style_analysis['baignoire']
                    print(f"      Baignoire: {'Oui' if baignoire_data.get('has_baignoire') else ('Douche' if baignoire_data.get('has_douche') else 'N/A')}")
                
                if style_analysis.get('visavis'):
                    visavis_data = style_analysis['visavis']
                    distance = visavis_data.get('distance')
                    if distance:
                        print(f"      Vis-à-vis: {distance}m ({visavis_data.get('category', 'N/A')})")
                
                if style_analysis.get('salon_size'):
                    salon_data = style_analysis['salon_size']
                    estimate = salon_data.get('estimate')
                    if estimate:
                        print(f"      Taille salon: {estimate}m² ({salon_data.get('category', 'N/A')})")
            else:
                print("   ⚠️  Analyse batch échouée (pas de photos?)")
            
            # Scorer l'appartement
            print("   🎯 Scoring de l'appartement...")
            score_result = score_apartment(apartment, config)
            
            if score_result:
                # Fusionner avec données originales
                score_result.update(apartment)
                scored_apartments.append(score_result)
                
                print(f"   ✅ Score total: {score_result.get('score_total', 'N/A')}/100")
                print(f"   📊 Tier: {score_result.get('tier', 'N/A')}")
            else:
                print("   ❌ Échec du scoring")
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Sauvegarder les scores (écrase les anciens pour ces appartements)
    print("💾 Sauvegarde des scores...")
    save_scores(scored_apartments, all_apartments)
    
    print()
    print("📊 RÉSULTATS FINAUX")
    print("=" * 80)
    print(f"✅ Appartements analysés et scorés: {len(scored_apartments)}/{len(apartments_to_test)}")
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Afficher un résumé des scores
    if scored_apartments:
        scores = [apt.get('score_total', 0) for apt in scored_apartments]
        print(f"\n📈 Statistiques des scores:")
        print(f"   Moyenne: {sum(scores) / len(scores):.1f}/100")
        print(f"   Min: {min(scores)}/100")
        print(f"   Max: {max(scores)}/100")
        
        # Compter par tier
        tiers = {}
        for apt in scored_apartments:
            tier = apt.get('tier', 'unknown')
            tiers[tier] = tiers.get(tier, 0) + 1
        
        print(f"\n🏆 Répartition par tier:")
        for tier, count in sorted(tiers.items()):
            print(f"   {tier}: {count}")


if __name__ == "__main__":
    test_batch_20e()


