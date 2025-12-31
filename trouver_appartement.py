#!/usr/bin/env python3
import json
from project_config import APARTMENTS_FILE

fichier_source = str(APARTMENTS_FILE)
with open(fichier_source, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Recherche de l'appartement: 770k · Goncourt (Hôpital Saint-Louis)\n")

# Chercher avec plusieurs critères combinés
candidats = []
for apt in data:
    localisation = str(apt.get('localisation', '')).lower()
    titre = str(apt.get('titre', '')).lower()
    prix_str = str(apt.get('prix', '')).replace(' ', '').replace('€', '').replace(',', '')
    
    score = 0
    # Critères de correspondance
    if 'goncourt' in localisation:
        score += 3
    if 'hopital' in localisation or 'hôpital' in localisation:
        score += 2
    if 'saint-louis' in localisation:
        score += 3
    if '770' in prix_str or '770000' in prix_str:
        score += 3
    if 'paris 10e' in titre or '10e' in localisation:
        score += 1
    
    if score >= 3:  # Au moins 2 critères
        candidats.append((score, apt))

# Trier par score décroissant
candidats.sort(reverse=True, key=lambda x: x[0])

print(f"Trouvé {len(candidats)} candidat(s):\n")
for score, apt in candidats[:10]:
    print(f"Score: {score}")
    print(f"  ID: {apt.get('id')}")
    print(f"  Titre: {apt.get('titre')}")
    print(f"  Prix: {apt.get('prix')}")
    print(f"  Localisation: {apt.get('localisation')}")
    print(f"  Surface: {apt.get('surface')}")
    print(f"  Photos: {len(apt.get('photos', []))}")
    print()

