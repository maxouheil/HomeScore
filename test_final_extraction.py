#!/usr/bin/env python3
"""
Test final de l'extraction des données avec toutes les améliorations
"""

import json
import os

def test_extraction_results():
    """Teste les résultats de l'extraction"""
    
    print("🔍 TEST FINAL DE L'EXTRACTION DES DONNÉES")
    print("=" * 60)
    
    # Charger les données scrapées
    data_file = "data/appartements/90931157.json"
    if not os.path.exists(data_file):
        print("❌ Fichier de données non trouvé")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 Données extraites pour l'appartement {data['id']}")
    print(f"🕒 Scrapé le: {data['scraped_at']}")
    print()
    
    # Test des données faciles
    print("✅ DONNÉES FACILES:")
    print(f"   💰 Prix: {data['prix']}")
    print(f"   📐 Surface: {data['surface']}")
    print(f"   🏢 Étage: {data['caracteristiques']}")
    print()
    
    # Test des données semi-faciles
    print("⚠️  DONNÉES SEMI-FACILES:")
    print(f"   📍 Localisation: {data['localisation']}")
    
    # Coordonnées GPS
    coords = data.get('coordinates', {})
    if coords.get('latitude') and coords.get('longitude'):
        print(f"   🗺️  Coordonnées GPS: {coords['latitude']}, {coords['longitude']}")
    else:
        print(f"   🗺️  Coordonnées GPS: Non trouvées ({coords.get('error', 'N/A')})")
    
    # Style haussmannien
    style = data.get('style_haussmannien', {})
    if style:
        print(f"   🏛️  Style haussmannien: {style['score']}/100")
        if style['elements']:
            for category, keywords in style['elements'].items():
                print(f"      {category.title()}: {', '.join(keywords)}")
    print()
    
    # Test des données bonus
    print("🎁 DONNÉES BONUS:")
    print(f"   🏠 Pièces: {data['pieces']}")
    print(f"   🍳 Cuisine: {'Américaine ouverte' if 'américaine' in data['description'].lower() else 'Type non spécifié'}")
    print(f"   ☀️ Luminosité: {'Lumineux' if 'lumineux' in data['description'].lower() else 'Non spécifié'}")
    print(f"   📏 Espace: {'Spacieux' if 'spacieux' in data['description'].lower() else 'Non spécifié'}")
    print()
    
    # Test de la description
    print("📝 DESCRIPTION:")
    desc = data.get('description', '')
    print(f"   Longueur: {len(desc)} caractères")
    print(f"   Extrait: {desc[:150]}...")
    print()
    
    # Test des caractéristiques
    print("🏠 CARACTÉRISTIQUES:")
    carac = data.get('caracteristiques', '')
    print(f"   {carac}")
    print()
    
    # Résumé du scoring
    print("📊 RÉSUMÉ DU SCORING:")
    style_score = style.get('score', 0)
    print(f"   Style haussmannien: {style_score}/100")
    
    # Calculer un score global approximatif
    prix_text = data.get('prix', '')
    prix_value = 0
    if '€' in prix_text:
        try:
            prix_value = int(''.join(filter(str.isdigit, prix_text)))
        except:
            pass
    
    # Score approximatif basé sur les données disponibles
    score_prix = min(20, max(0, 20 - (prix_value - 500000) // 50000)) if prix_value > 0 else 10
    score_localisation = 15 if 'Paris' in data.get('localisation', '') else 5
    score_surface = 15 if '70' in data.get('surface', '') else 10
    score_style = min(20, style_score // 5)
    
    score_total = score_prix + score_localisation + score_surface + score_style
    print(f"   Score approximatif: {score_total}/100")
    print(f"      - Prix: {score_prix}/20")
    print(f"      - Localisation: {score_localisation}/20") 
    print(f"      - Surface: {score_surface}/20")
    print(f"      - Style: {score_style}/20")
    print()
    
    print("✅ Test d'extraction terminé avec succès !")

if __name__ == "__main__":
    test_extraction_results()
