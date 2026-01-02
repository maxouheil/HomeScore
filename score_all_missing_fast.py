#!/usr/bin/env python3
"""
Script ULTRA-OPTIMISÉ pour scorer tous les appartements manquants
- Skip les analyses IA si pas nécessaires
- Scoring basé uniquement sur règles (gratuit, rapide)
- Pas d'appels API coûteux
"""

import json
import os
import time
import sys
from datetime import datetime
from scoring import (
    score_localisation, score_prix, score_ensoleillement,
    score_etage, score_surface,
    load_scoring_config, round_to_nearest_5
)

def load_apartments():
    """Charge tous les appartements"""
    with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_existing_scores():
    """Charge les scores existants"""
    scores_file = 'data/scores/all_apartments_scores.json'
    if os.path.exists(scores_file):
        with open(scores_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_scores(scored_apartments):
    """Sauvegarde tous les scores"""
    scores_file = 'data/scores/all_apartments_scores.json'
    with open(scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, ensure_ascii=False, indent=2)

def score_style_fast(apartment, config):
    """
    Score style RAPIDEMENT sans analyses IA
    Utilise uniquement API data et style_analysis existant
    """
    tier_config = config['axes']['style']['tiers']
    
    # PRIORITÉ 1: Utiliser buy_type et year depuis l'API
    api_data = apartment.get('_api_data', {})
    if api_data:
        buy_type = api_data.get('buy_type')
        features = api_data.get('features', {})
        year = features.get('year') if isinstance(features, dict) else None
        
        if buy_type == 'new':
            return {
                'score': tier_config['tier3']['score'],
                'tier': 'tier3',
                'justification': 'Appartement neuf (buy_type: new)',
                'source': 'api_buy_type'
            }
        
        if buy_type == 'old' and year:
            if 1850 <= year <= 1900:
                return {
                    'score': tier_config['tier1']['score'],
                    'tier': 'tier1',
                    'justification': f'Style haussmannien (construction {year})',
                    'source': 'api_year',
                    'year': year
                }
            elif year < 1850:
                return {
                    'score': tier_config['tier1']['score'],
                    'tier': 'tier1',
                    'justification': f'Style ancien (construction {year})',
                    'source': 'api_year',
                    'year': year
                }
            elif 1900 < year <= 1950:
                return {
                    'score': tier_config['tier2']['score'],
                    'tier': 'tier2',
                    'justification': f'Style ancien (construction {year})',
                    'source': 'api_year',
                    'year': year
                }
            elif year > 1950:
                return {
                    'score': tier_config['tier3']['score'],
                    'tier': 'tier3',
                    'justification': f'Style récent (construction {year})',
                    'source': 'api_year',
                    'year': year
                }
    
    # PRIORITÉ 2: Utiliser style_analysis existant (SANS générer)
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    style_type = style_data.get('type', '').lower()
    
    if style_data and style_type:
        tier1_styles = [s.lower() for s in tier_config['tier1']['styles']]
        if style_type in tier1_styles or 'haussmann' in style_type:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': style_data.get('justification', f"Style ancien: {style_type}"),
                'details': style_data.get('details', {})
            }
        
        if 'atypique' in style_type or 'loft' in style_type:
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': style_data.get('justification', f"Style atypique: {style_type}"),
                'details': style_data.get('details', {})
            }
        
        return {
            'score': tier_config['tier3']['score'],
            'tier': 'tier3',
            'justification': style_data.get('justification', f"Style neuf: {style_type}"),
            'details': style_data.get('details', {})
        }
    
    # FALLBACK: Analyse texte simple (rapide, pas d'IA)
    description = str(apartment.get('description', '')).lower()
    caracteristiques = str(apartment.get('caracteristiques', '')).lower()
    text_combined = f"{description} {caracteristiques}"
    
    # Mots-clés ancien
    ancien_keywords = ['haussmannien', 'haussmann', 'moulures', 'parquet', 'cheminée', 'balcon fer forgé', 'xixe', 'xixème']
    if any(kw in text_combined for kw in ancien_keywords):
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': 'Style ancien détecté dans le texte'
        }
    
    # Mots-clés atypique
    atypique_keywords = ['atypique', 'loft', 'poutres apparentes', 'ancien et moderne']
    if any(kw in text_combined for kw in atypique_keywords):
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': 'Style atypique détecté dans le texte'
        }
    
    # Par défaut: neuf/récent
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': 'Style non spécifié - considéré comme récent'
    }

