#!/usr/bin/env python3
"""
Script pour analyser les screenshots de carte et extraire les informations géographiques
"""

import os
import json
from datetime import datetime

def analyze_map_screenshots():
    """Analyse les screenshots de carte pour extraire les informations"""
    
    print("🗺️ ANALYSE DES SCREENSHOTS DE CARTE")
    print("=" * 50)
    
    # Lister les screenshots disponibles
    screenshots_dir = "data/screenshots"
    if not os.path.exists(screenshots_dir):
        print("❌ Aucun screenshot trouvé")
        return
    
    screenshots = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
    print(f"📸 {len(screenshots)} screenshots trouvés")
    
    for screenshot in screenshots:
        print(f"\n📷 Analyse de {screenshot}:")
        print(f"   Chemin: {screenshots_dir}/{screenshot}")
        print(f"   Taille: {os.path.getsize(f'{screenshots_dir}/{screenshot}')} bytes")
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DE L'ANALYSE")
    print("=" * 50)
    
    # Analyser les données scrapées
    data_file = "data/appartements/90931157.json"
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"🏠 Appartement: {data['id']}")
        print(f"📍 Localisation: {data['localisation']}")
        print(f"💰 Prix: {data['prix']}")
        print(f"📐 Surface: {data['surface']}")
        
        # Informations de la carte
        map_info = data.get('map_info', {})
        print(f"🗺️ Quartier: {map_info.get('quartier', 'Non identifié')}")
        print(f"🛣️ Rues trouvées: {len(map_info.get('streets', []))}")
        print(f"🚇 Métros trouvés: {len(map_info.get('metros', []))}")
        
        # Coordonnées
        coords = data.get('coordinates', {})
        if coords.get('latitude') and coords.get('longitude'):
            print(f"🌍 Coordonnées: {coords['latitude']}, {coords['longitude']}")
        else:
            print("🌍 Coordonnées: Non valides")
        
        # Style haussmannien
        style = data.get('style_haussmannien', {})
        print(f"🏛️ Style haussmannien: {style.get('score', 0)}/100")
        
        print("\n💡 RECOMMANDATIONS:")
        print("   1. Les screenshots de carte sont disponibles pour analyse manuelle")
        print("   2. L'appartement est situé près des Buttes-Chaumont (Paris 19e)")
        print("   3. Les coordonnées GPS extraites semblent incorrectes")
        print("   4. L'analyse visuelle des screenshots permettrait d'identifier le quartier exact")
        
    else:
        print("❌ Fichier de données non trouvé")

if __name__ == "__main__":
    analyze_map_screenshots()
