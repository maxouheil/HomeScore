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


def score_localisation(apartment, config):
    """Score localisation selon zones définies dans config - utilise TOUTES les stations et rues"""
    tier_config = config['axes']['localisation']['tiers']
    
    # Récupérer localisation, quartier, description, toutes les stations de métro
    localisation = apartment.get('localisation', '').lower()
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    text_combined = f"{localisation} {description} {caracteristiques}"
    
    quartier = get_quartier_name(apartment)
    if quartier:
        quartier = quartier.lower()
    
    # Récupérer TOUTES les stations de métro (pas seulement la meilleure pour l'affichage)
    all_stations = get_all_metro_stations(apartment)
    all_stations_lower = [s.lower() for s in all_stations] if all_stations else []
    
    # Vérifier tier1 (zones premium) - vérifier toutes les stations et dans le texte
    tier1_zones = [z.lower() for z in tier_config['tier1']['zones']]
    for zone in tier1_zones:
        # Vérifier dans localisation, quartier, texte combiné, ou n'importe quelle station
        zone_matched = False
        matched_station = None
        
        if zone in localisation or zone in text_combined:
            zone_matched = True
        elif quartier and zone in quartier:
            zone_matched = True
        else:
            # Vérifier toutes les stations
            for station in all_stations_lower:
                if zone in station or station in zone:
                    zone_matched = True
                    matched_station = station
                    break
        
        if zone_matched:
            score = tier_config['tier1']['score']
            # Bonus Place de la Réunion
            if 'place de la réunion' in localisation or (quartier and 'place de la réunion' in quartier) or 'place de la réunion' in text_combined:
                score += config['bonus']['place_reunion']
            
            # Construire la justification avec la station trouvée
            if matched_station:
                justification = f"Zone premium: {zone} (métro {matched_station})"
            else:
                justification = f"Zone premium: {zone}"
            
            return {
                'score': score,
                'tier': 'tier1',
                'justification': justification
            }
    
    # Vérifier tier2 (bonnes zones) - vérifier toutes les stations ET dans le texte (pour "Rue des Boulets", "Nation")
    tier2_zones = [z.lower() for z in tier_config['tier2']['zones']]
    for zone in tier2_zones:
        # Vérifier dans localisation, quartier, texte combiné, ou n'importe quelle station
        zone_matched = False
        matched_station = None
        
        # Chercher dans le texte combiné (description, caractéristiques) pour détecter les rues comme "Rue des Boulets"
        if zone in localisation or zone in text_combined:
            zone_matched = True
        elif quartier and zone in quartier:
            zone_matched = True
        else:
            # Vérifier toutes les stations (pour "Nation" par exemple)
            for station in all_stations_lower:
                if zone in station or station in zone:
                    zone_matched = True
                    matched_station = station
                    break
        
        if zone_matched:
            justification = f"Bonne zone: {zone}"
            if matched_station:
                justification += f" (métro {matched_station})"
            
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': justification
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
            'score': 0,
            'tier': 'tier3',
            'justification': "Prix/m² non disponible"
        }
    
    # Vérifier tier1 (< 9000)
    if prix_m2 < tier_config['tier1']['prix_m2_max']:
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': f"Excellent rapport qualité/prix: {prix_m2}€/m²"
        }
    
    # Vérifier tier2 (9000-10999)
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
    """Score style depuis style_analysis (IA images) + analyse texte - Ancien (20pts) / Atypique (10pts) / Neuf (0pts)"""
    tier_config = config['axes']['style']['tiers']
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    style_type = style_data.get('type', '').lower()
    
    # Analyser le texte pour détecter "Atypique" (loft, atypique, unique, original, ancien entrepôt, etc.)
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
    
    # Tier1: Ancien (Haussmannien) = 20 pts
    tier1_styles = [s.lower() for s in tier_config['tier1']['styles']]
    if style_type in tier1_styles or 'haussmann' in style_type:
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': f"Style ancien: {style_type}"
        }
    
    # Tier2: Atypique (détecté depuis texte: loft, atypique, unique, original) = 10 pts
    if is_atypique or 'loft' in style_type or 'atypique' in style_type:
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': f"Style atypique détecté (loft/atypique/unique/original)"
        }
    
    # Tout le reste = Neuf (0 pts): moderne, contemporain, récent, 70s, 60s, années 20-40, etc.
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': f"Style neuf: {style_type}"
    }


