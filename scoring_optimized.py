"""
Scoring optimisé - Analyse photos UNE SEULE FOIS et réutilise pour style/cuisine/baignoire
"""

import json
import os
import re
from criteria.localisation import get_metro_name, get_quartier_name, get_all_metro_stations
from scoring import (
    round_to_nearest_5, load_scoring_config, calculate_prix_m2,
    score_localisation, score_prix, score_ensoleillement, score_etage, score_surface
)

def analyze_photos_once(apartment):
    """
    Analyse toutes les photos UNE SEULE FOIS et extrait TOUTES les infos nécessaires
    pour style, cuisine, baignoire, luminosité en UNE SEULE passe
    
    Returns:
        Dict avec toutes les analyses : {
            'style_analysis': {...},
            'cuisine_result': {...},
            'baignoire_result': {...},
            'luminosite': {...}
        }
    """
    print("   📸 Analyse UNIFIÉE des photos (style + cuisine + luminosité + baignoire ensemble)...")
    
    result = {
        'style_analysis': None,
        'cuisine_result': None,
        'baignoire_result': None,
        'luminosite': None
    }
    
    # Extraire les URLs des photos
    photos = apartment.get('photos', [])
    photos_urls = []
    if photos:
        for photo in photos:
            if isinstance(photo, dict):
                photos_urls.append(photo.get('url', ''))
            elif isinstance(photo, str):
                photos_urls.append(photo)
    
    apartment_id = apartment.get('id', 'unknown')
    description = apartment.get('description', '')
    caracteristiques = apartment.get('caracteristiques', '')
    
    # ANALYSE UNIFIÉE : Tout en une seule requête GPT-4o-mini Vision
    try:
        from analyze_apartment_unified import UnifiedApartmentAnalyzer
        unified_analyzer = UnifiedApartmentAnalyzer()
        
        # Analyser l'appartement UNE SEULE FOIS pour tout extraire (style, cuisine, baignoire, luminosité)
        unified_result = unified_analyzer.analyze_apartment_unified(apartment, max_photos=5)
        
        if unified_result:
            # 1. Style
            style_type = unified_result.get('style', {}).get('type', 'autre')
            style_confidence = unified_result.get('style', {}).get('confidence', 0)
            style_justification = unified_result.get('style', {}).get('justification', '')
            
            result['style_analysis'] = {
                'style': {
                    'type': style_type,
                    'confidence': style_confidence,
                    'score': unified_result.get('style', {}).get('score', 0),
                    'justification': style_justification or f"Style {style_type} détecté avec confiance {style_confidence:.0%}",
                    'details': unified_result.get('style', {}).get('details', {})
                },
                'photos_analyzed': unified_result.get('photos_analyzed', 0),
                'method': unified_result.get('method', 'unified_analysis'),
                'model': unified_result.get('model', 'gpt-4o-mini')
            }
            
            # 2. Cuisine
            cuisine_ouverte = unified_result.get('cuisine', {}).get('ouverte', False)
            cuisine_confidence = unified_result.get('cuisine', {}).get('confidence', 0)
            cuisine_justification = unified_result.get('cuisine', {}).get('justification', '')
            
            result['cuisine_result'] = {
                'ouverte': cuisine_ouverte,
                'confidence': cuisine_confidence,
                'cuisine_detected': True,  # Toujours détecté si analyse réussie
                'justification': cuisine_justification or f"Cuisine {'ouverte' if cuisine_ouverte else 'fermée'} détectée (confiance: {cuisine_confidence:.0%})",
                'photo_validation': {
                    'photo_result': {
                        'ouverte': cuisine_ouverte
                    }
                },
                'validation_status': 'unified_analysis'
            }
            
            # 3. Luminosité
            luminosite_type = unified_result.get('luminosite', {}).get('type', 'moyen')
            luminosite_score = unified_result.get('luminosite', {}).get('score', 0)
            
            result['luminosite'] = {
                'type': luminosite_type,
                'score': luminosite_score,
                'confidence': unified_result.get('luminosite', {}).get('confidence', 0),
                'justification': unified_result.get('luminosite', {}).get('justification', '')
            }
            
            # 4. Baignoire
            baignoire_presente = unified_result.get('baignoire', {}).get('presente', False)
            baignoire_confidence = unified_result.get('baignoire', {}).get('confidence', 0)
            baignoire_justification = unified_result.get('baignoire', {}).get('justification', '')
            
            # Vérifier si douche est mentionnée dans la réponse (on peut l'extraire du JSON si présent)
            # Pour l'instant, on assume que si pas de baignoire, c'est une douche
            has_douche = not baignoire_presente
            
            result['baignoire_result'] = {
                'has_baignoire': baignoire_presente,
                'confidence': baignoire_confidence,
                'baignoire_detected': True,  # Toujours détecté si analyse réussie
                'justification': baignoire_justification or f"Baignoire {'présente' if baignoire_presente else 'absente'} (confiance: {baignoire_confidence:.0%})",
                'details': {
                    'photo_validation': {
                        'photo_result': {
                            'has_baignoire': baignoire_presente,
                            'has_douche': has_douche
                        }
                    },
                    'validation_status': 'unified_analysis',
                    'confidence': baignoire_confidence
                }
            }
            
            print(f"      ✅ Style: {style_type} ({style_confidence:.0%})")
            print(f"      ✅ Cuisine: {'Ouverte' if cuisine_ouverte else 'Fermée'} ({cuisine_confidence:.0%})")
            print(f"      ✅ Luminosité: {luminosite_type}")
            print(f"      ✅ Baignoire: {'Oui' if baignoire_presente else 'Non'} ({baignoire_confidence:.0%})")
            print(f"      📊 {unified_result.get('photos_analyzed', 0)} photos analysées en UNE SEULE requête GPT-4o-mini")
            
    except Exception as e:
        print(f"      ⚠️ Erreur analyse unifiée: {e}")
        import traceback
        traceback.print_exc()
        # Fallback sur méthode ancienne si erreur
        result = _fallback_analysis(apartment, photos_urls, description, caracteristiques)
    
    return result


