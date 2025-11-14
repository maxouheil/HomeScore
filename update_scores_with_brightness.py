#!/usr/bin/env python3
"""
Met à jour les scores existants avec les nouvelles données d'exposition contenant brightness_value
"""

import json
import os

def update_scores_with_brightness():
    """Met à jour les scores avec les nouvelles données d'exposition"""
    
    print("🔄 MISE À JOUR DES SCORES AVEC LA LUMINOSITÉ IMAGE")
    print("=" * 70)
    
    # Charger les données scrapées
    try:
        with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
            scraped_apartments = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier scraped_apartments.json non trouvé")
        return
    
    # Charger les scores
    try:
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            scored_apartments = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier all_apartments_scores.json non trouvé")
        return
    
    print(f"📊 {len(scraped_apartments)} appartements scrapés")
    print(f"📊 {len(scored_apartments)} appartements scorés")
    print()
    
    # Créer un dictionnaire pour accès rapide
    scraped_dict = {str(apt.get('id')): apt for apt in scraped_apartments}
    
    updated_count = 0
    
    for apt in scored_apartments:
        apt_id = str(apt.get('id'))
        scraped_apt = scraped_dict.get(apt_id)
        
        if not scraped_apt:
            continue
        
        # Mettre à jour l'exposition depuis les données scrapées
        scraped_expo = scraped_apt.get('exposition', {})
        scraped_expo_details = scraped_expo.get('details', {})
        
        if scraped_expo_details.get('brightness_value') is not None:
            # Mettre à jour l'exposition dans les scores
            if 'exposition' not in apt:
                apt['exposition'] = {}
            
            # Conserver les scores existants mais mettre à jour les détails
            if 'details' not in apt['exposition']:
                apt['exposition']['details'] = {}
            
            # Ajouter brightness_value aux détails
            apt['exposition']['details']['brightness_value'] = scraped_expo_details.get('brightness_value')
            apt['exposition']['details']['image_brightness'] = scraped_expo_details.get('image_brightness')
            
            # Mettre à jour aussi l'exposition principale si nécessaire
            if scraped_expo.get('exposition'):
                apt['exposition']['exposition'] = scraped_expo.get('exposition')
            
            updated_count += 1
            print(f"✅ {apt_id}: brightness_value = {scraped_expo_details.get('brightness_value'):.2f}")
    
    # Sauvegarder les scores mis à jour
    print()
    print(f"💾 Sauvegarde des scores mis à jour...")
    os.makedirs("data/scores", exist_ok=True)
    
    with open('data/scores/all_apartments_scores.json', 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, ensure_ascii=False, indent=2)
    
    print()
    print("📊 RÉSULTATS")
    print("=" * 70)
    print(f"✅ Appartements mis à jour: {updated_count}/{len(scored_apartments)}")
    print(f"💾 Fichier sauvegardé: data/scores/all_apartments_scores.json")

if __name__ == "__main__":
    update_scores_with_brightness()






