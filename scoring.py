"""
Scoring - Calcul des scores depuis règles simples (pas d'IA)
Utilise scoring_config.json pour les règles de scoring
"""

import json
import os
import re
from criteria.localisation import get_metro_name, get_quartier_name, get_all_metro_stations


def round_to_nearest_5(score):
    """Arrondit un score au multiple de 5 le plus proche"""
    return round(score / 5) * 5


def load_scoring_config():
    """Charge la configuration de scoring"""
    try:
        with open('scoring_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")
        return None


def calculate_prix_m2(apartment):
    """Calcule le prix/m² depuis les données scrapées"""
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
    
    return prix_m2


def get_api_metro_stations(apartment):
    """
    Récupère UNIQUEMENT les stations de métro depuis l'API (map_info.metros + transports)
    Ne cherche JAMAIS dans la description
    
    Returns:
        list: Liste des stations depuis l'API uniquement
    """
    import re
    all_stations = []
    
    # Source 1: map_info.metros (depuis API)
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
    
    # Source 2: transports (depuis API via stops[])
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
    
    # Dédupliquer en préservant l'ordre
    seen = set()
    unique_stations = []
    for station in all_stations:
        station_lower = station.lower()
        if station_lower not in seen:
            seen.add(station_lower)
            unique_stations.append(station)
    
    return unique_stations


def score_localisation(apartment, config):
    """Score localisation selon zones définies dans config
    
    UTILISE UNIQUEMENT les stations réelles de l'API (map_info.metros + transports)
    JAMAIS la description pour éviter les faux positifs
    """
    tier_config = config['axes']['localisation']['tiers']
    
    # Récupérer localisation et quartier (pour fallback si pas de stations)
    localisation = apartment.get('localisation', '').lower()
    quartier = get_quartier_name(apartment)
    if quartier:
        quartier = quartier.lower()
    
    # Récupérer UNIQUEMENT les stations de métro depuis l'API (pas la description)
    api_stations = get_api_metro_stations(apartment)
    api_stations_lower = [s.lower() for s in api_stations] if api_stations else []
    
    tier1_zones = [z.lower() for z in tier_config['tier1']['zones']]
    tier2_zones = [z.lower() for z in tier_config['tier2']['zones']]
    
    # PRIORITÉ 1 : Vérifier Tier 1 dans les STATIONS API uniquement
    for zone in tier1_zones:
        for station in api_stations_lower:
            if zone in station or station in zone:
                score = tier_config['tier1']['score']
                # Bonus Place de la Réunion
                if 'place de la réunion' in zone:
                    score += config['bonus']['place_reunion']
                return {
                    'score': score,
                    'tier': 'tier1',
                    'justification': f"Zone premium: {zone} (métro {station})"
                }
    
    # PRIORITÉ 2 : Vérifier Tier 2 dans les STATIONS API uniquement
    for zone in tier2_zones:
        for station in api_stations_lower:
            if zone in station or station in zone:
                return {
                    'score': tier_config['tier2']['score'],
                    'tier': 'tier2',
                    'justification': f"Bonne zone: {zone} (métro {station})"
                }
    
    # PRIORITÉ 3 : Fallback - Vérifier Tier 1 dans localisation/quartier (si pas de stations API)
    if not api_stations:  # Seulement si aucune station API disponible
        for zone in tier1_zones:
            if zone in localisation or (quartier and zone in quartier):
                score = tier_config['tier1']['score']
                # Bonus Place de la Réunion
                if 'place de la réunion' in localisation or (quartier and 'place de la réunion' in quartier):
                    score += config['bonus']['place_reunion']
                return {
                    'score': score,
                    'tier': 'tier1',
                    'justification': f"Zone premium: {zone}"
                }
        
        # PRIORITÉ 4 : Fallback - Vérifier Tier 2 dans localisation/quartier
        for zone in tier2_zones:
            if zone in localisation or (quartier and zone in quartier):
                return {
                    'score': tier_config['tier2']['score'],
                    'tier': 'tier2',
                    'justification': f"Bonne zone: {zone}"
                }
    
    # Par défaut tier3
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': "Zone correcte"
    }


def score_prix(apartment, config):
    """Score prix selon seuils définis dans config"""
    tier_config = config['axes']['prix']['tiers']
    prix_m2 = calculate_prix_m2(apartment)
    
    if prix_m2 is None:
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': "Prix/m² non disponible - note moyenne par défaut"
        }
    
    # Vérifier tier1 (< 9500)
    if prix_m2 <= tier_config['tier1']['prix_m2_max']:
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': f"Excellent rapport qualité/prix: {prix_m2}€/m²"
        }
    
    # Vérifier tier2 (9500-11000)
    if tier_config['tier2']['prix_m2_min'] <= prix_m2 <= tier_config['tier2']['prix_m2_max']:
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': f"Bon rapport qualité/prix: {prix_m2}€/m²"
        }
    
    # tier3 (> 11000)
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': f"Prix élevé: {prix_m2}€/m²"
    }


