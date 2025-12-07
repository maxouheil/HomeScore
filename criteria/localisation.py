"""
Critère Localisation - Extraction et formatage
Format: "Metro · Quartier"
"""

import re
import json
import os


def get_quartier_name(apartment):
    """Extrait le nom du quartier depuis différentes sources"""
    # Priorité 1: map_info.quartier
    map_info = apartment.get('map_info', {})
    quartier = map_info.get('quartier', '')
    
    # Nettoyer si c'est pas "Quartier non identifié"
    if quartier and quartier != "Quartier non identifié":
        # Enlever "(score: XX)" si présent
        quartier = re.sub(r'\s*\(score:\s*\d+\)', '', quartier).strip()
        if quartier and quartier != "Non identifié":
            return quartier
    
    # Priorité 2: scores_detaille.localisation.justification (extrait par l'IA de scoring)
    scores_detaille = apartment.get('scores_detaille', {})
    localisation_score = scores_detaille.get('localisation', {})
    justification = localisation_score.get('justification', '')
    
    # Chercher "quartier XXX" dans la justification
    quartier_match = re.search(r'quartier\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:[,\.])', justification, re.IGNORECASE)
    if quartier_match:
        quartier = quartier_match.group(1).strip()
        # Vérifier que ce n'est pas un faux positif
        if quartier and len(quartier) > 3 and quartier not in ['Non identifié', 'Non identifiée', 'correcte', 'bonnes zones']:
            return quartier
    
    # Priorité 3: exposition.details.photo_details.quartier
    exposition = apartment.get('exposition', {})
    details = exposition.get('details', {})
    photo_details = details.get('photo_details', {})
    quartier_data = photo_details.get('quartier', {})
    
    if isinstance(quartier_data, dict):
        quartier = quartier_data.get('quartier', '')
        if quartier and quartier not in ['Non identifié', 'Non identifiée']:
            # Enlever les suffixes de proximité
            quartier = re.sub(r'\s*\(proximité\)', '', quartier).strip()
            return quartier
    
    # Fallback: utiliser la localisation si elle contient un quartier spécifique
    localisation = apartment.get('localisation', '')
    # Chercher des patterns de quartiers connus dans la localisation
    quartiers_patterns = [
        r'Buttes[- ]Chaumont', r'Place des Fêtes', r'Place de la Réunion',
        r'Jourdain', r'Pyrénées', r'Belleville', r'Ménilmontant', r'Canal de l\'Ourcq'
    ]
    
    for pattern in quartiers_patterns:
        match = re.search(pattern, localisation, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None


def load_scoring_config():
    """Charge la configuration de scoring"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'scoring_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erreur chargement config pour métro: {e}")
        return None


def get_metro_tier(station_name, config=None):
    """
    Détermine le tier d'une station de métro selon scoring_config.json
    
    Returns:
        str: 'tier1', 'tier2', 'tier3', ou None si non trouvé
    """
    if not config:
        config = load_scoring_config()
    if not config:
        return None
    
    station_lower = station_name.lower().strip()
    tier_config = config.get('axes', {}).get('localisation', {}).get('tiers', {})
    
    # Mapping explicite des stations de métro par tier pour meilleure précision
    # Tier 1 stations
    tier1_stations = [
        'alexandre dumas', 'philippe auguste', 'belleville', 'ménilmontant', 'avron',
        'place de la réunion'
    ]
    
    # Tier 2 stations
    tier2_stations = [
        'goncourt', 'pyrénées', 'jourdain', 'rue des boulets', 'nation'
    ]
    
    # Vérifier d'abord avec le mapping explicite
    if station_lower in tier1_stations:
        return 'tier1'
    if station_lower in tier2_stations:
        return 'tier2'
    
    # Ensuite vérifier avec les zones du config (qui peuvent contenir des descriptions plus générales)
    # Vérifier tier1
    tier1_zones = [z.lower() for z in tier_config.get('tier1', {}).get('zones', [])]
    for zone in tier1_zones:
        # Vérifier si la zone est contenue dans le nom de la station ou vice versa
        # Utiliser un matching plus flexible (mots-clés)
        zone_words = set(zone.split())
        station_words = set(station_lower.split())
        # Si au moins 2 mots correspondent, c'est probablement la bonne zone
        if len(zone_words & station_words) >= 1 or zone in station_lower or station_lower in zone:
            return 'tier1'
    
    # Vérifier tier2
    tier2_zones = [z.lower() for z in tier_config.get('tier2', {}).get('zones', [])]
    for zone in tier2_zones:
        zone_words = set(zone.split())
        station_words = set(station_lower.split())
        if len(zone_words & station_words) >= 1 or zone in station_lower or station_lower in zone:
            return 'tier2'
    
    # Vérifier tier3
    tier3_zones = [z.lower() for z in tier_config.get('tier3', {}).get('zones', [])]
    for zone in tier3_zones:
        zone_words = set(zone.split())
        station_words = set(station_lower.split())
        if len(zone_words & station_words) >= 1 or zone in station_lower or station_lower in zone:
            return 'tier3'
    
    return None


def get_all_metro_stations(apartment):
    """
    Récupère TOUTES les stations de métro mentionnées dans l'annonce
    
    Returns:
        list: Liste de toutes les stations trouvées (nettoyées)
    """
    all_stations = []
    
    # Priorité 1: scores_detaille.localisation.justification (extrait par l'IA de scoring)
    scores_detaille = apartment.get('scores_detaille', {})
    localisation_score = scores_detaille.get('localisation', {})
    justification = localisation_score.get('justification', '')
    
    # Chercher "métro XXX" dans la justification
    metro_matches = re.findall(r'métro\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:[,\.]|\s+(?:zone|ligne|arrondissement)|\s*$)', justification, re.IGNORECASE)
    for metro in metro_matches:
        metro = metro.strip()
        if metro and len(metro) > 2 and len(metro) < 50 and metro not in ['non trouvé', 'proximité', 'immédiate']:
            all_stations.append(metro)
    
    # Chercher des noms de métros connus sans "métro" dans la justification
    known_metros = [
        'Philippe Auguste', 'Charonne', 'Pyrénées', 'Jourdain', 'Pelleport', 'Gambetta',
        'Ménilmontant', 'Alexandre Dumas', 'Rue des Boulets', 'Belleville', 'Couronnes',
        'Botzaris', 'Buttes-Chaumont', 'Place des Fêtes', 'Rébeval',
        'Goncourt', 'République', 'Nation', 'Bastille', 'Gare de Lyon', 'Avron'
    ]
    for station in known_metros:
        if station.lower() in justification.lower() and station not in all_stations:
            all_stations.append(station)
    
    # Priorité 2: map_info.metros (toutes les stations)
    map_info = apartment.get('map_info', {})
    metros = map_info.get('metros', [])
    for metro in metros:
        if isinstance(metro, str):
            # Nettoyer (enlever "métro " si présent)
            metro = re.sub(r'^métro\s+', '', metro, flags=re.IGNORECASE).strip()
            # Si trop long, extraire juste le nom de la station (avant le premier "-" ou ",")
            if len(metro) > 50:
                metro = metro.split('-')[0].split(',')[0].strip()
            if metro and len(metro) > 2 and metro != "m" and len(metro) < 50:
                # Extraire le nom de la station (enlever parenthèses, etc.)
                metro = re.sub(r'\s*\([^)]*\)', '', metro).strip()
                if metro and metro not in all_stations:
                    all_stations.append(metro)
    
    # Priorité 3: transports (toutes les stations valides)
    transports = apartment.get('transports', [])
    for transport in transports:
        if isinstance(transport, str):
            # Nettoyer le transport (enlever numéros de ligne, etc.)
            transport_clean = re.sub(r'\s+\d+\s*$', '', transport.strip())
            transport_clean = re.sub(r'\s*\([^)]*\)', '', transport_clean).strip()
            # Chercher une station de métro valide
            if re.search(r'^[A-Za-z\s\-éàèùîêôûçâë]+$', transport_clean) and len(transport_clean) > 2:
                # Vérifier que ce n'est pas un faux positif
                excluded = ['Paris', 'Entre', '€', 'm²', 'pièces', 'chambres', 'Proche']
                if not any(excl.lower() in transport_clean.lower() for excl in excluded):
                    if transport_clean not in all_stations:
                        all_stations.append(transport_clean)
    
    # Priorité 4: chercher dans la description (supporte "métro" et "métros")
    description = apartment.get('description', '')
    metro_matches_desc = re.findall(r'métro\w*\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:,|\s+\(ligne|\s+[Ll]|\.|\s+et|\-)', description, re.IGNORECASE)
    for metro in metro_matches_desc:
        metro = metro.strip()
        # Si trop long, extraire juste le nom de la station
        if len(metro) > 50:
            metro = metro.split('-')[0].split(',')[0].strip()
        if metro and len(metro) > 2 and len(metro) < 50:
            if metro not in all_stations:
                all_stations.append(metro)
    
    # Dédupliquer en préservant l'ordre
    seen = set()
    unique_stations = []
    for station in all_stations:
        station_lower = station.lower()
        if station_lower not in seen:
            seen.add(station_lower)
            unique_stations.append(station)
    
    return unique_stations


def get_metro_name(apartment):
    """
    Extrait le nom du métro - retourne la MEILLEURE station (tier 1 prioritaire)
    """
    # Récupérer toutes les stations disponibles
    all_stations = get_all_metro_stations(apartment)
    
    if not all_stations:
        return None
    
    # Charger la config pour classifier les stations
    config = load_scoring_config()
    
    # Classer les stations par tier (tier1 > tier2 > tier3 > None)
    stations_by_tier = {
        'tier1': [],
        'tier2': [],
        'tier3': [],
        'other': []
    }
    
    for station in all_stations:
        tier = get_metro_tier(station, config)
        if tier:
            stations_by_tier[tier].append(station)
        else:
            stations_by_tier['other'].append(station)
    
    # Retourner la première station du meilleur tier disponible
    if stations_by_tier['tier1']:
        return stations_by_tier['tier1'][0]
    elif stations_by_tier['tier2']:
        return stations_by_tier['tier2'][0]
    elif stations_by_tier['tier3']:
        return stations_by_tier['tier3'][0]
    elif stations_by_tier['other']:
        # Si aucune station n'est dans un tier connu, retourner la première trouvée
        return stations_by_tier['other'][0]
    
    return None


def format_localisation(apartment):
    """
    Formate le critère Localisation: "Metro · Quartier"
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Metro Ménilmontant · Sorbier"
            - confidence: None (données factuelles)
            - indices: None
    """
    metro = get_metro_name(apartment)
    quartier = get_quartier_name(apartment)
    
    parts = []
    if metro:
        parts.append(f"Metro {metro}")
    if quartier:
        parts.append(quartier)
    
    if parts:
        return {
            'main_value': " · ".join(parts),
            'confidence': None,  # Données factuelles, pas de confiance
            'indices': None
        }
    else:
        return {
            'main_value': "Non spécifié",
            'confidence': None,
            'indices': None
        }

