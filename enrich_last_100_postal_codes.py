#!/usr/bin/env python3
"""
Script pour enrichir les 100 derniers appartements avec le code postal
via géocodage inversé depuis les coordonnées GPS
"""

import sys
import json
import time
from pathlib import Path

# Ajouter le chemin pour les imports
sys.path.insert(0, 'backend')
sys.path.insert(0, '.')

from api.apartments import load_apartments_data
from normalizers.simple_normalizer import normalize_apartment
from geocoding import reverse_geocode

def enrich_last_100_postal_codes():
    """Enrichit les 100 derniers appartements avec le code postal via géocodage inversé"""
    
    # Charger tous les appartements
    print("📥 Chargement des appartements...")
    all_apts = load_apartments_data(enrich=False)
    last_100 = all_apts[-100:]
    
    print(f"✅ {len(all_apts)} appartements chargés, analyse des 100 derniers...")
    
    # Identifier ceux sans arrondissement mais avec coordonnées
    to_enrich = []
    for apt in last_100:
        normalized = normalize_apartment(apt)
        localisation = normalized.get('localisation', {})
        arrondissement = localisation.get('arrondissement')
        
        # Si pas d'arrondissement, vérifier si on a des coordonnées
        if not arrondissement:
            coordinates = localisation.get('coordinates', {})
            lat = coordinates.get('lat')
            lng = coordinates.get('lng')
            
            # Fallback sur api_data
            if not lat or not lng:
                api_data = apt.get('_api_data', {})
                lat = api_data.get('lat')
                lng = api_data.get('lng')
            
            if lat and lng:
                # Trouver l'index dans all_apts
                apt_id = apt.get('id')
                index = next((i for i, a in enumerate(all_apts) if a.get('id') == apt_id), None)
                if index is not None:
                    to_enrich.append({
                        'apt': apt,
                        'lat': float(lat),
                        'lng': float(lng),
                        'index': index,
                        'apt_id': apt_id
                    })
    
    print(f"\n🔍 {len(to_enrich)} appartements à enrichir (sans arrondissement mais avec coordonnées GPS)")
    
    if not to_enrich:
        print("✅ Aucun appartement à enrichir !")
        return
    
    # Enrichir avec géocodage inversé
    enriched_count = 0
    failed_count = 0
    
    for i, item in enumerate(to_enrich, 1):
        apt = item['apt']
        lat = item['lat']
        lng = item['lng']
        index = item['index']
        apt_id = item['apt_id']
        
        print(f"\n[{i}/{len(to_enrich)}] Enrichissement de l'appartement {apt_id}...")
        print(f"  Coordonnées: {lat}, {lng}")
        
        # Géocodage inversé
        try:
            result = reverse_geocode(lat, lng)
            
            if result and result.get('postal_code'):
                postal_code = result['postal_code']
                
                # Vérifier que c'est un code postal Paris valide
                if postal_code.startswith('75') and len(postal_code) == 5:
                    # Mettre à jour _api_data avec le code postal
                    if '_api_data' not in all_apts[index]:
                        all_apts[index]['_api_data'] = {}
                    
                    all_apts[index]['_api_data']['postal_code'] = postal_code
                    enriched_count += 1
                    print(f"  ✅ Code postal récupéré: {postal_code}")
                else:
                    print(f"  ⚠️ Code postal non-Paris: {postal_code}")
                    failed_count += 1
            else:
                print(f"  ❌ Aucun code postal trouvé")
                failed_count += 1
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            failed_count += 1
        
        # Rate limiting: 1 requête/seconde pour Nominatim gratuit
        if i < len(to_enrich):
            time.sleep(1)
    
    print(f"\n📊 Résultats:")
    print(f"  ✅ Enrichis: {enriched_count}")
    print(f"  ❌ Échecs: {failed_count}")
    
    if enriched_count > 0:
        # Sauvegarder le fichier JSON
        data_file = Path('data/all_apartments.json')
        print(f"\n💾 Sauvegarde dans {data_file}...")
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(all_apts, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {enriched_count} appartements enrichis et sauvegardés !")
    else:
        print("\n⚠️ Aucun appartement enrichi, pas de sauvegarde nécessaire")

if __name__ == '__main__':
    enrich_last_100_postal_codes()