def score_style(apartment, config):
    """Score style avec priorité sur données API (buy_type, year)
    PRIORITÉ 1: buy_type et year depuis l'API
    PRIORITÉ 2: style_analysis (analyse IA)
    PRIORITÉ 3: Analyse texte seule
    Ancien (20pts) / Atypique (10pts) / Neuf (0pts)
    """
    tier_config = config['axes']['style']['tiers']
    
    # PRIORITÉ 1: Utiliser buy_type et year depuis l'API si disponibles
    api_data = apartment.get('_api_data', {})
    if api_data:
        buy_type = api_data.get('buy_type')
        features = api_data.get('features', {})
        year = features.get('year') if isinstance(features, dict) else None
        
        # Si buy_type == "new" → Neuf (Tier3 = 0 pts)
        if buy_type == 'new':
            return {
                'score': tier_config['tier3']['score'],
                'tier': 'tier3',
                'justification': 'Appartement neuf (buy_type: new)',
                'source': 'api_buy_type'
            }
        
        # Si buy_type == "old" et qu'on a l'année
        if buy_type == 'old' and year:
            # Haussmannien (1850-1900) → Tier1 (20 pts)
            if 1850 <= year <= 1900:
                return {
                    'score': tier_config['tier1']['score'],
                    'tier': 'tier1',
                    'justification': f'Style haussmannien (construction {year})',
                    'source': 'api_year',
                    'year': year
                }
            # Ancien avant 1850 → Tier1 (20 pts)
            elif year < 1850:
                return {
                    'score': tier_config['tier1']['score'],
                    'tier': 'tier1',
                    'justification': f'Style ancien (construction {year})',
                    'source': 'api_year',
                    'year': year
                }
            # Ancien 1900-1950 → Tier2 (10 pts) - Ancien mais pas haussmannien
            elif 1900 < year <= 1950:
                return {
                    'score': tier_config['tier2']['score'],
                    'tier': 'tier2',
                    'justification': f'Style ancien (construction {year})',
                    'source': 'api_year',
                    'year': year
                }
            # Récent après 1950 → Tier3 (0 pts)
            elif year > 1950:
                return {
                    'score': tier_config['tier3']['score'],
                    'tier': 'tier3',
                    'justification': f'Style récent (construction {year})',
                    'source': 'api_year',
                    'year': year
                }
        
        # Si buy_type == "old" mais pas d'année, continuer avec fallback
    
    # PRIORITÉ 2: Essayer avec style_analysis existant (analyse IA)
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    style_type = style_data.get('type', '').lower()
    
    # Si style_analysis existe et contient des données enrichies, l'utiliser
    if style_data and style_type:
        # Tier1: Ancien (Haussmannien) = 20 pts
        tier1_styles = [s.lower() for s in tier_config['tier1']['styles']]
        if style_type in tier1_styles or 'haussmann' in style_type:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': style_data.get('justification', f"Style ancien: {style_type}"),
                'details': style_data.get('details', {})
            }
        
        # Tier2: Atypique = 10 pts
        if 'atypique' in style_type or 'loft' in style_type:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': style_data.get('justification', f"Style atypique: {style_type}"),
                'details': style_data.get('details', {})
            }
        
        # Tier3: Neuf = 0 pts
        return {
            'score': tier_config['tier3']['score'],
            'tier': 'tier3',
            'justification': style_data.get('justification', f"Style neuf: {style_type}"),
            'details': style_data.get('details', {})
        }
    
    # RÈGLE GÉNÉRALE: NE JAMAIS lancer d'analyse automatique
    # Si pas de style_analysis, retourner un score par défaut (tier3 = 0 points)
    if not style_analysis:
        return {
            'score': tier_config['tier3']['score'],
            'tier': 'tier3',
            'justification': 'Données d\'analyse de style non disponibles (analyse non effectuée)',
            'details': {}
        }
    
    # Si style_analysis existe, continuer avec le traitement
    style_data = style_analysis.get('style', {})
    style_type = style_data.get('type', '').lower()
    
    if style_type:
        # Tier1: Ancien (Haussmannien) = 20 pts
        tier1_styles = [s.lower() for s in tier_config['tier1']['styles']]
        if style_type in tier1_styles or 'haussmann' in style_type:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': style_data.get('justification', f"Style ancien: {style_type}"),
                'details': style_data.get('details', {})
            }
        
        # Tier2: Atypique = 10 pts
        if 'atypique' in style_type or 'loft' in style_type:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': style_data.get('justification', f"Style atypique: {style_type}"),
                'details': style_data.get('details', {})
            }
        
        # Tier3: Neuf = 0 pts
        return {
            'score': tier_config['tier3']['score'],
            'tier': 'tier3',
            'justification': style_data.get('justification', f"Style neuf: {style_type}"),
            'details': style_data.get('details', {})
        }
    
    # Fallback: méthode ancienne avec analyse texte seule
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    titre = apartment.get('titre', '').lower()
    text_combined = f"{titre} {description} {caracteristiques}"
    
    # Mots-clés directs pour détecter "Atypique"
    atypique_direct = ['loft', 'atypique', 'unique', 'original', 'atypiques', 'lofts', 'originaux', 'uniques']
    
    # Concepts atypiques (ancien entrepôt, atelier, hangar rénové, etc.)
    atypique_concepts = [
        'ancien entrepôt', 'ancien entrepot', 'ancien atelier', 'ancien hangar', 'ancien garage',
        'entrepôt rénové', 'entrepot renove', 'atelier rénové', 'atelier renove',
        'hangar rénové', 'hangar renove', 'garage rénové', 'garage renove',
        'réhabilité', 'rehabilite', 'réhabilitée', 'rehabilitee',
        'transformé', 'transforme', 'transformée', 'transformee',
        'reconverti', 'reconvertie', 'reconversion',
        'volume généreux', 'volume genereux', 'volumes généreux',
        'hauteur sous plafond importante', 'hauteur plafond importante',
        'caractère industriel', 'caractere industriel', 'style industriel',
        'poutres apparentes', 'poutre apparente', 'béton brut', 'beton brut',
        'espaces ouverts', 'espace ouvert', 'grands volumes'
    ]
    
    # Vérifier les mots-clés directs
    is_atypique_direct = any(keyword in text_combined for keyword in atypique_direct)
    
    # Vérifier les concepts atypiques
    is_atypique_concept = any(concept in text_combined for concept in atypique_concepts)
    
    is_atypique = is_atypique_direct or is_atypique_concept
    
    # Vérifier haussmannien dans le texte
    is_haussmannien = 'haussmann' in text_combined
    
    # Tier1: Ancien (Haussmannien) = 20 pts
    if is_haussmannien:
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': "Style haussmannien détecté dans le texte"
        }
    
    # Tier2: Atypique = 10 pts
    if is_atypique:
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': f"Style atypique détecté (loft/atypique/unique/original)"
        }
    
    # Si rien n'est trouvé après toutes les tentatives = note moyenne par défaut
    return {
        'score': tier_config['tier2']['score'],
        'tier': 'tier2',
        'justification': "Style non analysé - note moyenne par défaut"
    }


