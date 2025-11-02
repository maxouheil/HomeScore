#!/usr/bin/env python3
"""Test pour vérifier que l'API retourne bien les indices avec luminosité image"""

import requests
import json

# Tester l'API
response = requests.get('http://localhost:8000/api/apartments')
if response.status_code == 200:
    apartments = response.json()
    apt = next((a for a in apartments if str(a.get('id')) == '85653922'), None)
    
    if apt:
        print("=== APPARTEMENT 749k ===")
        print(f"ID: {apt.get('id')}")
        print()
        
        expo = apt.get('exposition', {})
        print("=== EXPOSITION ===")
        print(f"Exposition: {expo.get('exposition')}")
        print(f"Brightness value: {expo.get('details', {}).get('brightness_value')}")
        print()
        
        formatted = apt.get('formatted_data', {}).get('exposition', {})
        print("=== FORMATTED_DATA.EXPOSITION ===")
        print(json.dumps(formatted, indent=2, ensure_ascii=False))
        print()
        
        if formatted.get('indices'):
            print(f"✅ INDICES: {formatted.get('indices')}")
        else:
            print("❌ Pas d'indices dans formatted_data.exposition")
            print()
            print("=== DEBUG ===")
            print(f"scores_detaille.ensoleillement: {'ensoleillement' in apt.get('scores_detaille', {})}")
            print(f"exposition.details.brightness_value: {expo.get('details', {}).get('brightness_value')}")
    else:
        print("❌ Appartement 85653922 non trouvé")
else:
    print(f"❌ Erreur API: {response.status_code}")

