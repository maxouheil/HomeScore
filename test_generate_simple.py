#!/usr/bin/env python3
"""Test simple de génération HTML pour identifier les blocages"""

import json
import time

print("1. Chargement des données...")
start = time.time()
with open('data/scores.json', 'r') as f:
    apartments = json.load(f)
print(f"   ✅ {len(apartments)} appartements chargés en {time.time() - start:.2f}s")

print("\n2. Test imports criteria...")
start = time.time()
try:
    from criteria import format_localisation, format_prix, format_style, format_exposition, format_cuisine, format_baignoire
    print(f"   ✅ Imports OK en {time.time() - start:.2f}s")
except Exception as e:
    print(f"   ❌ Erreur imports: {e}")
    exit(1)

print("\n3. Test formatage d'un appartement...")
start = time.time()
apt = apartments[0]
try:
    print(f"   Test localisation...")
    format_localisation(apt)
    print(f"   Test prix...")
    format_prix(apt)
    print(f"   Test style...")
    format_style(apt)
    print(f"   Test exposition...")
    format_exposition(apt)
    print(f"   Test cuisine...")
    format_cuisine(apt)
    print(f"   Test baignoire...")
    format_baignoire(apt)
    print(f"   ✅ Formatage OK en {time.time() - start:.2f}s")
except Exception as e:
    print(f"   ❌ Erreur formatage: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✅ Tous les tests passés!")