def score_ensoleillement(apartment, config):
    """Score ensoleillement selon règles de vote par signal
    Barème: Lumineux = 20 pts, Moyenne = 10 pts, Sombre = 0 pts
    """
    tier_config = config['axes']['ensoleillement']['tiers']
    
    # Utiliser format_exposition qui implémente déjà les règles de vote
    from criteria.exposition import format_exposition
    
    try:
        result = format_exposition(apartment)
        main_value = result.get('main_value', 'Luminosité moyenne')
        confidence = result.get('confidence', 50)
        
        # Convertir main_value en tier et score
        if main_value == 'Lumineux':
            tier = 'tier1'
            score = tier_config['tier1']['score']
        elif main_value == 'Luminosité moyenne':
            tier = 'tier2'
            score = tier_config['tier2']['score']
        else:  # Sombre
            tier = 'tier3'
            score = tier_config['tier3']['score']
        
        # Construire la justification
        indices = result.get('indices', '')
        justification = main_value
        if indices:
            justification = f"{main_value} ({indices})"
        
        return {
            'score': score,
            'tier': tier,
            'justification': justification,
            'confidence': confidence,
            'details': apartment.get('exposition', {}).get('details', {})
        }
    except Exception as e:
        # Fallback en cas d'erreur - note moyenne par défaut
        import traceback
        print(f"⚠️ Erreur dans score_ensoleillement: {e}")
        traceback.print_exc()
        
        # Fallback avec note moyenne par défaut
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': 'Ensoleillement non analysé - note moyenne par défaut',
            'confidence': 50,
            'details': {}
        }


