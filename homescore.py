#!/usr/bin/env python3
"""
HomeScore - Orchestrateur central
Charge les données scrapées, calcule les scores, génère le HTML
"""

import json
import os
from scoring import score_all_apartments
from generate_html import generate_html, main as generate_html_main


def load_scraped_apartments():
    """Charge les données scrapées depuis data/scraped_apartments.json"""
    try:
        with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Fichier data/scraped_apartments.json non trouvé")
        return []


def save_scores(scored_apartments):
    """Sauvegarde les scores dans data/scores.json"""
    os.makedirs('data', exist_ok=True)
    with open('data/scores.json', 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, indent=2, ensure_ascii=False)
    print(f"✅ Scores sauvegardés: data/scores.json ({len(scored_apartments)} appartements)")


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
    
    os.makedirs('output', exist_ok=True)
    output_file = 'output/homepage.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML généré: {output_file}")
    
    print("\n🎉 Traitement terminé!")
    print(f"   - {len(scored_apartments)} appartements traités")
    print(f"   - Scores sauvegardés dans data/scores.json")
    print(f"   - HTML généré dans {output_file}")


if __name__ == "__main__":
    main()

