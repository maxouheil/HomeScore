"""
Critère Calme - Détection du calme d'un quartier via OpenStreetMap Overpass API et Nominatim
Utilise l'adresse exacte pour déterminer le type de rue, plus bars/restos et commerces agités dans 100m
Pondération égale: 33% type de rue, 33% bars/restos, 33% commerces agités
"""

import json
import os
import re
import time
import hashlib
import requests
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

# Cache directory pour éviter requêtes répétées
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cache', 'calme')
CACHE_DURATION_DAYS = 30  # Conserver le cache 30 jours


def ensure_cache_dir():
    """Crée le répertoire de cache s'il n'existe pas"""
    os.makedirs(CACHE_DIR, exist_ok=True)


def get_cache_key(latitude: float, longitude: float, radius: int) -> str:
    """Génère une clé de cache basée sur les coordonnées et le rayon"""
    # Arrondir les coordonnées à 4 décimales pour regrouper les requêtes proches
    lat_rounded = round(latitude, 4)
    lon_rounded = round(longitude, 4)
    cache_key = f"{lat_rounded}_{lon_rounded}_{radius}"
    return hashlib.md5(cache_key.encode()).hexdigest()


def load_from_cache(cache_key: str) -> Optional[Dict]:
    """Charge les données depuis le cache si elles existent et sont récentes"""
    ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
        
        # Vérifier l'âge du cache
        cache_time = datetime.fromisoformat(cached_data.get('cache_time', ''))
        age = datetime.now() - cache_time
        
        if age < timedelta(days=CACHE_DURATION_DAYS):
            return cached_data.get('data')
        else:
            # Cache expiré, supprimer le fichier
            os.remove(cache_file)
            return None
    except Exception as e:
        print(f"⚠️ Erreur lecture cache: {e}")
        return None


