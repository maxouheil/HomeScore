"""
Critère Localisation - Extraction et formatage
Format: "Metro · Quartier"
"""

import re


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


def get_metro_name(apartment):
    """Extrait le nom du métro depuis différentes sources"""
    # Priorité 1: scores_detaille.localisation.justification (extrait par l'IA de scoring)
    scores_detaille = apartment.get('scores_detaille', {})
    localisation_score = scores_detaille.get('localisation', {})
    justification = localisation_score.get('justification', '')
    
    # Chercher "métro XXX" dans la justification
    metro_match = re.search(r'métro\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:[,\.]|\s+(?:zone|ligne|arrondissement)|\s*$)', justification, re.IGNORECASE)
    if metro_match:
        metro = metro_match.group(1).strip()
        # Vérifier que ce n'est pas un faux positif
        if metro and len(metro) > 2 and len(metro) < 50 and metro not in ['non trouvé', 'proximité', 'immédiate']:
            return metro
    
    # Chercher des noms de métros connus sans "métro" dans la justification
    known_metros = [
        'Philippe Auguste', 'Charonne', 'Pyrénées', 'Jourdain', 'Pelleport', 'Gambetta',
        'Ménilmontant', 'Alexandre Dumas', 'Rue des Boulets', 'Belleville', 'Couronnes',
        'Botzaris', 'Buttes-Chaumont', 'Place des Fêtes', 'Rébeval', 'Pyrénées',
        'Goncourt', 'République', 'Nation', 'Bastille', 'Gare de Lyon'
    ]
    for station in known_metros:
        if station in justification:
            return station
    
    # Priorité 2: map_info.metros (première station)
    map_info = apartment.get('map_info', {})
    metros = map_info.get('metros', [])
    if metros and len(metros) > 0:
        metro = metros[0].strip()
        # Nettoyer (enlever "métro " si présent)
        metro = re.sub(r'^métro\s+', '', metro, flags=re.IGNORECASE).strip()
        # Si trop long, extraire juste le nom de la station (avant le premier "-" ou ",")
        if len(metro) > 50:  # Si description longue
            metro = metro.split('-')[0].split(',')[0].strip()
        if metro and len(metro) > 2 and metro != "m" and len(metro) < 50:
            return metro
    
    # Priorité 3: transports (première station valide)
    transports = apartment.get('transports', [])
    for transport in transports:
        # Chercher une station de métro valide (nom + numéro de ligne potentiel)
        if re.search(r'^[A-Za-z\s\-éàèùîêôûçâë]+$', transport.strip()) and len(transport.strip()) > 2:
            # Vérifier que ce n'est pas un faux positif
            excluded = ['Paris', 'Entre', '€', 'm²', 'pièces', 'chambres']
            if not any(excl in transport for excl in excluded):
                return transport.strip()
    
    # Priorité 4: chercher dans la description (supporte "métro" et "métros")
    description = apartment.get('description', '')
    metro_match = re.search(r'métro\w*\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:,|\s+\(ligne|\s+[Ll]|\.|\s+et|\-)', description, re.IGNORECASE)
    if metro_match:
        metro = metro_match.group(1).strip()
        # Si trop long, extraire juste le nom de la station
        if len(metro) > 50:
            metro = metro.split('-')[0].split(',')[0].strip()
        if metro and len(metro) > 2 and len(metro) < 50:
            return metro
    
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

