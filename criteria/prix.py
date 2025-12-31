"""
Critère Prix - Comparaison avec médian arrondissement
Format: "X / m² · Good/Moyen/Bad (médian arrondissement: Y €/m²)"
Règle V2: Comparer avec prix moyen de l'arrondissement comme médian
"""

import re
import json
import os
from pathlib import Path

# Cache pour éviter de recharger le fichier à chaque appel
_MEDIANS_CACHE = None


def get_station_metro_median_price(station_name: str) -> float:
    """
    Récupère le prix médian pour une station de métro depuis le fichier JSON
    
    Args:
        station_name: Nom de la station (ex: "Belleville", "Goncourt")
        
    Returns:
        Prix médian en €/m² ou None si non disponible
    """
    global _MEDIANS_CACHE
    
    # Charger le cache si pas déjà fait
    if _MEDIANS_CACHE is None:
        # Chercher le fichier JSON des stations
        possible_paths = [
            Path(__file__).parent.parent / 'data' / 'prix_medians' / 'stations_metro.json',
            Path(__file__).parent.parent.parent / 'data' / 'prix_medians' / 'stations_metro.json',
            'data/prix_medians/stations_metro.json',
        ]
        
        stations_file = None
        for path in possible_paths:
            if isinstance(path, str):
                path = Path(path)
            if path.exists():
                stations_file = path
                break
        
        if stations_file:
            try:
                with open(stations_file, 'r', encoding='utf-8') as f:
                    stations_data = json.load(f)
                    _MEDIANS_CACHE = stations_data.get('stations', {})
            except Exception as e:
                print(f"⚠️ Erreur chargement stations: {e}")
                _MEDIANS_CACHE = {}
        else:
            _MEDIANS_CACHE = {}
    
    # Chercher la station (matching flexible)
    station_lower = station_name.lower().strip()
    
    # Chercher correspondance exacte d'abord
    for station_key, station_data in _MEDIANS_CACHE.items():
        if station_key.lower() == station_lower:
            if isinstance(station_data, dict):
                return station_data.get('prix_median_m2')
            elif isinstance(station_data, (int, float)):
                return float(station_data)
    
    # Chercher correspondance partielle
    for station_key, station_data in _MEDIANS_CACHE.items():
        if station_lower in station_key.lower() or station_key.lower() in station_lower:
            if isinstance(station_data, dict):
                return station_data.get('prix_median_m2')
            elif isinstance(station_data, (int, float)):
                return float(station_data)
    
    return None


def get_arrondissement_median_price(postal_code: str) -> float:
    """
    Récupère le prix médian de l'arrondissement depuis le fichier JSON
    
    Le fichier est généré par scripts/scrape_meilleursagents_medians.py
    
    Args:
        postal_code: Code postal (ex: "75010", "75020")
        
    Returns:
        Prix médian en €/m² ou None si non disponible
    """
    global _MEDIANS_CACHE
    
    # Extraire l'arrondissement depuis le code postal
    if not postal_code or not postal_code.startswith('75'):
        return None
    
    # Normaliser le code postal (s'assurer qu'il est au format 750XX)
    if len(postal_code) == 5:
        postal_code = postal_code
    elif len(postal_code) == 2:
        postal_code = f"75{postal_code.zfill(3)}"
    else:
        return None
    
    # Charger le cache si pas déjà fait
    if _MEDIANS_CACHE is None:
        # Chercher le fichier JSON dans plusieurs emplacements possibles
        possible_paths = [
            Path(__file__).parent.parent / 'data' / 'prix_medians' / 'arrondissements.json',
            Path(__file__).parent.parent.parent / 'data' / 'prix_medians' / 'arrondissements.json',
            'data/prix_medians/arrondissements.json',
        ]
        
        medians_file = None
        for path in possible_paths:
            if isinstance(path, str):
                path = Path(path)
            if path.exists():
                medians_file = path
                break
        
        if medians_file:
            try:
                with open(medians_file, 'r', encoding='utf-8') as f:
                    _MEDIANS_CACHE = json.load(f)
            except Exception as e:
                print(f"⚠️ Erreur chargement médians: {e}")
                _MEDIANS_CACHE = {}
        else:
            # Fichier non trouvé, utiliser valeurs par défaut
            print("⚠️ Fichier prix_medians/arrondissements.json non trouvé")
            print("   Exécutez: python scripts/scrape_meilleursagents_medians.py")
            _MEDIANS_CACHE = {}
    
    # Chercher le prix médian pour ce code postal
    if postal_code in _MEDIANS_CACHE:
        median_data = _MEDIANS_CACHE[postal_code]
        if isinstance(median_data, dict):
            return median_data.get('prix_median_m2')
        elif isinstance(median_data, (int, float)):
            return float(median_data)
    
    # Fallback: valeurs par défaut approximatives si fichier non disponible
    fallback_prices = {
        '75010': 10500,
        '75011': 11000,
        '75019': 9500,
        '75020': 9000,
    }
    
    return fallback_prices.get(postal_code)


