#!/usr/bin/env python3
"""
Script pour scorer les 7 appartements scrapés en batch
"""

import asyncio
import json
import os
from datetime import datetime
from score_appartement import ApartmentScorer
from generate_html_report import generate_html_report

async def score_batch_apartments():
    """Score les 7 appartements scrapés"""
    print("🏠 SCORING DES 7 APPARTEMENTS SCRAPÉS")
    print("=" * 60)
    
    # Charger les données scrapées
    data_file = "data/batch_scraped_apartments.json"
    if not os.path.exists(data_file):
        print(f"❌ Fichier {data_file} non trouvé")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        apartments_data = json.load(f)
    
    print(f"📋 {len(apartments_data)} appartements trouvés")
    print()
    
    # Initialiser le scorer
    scorer = ApartmentScorer()
    
    # Créer le répertoire de sortie
    os.makedirs("data/scores", exist_ok=True)
    
    scored_apartments = []
    
    for i, apartment in enumerate(apartments_data, 1):
        print(f"🏠 SCORING APPARTEMENT {i}/{len(apartments_data)}")
        print(f"   ID: {apartment.get('id', 'N/A')}")
        print(f"   Localisation: {apartment.get('localisation', 'N/A')}")
        print(f"   Prix: {apartment.get('prix', 'N/A')}")
        print(f"   Surface: {apartment.get('surface', 'N/A')}")
        print("   " + "-" * 50)
        
        try:
            # Score l'appartement
            score_result = await scorer.score_apartment(apartment)
            
            if score_result:
                print(f"   ✅ Score: {score_result['score_total']}/100")
                print(f"   📊 Tier: {score_result.get('tier', 'N/A')}")
                print(f"   🎯 Recommandation: {score_result.get('recommandation', 'N/A')}")
                
                # Ajouter les données originales au résultat
                score_result.update(apartment)
                scored_apartments.append(score_result)
                
                # Sauvegarder individuellement
                score_file = f"data/scores/apartment_{apartment.get('id', i)}_score.json"
                with open(score_file, 'w', encoding='utf-8') as f:
                    json.dump(score_result, f, ensure_ascii=False, indent=2)
                
            else:
                print(f"   ❌ Échec du scoring")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print()
    
    # Sauvegarder tous les scores
    all_scores_file = "data/scores/all_apartments_scores.json"
    with open(all_scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, ensure_ascii=False, indent=2)
    
    print("📊 RÉSULTATS FINAUX")
    print("=" * 60)
    print(f"✅ Appartements scorés: {len(scored_apartments)}")
    print(f"💾 Scores sauvegardés: {all_scores_file}")
    print()
    
    # Afficher le classement
    if scored_apartments:
        print("🏆 CLASSEMENT PAR SCORE")
        print("-" * 40)
        sorted_apartments = sorted(scored_apartments, key=lambda x: x.get('score_total', 0), reverse=True)
        
        for i, apt in enumerate(sorted_apartments, 1):
            score = apt.get('score_total', 0)
            tier = apt.get('tier', 'N/A')
            loc = apt.get('localisation', 'N/A')
            prix = apt.get('prix', 'N/A')
            surface = apt.get('surface', 'N/A')
            
            print(f"{i:2d}. {score:2d}/100 - {tier:12s} - {loc} - {prix} - {surface}")
    
    print()
    
    # Générer le rapport HTML
    print("📊 GÉNÉRATION DU RAPPORT HTML")
    print("-" * 40)
    
    try:
        report_file = generate_html_report(scored_apartments)
        print(f"✅ Rapport généré: {report_file}")
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")
    
    print()
    print("🎉 SCORING TERMINÉ !")
    print(f"   📊 {len(scored_apartments)} appartements scorés")
    print(f"   📁 Données: {all_scores_file}")
    print(f"   🌐 Rapport: output/rapport_appartements.html")

if __name__ == "__main__":
    asyncio.run(score_batch_apartments())
