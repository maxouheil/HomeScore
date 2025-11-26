#!/usr/bin/env python3
"""
Script pour mettre à jour le format de localisation dans tous les fichiers
Format: "Metro X · rue Y" au lieu de "Paris Xe (750XX)"
"""

import json
from pathlib import Path
from criteria.localisation import get_metro_name
from geocoding import get_precise_location


def update_localisation_format(apartment):
    """Met à jour le format de localisation pour un appartement"""
    updated = False
    
    # Récupérer le métro
    metro_name = get_metro_name(apartment)
    
    # Récupérer l'adresse précise
    localisation_precise = apartment.get('localisation_precise')
    
    # Construire le nouveau format
    localisation_parts = []
    
    if metro_name:
        localisation_parts.append(f"Metro {metro_name}")
    
    if localisation_precise:
        # Extraire juste la rue (avant la virgule)
        if ',' in localisation_precise:
            street_address = localisation_precise.split(',')[0].strip()
        else:
            street_address = localisation_precise
        localisation_parts.append(street_address)
    
    # Mettre à jour si on a au moins le métro ou l'adresse
    if localisation_parts:
        new_localisation = " · ".join(localisation_parts)
        old_localisation = apartment.get('localisation', '')
        
        if new_localisation != old_localisation:
            apartment['localisation'] = new_localisation
            updated = True
    
    return updated


def update_all_localisations():
    """Met à jour le format de localisation pour tous les appartements"""
    print("🔄 MISE À JOUR DU FORMAT DE LOCALISATION")
    print("=" * 60)
    
    apartments_dir = Path('data/appartements')
    if not apartments_dir.exists():
        print(f"❌ Dossier {apartments_dir} non trouvé")
        return
    
    apartment_files = list(apartments_dir.glob('*.json'))
    total = len(apartment_files)
    
    if total == 0:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"📋 {total} appartements trouvés")
    print()
    
    updated_count = 0
    
    for i, apartment_file in enumerate(apartment_files, 1):
        apartment_id = apartment_file.stem
        print(f"🏠 [{i}/{total}] Appartement {apartment_id}")
        
        try:
            with open(apartment_file, 'r', encoding='utf-8') as f:
                apartment = json.load(f)
            
            old_localisation = apartment.get('localisation', 'N/A')
            
            if update_localisation_format(apartment):
                # Sauvegarder
                with open(apartment_file, 'w', encoding='utf-8') as f:
                    json.dump(apartment, f, ensure_ascii=False, indent=2)
                
                new_localisation = apartment.get('localisation', 'N/A')
                print(f"   ✅ Mis à jour:")
                print(f"      Avant: {old_localisation}")
                print(f"      Après: {new_localisation}")
                updated_count += 1
            else:
                print(f"   ⏭️ Déjà au bon format: {old_localisation}")
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print()
    
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print(f"✅ Appartements mis à jour: {updated_count}/{total}")
    print()


if __name__ == "__main__":
    update_all_localisations()




