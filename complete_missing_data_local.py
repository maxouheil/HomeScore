#!/usr/bin/env python3
"""
Script pour compléter les données manquantes des appartements en local
Sans connexion à Jinka - utilise uniquement les données déjà disponibles
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from geocoding import get_precise_location
from criteria.localisation import get_metro_name


def load_existing_apartments() -> List[Dict[str, Any]]:
    """Charge les appartements existants depuis scraped_apartments.json"""
    scraped_file = Path('data/scraped_apartments.json')
    
    if not scraped_file.exists():
        print("❌ Fichier scraped_apartments.json non trouvé")
        return []
    
    try:
        with open(scraped_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        print(f"✅ {len(apartments)} appartements chargés")
        return apartments
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return []


def calculate_prix_m2(apartment: Dict[str, Any]) -> Optional[str]:
    """Calcule le prix au m² depuis le prix et la surface"""
    prix_str = apartment.get('prix', '').replace(' ', '').replace('€', '').strip()
    surface_str = apartment.get('surface', '').replace('m²', '').strip()
    
    try:
        prix = int(prix_str)
        surface = int(surface_str)
        
        if surface > 0:
            prix_m2 = prix // surface
            return f"{prix_m2} € / m²"
    except (ValueError, TypeError):
        pass
    
    return None


def enrich_map_info(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """Enrichit map_info depuis les données disponibles"""
    map_info = apartment.get('map_info', {})
    
    # Si pas de métros mais qu'on a transports, les utiliser
    if not map_info.get('metros') and apartment.get('transports'):
        map_info['metros'] = apartment['transports']
    
    # Si pas de quartier mais qu'on a localisation précise, essayer de l'extraire
    if not map_info.get('quartier'):
        localisation = apartment.get('localisation', '')
        # Extraire le quartier depuis la localisation (ex: "Paris 11e" -> "11e")
        quartier_match = re.search(r'Paris\s+(\d+e)', localisation)
        if quartier_match:
            map_info['quartier'] = f"Paris {quartier_match.group(1)}"
    
    return map_info


def enrich_coordinates(apartment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Enrichit les coordonnées depuis _api_data si disponible"""
    if apartment.get('coordinates'):
        return apartment['coordinates']
    
    # Essayer depuis _api_data
    api_data = apartment.get('_api_data', {})
    lat = api_data.get('lat')
    lng = api_data.get('lng')
    
    if lat is not None and lng is not None:
        return {
            'latitude': lat,
            'longitude': lng,
            'raw_x': None,
            'raw_y': None,
            'scale': 1.0
        }
    
    return None


def enrich_localisation(apartment: Dict[str, Any]) -> Optional[str]:
    """Enrichit la localisation depuis les coordonnées si disponible"""
    if apartment.get('localisation_precise'):
        return apartment['localisation_precise']
    
    # Essayer de récupérer depuis les coordonnées
    coordinates = apartment.get('coordinates')
    if coordinates and coordinates.get('latitude') and coordinates.get('longitude'):
        try:
            localisation_precise = get_precise_location(apartment)
            return localisation_precise
        except Exception as e:
            print(f"   ⚠️  Erreur géocodage inverse: {e}")
    
    return None


def enrich_localisation_format(apartment: Dict[str, Any]) -> str:
    """Construit le format "Metro X · 34, rue X" pour localisation"""
    localisation_parts = []
    
    # 1. Récupérer le métro
    temp_apt = {
        'map_info': apartment.get('map_info', {}),
        'transports': apartment.get('transports', [])
    }
    metro_name = get_metro_name(temp_apt)
    if metro_name:
        localisation_parts.append(f"Metro {metro_name}")
    
    # 2. Extraire la rue depuis localisation_precise
    localisation_precise = apartment.get('localisation_precise')
    if localisation_precise:
        if ',' in localisation_precise:
            street_address = localisation_precise.split(',')[0].strip()
        else:
            street_address = localisation_precise
        
        if street_address:
            localisation_parts.append(street_address)
    
    # Construire la localisation finale
    if localisation_parts:
        return " · ".join(localisation_parts)
    
    # Fallback sur la localisation existante
    return apartment.get('localisation', '')


def complete_apartment_data(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """Complète les données manquantes d'un appartement"""
    updated = False
    apt_id = apartment.get('id', 'unknown')
    
    # 1. Calculer prix_m2 si manquant
    if not apartment.get('prix_m2'):
        prix_m2 = calculate_prix_m2(apartment)
        if prix_m2:
            apartment['prix_m2'] = prix_m2
            updated = True
            print(f"   ✅ {apt_id}: prix_m2 calculé ({prix_m2})")
    
    # 2. Enrichir coordinates depuis _api_data
    if not apartment.get('coordinates'):
        coordinates = enrich_coordinates(apartment)
        if coordinates:
            apartment['coordinates'] = coordinates
            updated = True
            print(f"   ✅ {apt_id}: coordinates ajoutées")
    
    # 3. Enrichir map_info
    map_info = enrich_map_info(apartment)
    if map_info != apartment.get('map_info', {}):
        apartment['map_info'] = map_info
        updated = True
        print(f"   ✅ {apt_id}: map_info enrichi")
    
    # 4. Enrichir localisation_precise depuis coordinates
    if not apartment.get('localisation_precise'):
        localisation_precise = enrich_localisation(apartment)
        if localisation_precise:
            apartment['localisation_precise'] = localisation_precise
            updated = True
            print(f"   ✅ {apt_id}: localisation_precise ajoutée")
    
    # 5. Améliorer le format de localisation
    if apartment.get('localisation'):
        new_localisation = enrich_localisation_format(apartment)
        if new_localisation and new_localisation != apartment.get('localisation'):
            apartment['localisation'] = new_localisation
            updated = True
            print(f"   ✅ {apt_id}: localisation formatée")
    
    return apartment, updated


def complete_all_missing_data():
    """Complète les données manquantes pour tous les appartements"""
    print("🔧 COMPLÉTION DES DONNÉES MANQUANTES")
    print("=" * 60)
    print()
    
    # Charger les appartements
    apartments = load_existing_apartments()
    
    if not apartments:
        print("❌ Aucun appartement à traiter")
        return
    
    print(f"📊 Traitement de {len(apartments)} appartements...")
    print()
    
    updated_count = 0
    for i, apartment in enumerate(apartments, 1):
        apt_id = apartment.get('id', 'unknown')
        if i % 10 == 0:
            print(f"   [{i}/{len(apartments)}] Traitement...")
        
        apartment, updated = complete_apartment_data(apartment)
        apartments[i-1] = apartment
        
        if updated:
            updated_count += 1
    
    print()
    print(f"✅ {updated_count} appartements mis à jour")
    print()
    
    # Sauvegarder
    print("💾 Sauvegarde...")
    output_file = Path('data/scraped_apartments.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ Données sauvegardées dans {output_file}")
    print()
    print("🎉 Complétion terminée !")


if __name__ == "__main__":
    complete_all_missing_data()