def score_etage(apartment, config):
    """Score étage depuis données scrapées"""
    tier_config = config['axes']['etage']['tiers']
    etage = apartment.get('etage', '')
    caracteristiques = apartment.get('caracteristiques', '').lower()
    has_ascenseur = 'ascenseur' in caracteristiques
    
    # Extraire numéro d'étage
    etage_match = re.search(r'(\d+)(?:er?|e|ème?)', str(etage), re.IGNORECASE)
    if etage_match:
        etage_num = int(etage_match.group(1))
        
        # tier1: 3e, 4e (ou plus si ascenseur)
        if etage_num in [3, 4] or (etage_num >= 5 and has_ascenseur):
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': f"{etage_num}e étage"
            }
        
        # tier2: 5e, 6e sans ascenseur, 2e
        if etage_num in [2, 5, 6]:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': f"{etage_num}e étage"
            }
    
    # RDC ou 1er
    if 'rdc' in str(etage).lower() or 'rez' in str(etage).lower() or '1er' in str(etage).lower():
        return {
            'score': tier_config['tier3']['score'],
            'tier': 'tier3',
            'justification': "RDC ou 1er étage"
        }
    
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': f"Étage: {etage}"
    }


def score_surface(apartment, config):
    """Score surface depuis données scrapées"""
    tier_config = config['axes']['surface']['tiers']
    surface = apartment.get('surface', '')
    
    # Extraire surface en nombre
    surface_match = re.search(r'(\d+)', surface)
    if surface_match:
        surface_num = int(surface_match.group(1))
        
        # tier1: > 80m²
        if surface_num > tier_config['tier1']['surface_min']:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': f"Grande surface: {surface_num}m²"
            }
        
        # tier2: 65-80m²
        if tier_config['tier2']['surface_min'] <= surface_num <= tier_config['tier2']['surface_max']:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': f"Surface correcte: {surface_num}m²"
            }
    
    # tier3: < 65m²
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': f"Surface limitée: {surface}"
    }