def format_prix(apartment):
    """
    Formate le critère Prix selon les règles V2
    
    Règles:
    - Comparer avec prix moyen de l'arrondissement (médian)
    - Good: Prix/m² < médian
    - Moyen: Prix/m² ≈ médian (±10%)
    - Bad: Prix/m² > médian
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "11 500 / m² · Moyen (médian arrondissement: 11 200 €/m²)"
            - confidence: None (données factuelles)
            - indices: "Prix Indice:\nPrix/m²: 11 500€ · Médian arrondissement: 11 200€"
    """
    # Calculer prix/m²
    prix = apartment.get('prix', '')
    surface = apartment.get('surface', '')
    prix_m2 = None
    
    # Extraire le prix en nombre
    prix_match = re.search(r'([\d\s]+)', prix.replace(' ', '')) if prix else None
    if prix_match:
        try:
            prix_num = int(prix_match.group(1))
            # Extraire la surface
            surface_match = re.search(r'(\d+)', surface) if surface else None
            if surface_match:
                surface_num = int(surface_match.group(1))
                if surface_num > 0:
                    prix_m2 = prix_num // surface_num
        except:
            pass
    
    # Si pas calculé, essayer depuis prix_m2 directement
    if prix_m2 is None:
        prix_m2_str = apartment.get('prix_m2', '')
        if prix_m2_str:
            prix_m2_match = re.search(r'(\d+)', prix_m2_str.replace(' ', ''))
            if prix_m2_match:
                try:
                    prix_m2 = int(prix_m2_match.group(1))
                except:
                    pass
    
    if prix_m2 is None:
        return {
            'main_value': "Prix/m<sup>2</sup> non disponible",
            'confidence': None,
            'indices': "Prix Indice:\nNon spécifié"
        }
    
    # Récupérer le code postal pour déterminer l'arrondissement
    postal_code = apartment.get('_api_data', {}).get('postal_code', '')
    if not postal_code:
        # Essayer depuis localisation ou autres sources
        localisation = apartment.get('localisation', '')
        postal_match = re.search(r'75\d{3}', localisation)
        if postal_match:
            postal_code = postal_match.group(0)
    
    # PRIORITÉ: Chercher le prix médian par station de métro d'abord
    # (plus précis que par arrondissement)
    median_price = None
    
    # Extraire la station de métro depuis localisation ou map_info
    map_info = apartment.get('map_info', {})
    metros = map_info.get('metros', [])
    
    if metros and isinstance(metros, list) and len(metros) > 0:
        # Prendre la première station de métro trouvée
        first_station = metros[0]
        if isinstance(first_station, str):
            # Nettoyer le nom de la station
            station_name = first_station.replace('métro ', '').replace('Metro ', '').strip()
            median_price = get_station_metro_median_price(station_name)
    
    # Fallback: utiliser le médian de l'arrondissement si pas de station trouvée
    if median_price is None:
        median_price = get_arrondissement_median_price(postal_code)
    
    # Classification selon tranches fixes autour du médian
    # Règle: Zone "Moyen" = toujours 1500€ de large, seuils arrondis à 500€
    # Exemple: médian = 9850€
    # - Seuil bas = arrondir(9850 - 750) à 500€ = 9000€
    # - Seuil haut = 9000 + 1500 = 10500€
    # - Good: < 9000€, Moyen: 9000-10500€, Bad: > 10500€
    if median_price:
        # Calculer le seuil bas: médian - 750€, arrondi à 500€
        seuil_bas_brut = median_price - 750
        seuil_bas = round(seuil_bas_brut / 500) * 500  # Arrondir à 500€
        
        # Le seuil haut = seuil bas + 1500€ (zone moyen toujours 1500€)
        seuil_haut = seuil_bas + 1500
        
        # Classification selon les tranches
        if prix_m2 < seuil_bas:
            tier = 'tier1'
            tier_label = 'Good'
            tier_class = 'good'
        elif prix_m2 <= seuil_haut:
            tier = 'tier2'
            tier_label = 'Moyen'
            tier_class = 'moyen'
        else:  # > seuil_haut
            tier = 'tier3'
            tier_label = 'Bad'
            tier_class = 'bad'
        
        # Formater avec médian et tranches
        prix_formatted = f"{prix_m2:,}".replace(',', ' ')
        median_formatted = f"{int(median_price):,}".replace(',', ' ')
        main_value = f"{prix_formatted} / m<sup>2</sup> · <span class=\"tier-label {tier_class}\">{tier_label}</span> (médian: {median_formatted} €/m²)"
        
        # Indices avec les tranches
        indices_str = f"Prix Indice:\nPrix/m²: {prix_m2:,}€ · Médian: {int(median_price):,}€ · Tranches: <{seuil_bas:,}€ Good, {seuil_bas:,}-{seuil_haut:,}€ Moyen, >{seuil_haut:,}€ Bad"
    else:
        # Pas de médian disponible, utiliser l'ancien système de scoring
        scores_detaille = apartment.get('scores_detaille', {})
        prix_score = scores_detaille.get('prix', {})
        tier = prix_score.get('tier', 'tier3')
        
        tier_mapping = {
            'tier1': ('Good', 'good'),
            'tier2': ('Moyen', 'moyen'),
            'tier3': ('Bad', 'bad')
        }
        tier_label, tier_class = tier_mapping.get(tier, ('Bad', 'bad'))
        
        prix_formatted = f"{prix_m2:,}".replace(',', ' ')
        main_value = f"{prix_formatted} / m<sup>2</sup> · <span class=\"tier-label {tier_class}\">{tier_label}</span>"
        
        indices_str = f"Prix Indice:\nPrix/m²: {prix_m2:,}€"
    
    return {
        'main_value': main_value,
        'confidence': None,  # Données factuelles
        'indices': indices_str
    }

