#!/usr/bin/env python3
"""Analyse hauteur plafond pour l'appartement 93083514"""

import json
import re

# Charger l'appartement directement depuis le fichier
with open('data/appartements/93083514.json', 'r') as f:
    apt = json.load(f)

print(f"🏠 Appartement {apt.get('id')}")
print(f"   Prix: {apt.get('prix')}")
print(f"   Surface: {apt.get('surface')}")

# Extraire les URLs des photos
photos = apt.get('photos', [])
photos_urls = []
for photo in photos:
    if isinstance(photo, dict):
        url = photo.get('url', '')
    else:
        url = photo
    if url:
        photos_urls.append(url)

print(f"\n📸 Photos disponibles: {len(photos_urls)}")

# Vérifier la description
description = apt.get('description', '')
if '3,30' in description or '3.30' in description:
    print(f"\n📝 La description mentionne: 'hauteur sous plafond de 3,30 m'")

print(f"\n🔍 Pour analyser les photos, exécutez:")
print(f"   python3 -c \"from scoring import score_hauteur_plafond, load_scoring_config; from data_loader import load_apartments;")
print(f"   apartments = load_apartments(prefer_api=True);")
print(f"   apt = next((a for a in apartments if str(a.get('id')) == '93083514'), None);")
print(f"   config = load_scoring_config();")
print(f"   result = score_hauteur_plafond(apt, config);")
print(f"   print(f'Hauteur: {{result.get(\\\"details\\\", {{}}).get(\\\"hauteur_estimate\\\", \\\"N/A\\\")}}m');")
print(f"   print(f'Score: {{result.get(\\\"score\\\")}}/10');")
print(f"   print(f'Tier: {{result.get(\\\"tier\\\")}}')\"")


