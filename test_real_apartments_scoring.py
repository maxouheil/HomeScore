#!/usr/bin/env python3
"""
Test avec des données réelles d'appartements pour trouver le problème
"""

import json
import os
from pathlib import Path
from scoring import score_localisation, load_scoring_config
from criteria.localisation import get_quartier_name, get_all_metro_stations


def test_real_apartments():
    """Test avec de vrais appartements depuis la base de données"""
    
    data_dir = Path('data/appartements')
    if not data_dir.exists():
        print("❌ Dossier data/appartements non trouvé")
        return
    
    config = load_scoring_config()
    
    # Trouver des appartements avec Pyrénées ou Combat
    print("🔍 Recherche d'appartements avec Pyrénées ou Combat...\n")
    
    apartments_found = []
    for json_file in data_dir.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                apt = json.load(f)
            
            localisation = apt.get('localisation', '').lower()
            quartier = get_quartier_name(apt)
            stations = get_all_metro_stations(apt)
            
            # Chercher Pyrénées ou Combat
            if ('pyrénées' in localisation or 
                'combat' in localisation.lower() or
                (quartier and ('pyrénées' in quartier.lower() or 'combat' in quartier.lower())) or
                any('pyrénées' in s.lower() or 'combat' in s.lower() for s in stations)):
                
                apartments_found.append((json_file.name, apt))
                
        except Exception as e:
            continue
    
    print(f"✅ {len(apartments_found)} appartements trouvés\n")
    
    # Tester chaque appartement
    for filename, apt in apartments_found[:5]:  # Limiter à 5 pour le test
        print("="*60)
        print(f"📋 Appartement: {filename}")
        print("="*60)
        
        localisation = apt.get('localisation', '')
        quartier = get_quartier_name(apt)
        stations = get_all_metro_stations(apt)
        description = apt.get('description', '')[:200]
        
        print(f"   Localisation: {localisation}")
        print(f"   Quartier: {quartier if quartier else 'Non trouvé'}")
        print(f"   Stations: {stations}")
        print(f"   Description: {description}...")
        
        # Calculer le score
        result = score_localisation(apt, config)
        
        print(f"\n   📊 Score: {result['score']} points")
        print(f"   Tier: {result['tier']}")
        print(f"   Justification: {result['justification']}")
        
        # Vérifier si c'est un problème
        if result['tier'] == 'tier1' and ('pyrénées' in localisation.lower() or (quartier and 'combat' in quartier.lower())):
            print(f"\n   ⚠️  PROBLÈME: Pyrénées/Combat devrait être Tier 2 mais reçoit Tier 1!")
            print(f"   → Vérifier si 'Belleville' ou autre zone Tier 1 est mentionnée quelque part")
        
        print()


if __name__ == "__main__":
    test_real_apartments()




