#!/usr/bin/env python3
"""
Test du nouveau système de scoring avec les règles affinées
"""

import json
import os
from datetime import datetime

def test_new_scoring_system():
    """Test le nouveau système de scoring avec les règles affinées"""
    
    print("🎯 TEST DU NOUVEAU SYSTÈME DE SCORING")
    print("=" * 60)
    
    # Charger la configuration
    with open('scoring_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("📋 CONFIGURATION CHARGÉE:")
    for axe, details in config['axes'].items():
        print(f"   {axe.upper()}: {details['poids']} points")
        if 'tiers' in details:
            for tier, tier_details in details['tiers'].items():
                print(f"      {tier}: {tier_details['score']} pts - {tier_details['description']}")
    
    print()
    
    # Charger les données de l'appartement test
    data_file = "data/appartements/90931157.json"
    if not os.path.exists(data_file):
        print("❌ Fichier de données non trouvé")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("🏠 ANALYSE DE L'APPARTEMENT TEST:")
    print(f"   ID: {data['id']}")
    print(f"   Prix: {data['prix']}")
    print(f"   Surface: {data['surface']}")
    print(f"   Localisation: {data['localisation']}")
    print(f"   Étage: {data['caracteristiques']}")
    print()
    
    # Analyser selon les nouveaux critères
    print("🔍 ANALYSE DÉTAILLÉE SELON LES NOUVEAUX CRITÈRES:")
    print()
    
    # 1. LOCALISATION
    print("1️⃣ LOCALISATION (20 pts):")
    localisation = data.get('localisation', '')
    map_info = data.get('map_info', {})
    quartier = map_info.get('quartier', '')
    
    if 'Place des Fêtes' in quartier or 'Jourdain' in quartier or 'Pyrénées' in quartier:
        score_localisation = 20
        tier = "TIER 1"
        justification = "Zone premium identifiée"
    elif '19e' in localisation and 'Buttes-Chaumont' in data.get('description', ''):
        score_localisation = 15
        tier = "TIER 2"
        justification = "19e proche des Buttes-Chaumont"
    elif '19e' in localisation or '20e' in localisation or '10e' in localisation:
        score_localisation = 10
        tier = "TIER 3"
        justification = "Zone correcte"
    else:
        score_localisation = 0
        tier = "ÉLIMINÉ"
        justification = "Zone non éligible"
    
    print(f"   Score: {score_localisation}/20 ({tier})")
    print(f"   Justification: {justification}")
    print()
    
    # 2. PRIX
    print("2️⃣ PRIX (20 pts):")
    prix_text = data.get('prix', '')
    prix_m2_text = data.get('prix_m2', '')
    
    # Extraire le prix au m²
    prix_m2 = 0
    if '€ / m²' in prix_m2_text:
        try:
            prix_m2 = int(''.join(filter(str.isdigit, prix_m2_text.split('€')[0])))
        except:
            pass
    
    if prix_m2 > 0:
        if prix_m2 < 9000:
            score_prix = 20
            tier = "TIER 1"
        elif prix_m2 <= 11000:
            score_prix = 15
            tier = "TIER 2"
        else:
            score_prix = 10
            tier = "TIER 3"
        justification = f"{prix_m2}€/m²"
    else:
        score_prix = 10  # Score par défaut si pas de prix/m²
        tier = "TIER 3"
        justification = "Prix/m² non trouvé"
    
    print(f"   Score: {score_prix}/20 ({tier})")
    print(f"   Justification: {justification}")
    print()
    
    # 3. STYLE
    print("3️⃣ STYLE (20 pts):")
    style_info = data.get('style_haussmannien', {})
    description = data.get('description', '')
    
    if style_info.get('score', 0) > 50 or 'haussmannien' in description.lower():
        score_style = 20
        tier = "TIER 1"
        justification = "Éléments haussmanniens détectés"
    elif 'restauré' in description.lower() or 'contemporain' in description.lower():
        score_style = 15
        tier = "TIER 2"
        justification = "Style correct"
    else:
        score_style = 5
        tier = "TIER 3"
        justification = "Style non spécifique"
    
    print(f"   Score: {score_style}/20 ({tier})")
    print(f"   Justification: {justification}")
    print()
    
    # 4. ENSOLEILLEMENT
    print("4️⃣ ENSOLEILLEMENT (10 pts):")
    if 'lumineux' in description.lower() and 'spacieux' in description.lower():
        score_ensoleillement = 10
        tier = "TIER 1"
        justification = "Lumineux et spacieux mentionnés"
    elif 'lumineux' in description.lower():
        score_ensoleillement = 7
        tier = "TIER 2"
        justification = "Lumineux mentionné"
    else:
        score_ensoleillement = 3
        tier = "TIER 3"
        justification = "Pas d'info sur la luminosité"
    
    print(f"   Score: {score_ensoleillement}/10 ({tier})")
    print(f"   Justification: {justification}")
    print()
    
    # 5. ÉTAGE
    print("5️⃣ ÉTAGE (10 pts):")
    caracteristiques = data.get('caracteristiques', '')
    if '4ème étage' in caracteristiques and 'Ascenseur' in caracteristiques:
        score_etage = 10
        tier = "TIER 1"
        justification = "4e étage avec ascenseur"
    elif '4ème étage' in caracteristiques:
        score_etage = 7
        tier = "TIER 2"
        justification = "4e étage"
    else:
        score_etage = 3
        tier = "TIER 3"
        justification = "Étage non optimal"
    
    print(f"   Score: {score_etage}/10 ({tier})")
    print(f"   Justification: {justification}")
    print()
    
    # 6. SURFACE
    print("6️⃣ SURFACE (5 pts):")
    surface_text = data.get('surface', '')
    surface = 0
    if 'm²' in surface_text:
        try:
            surface = int(''.join(filter(str.isdigit, surface_text.split('m²')[0])))
        except:
            pass
    
    if surface > 80:
        score_surface = 5
        tier = "TIER 1"
    elif surface >= 65:
        score_surface = 3
        tier = "TIER 2"
    else:
        score_surface = 1
        tier = "TIER 3"
    
    print(f"   Score: {score_surface}/5 ({tier})")
    print(f"   Justification: {surface}m²")
    print()
    
    # 7. CUISINE
    print("7️⃣ CUISINE (10 pts):")
    if 'américaine' in description.lower() and 'ouverte' in description.lower():
        score_cuisine = 10
        tier = "TIER 1"
        justification = "Cuisine américaine ouverte"
    elif 'cuisine' in description.lower():
        score_cuisine = 7
        tier = "TIER 2"
        justification = "Cuisine mentionnée"
    else:
        score_cuisine = 3
        tier = "TIER 3"
        justification = "Pas d'info cuisine"
    
    print(f"   Score: {score_cuisine}/10 ({tier})")
    print(f"   Justification: {justification}")
    print()
    
    # 8. VUE
    print("8️⃣ VUE (5 pts):")
    if 'balcon' in caracteristiques.lower() or 'terrasse' in caracteristiques.lower():
        score_vue = 5
        tier = "EXCELLENT"
        justification = "Balcon/terrasse mentionné"
    else:
        score_vue = 3
        tier = "BON"
        justification = "Pas d'info sur la vue"
    
    print(f"   Score: {score_vue}/5 ({tier})")
    print(f"   Justification: {justification}")
    print()
    
    # Calcul du score total
    score_total = (score_localisation + score_prix + score_style + 
                   score_ensoleillement + score_etage + score_surface + 
                   score_cuisine + score_vue)
    
    print("=" * 60)
    print("📊 RÉSULTAT FINAL:")
    print(f"   Score total: {score_total}/100")
    print(f"   Localisation: {score_localisation}/20")
    print(f"   Prix: {score_prix}/20")
    print(f"   Style: {score_style}/20")
    print(f"   Ensoleillement: {score_ensoleillement}/10")
    print(f"   Étage: {score_etage}/10")
    print(f"   Surface: {score_surface}/5")
    print(f"   Cuisine: {score_cuisine}/10")
    print(f"   Vue: {score_vue}/5")
    print()
    
    # Recommandation
    if score_total >= 80:
        recommandation = "🌟 EXCELLENT - Candidat prioritaire"
    elif score_total >= 60:
        recommandation = "✅ BON - Candidat intéressant"
    elif score_total >= 40:
        recommandation = "⚠️ MOYEN - À considérer"
    else:
        recommandation = "❌ FAIBLE - Non recommandé"
    
    print(f"   Recommandation: {recommandation}")
    print("=" * 60)

if __name__ == "__main__":
    test_new_scoring_system()
