#!/usr/bin/env python3
"""
Script simple pour mettre à jour manuellement les prix médians
Usage: python scripts/update_medians_manual.py
"""

import json
from pathlib import Path
from datetime import datetime

FILE_PATH = Path(__file__).parent.parent / 'data' / 'prix_medians' / 'arrondissements.json'

def update_medians(medians_dict):
    """
    Met à jour le fichier JSON avec les prix médians fournis
    
    Args:
        medians_dict: Dict avec format {"75010": 10500, "75011": 11000, ...}
    """
    # Charger le fichier existant
    if FILE_PATH.exists():
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print(f"❌ Fichier {FILE_PATH} non trouvé")
        return
    
    # Mettre à jour les valeurs
    updated_count = 0
    for postal_code, prix_median in medians_dict.items():
        if postal_code in data:
            data[postal_code]['prix_median_m2'] = prix_median
            data[postal_code]['source'] = 'manual'
            data[postal_code]['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            updated_count += 1
            print(f"✅ {postal_code} ({data[postal_code]['arrondissement']}): {prix_median} €/m²")
        else:
            print(f"⚠️  Code postal {postal_code} non trouvé")
    
    # Sauvegarder
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 {updated_count} arrondissements mis à jour")
    print(f"📁 Fichier sauvegardé: {FILE_PATH}")


if __name__ == "__main__":
    print("=" * 60)
    print("📊 MISE À JOUR MANUELLE DES PRIX MÉDIANS")
    print("=" * 60)
    print("\nModifiez le code ci-dessous avec vos prix médians :\n")
    print("""
# Exemple :
medians = {
    "75010": 10500,  # 10e arrondissement
    "75011": 11000,  # 11e arrondissement
    "75019": 9500,   # 19e arrondissement
    "75020": 9000,   # 20e arrondissement
    # ... ajoutez les autres arrondissements
}

update_medians(medians)
    """)
    
    # DÉCOMMENTEZ ET MODIFIEZ CI-DESSOUS :
    """
    medians = {
        "75010": 10500,
        "75011": 11000,
        "75019": 9500,
        "75020": 9000,
    }
    
    update_medians(medians)
    """

