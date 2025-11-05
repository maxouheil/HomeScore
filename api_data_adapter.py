#!/usr/bin/env python3
"""
Adaptateur de données API → Format scraping
Convertit les données de l'API Jinka vers le format utilisé par le système de scoring existant
"""

from typing import Dict, Any, List, Optional


def adapt_api_to_scraped_format(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit les données de l'API vers le format scraping actuel
    
    Args:
        api_data: Données brutes de l'API (format de /apiv2/alert/{token}/ad/{id})
    
    Returns:
        Données au format scraping compatible avec scoring existant
    """
    if 'ad' not in api_data:
        raise ValueError("Format API invalide: clé 'ad' manquante")
    
    ad = api_data['ad']
    
    # Extraire les données de base
    apartment_id = str(ad.get('id', ''))
    
    # Format prix (convertir number → string formaté)
    rent = ad.get('rent', 0)
    prix_str = f"{rent:,} €".replace(',', ' ')
    
    # Format surface (convertir number → string)
    area = ad.get('area', 0)
    surface_str = f"{area} m²"
    
    # Format pièces (convertir number → string)
    room = ad.get('room', 0)
    pieces_str = f"{room} pièces"
    
    # Prix/m² calculé
    prix_m2 = None
    if rent and area and area > 0:
        prix_m2 = rent // area
        prix_m2_str = f"{prix_m2} € / m²"
    else:
        prix_m2_str = None
    
    # Localisation
    city = ad.get('city', '')
    postal_code = ad.get('postal_code', '')
    localisation = f"{city} ({postal_code})" if postal_code else city
    
    # Coordonnées GPS
    lat = ad.get('lat')
    lng = ad.get('lng')
    coordinates = None
    if lat is not None and lng is not None:
        coordinates = {
            'latitude': lat,
            'longitude': lng,
            'raw_x': None,  # Non disponible via API
            'raw_y': None,  # Non disponible via API
            'scale': 1.0
        }
    
    # Transports (convertir stops[] → array de strings)
    transports = []
    stops = ad.get('stops', [])
    for stop in stops:
        stop_name = stop.get('name', '')
        if stop_name:
            transports.append(stop_name)
    
    # Photos (convertir CSV → array d'objets)
    photos = _convert_images_to_photos(ad.get('images', ''), area, ad.get('floor'))
    
    # Caractéristiques (convertir features{} → string)
    caracteristiques = _convert_features_to_string(ad.get('features', {}))
    
    # Étage (convertir number → string)
    etage_str = None
    floor = ad.get('floor')
    if floor is not None:
        if floor == 0:
            etage_str = "RDC"
        elif floor == 1:
            etage_str = "1er étage"
        else:
            etage_str = f"{floor}e étage"
    
    # Agence
    agence = ad.get('source_label', '')
    
    # Description
    description = ad.get('description', '')
    
    # Date (ISO → string formatée si nécessaire)
    created_at = ad.get('created_at', '')
    date_str = created_at  # Garder format ISO pour compatibilité
    
    # Titre (construit depuis les données)
    bedroom = ad.get('bedroom', 0)
    if bedroom > 0:
        titre = f"{city} - {surface_str} - {pieces_str} - {bedroom} chambres"
    else:
        titre = f"{city} - {surface_str} - {pieces_str}"
    
    # Map info (quartier depuis API)
    quartier_name = ad.get('quartier_name')
    map_info = {
        'streets': [],  # Non disponible via API directement
        'metros': transports,
        'quartier': quartier_name if quartier_name else None,
        'screenshot': None  # Nécessiterait génération séparée
    }
    
    # Construire l'objet final
    adapted_data = {
        'id': apartment_id,
        'url': f"https://www.jinka.fr/alert_result?token={api_data.get('token', '')}&ad={apartment_id}",
        'scraped_at': created_at,  # Utiliser created_at comme date de scraping
        'titre': titre,
        'prix': prix_str,
        'prix_m2': prix_m2_str,
        'localisation': localisation,
        'coordinates': coordinates,
        'map_info': map_info,
        'surface': surface_str,
        'pieces': pieces_str,
        'date': date_str,
        'transports': transports,
        'description': description,
        'photos': photos,
        'caracteristiques': caracteristiques,
        'etage': etage_str,
        'agence': agence,
        # Champs supplémentaires de l'API (conservés pour référence)
        '_api_data': {
            'rent': rent,
            'area': area,
            'room': room,
            'bedroom': bedroom,
            'floor': floor,
            'lat': lat,
            'lng': lng,
            'city': city,
            'postal_code': postal_code,
            'quartier_name': quartier_name,
            'type': ad.get('type'),
            'features': ad.get('features', {}),
            'furnished': ad.get('furnished'),
            'created_at': created_at,
            'expired_at': ad.get('expired_at'),
            'source': ad.get('source'),
            'source_label': agence,
            'source_logo': ad.get('source_logo'),
            'owner_type': ad.get('owner_type'),
            'buy_type': ad.get('buy_type'),
            'price_sector': ad.get('price_sector'),
            'fees': ad.get('fees', {}),
            'dpe_infos': ad.get('dpe_infos'),
            'favorite': ad.get('favorite'),
        }
    }
    
    return adapted_data


def _convert_images_to_photos(images_csv: str, area: Optional[int] = None, floor: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Convertit la string CSV d'images en array d'objets photos
    
    Args:
        images_csv: String CSV d'URLs d'images
        area: Surface pour générer alt text
        floor: Étage pour générer alt text
    
    Returns:
        Array d'objets {url, alt, selector}
    """
    if not images_csv:
        return []
    
    # Split par virgule et nettoyer
    urls = [url.strip() for url in images_csv.split(',') if url.strip()]
    
    # Générer alt text
    alt_parts = []
    if area:
        alt_parts.append(f"{area} m²")
    if floor is not None:
        if floor == 0:
            alt_parts.append("RDC")
        elif floor == 1:
            alt_parts.append("1er étage")
        else:
            alt_parts.append(f"{floor}e étage")
    
    alt_text = " · ".join(alt_parts) if alt_parts else "Photo appartement"
    
    # Construire array de photos
    photos = []
    for i, url in enumerate(urls):
        photos.append({
            'url': url,
            'alt': alt_text,
            'selector': 'api_images',
            'width': None,  # Non disponible directement via API
            'height': None  # Non disponible directement via API
        })
    
    return photos


def _convert_features_to_string(features: Dict[str, Any]) -> str:
    """
    Convertit l'objet features{} en string de caractéristiques
    
    Args:
        features: Objet features de l'API
    
    Returns:
        String formatée des caractéristiques
    """
    if not features:
        return "Caractéristiques non disponibles"
    
    caracteristiques_parts = []
    
    # Mapping des features vers texte français
    feature_map = {
        'lift': ('Ascenseur', lambda v: v == 1),
        'bath': ('Baignoire', lambda v: v is not None and v == 1),
        'shower': ('Douche', lambda v: v == 1),
        'parking': ('Parking', lambda v: v == 1),
        'box': ('Box', lambda v: v is not None and v == 1),
        'balcony': ('Balcon', lambda v: v == 1),
        'terracy': ('Terrasse', lambda v: v == 1),
        'cave': ('Cave', lambda v: v == 1),
        'garden': ('Jardin', lambda v: v == 1),
    }
    
    for key, (label, check) in feature_map.items():
        value = features.get(key)
        if check(value):
            caracteristiques_parts.append(label)
    
    # Ajouter l'étage si disponible
    floor = features.get('floor')
    if floor is not None:
        if floor == 0:
            caracteristiques_parts.append("RDC")
        elif floor == 1:
            caracteristiques_parts.append("1er étage")
        else:
            caracteristiques_parts.append(f"{floor}e étage")
    
    # Ajouter année si disponible
    year = features.get('year')
    if year:
        caracteristiques_parts.append(f"Année: {year}")
    
    if caracteristiques_parts:
        return " ".join(caracteristiques_parts)
    else:
        return "Caractéristiques non disponibles"


def adapt_dashboard_to_apartment_list(dashboard_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Convertit les données du dashboard en liste d'appartements
    
    Args:
        dashboard_data: Données du dashboard (format de /apiv2/alert/{token}/dashboard)
    
    Returns:
        Liste d'appartements avec id et url de base
    """
    if 'ads' not in dashboard_data:
        return []
    
    apartments = []
    for ad in dashboard_data['ads']:
        apartment_id = str(ad.get('id', ''))
        if apartment_id:
            apartments.append({
                'id': apartment_id,
                'url': f"https://www.jinka.fr/alert_result?token={dashboard_data.get('token', '')}&ad={apartment_id}"
            })
    
    return apartments


# Test
if __name__ == "__main__":
    import json
    from pathlib import Path
    
    # Charger un exemple de données API
    test_file = Path('data/api_exploration/api_responses_detailed.json')
    if test_file.exists():
        with open(test_file, 'r') as f:
            responses = json.load(f)
        
        # Trouver la réponse "Property Details"
        for response in responses:
            if response.get('endpoint') == 'Property Details':
                api_data = response.get('data', {})
                print("🔍 Test de l'adaptateur...")
                print("=" * 60)
                
                adapted = adapt_api_to_scraped_format(api_data)
                
                print("✅ Données adaptées:")
                print(f"   ID: {adapted['id']}")
                print(f"   Prix: {adapted['prix']}")
                print(f"   Surface: {adapted['surface']}")
                print(f"   Pièces: {adapted['pieces']}")
                print(f"   Localisation: {adapted['localisation']}")
                print(f"   Transports: {adapted['transports']}")
                print(f"   Photos: {len(adapted['photos'])} photos")
                print(f"   Caractéristiques: {adapted['caracteristiques']}")
                print(f"   Étage: {adapted['etage']}")
                print(f"   Agence: {adapted['agence']}")
                
                break
    else:
        print("❌ Fichier de test non trouvé")

