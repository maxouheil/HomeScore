#!/usr/bin/env python3
"""
HomeScore v2 - Version API
Orchestrateur central utilisant l'API Jinka au lieu du scraping HTML
Plus rapide, plus stable, plus fiable
"""

import json
import os
from datetime import datetime
from pathlib import Path
from data_loader import load_apartments
from scoring_optimized import score_apartment_optimized, load_scoring_config
from generate_html import generate_html


def save_scores_v2(scored_apartments):
    """Sauvegarde les scores dans data/scores_v2/"""
    scores_dir = Path('data/scores_v2')
    scores_dir.mkdir(exist_ok=True)
    
    # Sauvegarder dans scores.json (format principal)
    scores_file = scores_dir / 'scores.json'
    with open(scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, indent=2, ensure_ascii=False)
    print(f"✅ Scores sauvegardés: {scores_file} ({len(scored_apartments)} appartements)")
    
    # AUSSI sauvegarder dans all_apartments_scores.json (compatibilité)
    all_scores_file = scores_dir / 'all_apartments_scores.json'
    with open(all_scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, indent=2, ensure_ascii=False)
    print(f"✅ Scores sauvegardés: {all_scores_file} ({len(scored_apartments)} appartements)")


def save_scraped_data_v2(apartments):
    """Sauvegarde les données scrapées dans data/scraped_apartments_v2.json"""
    data_file = Path('data/scraped_apartments_v2.json')
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, indent=2, ensure_ascii=False)
    print(f"✅ Données sauvegardées: {data_file} ({len(apartments)} appartements)")


def main():
    """Fonction principale - Orchestration complète v2"""
    print("🏠 HomeScore v2 - Version API")
    print("=" * 60)
    print("📡 Utilise l'API Jinka (plus rapide et stable)")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Phase 1: Charger les données depuis API
    print("\n📥 Phase 1: Chargement des données depuis l'API...")
    apartments = load_apartments(prefer_api=True)
    
    if not apartments:
        print("❌ Aucune donnée trouvée")
        print("💡 Exécutez d'abord: python scrape_with_api.py")
        return
    
    print(f"✅ {len(apartments)} appartements chargés")
    
    # Sauvegarder les données dans le format v2
    save_scraped_data_v2(apartments)
    
    # Phase 2: Calculer les scores avec analyseur unifié
    print("\n📊 Phase 2: Calcul des scores (analyse IA unifiée)...")
    config = load_scoring_config()
    if not config:
        print("❌ Erreur chargement config scoring")
        return
    
    scored_apartments = []
    for i, apartment in enumerate(apartments, 1):
        print(f"\n🏠 Appartement {i}/{len(apartments)}: {apartment.get('id', 'N/A')}")
        score_result = score_apartment_optimized(apartment, config)
        if score_result:
            # Fusionner avec données originales
            score_result.update(apartment)
            scored_apartments.append(score_result)
    
    if not scored_apartments:
        print("❌ Erreur lors du calcul des scores")
        return
    
    print(f"\n✅ {len(scored_apartments)} appartements scorés")
    
    # Phase 3: Sauvegarder les scores
    print("\n💾 Phase 3: Sauvegarde des scores...")
    save_scores_v2(scored_apartments)
    
    # Phase 4: Générer le HTML
    print("\n📄 Phase 4: Génération du HTML...")
    html = generate_html(scored_apartments)
    
    output_dir = Path('output/v2')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'homepage.html'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML généré: {output_file}")
    
    # Statistiques finales
    elapsed_time = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("🎉 TRAITEMENT TERMINÉ (v2)")
    print("=" * 60)
    print(f"   ⏱️  Temps total: {elapsed_time:.1f} secondes")
    print(f"   🏠 Appartements traités: {len(scored_apartments)}")
    print(f"   💾 Scores: data/scores_v2/scores.json")
    print(f"   📄 HTML: {output_file}")
    print(f"   📡 Source: API Jinka")
    print("=" * 60)


if __name__ == "__main__":
    main()

