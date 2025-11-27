"""
Système de scoring personnalisé pour les alertes
Réutilise les fonctions de scoring existantes et normalise les scores selon les critères de l'alerte
"""

import json
from scoring import (
    score_localisation, score_prix, score_style, score_ensoleillement,
    score_cuisine, score_surface, score_ascenseur, score_renove,
    load_scoring_config
)


# Mapping des critères UI vers les fonctions de scoring
CRITERIA_MAPPING = {
    'haussmanien': {
        'function': score_style,
        'max_score': 20,  # Score max original
        'detect_haussmannien': True  # Flag spécial pour détecter uniquement Haussmannien
    },
    'quartier': {
        'function': score_localisation,
        'max_score': 20
    },
    'prix': {
        'function': score_prix,
        'max_score': 20
    },
    'luminosite': {
        'function': score_ensoleillement,
        'max_score': 20
    },
    'cuisine_ouverte': {
        'function': score_cuisine,
        'max_score': 10
    },
    'ascenseur': {
        'function': score_ascenseur,
        'max_score': 10
    },
    'large_piece_vie': {
        'function': score_surface,
        'max_score': 5
    },
    'renove': {
        'function': score_renove,
        'max_score': 10
    },
    'neuf': {
        'function': score_style,
        'max_score': 20,
        'detect_neuf': True  # Flag spécial pour détecter uniquement neuf
    }
}


def get_score_from_tier(tier, target_max_score):
    """
    Attribue un score selon le tier (good/moyen/bad)
    
    Args:
        tier: Tier du critère ('tier1', 'tier2', 'tier3')
        target_max_score: Score maximum pour ce critère (30pts pour critère principal, 20pts pour secondaire)
    
    Returns:
        Score selon le tier:
        - tier1 (good) = 100% de target_max_score
        - tier2 (moyen) = 50% de target_max_score
        - tier3 (bad) = 0
    """
    if tier == 'tier1':
        # Good = 100%
        return target_max_score
    elif tier == 'tier2':
        # Moyen = 50%
        return target_max_score * 0.5
    else:
        # Bad ou tier3 = 0
        return 0


def score_criterion_for_alert(apartment, criterion_name, config, target_max=30):
    """
    Score un critère spécifique pour une alerte
    
    Args:
        apartment: Dict avec données de l'appartement
        criterion_name: Nom du critère (ex: 'haussmanien', 'quartier')
        config: Config de scoring
        target_max: Score maximum pour ce critère (30pts ou 20pts)
    
    Returns:
        Dict avec score normalisé et détails
    """
    if criterion_name not in CRITERIA_MAPPING:
        return {
            'score': 0,
            'tier': 'tier3',
            'justification': f'Critère {criterion_name} non reconnu'
        }
    
    criterion_info = CRITERIA_MAPPING[criterion_name]
    scoring_function = criterion_info['function']
    max_original_score = criterion_info['max_score']
    
    # Cas spéciaux pour haussmanien et neuf qui utilisent score_style
    if criterion_name == 'haussmanien':
        # Appeler score_style et vérifier si c'est Haussmannien
        style_result = scoring_function(apartment, config)
        # Vérifier si c'est tier1 (Haussmannien)
        if style_result.get('tier') == 'tier1':
            # C'est haussmannien (good)
            style_result['tier'] = 'tier1'
        else:
            # Pas haussmannien (bad)
            style_result['tier'] = 'tier3'
            style_result['justification'] = 'Style non haussmannien'
        original_score = style_result.get('score', 0)
    elif criterion_name == 'neuf':
        # Détecter si l'appartement est neuf
        api_data = apartment.get('_api_data', {}) or {}
        buy_type = api_data.get('buy_type', '') or ''
        description = str(apartment.get('description') or '').lower()
        caracteristiques = str(apartment.get('caracteristiques') or '').lower()
        text_combined = f"{description} {caracteristiques}"
        
        # Mots-clés indiquant neuf
        neuf_keywords = ['neuf', 'nouveau', 'récent', 'recent', 'construction récente']
        
        is_neuf = False
        if buy_type == 'new':
            is_neuf = True
            justification = 'Appartement neuf (buy_type: new)'
        elif any(keyword in text_combined for keyword in neuf_keywords):
            is_neuf = True
            justification = 'Appartement neuf détecté dans le texte'
        else:
            # Vérifier aussi dans style_analysis
            style_analysis = apartment.get('style_analysis') or {}
            if style_analysis:
                style_text = str(style_analysis or '').lower()
                if any(keyword in style_text for keyword in neuf_keywords):
                    is_neuf = True
                    justification = 'Appartement neuf détecté dans analyse style'
                else:
                    justification = 'Appartement non neuf'
            else:
                justification = 'Appartement non neuf'
        
        # Pour 'neuf', tier1 = neuf détecté, tier3 = pas neuf
        style_result = {
            'tier': 'tier1' if is_neuf else 'tier3',
            'justification': justification
        }
        original_score = 20 if is_neuf else 0
    else:
        # Cas normal: appeler la fonction de scoring
        result = scoring_function(apartment, config)
        original_score = result.get('score', 0)
        style_result = result
    
    # Attribuer le score selon le tier (good/moyen/bad)
    tier = style_result.get('tier', 'tier3')
    score = get_score_from_tier(tier, target_max)
    
    return {
        'score': round(score, 2),
        'tier': tier,
        'justification': style_result.get('justification', ''),
        'original_score': original_score,
        'max_original_score': max_original_score
    }


