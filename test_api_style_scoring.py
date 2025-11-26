#!/usr/bin/env python3
"""
Test du nouveau système de scoring style utilisant buy_type et year de l'API
"""

import json
from scoring import score_style, load_scoring_config

def test_api_style_scoring():
    """Test le scoring style avec les données API"""
    print("🧪 TEST DU SCORING STYLE AVEC DONNÉES API")
    print("=" * 60)
    
    config = load_scoring_config()
    
    # Charger quelques appartements de test
    with open('data/paris_apartments.json', 'r') as f:
        apartments = json.load(f)
    
    # Trouver des exemples variés
    test_cases = []
    
    # 1. Appartement neuf (buy_type: new)
    for apt in apartments:
        api_data = apt.get('_api_data', {})
        if api_data and api_data.get('buy_type') == 'new':
            test_cases.append(('Neuf (buy_type: new)', apt))
            break
    
    # 2. Appartement haussmannien (year 1850-1900)
    for apt in apartments:
        api_data = apt.get('_api_data', {})
        if api_data:
            features = api_data.get('features', {})
            year = features.get('year') if isinstance(features, dict) else None
            if year and 1850 <= year <= 1900:
                test_cases.append((f'Haussmannien (year: {year})', apt))
                break
    
    # 3. Appartement ancien avant 1850
    for apt in apartments:
        api_data = apt.get('_api_data', {})
        if api_data:
            features = api_data.get('features', {})
            year = features.get('year') if isinstance(features, dict) else None
            if year and year < 1850:
                test_cases.append((f'Ancien avant 1850 (year: {year})', apt))
                break
    
    # 4. Appartement ancien 1900-1950
    for apt in apartments:
        api_data = apt.get('_api_data', {})
        if api_data:
            features = api_data.get('features', {})
            year = features.get('year') if isinstance(features, dict) else None
            if year and 1900 < year <= 1950:
                test_cases.append((f'Ancien 1900-1950 (year: {year})', apt))
                break
    
    # 5. Appartement récent après 1950
    for apt in apartments:
        api_data = apt.get('_api_data', {})
        if api_data:
            features = api_data.get('features', {})
            year = features.get('year') if isinstance(features, dict) else None
            if year and year > 1950:
                test_cases.append((f'Récent après 1950 (year: {year})', apt))
                break
    
    # 6. Appartement old sans année (fallback)
    for apt in apartments:
        api_data = apt.get('_api_data', {})
        if api_data:
            features = api_data.get('features', {})
            year = features.get('year') if isinstance(features, dict) else None
            if api_data.get('buy_type') == 'old' and not year:
                test_cases.append(('Old sans année (fallback)', apt))
                break
    
    print(f"\n📋 {len(test_cases)} cas de test trouvés\n")
    
    for i, (description, apt) in enumerate(test_cases, 1):
        print(f"{i}. {description}")
        print(f"   ID: {apt.get('id')}")
        print(f"   Titre: {apt.get('titre', 'N/A')[:60]}")
        
        api_data = apt.get('_api_data', {})
        if api_data:
            print(f"   buy_type: {api_data.get('buy_type')}")
            features = api_data.get('features', {})
            year = features.get('year') if isinstance(features, dict) else None
            print(f"   year: {year}")
        
        # Calculer le score
        result = score_style(apt, config)
        
        print(f"   ✅ Score: {result.get('score')}/20 (Tier: {result.get('tier')})")
        print(f"   📝 Justification: {result.get('justification')}")
        print(f"   🔍 Source: {result.get('source', 'fallback')}")
        print()
    
    print("=" * 60)
    print("✅ Tests terminés")


if __name__ == "__main__":
    test_api_style_scoring()

