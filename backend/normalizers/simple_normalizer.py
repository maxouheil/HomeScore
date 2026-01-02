#!/usr/bin/env python3
"""
Normaliseur simple pour standardiser les données d'appartements
Unifie les formats API et scraping vers un format unique
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# Ajouter le répertoire parent pour importer les modules criteria
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from criteria import (
        format_localisation, format_prix, format_style, format_exposition,
        format_cuisine, format_baignoire, format_hauteur, format_piece_vie
    )
    from criteria.prix import get_arrondissement_median_price
except ImportError as e:
    print(f"⚠️ Erreur import criteria: {e}")
    # Fallback: fonctions vides
    def format_localisation(apt): return {'title': '', 'description': '', 'indices': None}
    def format_prix(apt): return {'title': '', 'description': ''}
    def format_style(apt): return {'title': '', 'description': '', 'indices': None}
    def format_exposition(apt): return {'title': '', 'description': None, 'indices': None}
    def format_cuisine(apt): return {'title': '', 'description': None, 'indices': None}
    def format_baignoire(apt): return {'title': '', 'description': None, 'indices': None}
    def format_hauteur(apt): return {'title': '', 'description': None, 'indices': None}
    def format_piece_vie(apt): return {'title': '', 'description': None, 'indices': None}
    def get_arrondissement_median_price(postal_code): return None


def normalize_apartment(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise un appartement vers le format standard.
    Gère les sources API et scraping.
    
    IMPORTANT: Les appartements n'ont PAS de score absolu par défaut.
    Les scores sont calculés dynamiquement selon les critères choisis dans une alerte.
    """
    normalized = {
        'id': apartment.get('id', ''),
        'url': apartment.get('url', ''),
        'titre': apartment.get('titre', ''),
        
        # Données de base (normaliser depuis API ou scraping)
        'prix': _extract_prix(apartment),
        'prix_formatted': _format_prix(apartment),
        'prix_m2': _extract_prix_m2(apartment),
        'prix_m2_formatted': _format_prix_m2(apartment),
        'surface': _extract_surface(apartment),
        'surface_formatted': _format_surface(apartment),
        'pieces': _extract_pieces(apartment),
        'pieces_formatted': _format_pieces(apartment),
        'chambres': _extract_chambres(apartment),
        'etage': _extract_etage(apartment),
        'date_creation_annonce': apartment.get('date_creation_annonce') or apartment.get('scraped_at', ''),
        
        # Localisation (unifier map_info, _api_data, localisation)
        'localisation': _normalize_localisation(apartment),
        
        # Photos (normaliser URLs)
        'photos': _normalize_photos(apartment),
        
        # Critères (unifier formatted_data, scores_detaille)
        # IMPORTANT: Pas de score total, seulement scores individuels des critères
        'criteria': _normalize_criteria(apartment),
        
        # Métadonnées
        'metadata': {
            'source': 'api' if apartment.get('_api_data') else 'scraping',
            'normalized_at': datetime.now().isoformat()
        }
    }
    
    return normalized


def _extract_prix(apartment: Dict[str, Any]) -> int:
    """Extrait le prix en nombre depuis API ou scraping"""
    # Priorité: API
    api_data = apartment.get('_api_data', {})
    if api_data.get('rent'):
        return int(api_data['rent'])
    
    # Fallback: parsing depuis string
    prix_str = apartment.get('prix', '')
    if prix_str:
        match = re.search(r'([\d\s]+)', prix_str.replace(' ', ''))
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    
    return 0


def _format_prix(apartment: Dict[str, Any]) -> str:
    """Formate le prix en string"""
    prix = _extract_prix(apartment)
    if prix > 0:
        return f"{prix:,} €".replace(',', ' ')
    return apartment.get('prix', '')


def _extract_prix_m2(apartment: Dict[str, Any]) -> int:
    """Extrait le prix/m² en nombre"""
    prix = _extract_prix(apartment)
    surface = _extract_surface(apartment)
    
    if prix > 0 and surface > 0:
        return prix // surface
    
    # Fallback: parsing depuis prix_m2 string
    prix_m2_str = apartment.get('prix_m2', '')
    if prix_m2_str:
        match = re.search(r'(\d+)', prix_m2_str.replace(' ', ''))
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    
    return 0


def _format_prix_m2(apartment: Dict[str, Any]) -> str:
    """Formate le prix/m² en string"""
    prix_m2 = _extract_prix_m2(apartment)
    if prix_m2 > 0:
        return f"{prix_m2:,} €/m²".replace(',', ' ')
    return apartment.get('prix_m2', '')


def _extract_surface(apartment: Dict[str, Any]) -> int:
    """Extrait la surface en m² depuis API ou scraping"""
    # Priorité: API
    api_data = apartment.get('_api_data', {})
    if api_data.get('area'):
        return int(api_data['area'])
    
    # Fallback: parsing depuis string
    surface_str = apartment.get('surface', '')
    if surface_str:
        match = re.search(r'(\d+)', surface_str)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    
    return 0


def _format_surface(apartment: Dict[str, Any]) -> str:
    """Formate la surface en string"""
    surface = _extract_surface(apartment)
    if surface > 0:
        return f"{surface} m²"
    return apartment.get('surface', '')


def _extract_pieces(apartment: Dict[str, Any]) -> int:
    """Extrait le nombre de pièces depuis API ou scraping"""
    # Priorité: API
    api_data = apartment.get('_api_data', {})
    if api_data.get('room'):
        return int(api_data['room'])
    
    # Fallback: parsing depuis string
    pieces_str = apartment.get('pieces', '')
    if pieces_str:
        match = re.search(r'(\d+)', pieces_str)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    
    return 0


def _format_pieces(apartment: Dict[str, Any]) -> str:
    """Formate le nombre de pièces en string"""
    pieces = _extract_pieces(apartment)
    if pieces > 0:
        return f"{pieces} pièces"
    return apartment.get('pieces', '')


