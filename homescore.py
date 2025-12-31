#!/usr/bin/env python3
"""
HomeScore - Orchestrateur central
Charge les données scrapées, calcule les scores, génère le HTML
"""

import json
import os
from scoring import score_all_apartments
from generate_html import generate_html, main as generate_html_main
from project_config import DATA_DIR, SCORES_DIR, OUTPUT_DIR


def load_scraped_apartments():
    """Charge les données scrapées depuis data/scraped_apartments.json"""
    try:
        scraped_file = DATA_DIR / 'scraped_apartments.json'
        with open(scraped_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Fichier {DATA_DIR / 'scraped_apartments.json'} non trouvé")
        return []


def save_scores(scored_apartments):
    """Sauvegarde les scores dans data/scores.json ET all_apartments_scores.json"""
    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder dans scores.json (nouveau format)
    scores_file = SCORES_DIR / 'scores.json'
    with open(scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, indent=2, ensure_ascii=False)
    print(f"✅ Scores sauvegardés: {scores_file} ({len(scored_apartments)} appartements)")
    
    # AUSSI sauvegarder dans all_apartments_scores.json (format utilisé par generate_scorecard_html.py)
    from project_config import APARTMENTS_FILE
    with open(APARTMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, indent=2, ensure_ascii=False)
    print(f"✅ Scores sauvegardés: {APARTMENTS_FILE} ({len(scored_apartments)} appartements)")


def main():
    """Fonction principale - Orchestration complète"""
    print("🏠 HomeScore - Orchestrateur central")
    print("=" * 50)
    
    # Phase 1: Charger les données scrapées
    print("\n📥 Phase 1: Chargement des données scrapées...")
    scraped_apartments = load_scraped_apartments()
    if not scraped_apartments:
        print("❌ Aucune donnée scrapée trouvée")
        return
    
    print(f"✅ {len(scraped_apartments)} appartements chargés")
    
    # Phase 2: Calculer les scores (règles simples, pas d'IA)
    print("\n📊 Phase 2: Calcul des scores...")
    scored_apartments = score_all_apartments(scraped_apartments)
    if not scored_apartments:
        print("❌ Erreur lors du calcul des scores")
        return
    
    print(f"✅ {len(scored_apartments)} appartements scorés")
    
    # Phase 3: Sauvegarder les scores
    print("\n💾 Phase 3: Sauvegarde des scores...")
    save_scores(scored_apartments)
    
    # Phase 4: Générer le HTML
    print("\n📄 Phase 4: Génération du HTML...")
    html = generate_html(scored_apartments)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / 'homepage.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML généré: {output_file}")
    
    print("\n🎉 Traitement terminé!")
    print(f"   - {len(scored_apartments)} appartements traités")
    print(f"   - Scores sauvegardés dans data/scores.json")
    print(f"   - HTML généré dans {output_file}")


if __name__ == "__main__":
    main()