def score_large_piece_vie(apartment, config):
    """Score pour 'large pièce de vie' basé sur le % salon/surface totale
    
    PRIORITÉ 1: Vérifier la description textuelle pour la taille du salon
    PRIORITÉ 2: Analyser les photos pour estimer la taille du salon
    
    Puis compare à la surface totale pour obtenir un pourcentage.
    
    Tier1 (good): >35% de la surface totale
    Tier2 (moyen): 25-35% de la surface totale
    Tier3 (bad): <25% de la surface totale
    """
    # Extraire la surface totale de l'appartement
    surface = apartment.get('surface', '')
    surface_match = re.search(r'(\d+)', surface)
    if not surface_match:
        return {
            'score': 0,
            'tier': 'tier3',
            'justification': 'Surface totale non disponible',
            'details': {}
        }
    
    surface_totale = int(surface_match.group(1))
    
    # PRIORITÉ 1: Chercher la taille du salon dans la description textuelle
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    text_combined = f"{description} {caracteristiques}"
    
    salon_size_from_text = None
    # Chercher des patterns comme "salon de 30m²", "séjour de plus de 30m²", "salon 30 m²", etc.
    patterns = [
        r'salon[^\d]*(\d+)\s*m[²2]',
        r'séjour[^\d]*(\d+)\s*m[²2]',
        r'pièce[^\d]*vie[^\d]*(\d+)\s*m[²2]',
        r'salon[^\d]*de\s*plus\s*de\s*(\d+)\s*m[²2]',
        r'séjour[^\d]*de\s*plus\s*de\s*(\d+)\s*m[²2]',
        r'salon[^\d]*(\d+)\s*mètres?\s*carrés?',
        r'séjour[^\d]*(\d+)\s*mètres?\s*carrés?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_combined, re.IGNORECASE)
        if match:
            try:
                salon_size_from_text = int(match.group(1))
                break
            except:
                pass
    
    salon_size = salon_size_from_text
    salon_category = None
    confidence = 1.0  # Confiance élevée si trouvé dans le texte
    method_used = 'text_description'
    salon_analysis = None
    
    # PRIORITÉ 2: Si pas trouvé dans le texte, vérifier style_analysis puis analyser les photos
    if salon_size is None:
        # Vérifier d'abord si style_analysis contient déjà les données salon_size
        style_analysis = apartment.get('style_analysis')
        if style_analysis:
            salon_data = style_analysis.get('salon_size', {})
            if salon_data and salon_data.get('estimate') is not None:
                salon_size = salon_data.get('estimate')
                salon_category = salon_data.get('category')
                confidence = salon_data.get('confidence', 0)
                method_used = 'style_analysis_cache'
        
        # RÈGLE GÉNÉRALE: NE JAMAIS lancer d'analyse automatique
        # Si toujours pas trouvé, retourner un score par défaut (tier3 = 0 points)
        if salon_size is None:
            return {
                'score': 0,
                'tier': 'tier3',
                'justification': 'Données de taille salon non disponibles (analyse non effectuée)',
                'details': {}
            }
    
    # Calculer le pourcentage salon/surface totale
    pourcentage_salon = (salon_size / surface_totale) * 100 if surface_totale > 0 else 0
    
    # Déterminer le tier selon le pourcentage
    # Tier1: >35% (salon très grand par rapport à l'appartement)
    # Tier2: 25-35% (salon correct)
    # Tier3: <25% (salon petit)
    
    if pourcentage_salon > 35:
        tier = 'tier1'
        score = 10  # Score max pour large pièce de vie
        if method_used == 'text_description':
            justification = f"Grand salon: {salon_size}m² mentionné ({pourcentage_salon:.1f}% de la surface totale)"
        else:
            justification = f"Grand salon: {salon_size}m² estimé ({pourcentage_salon:.1f}% de la surface totale)"
    elif pourcentage_salon >= 25:
        tier = 'tier2'
        score = 5  # Score moyen
        if method_used == 'text_description':
            justification = f"Salon correct: {salon_size}m² mentionné ({pourcentage_salon:.1f}% de la surface totale)"
        else:
            justification = f"Salon correct: {salon_size}m² estimé ({pourcentage_salon:.1f}% de la surface totale)"
    else:
        tier = 'tier3'
        score = 0  # Score faible
        if method_used == 'text_description':
            justification = f"Salon petit: {salon_size}m² mentionné ({pourcentage_salon:.1f}% de la surface totale)"
        else:
            justification = f"Salon petit: {salon_size}m² estimé ({pourcentage_salon:.1f}% de la surface totale)"
    
    return {
        'score': score,
        'tier': tier,
        'justification': justification,
        'details': {
            'salon_size_estimate': salon_size,
            'salon_category': salon_category,
            'surface_totale': surface_totale,
            'pourcentage_salon': round(pourcentage_salon, 1),
            'confidence': confidence,
            'method': method_used,
            'salon_analysis': salon_analysis
        }
    }


def score_hauteur_plafond(apartment, config):
    """Score pour 'hauteur sous plafond' basé sur l'analyse des photos
    
    Analyse les photos pour estimer la hauteur sous plafond, puis catégorise selon:
    - Tier1 (good): >2.80m (haute ou très haute)
    - Tier2 (moyen): 2.50-2.80m (moyenne)
    - Tier3 (bad): <2.50m (basse)
    """
    # PRIORITÉ: Vérifier si les données de hauteur existent déjà dans l'appartement
    analyses = apartment.get('analyses', {})
    hauteur_data = analyses.get('hauteur_plafond', {})
    
    # Vérifier aussi dans style_analysis si disponible
    if not hauteur_data or not hauteur_data.get('hauteur_estimate'):
        style_analysis = apartment.get('style_analysis', {})
        if isinstance(style_analysis, dict):
            hauteur_style = style_analysis.get('hauteur_plafond', {})
            if isinstance(hauteur_style, dict) and hauteur_style.get('value'):
                # Utiliser les données depuis style_analysis
                hauteur_estimate = hauteur_style.get('value')
                hauteur_category = None
                # Déterminer la catégorie depuis la valeur
                if hauteur_estimate > 3.0:
                    hauteur_category = 'tres_haute'
                elif hauteur_estimate >= 2.80:
                    hauteur_category = 'haute'
                elif hauteur_estimate >= 2.50:
                    hauteur_category = 'moyenne'
                else:
                    hauteur_category = 'basse'
                
                confidence = hauteur_style.get('confidence', 0.5)
                hauteur_analysis = {
                    'hauteur_estimate': hauteur_estimate,
                    'hauteur_category': hauteur_category,
                    'confidence': confidence,
                    'justification': hauteur_style.get('details', f'Hauteur sous plafond estimée: {hauteur_estimate}m')
                }
            else:
                hauteur_analysis = None
        else:
            hauteur_analysis = None
    else:
        # Utiliser les données depuis analyses.hauteur_plafond
        hauteur_estimate = hauteur_data.get('hauteur_estimate')
        hauteur_category = hauteur_data.get('hauteur_category')
        confidence = hauteur_data.get('confidence', 0.5)
        hauteur_analysis = {
            'hauteur_estimate': hauteur_estimate,
            'hauteur_category': hauteur_category,
            'confidence': confidence,
            'justification': hauteur_data.get('justification', f'Hauteur sous plafond estimée: {hauteur_estimate}m')
        }
    
    # RÈGLE GÉNÉRALE: NE JAMAIS lancer d'analyse automatique
    # Si les données n'existent pas, retourner un score par défaut (tier3 = 0 points)
    if not hauteur_analysis or hauteur_analysis.get('hauteur_estimate') is None:
        return {
            'score': 0,
            'tier': 'tier3',
            'justification': 'Données de hauteur sous plafond non disponibles (analyse non effectuée)',
            'details': {}
        }
    
    # Extraire les valeurs depuis hauteur_analysis (qu'il vienne du cache ou de l'analyse)
    hauteur_estimate = hauteur_analysis.get('hauteur_estimate')
    hauteur_category = hauteur_analysis.get('hauteur_category')
    confidence = hauteur_analysis.get('confidence', 0)
    
    # Vérifier que l'analyse a retourné un résultat valide
    if not hauteur_analysis or not isinstance(hauteur_analysis, dict):
        return {
            'score': 0,
            'tier': 'tier3',
            'justification': 'Erreur: analyse de hauteur plafond a retourné un résultat invalide',
            'details': {}
        }
    
    if hauteur_estimate is None:
        return {
            'score': 0,
            'tier': 'tier3',
            'justification': hauteur_analysis.get('justification', 'Hauteur sous plafond non estimable depuis les photos'),
            'details': {
                'hauteur_analysis': hauteur_analysis
            }
        }
    
    # Vérifier que hauteur_estimate est un nombre valide
    try:
        hauteur_estimate = float(hauteur_estimate)
    except (ValueError, TypeError):
        return {
            'score': 0,
            'tier': 'tier3',
            'justification': f'Erreur: hauteur invalide ({hauteur_estimate})',
            'details': {
                'hauteur_analysis': hauteur_analysis
            }
        }
    
    # Déterminer le tier selon la hauteur
    # Tier1: >2.80m (haute ou très haute) = 10 points
    # Tier2: 2.50-2.80m (moyenne) = 5 points
    # Tier3: <2.50m (basse) = 0 points
    
    if hauteur_estimate > 2.80:
        tier = 'tier1'
        score = 10  # Score max pour hauteur élevée
        justification = f"Hauteur sous plafond élevée: {hauteur_estimate:.2f}m ({hauteur_category})"
    elif hauteur_estimate >= 2.50:
        tier = 'tier2'
        score = 5  # Score moyen
        justification = f"Hauteur sous plafond moyenne: {hauteur_estimate:.2f}m ({hauteur_category})"
    else:
        tier = 'tier3'
        score = 0  # Score faible
        justification = f"Hauteur sous plafond basse: {hauteur_estimate:.2f}m ({hauteur_category})"
    
    return {
        'score': score,
        'tier': tier,
        'justification': justification,
        'details': {
            'hauteur_estimate': hauteur_estimate,
            'hauteur_category': hauteur_category,
            'confidence': confidence,
            'hauteur_analysis': hauteur_analysis
        }
    }


def score_cuisine(apartment, config):
    """Score cuisine avec validation croisée texte + photos"""
    tier_config = config['axes']['cuisine']['tiers']
    
    # PRIORITÉ: Utiliser les données existantes si disponibles (depuis style_analysis)
    style_analysis = apartment.get('style_analysis', {})
    cuisine_data = style_analysis.get('cuisine', {})
    
    # Si on a déjà une analyse cuisine avec des données valides, l'utiliser
    if cuisine_data and cuisine_data.get('ouverte') is not None:
        cuisine_ouverte = cuisine_data.get('ouverte', False)
        confidence = cuisine_data.get('confidence', 0)
        justification = cuisine_data.get('justification', '')
        
        if cuisine_ouverte:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': justification or "Cuisine ouverte",
                'details': {
                    'confidence': confidence,
                    'photo_validation': cuisine_data.get('photo_validation'),
                    'validation_status': 'from_style_analysis'
                }
            }
        else:
            return {
                'score': tier_config['tier3']['score'],
                'tier': 'tier3',
                'justification': justification or "Cuisine fermée",
                'details': {
                    'confidence': confidence,
                    'photo_validation': cuisine_data.get('photo_validation'),
                    'validation_status': 'from_style_analysis'
                }
            }
    
    # RÈGLE GÉNÉRALE: NE JAMAIS lancer d'analyse automatique
    # Si les données n'existent pas, retourner un score par défaut (tier2 = note moyenne)
    return {
        'score': tier_config['tier2']['score'],
        'tier': 'tier2',
        'justification': 'Données d\'analyse de cuisine non disponibles (analyse non effectuée)',
        'details': {}
    }


