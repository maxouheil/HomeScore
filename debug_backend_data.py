#!/usr/bin/env python3
"""Script pour déboguer les données chargées par le backend"""

import json
import re

# Charger les données que le backend utilise réellement
with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
    apts = json.load(f)

print(f"📊 Total d'appartements dans all_apartments_scores.json: {len(apts)}")
print("=" * 60)

# Filtres de l'alerte
budget_min, budget_max = 500000, 900000
surface_min, surface_max = 65, 100
pieces_min, pieces_max = 3, 3

# Normaliser pour comparaison
def normalize_for_match(text):
    if not text:
        return ''
    import unicodedata
    import re as re_module
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re_module.sub(r'[-\s]+', ' ', text)
    return text.lower().strip()

# Filtrer par budget/surface/pièces
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

print(f"📋 Après filtrage budget/surface/pièces: {len(filtered)} appartements")
print()

# Test avec le filtre de localisation
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
                        metro_str in q_filter_clean or
                        q_filter_normalized.replace(' ', '') in metro_normalized.replace(' ', '') or
                        metro_normalized.replace(' ', '') in q_filter_normalized.replace(' ', '')):
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

print(f"✅ Appartements qui passent le filtre de localisation: {len(matching_apts)}")
print()
if len(matching_apts) > 0:
    print("  Exemples d'appartements qui passent:")
    for apt in matching_apts[:10]:
        print(f"    - {apt.get('id')}: {apt.get('localisation')} | Métros: {apt.get('map_info', {}).get('metros', [])}")
else:
    print("  ❌ Aucun appartement ne passe le filtre de localisation!")


