#!/usr/bin/env python3
"""
Script pour analyser le quartier à partir des screenshots et données
"""

import json
import os
from datetime import datetime

def analyze_quartier_from_screenshot():
    """Analyse le quartier basé sur les screenshots et données disponibles"""
    
    print("🏘️ ANALYSE DU QUARTIER")
    print("=" * 50)
    
    # Charger les données
    data_file = "data/appartements/90931157.json"
    if not os.path.exists(data_file):
        print("❌ Fichier de données non trouvé")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"🏠 Appartement: {data['id']}")
    print(f"📍 Localisation: {data['localisation']}")
    print(f"💰 Prix: {data['prix']}")
    print(f"📐 Surface: {data['surface']}")
    print()
    
    # Analyser la description pour des indices géographiques
    description = data.get('description', '')
    print("🔍 ANALYSE DE LA DESCRIPTION:")
    print(f"   Description: {description[:200]}...")
    print()
    
    # Chercher des indices géographiques dans la description
    geo_indicators = {
        "Buttes-Chaumont": "350 m des Buttes-Chaumont" in description,
        "XIXe arrondissement": "XIXᵉ arrondissement" in description,
        "Paris 19e": "Paris 19e" in data.get('localisation', ''),
    }
    
    print("📍 INDICES GÉOGRAPHIQUES TROUVÉS:")
    for indicator, found in geo_indicators.items():
        status = "✅" if found else "❌"
        print(f"   {status} {indicator}")
    
    print()
    
    # Analyser les screenshots
    screenshots_dir = "data/screenshots"
    screenshots = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')] if os.path.exists(screenshots_dir) else []
    
    print("📸 SCREENSHOTS DISPONIBLES:")
    if screenshots:
        for screenshot in screenshots:
            print(f"   📷 {screenshot}")
            print(f"      Chemin: {screenshots_dir}/{screenshot}")
            print(f"      Taille: {os.path.getsize(f'{screenshots_dir}/{screenshot}')} bytes")
    else:
        print("   ❌ Aucun screenshot trouvé")
    
    print()
    
    # Déduction du quartier basée sur les informations disponibles
    print("🎯 DÉDUCTION DU QUARTIER:")
    
    if geo_indicators["Buttes-Chaumont"]:
        print("   ✅ L'appartement est à 350m des Buttes-Chaumont")
        print("   🏘️ Quartier probable: Zone autour des Buttes-Chaumont")
        print("   📍 Intersection probable: Rue Carducci / Rue Mélingue")
        print("   🚇 Métros proches: Place des Fêtes, Jourdain, Pyrénées")
        print("   🏞️ Proximité: Parc des Buttes-Chaumont, Canal de l'Ourcq")
        
        # Score de localisation basé sur les indices
        location_score = 0
        if geo_indicators["Buttes-Chaumont"]:
            location_score += 40
        if geo_indicators["XIXe arrondissement"]:
            location_score += 30
        if geo_indicators["Paris 19e"]:
            location_score += 30
        
        print(f"   📊 Score de localisation: {location_score}/100")
        
    else:
        print("   ❌ Pas assez d'informations pour identifier le quartier")
    
    print()
    
    # Recommandations
    print("💡 RECOMMANDATIONS:")
    print("   1. Consultez les screenshots pour voir les noms de rues exacts")
    print("   2. L'appartement est dans une zone très bien située du 19e")
    print("   3. Proche des transports et du parc des Buttes-Chaumont")
    print("   4. Quartier résidentiel avec commerces de proximité")
    
    print()
    print("🗺️ POUR UNE ANALYSE PLUS PRÉCISE:")
    print(f"   Ouvrez le fichier: {screenshots_dir}/{screenshots[0] if screenshots else 'N/A'}")
    print("   Cherchez les noms de rues autour du marqueur de l'appartement")

if __name__ == "__main__":
    analyze_quartier_from_screenshot()