def save_to_cache(cache_key: str, data: Dict):
    """Sauvegarde les données dans le cache"""
    ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    try:
        cache_data = {
            'cache_time': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde cache: {e}")


def extract_address(apartment: Dict) -> Optional[str]:
    """
    Extrait l'adresse exacte depuis localisation ou localisation_precise
    
    Args:
        apartment: Dict avec les données de l'appartement
        
    Returns:
        Adresse extraite (ex: "35 Rue Mélingue") ou None
    """
    # Priorité 1: localisation_precise (adresse complète)
    localisation_precise = apartment.get('localisation_precise', '')
    if localisation_precise:
        # Extraire juste la partie adresse (avant la virgule si présente)
        # Ex: "35 Rue Mélingue, 75019 Paris 19e" -> "35 Rue Mélingue"
        address = localisation_precise.split(',')[0].strip()
        if address:
            return address
    
    # Priorité 2: localisation (peut contenir "Metro X · Adresse")
    localisation = apartment.get('localisation', '')
    if localisation:
        # Chercher un pattern d'adresse (numéro + rue/avenue/boulevard/etc.)
        # Pattern pour adresse: numéro suivi de rue/avenue/boulevard/etc.
        address_patterns = [
            r'(\d+\s+[Rr]ue\s+[^·,]+)',
            r'(\d+\s+[Aa]venue\s+[^·,]+)',
            r'(\d+\s+[Bb]oulevard\s+[^·,]+)',
            r'(\d+\s+[Pp]lace\s+[^·,]+)',
            r'(\d+\s+[Cc]ours\s+[^·,]+)',
            r'(\d+\s+[Vv]illa\s+[^·,]+)',
            r'(\d+\s+[Ii]mpasse\s+[^·,]+)',
            r'(\d+\s+[Aa]llée\s+[^·,]+)',
            r'(\d+\s+[Pp]assage\s+[^·,]+)',
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, localisation)
            if match:
                address = match.group(1).strip()
                if address:
                    return address
        
        # Si pas de pattern trouvé, essayer de prendre la partie après "·" si présente
        if '·' in localisation:
            parts = localisation.split('·')
            if len(parts) > 1:
                address = parts[-1].strip()
                # Vérifier que ça ressemble à une adresse (contient un chiffre)
                if re.search(r'\d', address):
                    return address
    
    return None


def geocode_address_nominatim(address: str) -> Optional[Tuple[float, float]]:
    """
    Géocode une adresse avec Nominatim OSM
    
    Args:
        address: Adresse à géocoder (ex: "35 Rue Mélingue")
        
    Returns:
        Tuple (latitude, longitude) ou None
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': f"{address}, Paris, France",
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'HomeScore/1.0'  # Nominatim requiert un User-Agent
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        if results and len(results) > 0:
            lat = float(results[0]['lat'])
            lon = float(results[0]['lon'])
            return (lat, lon)
        
        return None
    except Exception as e:
        print(f"⚠️ Erreur géocodage Nominatim pour '{address}': {e}")
        return None


def fetch_street_type_from_address(address: str, latitude: float, longitude: float) -> Dict:
    """
    Trouve le type de rue (highway) de l'adresse exacte en utilisant Nominatim + Overpass
    
    Args:
        address: Adresse exacte (ex: "35 Rue Mélingue")
        latitude: Latitude (peut être utilisée si Nominatim échoue)
        longitude: Longitude (peut être utilisée si Nominatim échoue)
        
    Returns:
        Dict avec le type de rue détecté
    """
    # Essayer d'abord de géocoder l'adresse avec Nominatim pour obtenir des coordonnées précises
    coords = geocode_address_nominatim(address)
    if coords:
        lat, lon = coords
    else:
        # Fallback sur les coordonnées fournies
        lat, lon = latitude, longitude
    
    # Utiliser Overpass pour trouver la rue (way) la plus proche dans un rayon de 10m
    query = f"""
    [out:json][timeout:25];
    (
      way["highway"](around:10,{lat},{lon});
    );
    out tags;
    """
    
    result = query_overpass_api(query)
    
    if not result or not result.get('elements'):
        return {
            'highway_type': None,
            'highway': None,
            'found': False
        }
    
    elements = result.get('elements', [])
    
    # Prendre le premier élément (le plus proche)
    if elements:
        element = elements[0]
        tags = element.get('tags', {})
        highway = tags.get('highway', '')
        
        return {
            'highway_type': highway,
            'highway': highway,
            'found': True,
            'address': address
        }
    
    return {
        'highway_type': None,
        'highway': None,
        'found': False
    }


def query_overpass_api(query: str, timeout: int = 25) -> Optional[Dict]:
    """
    Interroge l'API Overpass de OpenStreetMap
    
    Args:
        query: Requête Overpass QL
        timeout: Timeout en secondes
        
    Returns:
        Dict avec la réponse JSON ou None en cas d'erreur
    """
    url = "https://overpass-api.de/api/interpreter"
    
    try:
        response = requests.post(url, data=query, timeout=timeout)
        response.raise_for_status()
        
        result = response.json()
        
        # Vérifier s'il y a des erreurs dans la réponse
        if 'elements' not in result:
            print(f"⚠️ Réponse Overpass API invalide: {result}")
            return None
        
        return result
    except requests.exceptions.Timeout:
        print(f"⚠️ Timeout lors de la requête Overpass API")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erreur requête Overpass API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ Erreur décodage JSON Overpass API: {e}")
        return None


def fetch_bars_restos(latitude: float, longitude: float, radius: int = 100) -> Dict:
    """
    Compte les bars et restaurants dans un rayon autour des coordonnées
    
    Args:
        latitude: Latitude
        longitude: Longitude
        radius: Rayon de recherche en mètres (défaut: 100m)
        
    Returns:
        Dict avec le nombre de bars/restos
    """
    # Requête Overpass QL pour récupérer les bars/restaurants
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"^(restaurant|bar|pub|cafe|fast_food)$"](around:{radius},{latitude},{longitude});
      way["amenity"~"^(restaurant|bar|pub|cafe|fast_food)$"](around:{radius},{latitude},{longitude});
    );
    out;
    """
    
    result = query_overpass_api(query)
    
    if not result:
        return {
            'count': 0
        }
    
    elements = result.get('elements', [])
    
    return {
        'count': len(elements)
    }


def fetch_commerces_agites(latitude: float, longitude: float, radius: int = 100) -> Dict:
    """
    Compte les commerces "agités" (supermarchés, épiceries) dans un rayon autour des coordonnées
    
    Args:
        latitude: Latitude
        longitude: Longitude
        radius: Rayon de recherche en mètres (défaut: 100m)
        
    Returns:
        Dict avec le nombre de commerces agités
    """
    # Requête Overpass QL pour récupérer les supermarchés/épiceries
    query = f"""
    [out:json][timeout:25];
    (
      node["shop"~"^(supermarket|convenience|grocery)$"](around:{radius},{latitude},{longitude});
      way["shop"~"^(supermarket|convenience|grocery)$"](around:{radius},{latitude},{longitude});
    );
    out;
    """
    
    result = query_overpass_api(query)
    
    if not result:
        return {
            'count': 0
        }
    
    elements = result.get('elements', [])
    
    return {
        'count': len(elements)
    }


def fetch_calme_data(apartment: Dict, radius: int = 100) -> Dict:
    """
    Récupère toutes les données nécessaires pour calculer le score de calme
    Utilise le cache pour éviter les requêtes répétées
    
    Args:
        apartment: Dict avec les données de l'appartement (doit contenir coordinates et localisation/localisation_precise)
        radius: Rayon de recherche en mètres pour bars/restos et commerces (défaut: 100m)
        
    Returns:
        Dict avec toutes les données collectées
    """
    # Récupérer les coordonnées
    coordinates = apartment.get('coordinates', {})
    latitude = coordinates.get('latitude')
    longitude = coordinates.get('longitude')
    
    if not latitude or not longitude:
        return {
            'street_type': {'found': False},
            'bars_restos': {'count': 0},
            'commerces_agites': {'count': 0},
            'error': 'Coordonnées manquantes'
        }
    
    # Vérifier le cache (basé sur coordonnées + radius)
    cache_key = get_cache_key(latitude, longitude, radius)
    cached_data = load_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    # Récupérer les données depuis Overpass API
    print(f"📡 Récupération données calme depuis Overpass API pour ({latitude}, {longitude})...")
    
    # Extraire l'adresse exacte
    address = extract_address(apartment)
    
    # Récupérer le type de rue de l'adresse exacte
    street_type = None
    if address:
        street_type = fetch_street_type_from_address(address, latitude, longitude)
        # Délai réduit pour Nominatim (rate limit: 1 req/sec)
        time.sleep(1.1)  # 1.1s pour être sûr de respecter le rate limit
    else:
        street_type = {'found': False, 'highway': None}
    
    # Récupérer les bars/restos (rayon: 100m)
    bars_restos = fetch_bars_restos(latitude, longitude, radius=radius)
    
    # Délai réduit pour Overpass (rate limit plus souple: ~10 req/sec)
    time.sleep(0.2)  # 200ms suffisent pour Overpass
    
    # Récupérer les commerces agités (rayon: 100m)
    commerces_agites = fetch_commerces_agites(latitude, longitude, radius=radius)
    
    # Combiner les données
    calme_data = {
        'street_type': street_type,
        'bars_restos': bars_restos,
        'commerces_agites': commerces_agites,
        'address': address,
        'latitude': latitude,
        'longitude': longitude,
        'radius': radius,
        'fetch_time': datetime.now().isoformat()
    }
    
    # Sauvegarder dans le cache
    save_to_cache(cache_key, calme_data)
    
    return calme_data


def calculate_street_type_score(street_type: Dict) -> Dict:
    """
    Calcule le score pour le critère "type de rue" (pondération: 50% V2)
    
    Args:
        street_type: Dict avec le type de rue détecté (highway)
        
    Returns:
        Dict avec le score et les détails
    """
    highway = street_type.get('highway', '')
    found = street_type.get('found', False)
    
    if not found or not highway:
        # Si pas trouvé, score neutre
        return {
            'score': 0,
            'details': 'Type de rue non déterminé',
            'weight': 0.5  # V2: 50%
        }
    
    # Scoring simple selon le plan:
    # +100% si rue piétonne (calme)
    if highway == 'pedestrian':
        score = 100
        details = 'Rue piétonne'
    # 0% si rue résidentielle (neutre)
    elif highway == 'residential':
        score = 0
        details = 'Rue résidentielle'
    # -100% si axe routier (animé)
    elif highway in ['primary', 'secondary', 'tertiary', 'trunk', 'motorway']:
        score = -100
        details = f'Axe routier ({highway})'
    # Par défaut: score neutre pour autres types
    else:
        score = 0
        details = f'Rue ({highway})'
    
    return {
        'score': score,
        'details': details,
        'weight': 0.5,  # V2: 50% de pondération
        'highway': highway
    }


def calculate_bars_restos_score(bars_restos: Dict) -> Dict:
    """
    Calcule le score pour le critère "bars/restos" (pondération: 50% V2)
    
    Args:
        bars_restos: Dict avec le nombre de bars/restos
        
    Returns:
        Dict avec le score et les détails
    """
    count = bars_restos.get('count', 0)
    
    # Scoring selon le plan:
    # +100% si 0 bar/resto dans 100m (calme)
    if count == 0:
        score = 100
        details = f'{count} bar/resto dans 100m (calme)'
    # 0% si 1-2 bars/restos (moyen)
    elif count <= 2:
        score = 0
        details = f'{count} bars/restos dans 100m (moyen)'
    # -100% si >2 bars/restos (animé)
    else:
        score = -100
        details = f'{count} bars/restos dans 100m (animé)'
    
    return {
        'score': score,
        'details': details,
        'weight': 0.5,  # V2: 50% de pondération
        'count': count
    }


def calculate_commerces_agites_score(commerces_agites: Dict) -> Dict:
    """
    Calcule le score pour le critère "commerces agités" (pondération: 33%)
    
    Args:
        commerces_agites: Dict avec le nombre de commerces agités
        
    Returns:
        Dict avec le score et les détails
    """
    count = commerces_agites.get('count', 0)
    
    # Scoring selon le plan:
    # +100% si 0 supermarché/épicerie dans 100m (calme)
    if count == 0:
        score = 100
        details = f'{count} commerce agité dans 100m (calme)'
    # 0% si 1 commerce agité (moyen)
    elif count == 1:
        score = 0
        details = f'{count} commerce agité dans 100m (moyen)'
    # -100% si >1 commerce agité (animé)
    else:
        score = -100
        details = f'{count} commerces agités dans 100m (animé)'
    
    return {
        'score': score,
        'details': details,
        'weight': 0.33,  # 33% de pondération
        'count': count
    }


def calculate_calme_score(calme_data: Dict) -> Dict:
    """
    Calcule le score global de calme en combinant 2 sous-critères avec pondération égale (50% chacun)
    RÈGLE V2: 50% type de rue + 50% densité de bars
    
    Args:
        calme_data: Dict avec toutes les données collectées
        
    Returns:
        Dict avec le score global et les détails de chaque sous-critère
    """
    street_type = calme_data.get('street_type', {})
    bars_restos = calme_data.get('bars_restos', {})
    
    # Calculer les scores de chaque sous-critère
    rue_score = calculate_street_type_score(street_type)
    bars_restos_score = calculate_bars_restos_score(bars_restos)
    
    # RÈGLE V2: Pondération 50% type rue + 50% densité bars
    # Mettre à jour les poids
    rue_score['weight'] = 0.5
    bars_restos_score['weight'] = 0.5
    
    # Calculer le score pondéré global (pondération égale: 50% chacun)
    # Les scores sont en pourcentage (-100 à +100), on les pondère puis on les additionne
    total_score = (
        rue_score['score'] * rue_score['weight'] +
        bars_restos_score['score'] * bars_restos_score['weight']
    )
    
    # Convertir en score normalisé de 0 à 100 (où 100 = très calme, 0 = très animé)
    # Score total peut aller de -100 à +100, on le convertit en 0-100
    normalized_score = ((total_score + 100) / 200) * 100
    normalized_score = max(0, min(100, normalized_score))  # Clamper entre 0 et 100
    
    # Construire la justification
    justification_parts = []
    justification_parts.append(rue_score['details'])
    justification_parts.append(bars_restos_score['details'])
    justification = ', '.join(justification_parts)
    
    return {
        'total_score': round(normalized_score, 1),
        'normalized_score': round(normalized_score, 1),
        'raw_score': round(total_score, 1),
        'justification': justification,
        'details': {
            'type_rue': {
                'score': rue_score['score'],
                'details': rue_score['details'],
                'weight': rue_score['weight'],
                'highway': rue_score.get('highway')
            },
            'bars_restos': {
                'score': bars_restos_score['score'],
                'details': bars_restos_score['details'],
                'weight': bars_restos_score['weight'],
                'count': bars_restos_score.get('count', 0)
            }
        },
        'source': 'overpass_api'
    }


def format_calme(apartment):
    """
    Formate le critère Calme selon les règles V2
    
    Règles:
    - 50% type de rue + 50% densité de bars
    - Good: Très calme (rue piétonne, 0 bar/resto)
    - Moyen: Moyennement calme
    - Bad: Animé (axe routier, nombreux bars/restos)
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Calme" | "Moyennement calme" | "Animé"
            - confidence: 70-90
            - indices: "Calme Indice:\nRue résidentielle · 1 bar/resto dans 100m"
    """
    # Récupérer les données de calme
    calme_data = apartment.get('calme', {})
    
    # Si pas de données, essayer de les calculer
    if not calme_data or not calme_data.get('details'):
        # Les données doivent être calculées avant l'affichage
        # Pour l'instant, retourner non spécifié
        return {
            'main_value': "Non spécifié",
            'confidence': None,
            'indices': "Calme Indice:\nNon spécifié"
        }
    
    # Calculer le score si pas déjà fait
    if 'total_score' not in calme_data:
        calme_data = calculate_calme_score(calme_data)
    
    total_score = calme_data.get('total_score', 50)
    details = calme_data.get('details', {})
    
    # Classification selon le score
    if total_score >= 60:
        main_value = "Calme"
        tier = "tier1"
    elif total_score >= 40:
        main_value = "Moyennement calme"
        tier = "tier2"
    else:
        main_value = "Animé"
        tier = "tier3"
    
    # Construire les indices
    indices_parts = []
    
    type_rue_details = details.get('type_rue', {})
    if type_rue_details.get('details'):
        indices_parts.append(type_rue_details['details'])
    
    bars_restos_details = details.get('bars_restos', {})
    if bars_restos_details.get('details'):
        indices_parts.append(bars_restos_details['details'])
    
    indices_str = "Calme Indice:\n" + " · ".join(indices_parts) if indices_parts else "Calme Indice:\nNon spécifié"
    
    return {
        'main_value': main_value,
        'confidence': 80,  # Confiance moyenne pour analyse OSM
        'indices': indices_str,
        'tier': tier  # Pour scoring
    }