def score_cuisine_fast(apartment, config):
    """
    Score cuisine RAPIDEMENT sans analyses IA
    Utilise uniquement style_analysis existant ou texte
    """
    tier_config = config['axes']['cuisine']['tiers']
    
    # PRIORITÉ 1: Utiliser style_analysis.cuisine si disponible
    style_analysis = apartment.get('style_analysis', {})
    cuisine_data = style_analysis.get('cuisine', {})
    cuisine_ouverte = cuisine_data.get('ouverte')
    
    if cuisine_ouverte is not None:
        if cuisine_ouverte:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': 'Cuisine ouverte (style_analysis)'
            }
        else:
            return {
                'score': tier_config['tier3']['score'],
                'tier': 'tier3',
                'justification': 'Cuisine fermée (style_analysis)'
            }
    
    # PRIORITÉ 2: Analyser depuis le texte (rapide)
    description = str(apartment.get('description', '')).lower()
    caracteristiques = str(apartment.get('caracteristiques', '')).lower()
    text_combined = f"{description} {caracteristiques}"
    
    # Mots-clés cuisine ouverte
    ouverte_keywords = ['cuisine ouverte', 'cuisine américaine', 'cuisine ouverte sur', 'cuisine intégrée']
    if any(kw in text_combined for kw in ouverte_keywords):
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': 'Cuisine ouverte détectée dans le texte'
        }
    
    # Mots-clés cuisine fermée
    fermee_keywords = ['cuisine séparée', 'cuisine indépendante', 'cuisine fermée']
    if any(kw in text_combined for kw in fermee_keywords):
        return {
            'score': tier_config['tier3']['score'],
            'tier': 'tier3',
            'justification': 'Cuisine fermée détectée dans le texte'
        }
    
    # Par défaut: tier2 (ambigu)
    return {
        'score': tier_config['tier2']['score'],
        'tier': 'tier2',
        'justification': 'Cuisine non spécifiée - note moyenne'
    }

def score_baignoire_fast(apartment, config):
    """
    Score baignoire RAPIDEMENT sans analyses IA
    Utilise uniquement API data ou texte
    """
    tier_config = config['axes']['baignoire']['tiers']
    
    # PRIORITÉ 1: Utiliser _api_data.features.bath
    api_data = apartment.get('_api_data', {})
    features = api_data.get('features', {})
    if isinstance(features, dict):
        bath = features.get('bath')
        if bath == 1:
            return {
                'score': tier_config['tier1']['score'],
                'tier': 'tier1',
                'justification': 'Baignoire présente (données API)'
            }
        elif bath == 0:
            return {
                'score': tier_config['tier3']['score'],
                'tier': 'tier3',
                'justification': 'Pas de baignoire (données API)'
            }
    
    # PRIORITÉ 2: Analyser depuis le texte
    description = str(apartment.get('description', '')).lower()
    caracteristiques = str(apartment.get('caracteristiques', '')).lower()
    text_combined = f"{description} {caracteristiques}"
    
    # Mots-clés baignoire
    if 'baignoire' in text_combined or 'baignoires' in text_combined:
        return {
            'score': tier_config['tier1']['score'],
            'tier': 'tier1',
            'justification': 'Baignoire mentionnée dans le texte'
        }
    
    # Mots-clés douche uniquement
    if 'douche' in text_combined and 'baignoire' not in text_combined:
        return {
            'score': tier_config['tier3']['score'],
            'tier': 'tier3',
            'justification': 'Douche uniquement (pas de baignoire)'
        }
    
    # Par défaut: tier2 (non spécifié)
    return {
        'score': tier_config['tier2']['score'],
        'tier': 'tier2',
        'justification': 'Salle de bain non spécifiée - note moyenne'
    }

def score_apartment_fast(apartment, config):
    """
    Score un appartement RAPIDEMENT sans analyses IA
    Utilise uniquement les données existantes et les règles
    """
    scores_detaille = {}
    
    # Calculer chaque critère directement (pas d'analyses IA)
    try:
        scores_detaille['localisation'] = score_localisation(apartment, config)
    except:
        scores_detaille['localisation'] = {'score': 0, 'tier': 'tier3', 'justification': 'Erreur calcul'}
    
    try:
        scores_detaille['prix'] = score_prix(apartment, config)
    except:
        scores_detaille['prix'] = {'score': 0, 'tier': 'tier3', 'justification': 'Erreur calcul'}
    
    try:
        scores_detaille['style'] = score_style_fast(apartment, config)  # Version rapide
    except:
        scores_detaille['style'] = {'score': 0, 'tier': 'tier3', 'justification': 'Erreur calcul'}
    
    try:
        scores_detaille['ensoleillement'] = score_ensoleillement(apartment, config)
    except:
        scores_detaille['ensoleillement'] = {'score': 0, 'tier': 'tier3', 'justification': 'Erreur calcul'}
    
    try:
        scores_detaille['etage'] = score_etage(apartment, config)
    except:
        scores_detaille['etage'] = {'score': 0, 'tier': 'tier3', 'justification': 'Erreur calcul'}
    
    try:
        scores_detaille['surface'] = score_surface(apartment, config)
    except:
        scores_detaille['surface'] = {'score': 0, 'tier': 'tier3', 'justification': 'Erreur calcul'}
    
    try:
        scores_detaille['cuisine'] = score_cuisine_fast(apartment, config)
    except:
        scores_detaille['cuisine'] = {'score': 0, 'tier': 'tier3', 'justification': 'Erreur calcul'}
    
    try:
        scores_detaille['baignoire'] = score_baignoire_fast(apartment, config)
    except:
        scores_detaille['baignoire'] = {'score': 0, 'tier': 'tier3', 'justification': 'Erreur calcul'}
    
    # Calculer score total (5 critères à 20pts chacun = 100pts total)
    scored_criteria = ['localisation', 'prix', 'style', 'ensoleillement', 'cuisine']
    score_total = sum(scores_detaille.get(key, {}).get('score', 0) for key in scored_criteria)
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
        'bonus': 0,
        'malus': 0,
        'date_scoring': apartment.get('scraped_at', ''),
        'model_used': 'rules_based_fast'
    }