def _fallback_analysis(apartment, photos_urls, description, caracteristiques):
    """Fallback si l'analyse unifiée échoue"""
    result = {
        'style_analysis': None,
        'cuisine_result': None,
        'baignoire_result': None,
        'luminosite': None
    }
    
    try:
        from analyze_apartment_style import ApartmentStyleAnalyzer
        style_analyzer = ApartmentStyleAnalyzer()
        style_analysis = style_analyzer.analyze_apartment_photos_from_data(apartment)
        
        if style_analysis:
            result['style_analysis'] = style_analysis
            result['cuisine_result'] = {
                'ouverte': style_analysis.get('cuisine', {}).get('ouverte', False),
                'confidence': style_analysis.get('cuisine', {}).get('confidence', 0),
                'justification': style_analysis.get('cuisine', {}).get('justification', ''),
                'method': 'fallback_style_analysis'
            }
            result['luminosite'] = style_analysis.get('luminosite', {})
    except:
        pass
    
    return result


def score_style_optimized(apartment, config, photo_analysis_cache):
    """Score style en utilisant le cache d'analyse photo"""
    tier_config = config['axes']['style']['tiers']
    
    # Utiliser le cache d'analyse photo
    style_analysis = photo_analysis_cache.get('style_analysis')
    
    if style_analysis:
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
            # Inclure "moderne", "contemporain", "récent", "70s", "60s", "autre" comme Neuf
            # Si le style n'est ni haussmannien ni atypique, c'est forcément Neuf
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
    atypique_keywords = ['atypique', 'loft', 'unique', 'original', 'décalé', 'insolite']
    if any(keyword in text_combined for keyword in atypique_keywords):
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': "Style atypique détecté dans le texte"
        }
    
    # Mots-clés Haussmannien
    haussmann_keywords = ['haussmann', 'moulur', 'parquet', 'cheminée', 'ancien immeuble']
    if any(keyword in text_combined for keyword in haussmann_keywords):
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': "Style haussmannien détecté dans le texte"
        }
    
    # Par défaut: Neuf
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': "Style moderne/neuf"
    }


def score_cuisine_optimized(apartment, config, photo_analysis_cache):
    """Score cuisine en utilisant le cache d'analyse photo"""
    tier_config = config['axes']['cuisine']['tiers']
    
    # Utiliser le cache d'analyse photo
    cuisine_result = photo_analysis_cache.get('cuisine_result')
    
    if cuisine_result:
        cuisine_ouverte = cuisine_result.get('ouverte', False)
        cuisine_detected = cuisine_result.get('cuisine_detected', True)  # Par défaut True pour compatibilité
        
        # Si aucune image de cuisine n'a été trouvée → tier2 (5 pts)
        # Score neutre car on ne peut pas savoir si elle est ouverte ou fermée
        if not cuisine_detected:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': "Cuisine non trouvée dans les photos",
                'details': {
                    'confidence': 0,
                    'photo_validation': cuisine_result.get('photo_validation'),
                    'validation_status': cuisine_result.get('validation_status')
                }
            }
        
        # tier1: ouverte uniquement (10pts)
        if cuisine_ouverte:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': cuisine_result.get('justification', "Cuisine ouverte"),
                'details': {
                    'confidence': cuisine_result.get('confidence', 0),
                    'photo_validation': cuisine_result.get('photo_validation'),
                    'validation_status': cuisine_result.get('validation_status')
                }
            }
        
        # tier3: fermée ou ambigu (0pts)
        return {
            'score': tier_config['tier3']['score'],
            'tier': 'tier3',
            'justification': cuisine_result.get('justification', "Cuisine fermée"),
            'details': {
                'confidence': cuisine_result.get('confidence', 0),
                'photo_validation': cuisine_result.get('photo_validation'),
                'validation_status': cuisine_result.get('validation_status')
            }
        }
    
    # Fallback sur méthode ancienne - Si pas de résultat photo, considérer comme non trouvée
    style_analysis = apartment.get('style_analysis', {})
    cuisine_data = style_analysis.get('cuisine') if style_analysis else None
    cuisine_ouverte = cuisine_data.get('ouverte', False) if cuisine_data else False
    
    if cuisine_ouverte:
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': "Cuisine ouverte"
        }
    
    # Si aucune image trouvée → tier2 (5 pts)
    # Score neutre car on ne peut pas savoir si elle est ouverte ou fermée
    return {
        'score': tier_config['tier2']['score'],
        'tier': 'tier2',
        'justification': "Cuisine non trouvée dans les photos"
    }


