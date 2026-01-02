#!/usr/bin/env python3
"""Script pour déboguer le filtre de localisation"""

import json

# Charger les appartements
with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
    apts = json.load(f)

print(f"📊 Total d'appartements: {len(apts)}")
print("=" * 60)

# Filtres de l'alerte
filters = [
    'Alexandre Dumas',
    'Place de la Réunion', 
    'Belleville',
    'Saint-Ambroise',
    'Goncourt'
]

print("🔍 Recherche des stations dans les appartements:")
print()

for f in filters:
    matching = []
    for apt in apts:
        # Vérifier dans les métros
        metros = apt.get('map_info', {}).get('metros', []) or []
        metro_match = any(f.lower() in str(m).lower() for m in metros if m)
        
        # Vérifier dans la localisation
        localisation = str(apt.get('localisation', '')).lower()
        loc_match = f.lower() in localisation
        
        if metro_match or loc_match:
            matching.append(apt)
    
    print(f"  {f}: {len(matching)} appartements")
    if len(matching) > 0 and len(matching) <= 5:
        for apt in matching[:3]:
            print(f"    - {apt.get('id')}: {apt.get('localisation')} | Métros: {apt.get('map_info', {}).get('metros', [])}")

print()
print("=" * 60)
print("🔍 Recherche flexible (sans accents, tirets, espaces):")
print()

def normalize(text):
    """Normalise un texte pour comparaison"""
    if not text:
        return ''
    import unicodedata
    import re
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[-\s]+', '', text)
    return text.lower()

for f in filters:
    matching = []
    f_normalized = normalize(f)
    
    for apt in apts:
        # Vérifier dans les métros
        metros = apt.get('map_info', {}).get('metros', []) or []
        metro_match = any(f_normalized in normalize(str(m)) for m in metros if m)
        
        # Vérifier dans la localisation
        localisation = str(apt.get('localisation', ''))
        loc_match = f_normalized in normalize(localisation)
        
        if metro_match or loc_match:
            matching.append(apt)
    
    print(f"  {f}: {len(matching)} appartements")
    if len(matching) > 0 and len(matching) <= 5:
        for apt in matching[:3]:
            print(f"    - {apt.get('id')}: {apt.get('localisation')} | Métros: {apt.get('map_info', {}).get('metros', [])}")

print()
print("=" * 60)
print("📋 Appartements qui passent le filtre budget/surface/pièces:")
print()

# Simuler les filtres de l'alerte
budget_min, budget_max = 500000, 900000
surface_min, surface_max = 65, 100
pieces_min, pieces_max = 3, 3

import re

filtered = []
for apt in apts:
    # Budget
    prix_str = apt.get('prix', '').replace(' ', '').replace('€', '')
    prix_match = re.search(r'(\d+)', prix_str)
    if not prix_match:
        continue
    prix = int(prix_match.group(1))
    if prix < budget_min or prix > budget_max:
        continue
    
    # Surface
    surface_str = apt.get('surface', '')
    surface_match = re.search(r'(\d+)', surface_str)
    if not surface_match:
        continue
    surface = int(surface_match.group(1))
    if surface < surface_min or surface > surface_max:
        continue
    
    # Pièces
    pieces_str = apt.get('pieces', '')
    pieces_match = re.search(r'(\d+)', pieces_str)
    if not pieces_match:
        continue
    pieces = int(pieces_match.group(1))
    if pieces < pieces_min or pieces > pieces_max:
        continue
    
    filtered.append(apt)

print(f"  Après filtrage budget/surface/pièces: {len(filtered)} appartements")
print()
print("🔍 Test avec le code EXACT du filtre de localisation:")
print()

# Simuler exactement le code du filtre
def normalize_for_match(text):
    if not text:
        return ''
    import unicodedata
    import re
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[-\s]+', ' ', text)
    return text.lower().strip()

localisation_filter = 'Métro Alexandre Dumas, Place de la Réunion, Métro Belleville, Métro Saint-Ambroise, Métro Goncourt'
quartier_filters = [q.strip() for q in localisation_filter.split(',')]

matching_apts = []
for apt in filtered:
    localisation = str(apt.get('localisation') or '').lower()
    map_info = apt.get('map_info', {}) or {}
    quartier = str(map_info.get('quartier') or '').lower()
    metros = map_info.get('metros', []) or []
    streets = map_info.get('streets', []) or []
    
    matches = False
    for q_filter in quartier_filters:
        if not q_filter:
            continue
        q_filter_lower = q_filter.lower().strip()
        q_filter_clean = q_filter_lower.replace('métro ', '').replace('metro ', '').strip()
        q_filter_normalized = normalize_for_match(q_filter_clean)
        
        # Vérifier dans la localisation
        if localisation:
            localisation_normalized = normalize_for_match(localisation)
            if q_filter_normalized in localisation_normalized or q_filter_clean in localisation:
                matches = True
                break
        
        # Vérifier dans le quartier
        if quartier:
            quartier_normalized = normalize_for_match(quartier)
            if q_filter_normalized in quartier_normalized or q_filter_clean in quartier:
                matches = True
                break
        
        # Vérifier dans les métros
        if metros:
            for metro in metros:
                if metro:
                    metro_str = str(metro).lower().strip()
                    metro_normalized = normalize_for_match(metro_str)
                    if (q_filter_clean in metro_str or 
                        q_filter_normalized in metro_normalized or
                        metro_normalized in q_filter_normalized or
                        metro_str in q_filter_clean):
                        matches = True
                        break
            if matches:
                break
        
        # Vérifier dans les rues
        if streets:
            for street in streets:
                if street:
                    street_str = str(street).lower()
                    street_normalized = normalize_for_match(street_str)
                    if (q_filter_clean in street_str or 
                        q_filter_normalized in street_normalized):
                        matches = True
                        break
            if matches:
                break
    
    if matches:
        matching_apts.append(apt)

print(f"  Appartements qui passent le filtre de localisation: {len(matching_apts)}")
print()
if len(matching_apts) > 0:
    print("  Exemples d'appartements qui passent:")
    for apt in matching_apts[:10]:
        print(f"    - {apt.get('id')}: {apt.get('localisation')} | Métros: {apt.get('map_info', {}).get('metros', [])}")
else:
    print("  ❌ Aucun appartement ne passe le filtre de localisation!")
    print()
    print("  🔍 Debug: Testons chaque station individuellement:")
    for f in filters:
        f_normalized = normalize(f)
        matching = []
        for apt in filtered:
            metros = apt.get('map_info', {}).get('metros', []) or []
            metro_match = any(f_normalized in normalize(str(m)) for m in metros if m)
            localisation = str(apt.get('localisation', ''))
            loc_match = f_normalized in normalize(localisation)
            if metro_match or loc_match:
                matching.append(apt)
        print(f"    {f}: {len(matching)} appartements")

