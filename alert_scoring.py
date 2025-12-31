"""
Système de scoring personnalisé pour les alertes
Réutilise les fonctions de scoring existantes et normalise les scores selon les critères de l'alerte
"""

import json
from scoring import (
    score_localisation, score_prix, score_style, score_ensoleillement,
    score_cuisine, score_surface, score_ascenseur, score_renove,
    score_large_piece_vie, score_hauteur_plafond, score_calme, load_scoring_config
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
        'function': score_large_piece_vie,
        'max_score': 10
    },
    'hauteur_plafond': {
        'function': score_hauteur_plafond,
        'max_score': 10
    },
    'renove': {
        'function': score_renove,
        'max_score': 10
    },
    'neuf': {
        'function': score_style,
        'max_score': 20,
        'detect_neuf': True  # Flag spécial pour détecter uniquement neuf
    },
    'calme': {
        'function': score_calme,
        'max_score': 10
    }
}


def get_score_from_tier(tier, target_max_score):
    """
    Attribue un score selon le tier (good/moyen/bad)
    
    Args:
        tier: Tier du critère ('tier1', 'tier2', 'tier3')
        target_max_score: Score maximum pour ce critère (IGNORÉ - toujours 1pt par critère)
    
    Returns:
        Score selon le tier:
        - tier1 (good) = 1pt
        - tier2 (moyen) = 0.5pt
        - tier3 (bad) = 0pt
    """
    # NOUVEAU SYSTÈME: Ignorer target_max_score, toujours retourner 1pt, 0.5pt ou 0pt
    if tier == 'tier1':
        # Good = 1pt
        return 1.0
    elif tier == 'tier2':
        # Moyen = 0.5pt
        return 0.5
    else:
        # Bad ou tier3 = 0pt
        return 0.0


