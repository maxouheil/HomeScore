#!/usr/bin/env python3
"""
Script pour enrichir tous les appartements avec :
- Stations de métro depuis l'API (si manquantes)
- Adresse précise via géocodage inverse (si manquante)
"""

import json
import os
import time
from pathlib import Path
from geocoding import get_precise_location, reverse_geocode
from criteria.localisation import get_metro_name
from scoring import get_api_metro_stations


def load_apartment(apartment_id):
    """Charge un appartement depuis data/appartements/"""
    apartment_file = Path(f"data/appartements/{apartment_id}.json")
    if not apartment_file.exists():
        return None
    
    try:
        with open(apartment_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"   ❌ Erreur chargement {apartment_id}: {e}")
        return None


def save_apartment(apartment_data):
    """Sauvegarde un appartement mis à jour"""
    apartment_id = apartment_data.get('id')
    if not apartment_id:
        return False
    
    apartment_file = Path(f"data/appartements/{apartment_id}.json")
    try:
        with open(apartment_file, 'w', encoding='utf-8') as f:
            json.dump(apartment_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"   ❌ Erreur sauvegarde {apartment_id}: {e}")
        return False


def enrich_apartment_metro_address(apartment):
    """Enrichit un appartement avec métro et adresse précise"""
    updated = False
    updates = []
    
    apartment_id = apartment.get('id', 'unknown')
    
    # 1. Vérifier et enrichir les stations de métro depuis l'API
    transports = apartment.get('transports', [])
    map_info = apartment.get('map_info', {})
    metros_from_map = map_info.get('metros', [])
    
    # Utiliser get_api_metro_stations pour récupérer uniquement depuis API
    api_stations = get_api_metro_stations(apartment)
    
    if api_stations:
        # Mettre à jour transports si nécessaire
        if not transports or set(transports) != set(api_stations):
            apartment['transports'] = api_stations
            if 'map_info' not in apartment:
                apartment['map_info'] = {}
            apartment['map_info']['metros'] = api_stations
            updated = True
            updates.append(f"Métro: {', '.join(api_stations)}")
    
    # 2. Vérifier et enrichir l'adresse précise via géocodage inverse
    localisation_precise = apartment.get('localisation_precise')
    coordinates = apartment.get('coordinates', {})
    lat = coordinates.get('latitude')
    lng = coordinates.get('longitude')
    
    # Fallback sur _api_data si coordinates non disponible
    if lat is None or lng is None:
        api_data = apartment.get('_api_data', {})
        lat = api_data.get('lat')
        lng = api_data.get('lng')
    
    if (lat is not None and lng is not None) and not localisation_precise:
        # Faire le géocodage inverse
        print(f"      🔄 Géocodage inverse en cours...")
        address_data = reverse_geocode(lat, lng)
        
        if address_data and address_data.get('full_address'):
            apartment['localisation_precise'] = address_data['full_address']
            updated = True
            updates.append(f"Adresse: {address_data['full_address']}")
            # Respecter le rate limiting de Nominatim (1 req/sec)
            time.sleep(1.1)
        else:
            print(f"      ⚠️ Impossible de récupérer l'adresse pour {apartment_id}")
    
    return updated, updates


def enrich_all_apartments():
    """Enrichit tous les appartements avec métro et adresse"""
    print("🔄 ENRICHISSEMENT DES APPARTEMENTS")
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
    error_count = 0
    metro_added = 0
    address_added = 0
    
    for i, apartment_file in enumerate(apartment_files, 1):
        apartment_id = apartment_file.stem
        print(f"🏠 [{i}/{total}] Appartement {apartment_id}")
        
        # Charger l'appartement
        apartment = load_apartment(apartment_id)
        if not apartment:
            error_count += 1
            continue
        
        try:
            # Enrichir avec métro et adresse
            updated, updates = enrich_apartment_metro_address(apartment)
            
            if updated:
                # Sauvegarder
                if save_apartment(apartment):
                    updated_count += 1
                    print(f"   ✅ Mis à jour:")
                    for update in updates:
                        print(f"      - {update}")
                        if "Métro:" in update:
                            metro_added += 1
                        if "Adresse:" in update:
                            address_added += 1
                else:
                    error_count += 1
            else:
                print(f"   ⏭️ Déjà à jour")
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
        
        print()
    
    # Résumé
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print(f"✅ Appartements mis à jour: {updated_count}/{total}")
    print(f"🚇 Métros ajoutés: {metro_added}")
    print(f"📍 Adresses ajoutées: {address_added}")
    if error_count > 0:
        print(f"❌ Erreurs: {error_count}")
    print()


if __name__ == "__main__":
    enrich_all_apartments()

