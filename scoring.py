"""
Scoring - Calcul des scores depuis règles simples (pas d'IA)
Utilise scoring_config.json pour les règles de scoring
"""

import json
import os
import re
from criteria.localisation import get_metro_name, get_quartier_name


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
    """Score localisation selon zones définies dans config"""
    tier_config = config['axes']['localisation']['tiers']
    
    # Récupérer localisation, quartier, métro
    localisation = apartment.get('localisation', '').lower()
    quartier = get_quartier_name(apartment)
    if quartier:
        quartier = quartier.lower()
    metro = get_metro_name(apartment)
    if metro:
        metro = metro.lower()
    
    # Vérifier tier1 (zones premium)
    tier1_zones = [z.lower() for z in tier_config['tier1']['zones']]
    for zone in tier1_zones:
        if zone in localisation or (quartier and zone in quartier) or (metro and zone in metro):
            score = tier_config['tier1']['score']
            # Bonus Place de la Réunion
            if 'place de la réunion' in localisation or (quartier and 'place de la réunion' in quartier):
                score += config['bonus']['place_reunion']
            return {
                'score': score,
                'tier': 'tier1',
                'justification': f"Zone premium: {zone}"
            }
    
    # Vérifier tier2 (bonnes zones)
    tier2_zones = [z.lower() for z in tier_config['tier2']['zones']]
    for zone in tier2_zones:
        if zone in localisation or (quartier and zone in quartier) or (metro and zone in metro):
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
    """Score style depuis style_analysis (IA images)"""
    tier_config = config['axes']['style']['tiers']
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    style_type = style_data.get('type', '').lower()
    
    # Vérifier tier1 (haussmannien, loft, atypique)
    tier1_styles = [s.lower() for s in tier_config['tier1']['styles']]
    if style_type in tier1_styles or 'haussmann' in style_type:
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': f"Style premium: {style_type}"
        }
    
    # Vérifier tier3 (années 60-70 - veto)
    if '70' in style_type or '60' in style_type or 'seventies' in style_type:
        return {
            'score': tier_config['veto']['score'],
            'tier': 'tier3',
            'justification': f"Style années 60-70: {style_type}"
        }
    
    # tier2: Moderne, Récent, Contemporain (styles acceptables)
    if 'moderne' in style_type or 'contemporain' in style_type or 'récent' in style_type:
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': f"Style: {style_type}"
        }
    
    # Par défaut tier2 (autres styles acceptables)
    return {
        'score': tier_config['tier2']['score'],
        'tier': 'tier2',
        'justification': f"Style: {style_type}"
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
    
    # tier3 par défaut (faible luminosité)
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': f"Luminosité: {luminosite_type}"
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
    
    # Calculer score total
    score_total = sum(s.get('score', 0) for s in scores_detaille.values())
    
    # Ajouter bonus/malus
    bonus, malus = calculate_bonus_malus(apartment, config)
    score_total += bonus - malus
    
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
        'bonus': bonus,
        'malus': malus,
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

