#!/usr/bin/env python3
"""
Géocodage inverse - Conversion coordonnées GPS → Adresse précise
Utilise Nominatim (OpenStreetMap) - gratuit, pas besoin d'API key
"""

import time
import requests
from typing import Optional, Dict, Any


def reverse_geocode(lat: float, lng: float, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """
    Convertit des coordonnées GPS en adresse précise (géocodage inverse)
    
    Args:
        lat: Latitude
        lng: Longitude
        timeout: Timeout en secondes
    
    Returns:
        Dict avec les informations d'adresse ou None si erreur
    """
    if lat is None or lng is None:
        return None
    
    # URL Nominatim (OpenStreetMap) - gratuit, pas besoin d'API key
    url = "https://nominatim.openstreetmap.org/reverse"
    
    params = {
        'lat': lat,
        'lon': lng,
        'format': 'json',
        'addressdetails': 1,
        'accept-language': 'fr'
    }
    
    headers = {
        'User-Agent': 'HomeScore/1.0 (apartment scoring system)'  # Requis par Nominatim
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        
        if 'error' in data:
            return None
        
        # Extraire l'adresse
        address = data.get('address', {})
        
        # Construire l'adresse complète
        address_parts = []
        
        # Numéro et rue
        if address.get('house_number'):
            address_parts.append(address['house_number'])
        if address.get('road'):
            address_parts.append(address['road'])
        
        # Code postal
        postal_code = address.get('postcode', '')
        
        # Ville et arrondissement (pour Paris)
        city = address.get('city') or address.get('town') or address.get('village', '')
        suburb = address.get('suburb', '')
        
        # Gérer les arrondissements de Paris
        if 'paris' in city.lower():
            # Extraire l'arrondissement depuis suburb si disponible
            if suburb:
                # Nettoyer suburb (peut être "Paris 19e Arrondissement" ou juste "19e Arrondissement")
                suburb_clean = suburb.replace('Paris', '').replace('Arrondissement', '').strip()
                # Extraire le numéro d'arrondissement
                import re
                arr_match = re.search(r'(\d+)', suburb_clean)
                if arr_match:
                    arr_num = arr_match.group(1)
                    city = f"Paris {arr_num}e"
            # Sinon, utiliser le code postal pour déterminer l'arrondissement
            elif postal_code and postal_code.startswith('75'):
                arr_num = postal_code[-2:]  # Derniers 2 chiffres
                if arr_num.isdigit() and int(arr_num) <= 20:
                    city = f"Paris {arr_num}e"
        elif city:
            # Pour les autres villes, garder tel quel
            pass
        
        # Construire l'adresse complète
        street_address = ' '.join(address_parts) if address_parts else None
        
        result = {
            'street_address': street_address,
            'postal_code': postal_code,
            'city': city,
            'full_address': None,
            'raw': data  # Données brutes pour debug
        }
        
        # Construire l'adresse complète formatée (format propre)
        if street_address:
            if postal_code and city:
                result['full_address'] = f"{street_address}, {postal_code} {city}"
            elif city:
                result['full_address'] = f"{street_address}, {city}"
            else:
                result['full_address'] = street_address
        elif postal_code and city:
            result['full_address'] = f"{postal_code} {city}"
        elif city:
            result['full_address'] = city
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erreur géocodage inverse: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Erreur inattendue: {e}")
        return None


def get_precise_location(apartment: Dict[str, Any]) -> Optional[str]:
    """
    Récupère la localisation précise d'un appartement depuis ses coordonnées GPS
    
    Args:
        apartment: Dict avec les données de l'appartement
    
    Returns:
        Adresse précise ou None si indisponible
    """
    # Essayer d'abord depuis coordinates
    coordinates = apartment.get('coordinates', {})
    lat = coordinates.get('latitude')
    lng = coordinates.get('longitude')
    
    # Fallback sur _api_data
    if lat is None or lng is None:
        api_data = apartment.get('_api_data', {})
        lat = api_data.get('lat')
        lng = api_data.get('lng')
    
    if lat is None or lng is None:
        return None
    
    # Faire le géocodage inverse
    address_data = reverse_geocode(lat, lng)
    
    if address_data and address_data.get('full_address'):
        return address_data['full_address']
    
    return None


def enrich_apartment_with_precise_location(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrichit un appartement avec sa localisation précise depuis les coordonnées GPS
    
    Args:
        apartment: Dict avec les données de l'appartement
    
    Returns:
        Appartement enrichi avec 'localisation_precise'
    """
    precise_location = get_precise_location(apartment)
    
    if precise_location:
        apartment['localisation_precise'] = precise_location
    
    return apartment


# Test
if __name__ == "__main__":
    import json
    from pathlib import Path
    
    print("🧪 TEST GÉOCODAGE INVERSE")
    print("=" * 60)
    
    # Test avec un appartement réel
    apt_file = Path('data/appartements/90931157.json')
    if apt_file.exists():
        with open(apt_file, 'r', encoding='utf-8') as f:
            apt = json.load(f)
        
        print(f"📋 Appartement: {apt.get('id')}")
        print(f"📍 Localisation actuelle: {apt.get('localisation')}")
        
        coords = apt.get('coordinates', {})
        lat = coords.get('latitude')
        lng = coords.get('longitude')
        
        if lat and lng:
            print(f"🌍 Coordonnées GPS: {lat}, {lng}")
            print()
            print("🔄 Géocodage inverse en cours...")
            
            address_data = reverse_geocode(lat, lng)
            
            if address_data:
                print("✅ Adresse trouvée:")
                print(f"   Rue: {address_data.get('street_address', 'N/A')}")
                print(f"   Code postal: {address_data.get('postal_code', 'N/A')}")
                print(f"   Ville: {address_data.get('city', 'N/A')}")
                print(f"   Adresse complète: {address_data.get('full_address', 'N/A')}")
            else:
                print("❌ Impossible de récupérer l'adresse")
        else:
            print("❌ Pas de coordonnées GPS disponibles")
    else:
        print("❌ Fichier de test non trouvé")
        
        # Test avec coordonnées de test (Place de la République, Paris)
        print()
        print("🧪 Test avec coordonnées de test (Place de la République)")
        lat_test = 48.8676
        lng_test = 2.3631
        print(f"🌍 Coordonnées: {lat_test}, {lng_test}")
        
        address_data = reverse_geocode(lat_test, lng_test)
        if address_data:
            print(f"✅ Adresse: {address_data.get('full_address', 'N/A')}")