def score_baignoire_optimized(apartment, config, photo_analysis_cache):
    """Score baignoire en utilisant le cache d'analyse photo"""
    tier_config = config['axes']['baignoire']['tiers']
    
    # Utiliser le cache d'analyse photo
    baignoire_result = photo_analysis_cache.get('baignoire_result')
    
    if baignoire_result:
        # extract_baignoire_complete retourne 'has_baignoire'
        has_baignoire = baignoire_result.get('has_baignoire', False)
        baignoire_detected = baignoire_result.get('baignoire_detected', True)  # Par défaut True pour compatibilité
        
        # Récupérer les détails qui doivent contenir photo_validation
        details = baignoire_result.get('details', {})
        
        # Si aucune image de SDB n'a été trouvée → tier2 (5 pts) selon config
        # La config indique que tier2 = "Cuisine/SDB non trouvée" (score neutre)
        if not baignoire_detected:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': "Salle de bain non trouvée dans les photos",
                'details': details
            }
        
        if has_baignoire:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': baignoire_result.get('justification', "Baignoire présente"),
                'details': details
            }
        else:
            return {
                'score': tier_config['tier3']['score'],
                'tier': 'tier3',
                'justification': baignoire_result.get('justification', "Pas de baignoire"),
                'details': details
            }
    
    # Fallback: méthode texte seule
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    text = f"{description} {caracteristiques}"
    
    if 'baignoire' in text:
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': "Baignoire mentionnée"
        }
    
    # Si aucune image trouvée → tier2 (5 pts) selon config
    # La config indique que tier2 = "Cuisine/SDB non trouvée" (score neutre)
    return {
        'score': tier_config['tier2']['score'],
        'tier': 'tier2',
        'justification': "Salle de bain non trouvée dans les photos"
    }


def score_apartment_optimized(apartment, config):
    """
    Score un appartement avec analyse photo UNE SEULE FOIS
    
    Args:
        apartment: Dict avec données scrapées + analyses IA
        config: Dict avec scoring_config.json
        
    Returns:
        Dict avec scores détaillés + score total
    """
    print(f"   🎯 Scoring optimisé pour {apartment.get('id')}...")
    
    # 1. Analyser toutes les photos UNE SEULE FOIS
    photo_analysis_cache = analyze_photos_once(apartment)
    
    # 2. Calculer chaque critère en utilisant le cache
    scores_detaille = {}
    
    scores_detaille['localisation'] = score_localisation(apartment, config)
    scores_detaille['prix'] = score_prix(apartment, config)
    scores_detaille['style'] = score_style_optimized(apartment, config, photo_analysis_cache)
    scores_detaille['ensoleillement'] = score_ensoleillement(apartment, config)
    scores_detaille['etage'] = score_etage(apartment, config)
    scores_detaille['surface'] = score_surface(apartment, config)
    scores_detaille['cuisine'] = score_cuisine_optimized(apartment, config, photo_analysis_cache)
    scores_detaille['baignoire'] = score_baignoire_optimized(apartment, config, photo_analysis_cache)
    
    # 3. Calculer score total
    scored_criteria = ['localisation', 'prix', 'style', 'ensoleillement', 'cuisine', 'baignoire']
    score_total = sum(scores_detaille.get(key, {}).get('score', 0) for key in scored_criteria)
    
    # Arrondir au multiple de 5 le plus proche
    score_total = round_to_nearest_5(score_total)
    
    # Déterminer tier global
    if score_total >= 80:
        tier = 'tier1'
    elif score_total >= 60:
        tier = 'tier2'
    else:
        tier = 'tier3'
    
    # Ajouter style_analysis au résultat pour être réutilisé
    result = {
        'id': apartment.get('id'),
        'score_total': score_total,
        'score_global': score_total,  # Alias pour compatibilité
        'tier': tier,
        'scores_detaille': scores_detaille,
        'bonus': 0,
        'malus': 0,
        'date_scoring': apartment.get('scraped_at', ''),
        'model_used': 'rules_based_optimized'
    }
    
    # Ajouter style_analysis si disponible
    if photo_analysis_cache.get('style_analysis'):
        result['style_analysis'] = photo_analysis_cache['style_analysis']
    
    return result