def score_criterion_for_alert(apartment, criterion_name, config, target_max=1):
    """
    Score un critère spécifique pour une alerte
    
    Args:
        apartment: Dict avec données de l'appartement
        criterion_name: Nom du critère (ex: 'haussmanien', 'quartier')
        config: Config de scoring
        target_max: Score maximum pour ce critère (1pt par critère)
    
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
        # Utiliser uniquement les données existantes (ne pas déclencher d'analyses)
        # Vérifier d'abord si style_analysis existe
        style_analysis = apartment.get('style_analysis', {})
        if style_analysis:
            # Utiliser les données existantes
            style_result = scoring_function(apartment, config)
        else:
            # Pas de style_analysis, utiliser un score par défaut (tier3 = 0pt)
            style_result = {
                'tier': 'tier3',
                'justification': 'Style non analysé (données manquantes)',
                'score': 0
            }
        # Vérifier si c'est tier1 (Haussmannien)
        if style_result.get('tier') == 'tier1':
            # C'est haussmannien (good)
            style_result['tier'] = 'tier1'
        else:
            # Pas haussmannien (bad)
            style_result['tier'] = 'tier3'
            if not style_result.get('justification'):
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
        # IMPORTANT: Utiliser uniquement les données existantes, ne pas déclencher d'analyses
        # Pour éviter de bloquer le chargement, on vérifie d'abord si les données nécessaires existent
        try:
            # Pour les critères qui nécessitent des analyses (style, cuisine), vérifier si les données existent
            needs_analysis = criterion_name in ['haussmanien', 'neuf', 'cuisine_ouverte']
            if needs_analysis:
                # Vérifier si les données d'analyse existent déjà
                style_analysis = apartment.get('style_analysis', {})
                if not style_analysis and criterion_name in ['haussmanien', 'neuf']:
                    # Pas de style_analysis, retourner un score par défaut (tier3 = 0pt)
                    style_result = {
                        'tier': 'tier3',
                        'justification': f'Données d\'analyse manquantes pour {criterion_name}',
                        'score': 0
                    }
                    original_score = 0
                else:
                    # Données existantes, appeler la fonction de scoring
                    result = scoring_function(apartment, config)
                    original_score = result.get('score', 0)
                    style_result = result
            else:
                # Critères qui n'ont pas besoin d'analyses (localisation, prix, etc.)
                result = scoring_function(apartment, config)
                original_score = result.get('score', 0)
                style_result = result
        except Exception as e:
            # En cas d'erreur, retourner un score par défaut (tier3 = 0pt)
            print(f"⚠️ Erreur scoring critère {criterion_name}: {e}")
            import traceback
            traceback.print_exc()
            style_result = {
                'tier': 'tier3',
                'justification': f'Erreur lors du scoring: {str(e)}',
                'score': 0
            }
            original_score = 0
    
    # Attribuer le score selon le tier (good/moyen/bad)
    tier = style_result.get('tier', 'tier3')
    score = get_score_from_tier(tier, target_max)
    
    # DEBUG: Vérifier que le score est bien sur 1pt max
    if score > 1.0:
        print(f"⚠️ ERREUR: Score {score} > 1.0 pour critère {criterion_name}, tier {tier}")
    
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
                    'all': ['critere1', 'critere2', 'critere3', 'critere4', 'critere5']
                }
                # Support ancien format pour compatibilité:
                # 'primary': ['critere1', 'critere2', 'critere3'],
                # 'secondary': ['critere4']
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
    
    # Support nouveau format (all) et ancien format (primary/secondary) pour compatibilité
    if 'all' in criteria_config:
        all_criteria = criteria_config['all']
    else:
        # Ancien format: combiner primary et secondary
        primary_criteria = criteria_config.get('primary', [])
        secondary_criteria = criteria_config.get('secondary', [])
        all_criteria = primary_criteria + secondary_criteria
    
    # Tous les critères valent 1pt chacun (good=1pt, moyen=0.5pt, bad=0pt)
    # Score total sur 5 (5 critères × 1pt max = 5pts)
    criteria_scores = {}
    total_score = 0
    
    # Score de tous les critères (1pt chacun max)
    for criterion in all_criteria:
        criterion_result = score_criterion_for_alert(
            apartment, criterion, scoring_config, target_max=1
        )
        criteria_scores[criterion] = criterion_result
        crit_score = criterion_result['score']
        
        # DEBUG: Vérifier chaque score individuel
        if crit_score > 1.0:
            print(f"⚠️ ERREUR: Score critère {criterion} = {crit_score} > 1.0")
        
        total_score += crit_score
    
    # Arrondir le score total
    total_score = round(total_score, 2)
    
    # DEBUG: Vérifier le score total
    if total_score > 5.0:
        print(f"⚠️ ERREUR: Score total {total_score} > 5.0 pour appartement {apartment.get('id', 'unknown')}")
        print(f"   Scores individuels: {[(k, v['score']) for k, v in criteria_scores.items()]}")
    
    # Déterminer le tier global (sur 5pts max)
    if total_score >= 4:
        tier = 'tier1'
    elif total_score >= 2.5:
        tier = 'tier2'
    else:
        tier = 'tier3'
    
    return {
        'score': total_score,
        'tier': tier,
        'criteria_scores': criteria_scores,
        'max_score': 5  # 5 critères × 1pt max
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
    
    # DEBUG: Compter les raisons de filtrage
    debug_stats = {
        'total': len(apartments),
        'filtered_by_budget': 0,
        'filtered_by_surface': 0,
        'filtered_by_pieces': 0,
        'filtered_by_localisation': 0,
        'passed_all_filters': 0
    }
    
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
                    debug_stats['filtered_by_budget'] += 1
                    continue
            except:
                pass
        elif filters.get('budget_min', 0) > 0 or filters.get('budget_max', 10000000) < 10000000:
            # Si pas de prix mais qu'un budget est spécifié, filtrer (sauf si budget très large)
            debug_stats['filtered_by_budget'] += 1
            continue
        
        # Filtre surface
        surface_str = apartment.get('surface', '')
        surface_match = re.search(r'(\d+)', surface_str) if surface_str else None
        if surface_match:
            try:
                surface = int(surface_match.group(1))
                surface_min = filters.get('surface_min', 0)
                surface_max = filters.get('surface_max', 1000)
                if surface < surface_min or surface > surface_max:
                    debug_stats['filtered_by_surface'] += 1
                    continue
            except:
                pass
        elif filters.get('surface_min', 0) > 0 or filters.get('surface_max', 1000) < 1000:
            # Si pas de surface mais qu'une surface est spécifiée, filtrer (sauf si très large)
            debug_stats['filtered_by_surface'] += 1
            continue
        
        # Filtre pièces
        pieces_str = apartment.get('pieces', '')
        pieces_match = re.search(r'(\d+)', pieces_str) if pieces_str else None
        pieces_filtered = False
        if pieces_match:
            try:
                pieces = int(pieces_match.group(1))
                pieces_min = filters.get('pieces_min', 0)
                pieces_max = filters.get('pieces_max', 20)
                if pieces < pieces_min or pieces > pieces_max:
                    debug_stats['filtered_by_pieces'] += 1
                    pieces_filtered = True
                    continue
            except:
                pass
        elif filters.get('pieces_min', 0) > 0 or filters.get('pieces_max', 20) < 20:
            # Si pas de pièces mais qu'un nombre de pièces est spécifié, ne pas filtrer (on ne sait pas)
            # On laisse passer si pas d'info sur les pièces
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
            
            # Mapping des stations proches géographiquement (même ligne ou zones proches)
            # Format: {station_filtre: [stations_proches]}
            nearby_stations = {
                'alexandre dumas': ['rue des boulets', 'philippe auguste', 'avron', 'charonne', 'nation', 'place de la réunion'],
                'philippe auguste': ['alexandre dumas', 'rue des boulets', 'avron', 'charonne', 'nation', 'place de la réunion'],
                'rue des boulets': ['alexandre dumas', 'philippe auguste', 'avron', 'charonne', 'nation', 'place de la réunion'],
                'avron': ['alexandre dumas', 'philippe auguste', 'rue des boulets', 'charonne', 'nation', 'place de la réunion'],
                'charonne': ['alexandre dumas', 'philippe auguste', 'rue des boulets', 'avron', 'nation', 'place de la réunion'],
                'place de la réunion': ['rue des boulets', 'philippe auguste', 'alexandre dumas', 'avron', 'charonne', 'nation'],
                'belleville': ['ménilmontant', 'couronnes', 'père lachaise', 'goncourt', 'saint ambroise', 'pyrénées', 'jourdain'],
                'ménilmontant': ['belleville', 'couronnes', 'père lachaise', 'goncourt', 'saint ambroise', 'pyrénées', 'jourdain'],
                'saint ambroise': ['belleville', 'ménilmontant', 'couronnes', 'père lachaise', 'goncourt', 'pyrénées', 'jourdain'],
                'goncourt': ['belleville', 'ménilmontant', 'couronnes', 'père lachaise', 'saint ambroise', 'pyrénées', 'jourdain'],
                'pyrénées': ['belleville', 'ménilmontant', 'couronnes', 'père lachaise', 'goncourt', 'saint ambroise', 'jourdain'],
                'jourdain': ['belleville', 'ménilmontant', 'couronnes', 'père lachaise', 'goncourt', 'saint ambroise', 'pyrénées'],
            }
            
            # Vérifier si au moins un des quartiers correspond (LOGIQUE SIMPLE comme avant)
            matches = False
            for q_filter in quartier_filters:
                if not q_filter:  # Ignorer les filtres vides
                    continue
                q_filter_lower = q_filter.lower().strip()
                # Enlever "Métro " si présent pour la comparaison
                q_filter_clean = q_filter_lower.replace('métro ', '').replace('metro ', '').strip()
                
                # Normaliser les tirets et espaces pour comparaison flexible
                def normalize_simple(text):
                    """Normalise simplement : enlève tirets et espaces multiples"""
                    if not text:
                        return ''
                    import re
                    # Remplacer tirets par espaces, puis espaces multiples par un seul espace
                    text = text.replace('-', ' ').replace('_', ' ')
                    text = re.sub(r'\s+', ' ', text)
                    return text.lower().strip()
                
                q_filter_normalized = normalize_simple(q_filter_clean)
                
                # Récupérer les stations proches pour ce filtre
                nearby_for_filter = nearby_stations.get(q_filter_normalized, [])
                
                # Vérifier dans la localisation (correspondance partielle simple)
                if localisation:
                    localisation_normalized = normalize_simple(localisation)
                    # Chercher le filtre dans la localisation (ou l'inverse pour flexibilité)
                    if (q_filter_lower in localisation or 
                        q_filter_clean in localisation or
                        q_filter_normalized in localisation_normalized or
                        localisation_normalized in q_filter_normalized):
                        matches = True
                        break
                    # Vérifier aussi les stations proches dans la localisation
                    for nearby in nearby_for_filter:
                        if nearby in localisation_normalized:
                            matches = True
                            break
                    if matches:
                        break
                
                # Vérifier dans le quartier
                if quartier:
                    quartier_normalized = normalize_simple(quartier)
                    if (q_filter_lower in quartier or 
                        q_filter_clean in quartier or
                        q_filter_normalized in quartier_normalized or
                        quartier_normalized in q_filter_normalized):
                        matches = True
                        break
                    # Vérifier aussi les stations proches dans le quartier
                    for nearby in nearby_for_filter:
                        if nearby in quartier_normalized:
                            matches = True
                            break
                    if matches:
                        break
                
                # Vérifier dans les métros (liste de strings) - LOGIQUE SIMPLE + stations proches
                metros = map_info.get('metros', []) or []
                transports = apartment.get('transports', []) or []
                all_metros = metros + transports
                if all_metros:
                    for metro in all_metros:
                        if metro:
                            metro_str = str(metro).lower().strip()
                            metro_normalized = normalize_simple(metro_str)
                            # Correspondance simple : filtre dans métro ou métro dans filtre
                            if (q_filter_lower in metro_str or 
                                q_filter_clean in metro_str or
                                q_filter_normalized in metro_normalized or
                                metro_normalized in q_filter_normalized or
                                metro_str in q_filter_clean):
                                matches = True
                                break
                            # Vérifier aussi les stations proches
                            for nearby in nearby_for_filter:
                                if nearby in metro_normalized or metro_normalized in nearby:
                                    matches = True
                                    break
                            if matches:
                                break
                    if matches:
                        break
            
            if not matches:
                debug_stats['filtered_by_localisation'] += 1
                continue
        
        debug_stats['passed_all_filters'] += 1
        filtered.append(apartment)
    
    # DEBUG: Afficher les statistiques de filtrage
    print(f"📊 Statistiques de filtrage:")
    print(f"   Total: {debug_stats['total']}")
    print(f"   Filtrés par budget: {debug_stats['filtered_by_budget']}")
    print(f"   Filtrés par surface: {debug_stats['filtered_by_surface']}")
    print(f"   Filtrés par pièces: {debug_stats['filtered_by_pieces']}")
    print(f"   Filtrés par localisation: {debug_stats['filtered_by_localisation']}")
    print(f"   Passent tous les filtres: {debug_stats['passed_all_filters']}")
    
    return filtered