def calculate_bonus_malus(apartment, config):
    """Calcule les bonus/malus depuis caractéristiques"""
    bonus = 0
    malus = 0
    caracteristiques = apartment.get('caracteristiques', '').lower()
    description = apartment.get('description', '').lower()
    text = f"{caracteristiques} {description}"
    
    # Bonus
    if 'balcon' in text:
        bonus += config['bonus']['balcon']
    if 'terrasse' in text:
        bonus += config['bonus']['terrasse']
    if 'ascenseur' in text:
        bonus += config['bonus']['ascenseur']
    if 'parking' in text:
        bonus += config['bonus']['parking']
    if 'cave' in text:
        bonus += config['bonus']['cave']
    if 'croisement' in text or 'croise' in text:
        bonus += config['bonus']['croisement_rue']
    if 'vue dégagée' in text or 'vue degagee' in text:
        bonus += config['bonus']['vue_degagee']
    
    # Malus
    if 'vis-à-vis' in text or 'vis à vis' in text:
        malus += abs(config['malus']['vis_a_vis'])
    if 'nord' in text and ('exposition' in text or 'orientation' in text):
        malus += abs(config['malus']['nord'])
    if 'rdc' in text or 'rez' in text:
        malus += abs(config['malus']['rdc'])
    
    return bonus, malus