def _extract_chambres(apartment: Dict[str, Any]) -> int:
    """Extrait le nombre de chambres depuis API ou scraping"""
    # Priorité: API
    api_data = apartment.get('_api_data', {})
    if api_data.get('bedroom') is not None:
        return int(api_data['bedroom'])
    
    # Fallback: parsing depuis description ou caracteristiques
    description = apartment.get('description', '')
    caracteristiques = apartment.get('caracteristiques', '')
    text = f"{description} {caracteristiques}"
    
    # Chercher "X chambre(s)"
    match = re.search(r'(\d+)\s*chambre', text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except:
            pass
    
    return 0


def _extract_etage(apartment: Dict[str, Any]) -> Optional[str]:
    """Extrait l'étage depuis API ou scraping"""
    # Priorité: API
    api_data = apartment.get('_api_data', {})
    floor = api_data.get('floor')
    if floor is not None:
        if floor == 0:
            return "RDC"
        elif floor == 1:
            return "1er étage"
        else:
            return f"{floor}e étage"
    
    # Fallback: depuis etage string
    etage_str = apartment.get('etage', '')
    if etage_str:
        return etage_str
    
    # Fallback: parsing depuis description
    description = apartment.get('description', '')
    if description:
        # Chercher "Xe étage" ou "RDC"
        match = re.search(r'(\d+)(?:er?|e|ème?)\s*étage|RDC|rez-de-chaussée|rez de chaussée', description, re.IGNORECASE)
        if match:
            if 'RDC' in match.group(0) or 'rez' in match.group(0).lower():
                return "RDC"
            num_match = re.search(r'(\d+)', match.group(0))
            if num_match:
                num = int(num_match.group(1))
                if num == 1:
                    return "1er étage"
                return f"{num}e étage"
    
    return None


def _normalize_localisation(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise les données de localisation"""
    api_data = apartment.get('_api_data', {})
    map_info = apartment.get('map_info', {})
    localisation_str = apartment.get('localisation', '')
    
    # Coordonnées
    coordinates = {}
    if api_data.get('lat') and api_data.get('lng'):
        coordinates = {
            'lat': float(api_data['lat']),
            'lng': float(api_data['lng'])
        }
    elif apartment.get('coordinates'):
        coords = apartment['coordinates']
        if coords.get('latitude') and coords.get('longitude'):
            coordinates = {
                'lat': float(coords['latitude']),
                'lng': float(coords['longitude'])
            }
    
    # Quartier
    quartier = None
    if map_info.get('quartier') and map_info['quartier'] != 'Quartier non identifié':
        quartier = re.sub(r'\s*\(score:\s*\d+\)', '', map_info['quartier']).strip()
    elif api_data.get('quartier_name'):
        quartier = api_data['quartier_name']
    
    # Arrondissement
    arrondissement = None
    if api_data.get('postal_code'):
        arrondissement = api_data['postal_code']
    elif localisation_str:
        # Chercher un code postal au format 750XX dans la chaîne
        match = re.search(r'(75\d{3})', localisation_str)
        if match:
            arrondissement = match.group(1)
        else:
            # Chercher un pattern comme "20e" ou "20e arrondissement" et construire 75020
            match = re.search(r'(\d{1,2})e\s*(?:arrondissement|arr\.)?', localisation_str, re.IGNORECASE)
            if match:
                arr_num = match.group(1).zfill(2)
                if int(arr_num) <= 20:
                    arrondissement = f"75{arr_num}"
    
    # Métro
    metro = None
    metro_stations = []
    
    # Depuis API (stops)
    if api_data.get('stops'):
        for stop in api_data['stops']:
            station_name = stop.get('name', '')
            if station_name:
                metro_stations.append({
                    'name': station_name,
                    'lines': stop.get('lines', [])
                })
                if not metro:
                    metro = f"Métro {station_name}"
    
    # Depuis map_info.metros
    if not metro_stations and map_info.get('metros'):
        for metro_name in map_info['metros']:
            if metro_name:
                metro_stations.append({
                    'name': metro_name.replace('métro ', '').replace('Métro ', '').strip(),
                    'lines': []
                })
                if not metro:
                    metro = f"Métro {metro_name.replace('métro ', '').replace('Métro ', '').strip()}"
    
    # Adresse
    adresse = None
    if map_info.get('streets'):
        adresse = map_info['streets'][0]
    elif localisation_str:
        # Extraire l'adresse depuis localisation (format "Metro X · 34, rue X")
        parts = localisation_str.split(' · ')
        if len(parts) > 1:
            adresse = parts[1]
        elif not localisation_str.startswith('Metro'):
            adresse = localisation_str
    
    return {
        'adresse': adresse,
        'arrondissement': arrondissement,
        'quartier': quartier,
        'metro': metro,
        'metro_stations': metro_stations,
        'coordinates': coordinates
    }


def _normalize_photos(apartment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalise les photos"""
    photos = []
    
    # Depuis photos array
    photos_raw = apartment.get('photos', [])
    if photos_raw:
        for i, photo in enumerate(photos_raw):
            if isinstance(photo, str):
                url = photo
            elif isinstance(photo, dict):
                url = photo.get('url') or photo.get('local_path', '')
            else:
                continue
            
            if url and url.strip():
                # Déterminer si c'est local ou externe
                is_local = (
                    url.startswith('/data/photos/') or
                    url.startswith('../data/photos/') or
                    url.startswith('data/photos/') or
                    (not url.startswith('http') and not url.startswith('https'))
                )
                
                photos.append({
                    'url': url.strip(),
                    'index': i,
                    'is_local': is_local
                })
    
    # Depuis API (images CSV)
    api_data = apartment.get('_api_data', {})
    if not photos and api_data.get('images'):
        images_csv = api_data['images']
        urls = [url.strip() for url in images_csv.split(',') if url.strip()]
        for i, url in enumerate(urls):
            photos.append({
                'url': url,
                'index': i,
                'is_local': False
            })
    
    return photos


def _build_display_data(apartment: Dict[str, Any], criterion_name: str, score_data: Optional[Dict[str, Any]], formatted: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Construit les données d'affichage selon les spécifications:
    - Séparer données API (gris) et données IA (bleu)
    - Format spécifique pour chaque critère
    """
    api_data = apartment.get('_api_data', {}) or {}
    
    # localisation peut être une string ou un dict (format normalisé)
    localisation_raw = apartment.get('localisation', {})
    if isinstance(localisation_raw, str):
        # Format ancien: string, utiliser _normalize_localisation pour obtenir un dict
        localisation = _normalize_localisation(apartment)
    else:
        localisation = localisation_raw or {}
    
    map_info = apartment.get('map_info', {}) or {}
    
    # S'assurer que score_data et formatted sont des dicts
    if score_data is None:
        score_data = {}
    if formatted is None:
        formatted = {}
    
    if criterion_name == 'localisation':
        # Titre: métro
        metro = localisation.get('metro', '')
        if metro:
            # Enlever "Métro " si présent
            metro_name = metro.replace('Métro ', '').replace('metro ', '')
            title = f"Metro {metro_name}"
        else:
            title = 'Localisation'
        
        # Description: adresse (API, gris)
        adresse = localisation.get('adresse', '')
        description = adresse if adresse else None
        
        return {
            'title': title,
            'description': description,  # API, sera en gris
            'indices': None
        }
    
    elif criterion_name == 'prix':
        # #region agent log
        apt_id = apartment.get('id', 'unknown')
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            import time
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:prix_entry","message":"Prix debug - entry","data":{"apt_id":apt_id,"has_api_data":bool(api_data),"api_postal_code":api_data.get('postal_code', '') if api_data else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        # #endregion
        
        # Titre: X €/m²
        prix_m2 = _extract_prix_m2(apartment)
        if prix_m2 > 0:
            title = f"{prix_m2:,} €/m²".replace(',', ' ')
        else:
            title = 'Prix'
        
        # Description: "20e : X €/m² (médian: Y €/m²) · au dessus/dessous du marché"
        # Récupérer le code postal depuis api_data en priorité
        postal_code = api_data.get('postal_code', '')
        if not postal_code:
            # Fallback 1: chercher dans localisation normalisée
            arrondissement = localisation.get('arrondissement', '')
            if arrondissement and arrondissement.startswith('75'):
                postal_code = arrondissement
            else:
                # Fallback 2: chercher directement dans la chaîne localisation brute
                localisation_str = apartment.get('localisation', '')
                if isinstance(localisation_str, str):
                    # Chercher un code postal au format 750XX dans la chaîne
                    match = re.search(r'(75\d{3})', localisation_str)
                    if match:
                        postal_code = match.group(1)
                    else:
                        # Chercher un pattern comme "20e" ou "20e arrondissement" et construire 75020
                        match = re.search(r'(\d{1,2})e\s*(?:arrondissement|arr\.)?', localisation_str, re.IGNORECASE)
                        if match:
                            arr_num = match.group(1).zfill(2)
                            if int(arr_num) <= 20:
                                postal_code = f"75{arr_num}"
        
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            import time
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:prix_postal_code","message":"Prix debug - postal code retrieved","data":{"apt_id":apt_id,"postal_code":postal_code,"from_api_data":bool(api_data.get('postal_code', ''))},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        # #endregion
        
        arr_num = None
        if postal_code and postal_code.startswith('75'):
            arr_num = postal_code[-2:]
        
        # Récupérer le prix médian de l'arrondissement
        median_price = None
        if postal_code and postal_code.startswith('75'):
            try:
                median_price = get_arrondissement_median_price(postal_code)
                # #region agent log
                with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                    import json as json_module
                    import time
                    logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:prix_median_price","message":"Prix debug - median price retrieved","data":{"apt_id":apt_id,"postal_code":postal_code,"median_price":median_price},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
                # #endregion
            except Exception as e:
                # #region agent log
                with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                    import json as json_module
                    import time
                    logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:prix_median_error","message":"Prix debug - error getting median price","data":{"apt_id":apt_id,"postal_code":postal_code,"error":str(e)},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
                # #endregion
                pass
        
        # Déterminer le tier en fonction de la différence avec le médian (±500€ = du marché)
        tier = 'tier3'  # Par défaut: au dessus
        if median_price and prix_m2 > 0:
            diff = abs(prix_m2 - median_price)
            if diff <= 500:
                tier = 'tier2'  # Du marché si ±500€
            elif prix_m2 > median_price:
                tier = 'tier3'  # Au dessus
            else:
                tier = 'tier1'  # En dessous
        elif score_data and score_data.get('tier'):
            # Fallback sur score_data si pas de médian
            tier = score_data.get('tier')
        
        tier_text = 'Du marché' if tier == 'tier2' else 'Au dessus du marché' if tier == 'tier3' else 'En dessous du marché'
        
        # Arrondir le prix/m² à 500€ près
        prix_m2_rounded = round(prix_m2 / 500) * 500 if prix_m2 > 0 else 0
        
        if prix_m2 > 0:
            if arr_num:
                # Format: "Moyenne 20e: 8 500€ /m² · Au dessus du marché"
                description = f"Moyenne {arr_num}e: {prix_m2_rounded:,}€ /m² · {tier_text}".replace(',', ' ')
            else:
                # Format sans arrondissement: "8 500€ /m² · Au dessus du marché"
                description = f"{prix_m2_rounded:,}€ /m² · {tier_text}".replace(',', ' ')
        else:
            description = None
        
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            import time
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:prix_final","message":"Prix debug - final description","data":{"apt_id":apt_id,"description":description,"has_median":bool(median_price)},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
        # #endregion
        
        return {
            'title': title,
            'description': description,
            'indices': None
        }
    
    elif criterion_name == 'style':
        # Titre: déterminé depuis le style
        style_analysis = apartment.get('style_analysis', {})
        style_data = style_analysis.get('style', {})
        style_type = style_data.get('type', '')
        
        # Vérifier si on a une année de construction depuis API
        construction_year = None
        features = api_data.get('features')
        if features and isinstance(features, dict) and features.get('year'):
            construction_year = features['year']
        elif apartment.get('caracteristiques'):
            # Parser depuis caracteristiques
            caracteristiques = apartment.get('caracteristiques', '')
            if isinstance(caracteristiques, str):
                year_match = re.search(r'(\d{4})', caracteristiques)
                if year_match:
                    try:
                        construction_year = int(year_match.group(1))
                    except:
                        pass
        
        # Déterminer le titre depuis l'année ou le style
        if construction_year:
            if construction_year < 1910:
                title = 'Style Haussmannien'
            elif 1910 <= construction_year <= 1980:
                decade = (construction_year // 10) * 10
                title = f"Style années {str(decade)[-2:]}"
            else:
                title = 'Style Moderne'
        elif style_type:
            if 'haussmann' in style_type.lower():
                title = 'Style Haussmannien'
            elif '70' in style_type.lower():
                title = 'Style années 70'
            elif 'moderne' in style_type.lower():
                title = 'Style Moderne'
            else:
                title = f"Style {style_type.capitalize()}"
        else:
            title = 'Style'
        
        # Description: "construit en X" (API, gris) · indices (IA, bleu)
        description_parts = []
        indices_parts = []
        
        if construction_year:
            description_parts.append(f"Construit en {construction_year}")  # API, gris
        
        # Indices IA (moulures, cheminées, etc.)
        style_details = style_data.get('details') or {}
        if isinstance(style_details, dict):
            elements_detectes = style_details.get('elements_detectes', [])
            if elements_detectes and isinstance(elements_detectes, list):
                # Filtrer les éléments pertinents (moulures, cheminée, parquet, etc.)
                keywords = ['moulures', 'cheminée', 'parquet', 'corniche', 'balcon', 'fer forgé', 'moldings', 'fireplace']
                filtered_elements = [elem for elem in elements_detectes[:10] 
                                   if any(kw in str(elem).lower() for kw in keywords)]
                if filtered_elements:
                    # Capitaliser la première lettre
                    indices_parts.extend([str(elem).capitalize() for elem in filtered_elements[:5]])
                elif elements_detectes:
                    # Si pas de filtrage, prendre les premiers éléments
                    indices_parts.extend([str(elem).capitalize() for elem in elements_detectes[:5]])
        
        # Utiliser formatted_data.indices si disponible
        if formatted and isinstance(formatted, dict) and formatted.get('indices'):
            indices_str = formatted['indices']
            # Nettoyer le préfixe "Style Indice:"
            indices_str = indices_str.replace('Style Indice:\n', '').replace('Style Indice:', '').strip()
            if indices_str and 'Construit en' not in indices_str:
                # Extraire les mots-clés depuis les indices
                keywords_found = []
                for kw in ['moulures', 'cheminée', 'parquet', 'corniche', 'balcon']:
                    if kw in indices_str.lower():
                        keywords_found.append(kw.capitalize())
                if keywords_found and not indices_parts:
                    indices_parts.extend(keywords_found)
                elif not indices_parts and indices_str:
                    # Si pas de mots-clés trouvés, utiliser les indices tels quels
                    indices_parts.append(indices_str)
        
        description = ' · '.join(description_parts) if description_parts else None
        indices = ' · '.join(indices_parts) if indices_parts else None
        
        return {
            'title': title,
            'description': description,  # API, gris
            'indices': indices  # IA, bleu
        }
    
    elif criterion_name == 'exposition':
        # Titre: déterminé depuis le tier
        tier = score_data.get('tier', 'tier3') if score_data else 'tier3'
        if tier == 'tier1':
            title = 'Bonne luminosité'
        elif tier == 'tier2':
            title = 'Luminosité moyenne'
        else:
            title = 'Faible luminosité'
        
        # Description: étage (API, gris) · vis-à-vis (IA, bleu)
        description_parts = []
        indices_parts = []
        
        # Étage depuis API
        etage = _extract_etage(apartment)
        if etage:
            description_parts.append(etage)  # API, gris
        
        # Vis-à-vis depuis exposition.details (IA)
        exposition = apartment.get('exposition', {})
        exposition_details = exposition.get('details') or {}
        if isinstance(exposition_details, dict):
            visavis_dist = exposition_details.get('visavis_distance')
            visavis_cat = exposition_details.get('visavis_category')
            
            if visavis_dist is not None:
                if visavis_cat:
                    cat_fr = {'good': 'bon', 'moyen': 'moyen', 'bad': 'mauvais'}.get(visavis_cat, visavis_cat)
                    indices_parts.append(f"Vis a vis {cat_fr} ({visavis_dist}m)")
                else:
                    indices_parts.append(f"Vis a vis {visavis_dist}m")
        
        # Chercher aussi dans formatted_data
        if formatted and isinstance(formatted, dict) and formatted.get('indices'):
            indices_str = formatted['indices']
            visavis_match = re.search(r'Vis a vis (?:bon|moyen|mauvais)?\s*\(?(\d+)m\)?', indices_str, re.IGNORECASE)
            if visavis_match and not indices_parts:
                # Extraire aussi la catégorie si présente
                cat_match = re.search(r'Vis a vis (bon|moyen|mauvais)', indices_str, re.IGNORECASE)
                if cat_match:
                    cat_fr = cat_match.group(1).lower()
                    indices_parts.append(f"Vis a vis {cat_fr} ({visavis_match.group(1)}m)")
                else:
                    indices_parts.append(f"Vis a vis {visavis_match.group(1)}m")
        
        description = ' · '.join(description_parts) if description_parts else None
        indices = ' · '.join(indices_parts) if indices_parts else None
        
        return {
            'title': title,
            'description': description,  # API, gris
            'indices': indices  # IA, bleu
        }
    
    elif criterion_name == 'cuisine':
        # Titre: "Cuisine ouverte" ou "Cuisine fermée"
        cuisine_ouverte = None
        style_cuisine = apartment.get('style_analysis', {}).get('cuisine', {})
        if style_cuisine.get('ouverte') is not None:
            cuisine_ouverte = style_cuisine['ouverte']
        else:
            # Chercher dans photo_validation
            cuisine_score = apartment.get('scores_detaille', {}) or {}
            cuisine_score = cuisine_score.get('cuisine') or {}
            if isinstance(cuisine_score, dict):
                cuisine_details = cuisine_score.get('details')
                if cuisine_details and isinstance(cuisine_details, dict):
                    photo_validation = cuisine_details.get('photo_validation')
                    if photo_validation and isinstance(photo_validation, dict):
                        photo_result = photo_validation.get('photo_result') or {}
                        if isinstance(photo_result, dict):
                            cuisine_ouverte = photo_result.get('ouverte')
        
        if cuisine_ouverte is True:
            title = 'Cuisine ouverte'
        elif cuisine_ouverte is False:
            title = 'Cuisine fermée'
        else:
            title = 'Cuisine'
        
        # Description: "cuisine détectée image X" (IA, bleu)
        detected_photos = []
        if style_cuisine.get('detected_photos'):
            detected_photos = style_cuisine['detected_photos']
        else:
            cuisine_score = apartment.get('scores_detaille', {}) or {}
            cuisine_score = cuisine_score.get('cuisine') or {}
            if isinstance(cuisine_score, dict):
                cuisine_details = cuisine_score.get('details')
                if cuisine_details and isinstance(cuisine_details, dict):
                    photo_validation = cuisine_details.get('photo_validation')
                    if photo_validation and isinstance(photo_validation, dict):
                        photo_result = photo_validation.get('photo_result') or {}
                        if isinstance(photo_result, dict):
                            detected_photos = photo_result.get('detected_photos', [])
        
        # Description: "cuisine détectée image X" (IA, bleu) - mettre dans indices au lieu de description
        description = None
        indices = None
        photo_num = None
        
        # #region agent log
        apt_id = apartment.get('id', 'unknown')
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            import time
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:630","message":"Cuisine debug - entry","data":{"apt_id":apt_id,"cuisine_ouverte":cuisine_ouverte,"style_cuisine_detected_photos":style_cuisine.get('detected_photos'),"detected_photos":detected_photos,"style_cuisine_keys":list(style_cuisine.keys())},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        # #endregion
        
        # Priorité 1: Utiliser detected_photos si disponible
        if detected_photos and len(detected_photos) > 0:
            photo_num = detected_photos[0]
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                import time
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:653","message":"Cuisine debug - photo_num from detected_photos","data":{"apt_id":apt_id,"photo_num":photo_num},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
            # #endregion
        
        # Priorité 2: Extraire depuis la justification si pas de detected_photos
        if not photo_num:
            justification = style_cuisine.get('justification', '')
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                import time
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:658","message":"Cuisine debug - checking justification","data":{"apt_id":apt_id,"justification":justification[:200] if justification else None,"justification_length":len(justification) if justification else 0},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
            # #endregion
            if justification:
                # Chercher "image X" ou "photo X" (numéro en chiffres)
                img_match = re.search(r'(?:image|photo)\s+(\d+)', justification, re.IGNORECASE)
                if img_match:
                    photo_num = img_match.group(1)
                    # #region agent log
                    with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                        import json as json_module
                        import time
                        logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:662","message":"Cuisine debug - photo_num from justification (numeric)","data":{"apt_id":apt_id,"photo_num":photo_num},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
                    # #endregion
                else:
                    # Chercher les numéros en toutes lettres (première, deuxième, troisième, etc.)
                    french_numbers = {
                        'première': '1', 'premier': '1', '1ère': '1', '1er': '1',
                        'deuxième': '2', 'deuxieme': '2', '2ème': '2', '2eme': '2',
                        'troisième': '3', 'troisieme': '3', '3ème': '3', '3eme': '3',
                        'quatrième': '4', 'quatrieme': '4', '4ème': '4', '4eme': '4',
                        'cinquième': '5', 'cinquieme': '5', '5ème': '5', '5eme': '5',
                        'sixième': '6', 'sixieme': '6', '6ème': '6', '6eme': '6',
                        'septième': '7', 'septieme': '7', '7ème': '7', '7eme': '7',
                        'huitième': '8', 'huitieme': '8', '8ème': '8', '8eme': '8',
                        'neuvième': '9', 'neuvieme': '9', '9ème': '9', '9eme': '9',
                        'dixième': '10', 'dixieme': '10', '10ème': '10', '10eme': '10'
                    }
                    # Chercher "Xème photo" ou "photo Xème" ou "Xème image"
                    for num_word, num_value in french_numbers.items():
                        pattern = rf'(?:{num_word}|{num_value})\s+(?:photo|image)|(?:photo|image)\s+(?:{num_word}|{num_value})'
                        match = re.search(pattern, justification, re.IGNORECASE)
                        if match:
                            photo_num = num_value
                            # #region agent log
                            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                                import json as json_module
                                import time
                                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:680","message":"Cuisine debug - photo_num from justification (french)","data":{"apt_id":apt_id,"photo_num":photo_num,"matched_text":match.group(0)},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
                            # #endregion
                            break
        
        # Priorité 3: Chercher dans formatted_data.indices
        if not photo_num and formatted and isinstance(formatted, dict):
            formatted_indices = formatted.get('indices', '')
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                import time
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:666","message":"Cuisine debug - checking formatted_data.indices","data":{"apt_id":apt_id,"formatted_indices":formatted_indices[:200] if formatted_indices else None,"formatted_indices_length":len(formatted_indices) if formatted_indices else 0,"formatted_keys":list(formatted.keys()) if formatted else []},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            # #endregion
            if formatted_indices:
                # Chercher "image X" ou "photo X" (numéro en chiffres)
                img_match = re.search(r'(?:image|photo)\s+(\d+)', formatted_indices, re.IGNORECASE)
                if img_match:
                    photo_num = img_match.group(1)
                    # #region agent log
                    with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                        import json as json_module
                        import time
                        logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:699","message":"Cuisine debug - photo_num from formatted_data.indices","data":{"apt_id":apt_id,"photo_num":photo_num},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
                    # #endregion
                else:
                    # Chercher les numéros en toutes lettres
                    french_numbers = {
                        'première': '1', 'premier': '1', '1ère': '1', '1er': '1',
                        'deuxième': '2', 'deuxieme': '2', '2ème': '2', '2eme': '2',
                        'troisième': '3', 'troisieme': '3', '3ème': '3', '3eme': '3',
                        'quatrième': '4', 'quatrieme': '4', '4ème': '4', '4eme': '4',
                        'cinquième': '5', 'cinquieme': '5', '5ème': '5', '5eme': '5',
                        'sixième': '6', 'sixieme': '6', '6ème': '6', '6eme': '6',
                        'septième': '7', 'septieme': '7', '7ème': '7', '7eme': '7',
                        'huitième': '8', 'huitieme': '8', '8ème': '8', '8eme': '8',
                        'neuvième': '9', 'neuvieme': '9', '9ème': '9', '9eme': '9',
                        'dixième': '10', 'dixieme': '10', '10ème': '10', '10eme': '10'
                    }
                    for num_word, num_value in french_numbers.items():
                        pattern = rf'(?:{num_word}|{num_value})\s+(?:photo|image)|(?:photo|image)\s+(?:{num_word}|{num_value})'
                        match = re.search(pattern, formatted_indices, re.IGNORECASE)
                        if match:
                            photo_num = num_value
                            # #region agent log
                            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                                import json as json_module
                                import time
                                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:720","message":"Cuisine debug - photo_num from formatted_data.indices (french)","data":{"apt_id":apt_id,"photo_num":photo_num},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
                            # #endregion
                            break
        
        # Priorité 4: Chercher dans formatted_data.detected_photos (hypothèse C)
        if not photo_num and formatted and isinstance(formatted, dict):
            formatted_detected = formatted.get('detected_photos', [])
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                import time
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:675","message":"Cuisine debug - checking formatted_data.detected_photos","data":{"apt_id":apt_id,"formatted_detected_photos":formatted_detected},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            # #endregion
            if formatted_detected and len(formatted_detected) > 0:
                photo_num = formatted_detected[0]
                # #region agent log
                with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                    import json as json_module
                    import time
                    logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:678","message":"Cuisine debug - photo_num from formatted_data.detected_photos","data":{"apt_id":apt_id,"photo_num":photo_num},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                # #endregion
        
        # Construire le message avec le numéro de photo si disponible
        if cuisine_ouverte is not None:
            if photo_num:
                if cuisine_ouverte:
                    indices = f"Cuisine ouverte détectée image {photo_num}"
                else:
                    indices = f"Cuisine fermée détectée image {photo_num}"
            else:
                # Fallback: juste indiquer que c'est détecté (sans numéro)
                if cuisine_ouverte:
                    indices = "Cuisine ouverte détectée"
                else:
                    indices = "Cuisine fermée détectée"
        
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            import time
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:690","message":"Cuisine debug - final result","data":{"apt_id":apt_id,"cuisine_ouverte":cuisine_ouverte,"photo_num":photo_num,"indices":indices},"sessionId":"debug-session","runId":"run1","hypothesisId":"E"}) + "\n")
        # #endregion
        
        return {
            'title': title,
            'description': description,  # Pas de description API pour cuisine
            'indices': indices  # IA, bleu
        }
    
    elif criterion_name == 'baignoire':
        # Titre: "Baignoire" ou "Douche"
        has_baignoire = None
        has_douche = None
        
        # Chercher dans photo_validation (priorité)
        baignoire_score = apartment.get('scores_detaille', {}) or {}
        baignoire_score = baignoire_score.get('baignoire') or {}
        if isinstance(baignoire_score, dict):
            baignoire_details = baignoire_score.get('details')
            if baignoire_details and isinstance(baignoire_details, dict):
                photo_validation = baignoire_details.get('photo_validation')
                if photo_validation and isinstance(photo_validation, dict):
                    photo_result = photo_validation.get('photo_result') or {}
                    if isinstance(photo_result, dict):
                        has_baignoire = photo_result.get('has_baignoire')
                        has_douche = photo_result.get('has_douche')
        
        # Fallback: chercher dans baignoire_data
        if has_baignoire is None and has_douche is None:
            baignoire_data = apartment.get('baignoire', {}) or apartment.get('baignoire_data', {})
            if has_baignoire is None:
                has_baignoire = baignoire_data.get('has_baignoire')
            if has_douche is None:
                has_douche = baignoire_data.get('has_douche')
        
        # Déterminer le titre
        if has_baignoire is True:
            title = 'Baignoire'
        elif has_douche is True:
            title = 'Douche'
        else:
            title = 'Baignoire'
        
        # Récupérer detected_photos depuis plusieurs sources
        detected_photos = []
        
        # Priorité 1: depuis photo_validation.photo_result
        if isinstance(baignoire_score, dict):
            baignoire_details = baignoire_score.get('details')
            if baignoire_details and isinstance(baignoire_details, dict):
                photo_validation = baignoire_details.get('photo_validation')
                if photo_validation and isinstance(photo_validation, dict):
                    photo_result = photo_validation.get('photo_result') or {}
                    if isinstance(photo_result, dict):
                        detected_photos = photo_result.get('detected_photos', [])
        
        # Priorité 2: depuis baignoire_data
        if not detected_photos:
            baignoire_data = apartment.get('baignoire', {}) or apartment.get('baignoire_data', {})
            detected_photos = baignoire_data.get('detected_photos', [])
        
        # Description: "baignoire détectée image X" ou "douche détectée image X" (IA, bleu)
        description = None
        indices = None
        photo_num = None
        
        # #region agent log
        apt_id = apartment.get('id', 'unknown')
        # Log de toutes les sources potentielles pour debugging
        baignoire_data_for_log = apartment.get('baignoire', {}) or apartment.get('baignoire_data', {})
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            import time
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:baignoire_entry","message":"Baignoire debug - entry","data":{"apt_id":apt_id,"has_baignoire":has_baignoire,"has_douche":has_douche,"detected_photos_from_photo_result":detected_photos,"baignoire_data_keys":list(baignoire_data_for_log.keys()) if baignoire_data_for_log else [],"baignoire_data_detected_photos":baignoire_data_for_log.get('detected_photos', []) if baignoire_data_for_log else [],"formatted_keys":list(formatted.keys()) if formatted else []},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        # #endregion
        
        # Priorité 1: Utiliser detected_photos si disponible
        if detected_photos and len(detected_photos) > 0:
            photo_num = detected_photos[0]
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                import time
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:baignoire_photo_num","message":"Baignoire debug - photo_num from detected_photos","data":{"apt_id":apt_id,"photo_num":photo_num},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
            # #endregion
        
        # Priorité 2: Extraire depuis formatted_data.indices
        if not photo_num and formatted and isinstance(formatted, dict):
            formatted_indices = formatted.get('indices', '')
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                import time
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:baignoire_formatted_indices","message":"Baignoire debug - checking formatted_data.indices","data":{"apt_id":apt_id,"formatted_indices":formatted_indices[:300] if formatted_indices else None,"formatted_indices_full_length":len(formatted_indices) if formatted_indices else 0},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            # #endregion
            if formatted_indices:
                # Chercher "image X" ou "photo X" (numéro en chiffres) - format: "Baignoire détectée image 1, image 3"
                # Chercher TOUS les numéros d'images (peut y en avoir plusieurs)
                img_matches = re.findall(r'(?:image|photo)\s+(\d+)', formatted_indices, re.IGNORECASE)
                if img_matches:
                    # Prendre le premier numéro trouvé
                    photo_num = img_matches[0]
                    # #region agent log
                    with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                        import json as json_module
                        import time
                        logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:baignoire_formatted_photo_num","message":"Baignoire debug - photo_num from formatted_data.indices","data":{"apt_id":apt_id,"photo_num":photo_num,"all_matches":img_matches},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
                    # #endregion
        
        # Priorité 3: Chercher dans formatted_data.detected_photos
        if not photo_num and formatted and isinstance(formatted, dict):
            formatted_detected = formatted.get('detected_photos', [])
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                import time
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:baignoire_formatted_detected","message":"Baignoire debug - checking formatted_data.detected_photos","data":{"apt_id":apt_id,"formatted_detected_photos":formatted_detected},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            # #endregion
            if formatted_detected and len(formatted_detected) > 0:
                photo_num = formatted_detected[0]
                # #region agent log
                with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                    import json as json_module
                    import time
                    logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:baignoire_formatted_detected_photo_num","message":"Baignoire debug - photo_num from formatted_data.detected_photos","data":{"apt_id":apt_id,"photo_num":photo_num},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                # #endregion
        
        # Construire le message avec le numéro de photo si disponible
        if has_baignoire is not None or has_douche is not None:
            if photo_num:
                if has_baignoire is True:
                    indices = f"Baignoire détectée image {photo_num}"
                elif has_douche is True:
                    indices = f"Douche détectée image {photo_num}"
                else:
                    indices = f"Détectée image {photo_num}"
            else:
                # Fallback: juste indiquer que c'est détecté (sans numéro)
                if has_baignoire is True:
                    indices = "Baignoire détectée"
                elif has_douche is True:
                    indices = "Douche détectée"
                else:
                    indices = "Détectée"
        
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            import time
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"simple_normalizer.py:baignoire_final","message":"Baignoire debug - final result","data":{"apt_id":apt_id,"has_baignoire":has_baignoire,"has_douche":has_douche,"photo_num":photo_num,"indices":indices},"sessionId":"debug-session","runId":"run1","hypothesisId":"E"}) + "\n")
        # #endregion
        
        return {
            'title': title,
            'description': description,  # Pas de description API pour baignoire
            'indices': indices  # IA, bleu
        }
    
    elif criterion_name == 'hauteur_plafond':
        # Titre: "Hauteur sous plafond élevée / moyenne / basse"
        tier = score_data.get('tier', 'tier3') if score_data else 'tier3'
        if tier == 'tier1':
            title = 'Hauteur sous plafond élevée'
        elif tier == 'tier2':
            title = 'Hauteur sous plafond moyenne'
        else:
            title = 'Hauteur sous plafond basse'
        
        # Description: "Xm en moyenne" (IA, bleu)
        hauteur_estimee = None
        # Chercher dans formatted_data
        if formatted and formatted.get('indices'):
            indices_str = formatted['indices']
            match = re.search(r'(\d+[.,]\d+)\s*m', indices_str)
            if match:
                hauteur_estimee = float(match.group(1).replace(',', '.'))
        
        # Chercher dans analyses
        if not hauteur_estimee:
            analyses = apartment.get('analyses', {})
            hauteur_data = analyses.get('hauteur_plafond', {})
            hauteur_estimee = hauteur_data.get('hauteur_estimee') or hauteur_data.get('hauteur_estimate')
        
        # Chercher dans style_analysis
        if not hauteur_estimee:
            style_analysis = apartment.get('style_analysis', {})
            hauteur_style = style_analysis.get('hauteur_plafond', {})
            hauteur_estimee = hauteur_style.get('value')
        
        # Description: "Xm en moyenne" (IA, bleu) - mettre dans indices
        description = None
        indices = None
        if hauteur_estimee:
            indices = f"{hauteur_estimee:.2f}m en moyenne".replace('.', ',')
        
        return {
            'title': title,
            'description': description,  # Pas de description API
            'indices': indices  # IA, bleu
        }
    
    elif criterion_name == 'piece_vie':
        # Titre: "Grande pièce de vie" / "Pièce de vie correcte" / "Petite pièce de vie"
        # IMPORTANT: Les scores sont stockés sous 'large_piece_vie' dans scores_detaille
        scores_detaille = apartment.get('scores_detaille', {})
        large_piece_vie_score = scores_detaille.get('large_piece_vie', {}) or {}
        # Utiliser large_piece_vie si disponible, sinon score_data (pour compatibilité)
        score_data_to_use = large_piece_vie_score if large_piece_vie_score else score_data
        
        tier = score_data_to_use.get('tier', 'tier3') if score_data_to_use else 'tier3'
        if tier == 'tier1':
            title = 'Grande pièce de vie'
        elif tier == 'tier2':
            title = 'Pièce de vie correcte'
        else:
            title = 'Petite pièce de vie'
        
        # Description: "X% de la surface totale de l'appartement" (IA, bleu)
        description = None
        indices = None
        
        # PRIORITÉ 1: Utiliser les indices depuis formatted_data s'ils existent et contiennent déjà "de l'appartement"
        if formatted and isinstance(formatted, dict) and formatted.get('indices'):
            indices_str = formatted['indices']
            # Nettoyer le préfixe "Pièce de vie Indice:" si présent
            indices_clean = indices_str.replace('Pièce de vie Indice:', '').replace('Pièce de vie:', '').strip()
            # Si les indices contiennent déjà "de l'appartement", les utiliser tels quels
            if 'de l\'appartement' in indices_clean or "de l'appartement" in indices_clean:
                indices = indices_clean
            # Sinon, chercher le pourcentage et reconstruire
            elif '%' in indices_clean:
                match = re.search(r'(\d+[.,]?\d*)%\s*de\s*la\s*surface\s*totale', indices_clean, re.IGNORECASE)
                if match:
                    pourcentage = float(match.group(1).replace(',', '.'))
                    indices = f"{pourcentage:.1f}% de la surface totale de l'appartement".replace('.', ',')
                else:
                    indices = indices_clean
        
        # PRIORITÉ 2: Si pas d'indices depuis formatted_data, chercher le pourcentage et construire
        if not indices:
            pourcentage = None
            # Chercher dans scores_detaille.large_piece_vie.details (PRIORITÉ)
            details = large_piece_vie_score.get('details', {}) if large_piece_vie_score else {}
            pourcentage = details.get('pourcentage_salon')
            
            # Fallback: chercher dans score_data.details (compatibilité)
            if not pourcentage and score_data:
                details_old = score_data.get('details', {})
                pourcentage = details_old.get('pourcentage_salon')
            
            # Fallback: chercher dans style_analysis
            if not pourcentage:
                style_analysis = apartment.get('style_analysis', {})
                piece_vie_style = style_analysis.get('piece_vie', {})
                details_style = piece_vie_style.get('details', {})
                pourcentage = details_style.get('pourcentage_salon') or details_style.get('pourcentage')
            
            # Fallback: calculer depuis piece_vie.taille_m2 et surface totale
            if not pourcentage:
                piece_vie_data = apartment.get('piece_vie', {})
                taille_m2 = piece_vie_data.get('taille_m2')
                if taille_m2:
                    try:
                        taille_m2_float = float(taille_m2)
                        # Extraire la surface totale depuis apartment.surface
                        surface = apartment.get('surface', '')
                        surface_match = re.search(r'(\d+)', surface)
                        if surface_match:
                            surface_totale = float(surface_match.group(1))
                            if surface_totale > 0:
                                pourcentage = (taille_m2_float / surface_totale) * 100
                    except (ValueError, TypeError):
                        pass
            
            if pourcentage:
                indices = f"{pourcentage:.1f}% de la surface totale de l'appartement".replace('.', ',')
        
        return {
            'title': title,
            'description': description,  # Pas de description API
            'indices': indices  # IA, bleu
        }
    
    return None


def _normalize_criteria(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise les critères depuis formatted_data et scores_detaille.
    IMPORTANT: Pas de score total, seulement scores individuels des critères.
    """
    criteria = {}
    
    scores_detaille = apartment.get('scores_detaille', {})
    formatted_data = apartment.get('formatted_data', {})
    
    # Liste des critères à normaliser
    criterion_names = [
        'localisation', 'prix', 'style', 'exposition', 'cuisine',
        'baignoire', 'hauteur_plafond', 'piece_vie'
    ]
    
    for criterion_name in criterion_names:
        # Récupérer score et tier depuis scores_detaille
        # IMPORTANT: Pour 'piece_vie', les scores sont sous 'large_piece_vie'
        if criterion_name == 'piece_vie':
            score_data = scores_detaille.get('large_piece_vie', {}) or scores_detaille.get(criterion_name, {})
        else:
            score_data = scores_detaille.get(criterion_name, {})
        score = score_data.get('score', 0) if score_data else 0
        tier = score_data.get('tier', 'tier3') if score_data else 'tier3'
        
        # Récupérer les données formatées
        formatted = formatted_data.get(criterion_name, {})
        
        # Construire les données d'affichage selon les spécifications
        display_data = _build_display_data(apartment, criterion_name, score_data, formatted)
        
        # Fallback si _build_display_data retourne None
        if not display_data:
            display_data = {
                'title': '',
                'description': None,
                'indices': None
            }
        
        # Construire le critère normalisé
        criteria[criterion_name] = {
            'score': score,
            'tier': tier,
            'display': display_data or {
                'title': '',
                'description': None,
                'indices': None
            }
        }
    
    return criteria