def score_all_missing_fast():
    """Score tous les appartements manquants ULTRA-RAPIDEMENT"""
    print("=" * 80)
    print("🚀 SCORING ULTRA-OPTIMISÉ DES APPARTEMENTS MANQUANTS")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Charger tous les appartements
    print("📂 Chargement des appartements...")
    apartments = load_apartments()
    print(f"✅ {len(apartments)} appartements chargés")
    
    # Charger les scores existants
    print("📂 Chargement des scores existants...")
    existing_scores = load_existing_scores()
    scored_ids = {apt.get('id') for apt in existing_scores if apt.get('id') and apt.get('scores_detaille')}
    print(f"✅ {len(scored_ids)} appartements déjà scorés")
    print()
    
    # Identifier les appartements à scorer
    apartments_to_score = []
    for apt in apartments:
        apt_id = apt.get('id')
        if apt_id and apt_id not in scored_ids:
            apartments_to_score.append(apt)
    
    total_to_score = len(apartments_to_score)
    print(f"📊 Appartements à scorer: {total_to_score}")
    print()
    
    if total_to_score == 0:
        print("✅ Tous les appartements sont déjà scorés !")
        return
    
    # Créer un dict des scores existants pour fusion
    scores_dict = {apt.get('id'): apt for apt in existing_scores}
    
    # Scorer avec feedback live
    scored_count = 0
    error_count = 0
    start_time = time.time()
    batch_size = 50  # Sauvegarder tous les 50 appartements (plus efficace)
    last_save_time = time.time()
    
    print("🔄 DÉMARRAGE DU SCORING ULTRA-RAPIDE...")
    print("=" * 80)
    print()
    
    for i, apartment in enumerate(apartments_to_score, 1):
        apt_id = apartment.get('id', 'N/A')
        
        try:
            # Scorer RAPIDEMENT (pas d'analyses IA)
            score_result = score_apartment_fast(apartment, config)
            
            if score_result:
                # Fusionner avec données originales
                score_result.update(apartment)
                scores_dict[apt_id] = score_result
                scored_count += 1
            else:
                scores_dict[apt_id] = apartment
                error_count += 1
        
        except Exception as e:
            scores_dict[apt_id] = apartment
            error_count += 1
        
        # Afficher la progression tous les 10 appartements
        if i % 10 == 0 or i == total_to_score:
            elapsed = time.time() - start_time
            percentage = (i / total_to_score * 100) if total_to_score > 0 else 0
            
            if i > 1:
                avg_time = elapsed / i
                remaining = (total_to_score - i) * avg_time
                eta_min = int(remaining // 60)
                eta_sec = int(remaining % 60)
                eta_str = f"ETA: {eta_min}m{eta_sec}s"
                speed = f"{avg_time*1000:.0f}ms/appt"
            else:
                eta_str = "ETA: calcul..."
                speed = "calcul..."
            
            sys.stdout.write(f"\r[{i}/{total_to_score}] {percentage:5.1f}% | ✅ {scored_count} | ❌ {error_count} | {speed} | {eta_str}")
            sys.stdout.flush()
        
        # Sauvegarder tous les batch_size appartements ou toutes les 30 secondes
        current_time = time.time()
        if (i % batch_size == 0) or (current_time - last_save_time > 30):
            scored_list = list(scores_dict.values())
            save_scores(scored_list)
            last_save_time = current_time
    
    # Sauvegarde finale
    scored_list = list(scores_dict.values())
    save_scores(scored_list)
    
    # Résumé final
    total_time = time.time() - start_time
    print()
    print()
    print("=" * 80)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"✅ Appartements scorés avec succès: {scored_count}")
    print(f"⚠️  Appartements avec erreurs: {error_count}")
    print(f"📦 Total traité: {scored_count + error_count}")
    print(f"⏱️  Temps total: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    if scored_count > 0:
        print(f"⚡ Vitesse moyenne: {total_time/scored_count:.3f}s par appartement ({scored_count/total_time:.1f} appt/s)")
    print()
    print(f"💾 Fichier final: data/scores/all_apartments_scores.json")
    print(f"📊 Total d'appartements dans le fichier: {len(scores_dict)}")
    print()
    print("🎉 Scoring terminé avec succès !")
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    score_all_missing_fast()