def score_apartment_for_alert(apartment, alert_config, scoring_config=None):
    """
    Score un appartement selon les critères d'une alerte personnalisée
    
    Args:
        apartment: Dict avec données de l'appartement
        alert_config: Dict avec configuration de l'alerte:
            {
                'criteria': {
                    'primary': ['critere1', 'critere2', 'critere3'],
                    'secondary': ['critere4']
                }
            }
        scoring_config: Config de scoring (optionnel, chargé automatiquement si None)
    
    Returns:
        Dict avec score personnalisé et détails par critère
    """
    if scoring_config is None:
        scoring_config = load_scoring_config()
        if not scoring_config:
            return {
                'score': 0,
                'tier': 'tier3',
                'justification': 'Erreur: config de scoring non disponible',
                'criteria_scores': {}
            }
    
    criteria_config = alert_config.get('criteria', {})
    primary_criteria = criteria_config.get('primary', [])
    secondary_criteria = criteria_config.get('secondary', [])
    
    # Répartition: 2 critères principaux à 30pts + 2 critères secondaires à 20pts = 100pts
    # Les critères dans primary[] = 30pts chacun
    # Les critères dans secondary[] = 20pts chacun
    
    criteria_scores = {}
    total_score = 0
    
    # Score des critères principaux (30pts chacun)
    for criterion in primary_criteria:
        criterion_result = score_criterion_for_alert(
            apartment, criterion, scoring_config, target_max=30
        )
        criteria_scores[criterion] = criterion_result
        total_score += criterion_result['score']
    
    # Score des critères secondaires (20pts chacun)
    for criterion in secondary_criteria:
        criterion_result = score_criterion_for_alert(
            apartment, criterion, scoring_config, target_max=20
        )
        criteria_scores[criterion] = criterion_result
        total_score += criterion_result['score']
    
    # Arrondir le score total
    total_score = round(total_score, 2)
    
    # Déterminer le tier global
    if total_score >= 80:
        tier = 'tier1'
    elif total_score >= 60:
        tier = 'tier2'
    else:
        tier = 'tier3'
    
    return {
        'score': total_score,
        'tier': tier,
        'criteria_scores': criteria_scores,
        'max_score': 100  # 2×30 + 2×20
    }


def filter_apartments_by_alert(apartments, alert_config):
    """
    Filtre les appartements selon les critères de l'alerte (localisation, budget, surface, pièces)
    
    Args:
        apartments: Liste d'appartements
        alert_config: Dict avec configuration de l'alerte:
            {
                'filters': {
                    'localisation': 'zone/quartier' (optionnel),
                    'budget_min': 0,
                    'budget_max': 1000000,
                    'surface_min': 0,
                    'surface_max': 200,
                    'pieces_min': 0,
                    'pieces_max': 10
                }
            }
    
    Returns:
        Liste d'appartements filtrés
    """
    filters = alert_config.get('filters', {})
    filtered = []
    
    for apartment in apartments:
        # Filtre budget
        prix_str = apartment.get('prix', '')
        import re
        prix_match = re.search(r'([\d\s]+)', prix_str.replace(' ', '')) if prix_str else None
        if prix_match:
            try:
                prix = int(prix_match.group(1))
                budget_min = filters.get('budget_min', 0)
                budget_max = filters.get('budget_max', 10000000)
                if prix < budget_min or prix > budget_max:
                    continue
            except:
                pass
        
        # Filtre surface
        surface_str = apartment.get('surface', '')
        surface_match = re.search(r'(\d+)', surface_str) if surface_str else None
        if surface_match:
            try:
                surface = int(surface_match.group(1))
                surface_min = filters.get('surface_min', 0)
                surface_max = filters.get('surface_max', 1000)
                if surface < surface_min or surface > surface_max:
                    continue
            except:
                pass
        
        # Filtre pièces
        pieces_str = apartment.get('pieces', '')
        pieces_match = re.search(r'(\d+)', pieces_str) if pieces_str else None
        if pieces_match:
            try:
                pieces = int(pieces_match.group(1))
                pieces_min = filters.get('pieces_min', 0)
                pieces_max = filters.get('pieces_max', 20)
                if pieces < pieces_min or pieces > pieces_max:
                    continue
            except:
                pass
        
        # Filtre localisation (optionnel)
        localisation_filter = filters.get('localisation', '')
        if localisation_filter:
            # Gérer plusieurs quartiers séparés par des virgules
            quartier_filters = [q.strip() for q in localisation_filter.split(',')]
            # S'assurer que les valeurs sont des chaînes (pas None)
            localisation = str(apartment.get('localisation') or '').lower()
            map_info = apartment.get('map_info', {}) or {}
            quartier = str(map_info.get('quartier') or '').lower()
            
            # Vérifier si au moins un des quartiers correspond
            matches = False
            for q_filter in quartier_filters:
                if not q_filter:  # Ignorer les filtres vides
                    continue
                q_filter_lower = q_filter.lower()
                # Enlever "Métro " si présent pour la comparaison
                q_filter_clean = q_filter_lower.replace('métro ', '').replace('metro ', '')
                
                # Vérifier dans la localisation
                if localisation and (q_filter_lower in localisation or q_filter_clean in localisation):
                    matches = True
                    break
                
                # Vérifier dans le quartier
                if quartier and (q_filter_lower in quartier or q_filter_clean in quartier):
                    matches = True
                    break
                
                # Vérifier dans les métros
                metros = map_info.get('metros', []) or []
                if metros:
                    metro_match = any(
                        q_filter_lower in str(m).lower() or q_filter_clean in str(m).lower()
                        for m in metros if m is not None
                    )
                    if metro_match:
                        matches = True
                        break
            
            if not matches:
                continue
        
        filtered.append(apartment)
    
    return filtered