def score_ensoleillement(apartment, config):
    """Score ensoleillement depuis style_analysis.luminosite + exposition"""
    tier_config = config['axes']['ensoleillement']['tiers']
    style_analysis = apartment.get('style_analysis', {})
    luminosite_data = style_analysis.get('luminosite', {})
    luminosite_type = luminosite_data.get('type', '').lower()
    
    exposition = apartment.get('exposition', {})
    exposition_dir = exposition.get('exposition', '').lower()
    
    # Vérifier tier1 (excellente luminosité + Sud/Sud-Ouest)
    if 'excellente' in luminosite_type:
        if exposition_dir in ['sud', 'sud-ouest', 'sud-ouest']:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': f"Excellente luminosité, exposition {exposition_dir}"
            }
        # Si luminosité excellente mais exposition différente → tier2 quand même
        elif exposition_dir:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': f"Excellente luminosité, exposition {exposition_dir}"
            }
        # Luminosité excellente mais pas d'exposition → tier2
        else:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': f"Excellente luminosité"
            }
    
    # Vérifier tier2 (bonne OU moyenne luminosité)
    if 'bonne' in luminosite_type or 'moyenne' in luminosite_type or 'moyen' in luminosite_type:
        # Si exposition Ouest/Est ou Sud-Ouest → tier2
        if exposition_dir in ['ouest', 'est', 'sud-ouest']:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': f"Luminosité {luminosite_type}, exposition {exposition_dir}"
            }
        # Sinon, même avec moyenne luminosité → tier2 (10pts selon config)
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': f"Luminosité {luminosite_type}"
        }
    
    # Si luminosité manquante mais exposition disponible, utiliser l'exposition
    if not luminosite_type or luminosite_type == 'inconnue' or luminosite_type == 'inconnu':
        if exposition_dir:
            # Tier1: Sud, Sud-Ouest
            if exposition_dir in ['sud', 'sud-ouest', 'sud-ouest']:
                return {
                    'score': tier_config['tier1']['score'],
                    'tier': 'tier1',
                    'justification': f"Exposition {exposition_dir} détectée"
                }
            # Tier2: Ouest, Est
            elif exposition_dir in ['ouest', 'est']:
                return {
                    'score': tier_config['tier2']['score'],
                    'tier': 'tier2',
                    'justification': f"Exposition {exposition_dir} détectée"
                }
            # Tier3: Nord, Nord-Est
            elif exposition_dir in ['nord', 'nord-est']:
                return {
                    'score': tier_config['tier3']['score'],
                    'tier': 'tier3',
                    'justification': f"Exposition {exposition_dir} détectée"
                }
    
    # tier3 par défaut (faible luminosité ou aucune info)
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': f"Luminosité: {luminosite_type if luminosite_type else 'non disponible'}"
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


def score_cuisine(apartment, config):
    """Score cuisine depuis style_analysis.cuisine (IA images)
    Simplifié: Ouverte (10pts) ou Fermée (0pts)
    """
    tier_config = config['axes']['cuisine']['tiers']
    style_analysis = apartment.get('style_analysis', {})
    cuisine_data = style_analysis.get('cuisine', {})
    cuisine_ouverte = cuisine_data.get('ouverte', False)
    
    # tier1: ouverte uniquement (10pts)
    if cuisine_ouverte:
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': "Cuisine ouverte"
        }
    
    # tier3: fermée (0pts)
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': "Cuisine fermée"
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
    """Score baignoire depuis analyse texte/IA"""
    # Utiliser criteria/baignoire pour obtenir les données
    from criteria.baignoire import format_baignoire
    
    formatted = format_baignoire(apartment)
    has_baignoire = formatted.get('main_value') == 'Oui'
    
    # tier1: baignoire présente = 10pts (good)
    if has_baignoire:
        return {
            'score': 10,
            'tier': 'tier1',
            'justification': 'Baignoire détectée'
        }
    
    # tier3: pas de baignoire = 0pts
    return {
        'score': 0,
        'tier': 'tier3',
        'justification': 'Pas de baignoire détectée'
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
    
    # Calculer score total : SEULEMENT les 6 critères de scoring (exclure etage, surface qui sont des indices)
    scored_criteria = ['localisation', 'prix', 'style', 'ensoleillement', 'cuisine', 'baignoire']
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