def score_baignoire(apartment, config):
    """Score baignoire avec validation croisée texte + photos"""
    tier_config = config['axes']['baignoire']['tiers']
    
    # PRIORITÉ: Utiliser les données existantes si disponibles
    baignoire_data = apartment.get('baignoire', {})
    
    # Si on a déjà une analyse baignoire avec des données valides, l'utiliser
    if baignoire_data and baignoire_data.get('has_baignoire') is not None:
        has_baignoire = baignoire_data.get('has_baignoire', False)
        confidence = baignoire_data.get('confidence', 0)
        justification = baignoire_data.get('justification', '')
        details = baignoire_data.get('details', {})
        
        if has_baignoire:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': justification or 'Baignoire détectée',
                'details': details
            }
        else:
            return {
                'score': tier_config['tier3']['score'],
                'tier': 'tier3',
                'justification': justification or 'Pas de baignoire détectée',
                'details': details
            }
    
    # RÈGLE GÉNÉRALE: NE JAMAIS lancer d'analyse automatique
    # Si les données n'existent pas, retourner un score par défaut (tier2 = note moyenne)
    return {
        'score': tier_config['tier2']['score'],
        'tier': 'tier2',
        'justification': 'Données d\'analyse de baignoire non disponibles (analyse non effectuée)',
        'details': {}
    }


def score_ascenseur(apartment, config):
    """Score présence d'ascenseur
    Score: 10pts si présent, 0pts sinon
    """
    # Vérifier depuis API data en priorité
    api_data = apartment.get('_api_data', {})
    features = api_data.get('features', {})
    if isinstance(features, dict):
        lift = features.get('lift', 0)
        if lift == 1:
            return {
                'score': 10,
                'tier': 'tier1',
                'justification': 'Ascenseur présent (données API)'
            }
    
    # Vérifier depuis caractéristiques
    caracteristiques = apartment.get('caracteristiques', '').lower()
    description = apartment.get('description', '').lower()
    text_combined = f"{caracteristiques} {description}"
    
    if 'ascenseur' in text_combined:
        return {
            'score': 10,
            'tier': 'tier1',
            'justification': 'Ascenseur détecté dans le texte'
        }
    
    # Pas d'ascenseur détecté
    return {
        'score': 0,
        'tier': 'tier3',
        'justification': 'Pas d\'ascenseur détecté'
    }


def score_renove(apartment, config):
    """Score rénové/restauré
    Score: 10pts si rénové, 0pts sinon
    """
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    text_combined = f"{description} {caracteristiques}"
    
    # Mots-clés indiquant rénovation
    renov_keywords = ['rénové', 'renove', 'restauré', 'restaure', 'refait', 'refait à neuf', 
                     'entièrement rénové', 'entièrement restaure', 'récemment rénové']
    
    for keyword in renov_keywords:
        if keyword in text_combined:
            return {
                'score': 10,
                'tier': 'tier1',
                'justification': f'Appartement rénové détecté ({keyword})'
            }
    
    # Vérifier aussi dans style_analysis si disponible
    style_analysis = apartment.get('style_analysis', {})
    if style_analysis:
        style_text = str(style_analysis).lower()
        for keyword in renov_keywords:
            if keyword in style_text:
                return {
                    'score': 10,
                    'tier': 'tier1',
                    'justification': f'Appartement rénové détecté dans analyse style'
                }
    
    # Pas de rénovation détectée
    return {
        'score': 0,
        'tier': 'tier3',
        'justification': 'Pas de rénovation détectée'
    }


def score_calme(apartment, config):
    """Score calme du quartier basé sur données Overpass API
    Utilise l'adresse exacte pour trouver le type de rue, plus bars/restos et commerces agités dans 100m
    Pondération égale: 33% type de rue, 33% bars/restos, 33% commerces agités
    Score: tier1 (10pts) si très calme, tier2 (5pts) si moyen, tier3 (0pts) si animé
    """
    tier_config = config['axes']['calme']['tiers']
    
    # Vérifier que l'appartement a les coordonnées nécessaires
    coordinates = apartment.get('coordinates', {})
    latitude = coordinates.get('latitude')
    longitude = coordinates.get('longitude')
    
    if not latitude or not longitude:
        # Fallback: tier2 (moyen) si pas de coordonnées
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': 'Coordonnées non disponibles - note moyenne par défaut',
            'details': {}
        }
    
    try:
        from criteria.calme import fetch_calme_data, calculate_calme_score
        
        # Récupérer les données depuis Overpass API (avec cache)
        # fetch_calme_data prend maintenant apartment complet pour extraire l'adresse
        calme_data = fetch_calme_data(apartment, radius=100)
        
        # Vérifier s'il y a une erreur
        if calme_data.get('error'):
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': calme_data.get('error', 'Erreur récupération données'),
                'details': {}
            }
        
        # Calculer le score pondéré
        calme_score_result = calculate_calme_score(calme_data)
        
        # Convertir le score normalisé (0-100) en tier
        normalized_score = calme_score_result.get('normalized_score', 50)
        seuils = config['axes']['calme'].get('seuils', {})
        tier1_min = seuils.get('tier1_min', 60)
        tier2_min = seuils.get('tier2_min', 40)
        
        if normalized_score >= tier1_min:
            tier = 'tier1'
            score = tier_config['tier1']['score']
        elif normalized_score >= tier2_min:
            tier = 'tier2'
            score = tier_config['tier2']['score']
        else:
            tier = 'tier3'
            score = tier_config['tier3']['score']
        
        return {
            'score': score,
            'tier': tier,
            'justification': calme_score_result.get('justification', 'Quartier analysé'),
            'details': calme_score_result.get('details', {}),
            'normalized_score': normalized_score,
            'source': 'overpass_api'
        }
        
    except Exception as e:
        # En cas d'erreur, fallback sur tier2 (moyen)
        import traceback
        print(f"⚠️ Erreur dans score_calme: {e}")
        traceback.print_exc()
        
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': f'Erreur analyse calme - note moyenne par défaut: {str(e)}',
            'details': {}
        }


def score_apartment(apartment, config):
    """
    Score un appartement avec règles simples depuis config
    
    Args:
        apartment: Dict avec données scrapées + analyses IA
        config: Dict avec scoring_config.json
        
    Returns:
        Dict avec scores détaillés + score total
    """
    scores_detaille = {}
    
    # Calculer chaque critère
    scores_detaille['localisation'] = score_localisation(apartment, config)
    scores_detaille['prix'] = score_prix(apartment, config)
    scores_detaille['style'] = score_style(apartment, config)
    scores_detaille['ensoleillement'] = score_ensoleillement(apartment, config)
    scores_detaille['etage'] = score_etage(apartment, config)
    scores_detaille['surface'] = score_surface(apartment, config)
    scores_detaille['cuisine'] = score_cuisine(apartment, config)
    scores_detaille['baignoire'] = score_baignoire(apartment, config)
    scores_detaille['calme'] = score_calme(apartment, config)
    
    # Calculer score total : SEULEMENT les 5 critères de scoring (20pts chacun = 100pts total)
    scored_criteria = ['localisation', 'prix', 'style', 'ensoleillement', 'cuisine']
    score_total = sum(scores_detaille.get(key, {}).get('score', 0) for key in scored_criteria)
    
    # Pas de bonus/malus (supprimés - jamais validés)
    bonus = 0
    malus = 0
    
    # Arrondir au multiple de 5 le plus proche
    score_total = round_to_nearest_5(score_total)
    
    # Déterminer tier global
    if score_total >= 80:
        tier = 'tier1'
    elif score_total >= 60:
        tier = 'tier2'
    else:
        tier = 'tier3'
    
    return {
        'id': apartment.get('id'),
        'score_total': score_total,
        'tier': tier,
        'scores_detaille': scores_detaille,
        'bonus': 0,  # Bonus/malus supprimés - jamais validés
        'malus': 0,  # Bonus/malus supprimés - jamais validés
        'date_scoring': apartment.get('scraped_at', ''),
        'model_used': 'rules_based'  # Pas d'IA
    }


def score_all_apartments(scraped_apartments):
    """
    Score tous les appartements scrapés
    
    Args:
        scraped_apartments: List de dicts avec données scrapées
        
    Returns:
        List de dicts avec scores calculés
    """
    config = load_scoring_config()
    if not config:
        return []
    
    scored_apartments = []
    for apartment in scraped_apartments:
        score_result = score_apartment(apartment, config)
        # Fusionner avec données originales
        score_result.update(apartment)
        scored_apartments.append(score_result)
    
    return scored_apartments

