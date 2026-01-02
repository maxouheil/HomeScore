#!/usr/bin/env python3
"""
Script pour générer un récapitulatif des analyses des 43 nouveaux appartements
selon 9 critères (oui/non)
"""

import json
import os
from typing import Dict, List
from datetime import datetime


def load_apartment_data(apartment_id: str) -> Dict:
    """Charge les données d'un appartement depuis data/appartements/"""
    filepath = f"data/appartements/{apartment_id}.json"
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement {apartment_id}: {e}")
        return None


def load_score_data(apartment_id: str) -> Dict:
    """Charge les données de score d'un appartement"""
    filepath = f"data/scores/apartment_{apartment_id}_score.json"
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None


def get_new_apartments() -> List[str]:
    """Identifie les nouveaux appartements qui ont été récemment scorés"""
    apartments_dir = 'data/appartements'
    scores_dir = 'data/scores'
    
    if not os.path.exists(apartments_dir):
        return []
    
    # Trouver tous les appartements scrapés
    apartment_files = [f for f in os.listdir(apartments_dir) 
                      if f.endswith('.json') and not f.startswith('test_')]
    
    # Trouver ceux qui ont un score récent (nouveaux)
    new_apartments = []
    for apartment_file in apartment_files:
        apartment_id = apartment_file.replace('.json', '')
        
        # Vérifier si a un score
        score_file = f"{scores_dir}/apartment_{apartment_id}_score.json"
        if os.path.exists(score_file):
            # Vérifier la date de création du fichier de score
            score_mtime = os.path.getmtime(score_file)
            # Considérer comme nouveau si créé dans les 7 derniers jours
            import time
            if time.time() - score_mtime < 7 * 24 * 3600:
                new_apartments.append(apartment_id)
    
    # Si moins de 43, prendre les 43 plus récents
    if len(new_apartments) < 43:
        # Trier tous les appartements par date de score
        all_scored = []
        for apartment_file in apartment_files:
            apartment_id = apartment_file.replace('.json', '')
            score_file = f"{scores_dir}/apartment_{apartment_id}_score.json"
            if os.path.exists(score_file):
                score_mtime = os.path.getmtime(score_file)
                all_scored.append((apartment_id, score_mtime))
        
        # Trier par date décroissante et prendre les 43 plus récents
        all_scored.sort(key=lambda x: x[1], reverse=True)
        new_apartments = [apt_id for apt_id, _ in all_scored[:43]]
    
    return new_apartments[:43]  # Limiter à 43


def check_criterion_data_exists(apartment: Dict, criterion: str) -> str:
    """
    Vérifie si les données d'analyse existent pour un critère
    Retourne 'Oui' si les données existent, 'Non' sinon
    """
    scores_detaille = apartment.get('scores_detaille', {})
    
    if criterion == 'localisation':
        loc_score = scores_detaille.get('localisation', {})
        # Vérifier si le score existe (même si tier3)
        if loc_score and (loc_score.get('tier') or loc_score.get('score') is not None):
            return 'Oui'
        return 'Non'
    
    elif criterion == 'prix':
        prix_score = scores_detaille.get('prix', {})
        # Vérifier si le score existe
        if prix_score and (prix_score.get('tier') or prix_score.get('score') is not None):
            return 'Oui'
        return 'Non'
    
    elif criterion == 'haussmanien':
        # Pour être considéré comme analysé selon le frontend (formatStyleCriterion),
        # il faut qu'il y ait une description non-null, ce qui nécessite :
        # 1. Soit une année de construction disponible (donnée brute OK)
        # 2. Soit des indices valides dans formatted_data.style (pas "Style expo cuisine et baignoire")
        # 3. Soit style_analysis.style avec type valide ET (details ou justification avec keywords)
        
        # Vérifier l'année de construction (donnée brute - OK pour analyse)
        caracteristiques = apartment.get('caracteristiques', {})
        annee_construction = None
        if isinstance(caracteristiques, dict):
            annee_construction = caracteristiques.get('annee_construction')
        if not annee_construction:
            annee_construction = apartment.get('annee_construction')
        if not annee_construction:
            # Vérifier dans _api_data.features.year
            api_data = apartment.get('_api_data', {})
            if api_data:
                features = api_data.get('features', {})
                if features:
                    year_value = features.get('year')
                    if year_value and year_value != 'null' and year_value is not None:
                        annee_construction = str(year_value)
        
        if annee_construction:
            return 'Oui'
        
        # Vérifier dans formatted_data (indices d'analyse) - PRIORITÉ
        formatted_data = apartment.get('formatted_data', {})
        if formatted_data:
            style_data = formatted_data.get('style', {})
            if style_data:
                indices = style_data.get('indices', '')
                # Si on a des indices valides (pas juste "Style expo cuisine et baignoire")
                if (indices and indices != 'Style expo cuisine et baignoire' and 
                    indices.lower() not in ['non spécifié', 'non specifie', ''] and
                    len(indices.strip()) > 5):
                    return 'Oui'
        
        # Vérifier dans style_analysis (analyse IA des photos)
        style_analysis = apartment.get('style_analysis', {})
        if style_analysis:
            style_data = style_analysis.get('style', {})
            style_type = style_data.get('type', '')
            details = style_data.get('details', '')
            justification = style_data.get('justification', '')
            
            # Si style_type existe et n'est pas 'autre' ou 'inconnu'
            if style_type and style_type.lower() not in ['autre', 'inconnu', '']:
                # Vérifier si on a des détails ou justification avec keywords (moulures, parquet, etc.)
                text_to_search = f"{details} {justification}".lower()
                keywords = ['moulures', 'moldings', 'cheminée', 'fireplace', 'parquet', 'hauteur sous plafond']
                has_keywords = any(keyword in text_to_search for keyword in keywords)
                
                # Si on a des keywords, c'est analysé
                if has_keywords:
                    return 'Oui'
                # Sinon, même avec un type valide, sans keywords c'est considéré comme non analysé
                # (car formatStyleCriterion retournera description: null)
        
        # Si on arrive ici, pas d'année, pas d'indices valides, pas de keywords
        return 'Non'
    
    elif criterion == 'luminosite':
        ensoleillement_score = scores_detaille.get('ensoleillement', {})
        if ensoleillement_score and (ensoleillement_score.get('tier') or ensoleillement_score.get('score') is not None):
            return 'Oui'
        # Vérifier dans formatted_data.exposition
        formatted_data = apartment.get('formatted_data', {})
        if formatted_data and formatted_data.get('exposition'):
            return 'Oui'
        # Vérifier dans exposition
        exposition = apartment.get('exposition', {})
        if exposition:
            return 'Oui'
        return 'Non'
    
    elif criterion == 'cuisine_ouverte':
        cuisine_score = scores_detaille.get('cuisine', {})
        if cuisine_score and (cuisine_score.get('tier') or cuisine_score.get('score') is not None):
            return 'Oui'
        # Vérifier dans les détails avec photo_validation
        cuisine_details = cuisine_score.get('details', {})
        if cuisine_details:
            photo_validation = cuisine_details.get('photo_validation', {})
            if photo_validation:
                return 'Oui'
        # Vérifier dans style_analysis
        style_analysis = apartment.get('style_analysis', {})
        if style_analysis:
            cuisine_data = style_analysis.get('cuisine', {})
            if cuisine_data and cuisine_data.get('ouverte') is not None:
                return 'Oui'
        return 'Non'
    
    elif criterion == 'ascenseur':
        # Chercher dans caracteristiques (donnée brute)
        caracteristiques = apartment.get('caracteristiques', {})
        if isinstance(caracteristiques, dict):
            ascenseur = caracteristiques.get('ascenseur')
            if ascenseur is not None:
                return 'Oui'
        # Chercher dans description (mention explicite)
        description = apartment.get('description', '')
        if description and 'ascenseur' in description.lower():
            return 'Oui'
        return 'Non'
    
    elif criterion == 'large_piece_vie':
        large_piece_vie_score = scores_detaille.get('large_piece_vie', {})
        if large_piece_vie_score:
            # Vérifier si les détails existent (même si tier3)
            if large_piece_vie_score.get('tier') or large_piece_vie_score.get('details'):
                return 'Oui'
        # Vérifier dans style_analysis (analyse des photos)
        style_analysis = apartment.get('style_analysis', {})
        if style_analysis:
            salon_data = style_analysis.get('salon_size', {})
            if salon_data and salon_data.get('estimate') is not None:
                return 'Oui'
        return 'Non'
    
    elif criterion == 'hauteur_plafond':
        # Chercher dans les scores détaillés
        hauteur_score = scores_detaille.get('hauteur_plafond', {})
        if hauteur_score and (hauteur_score.get('tier') or hauteur_score.get('score') is not None):
            return 'Oui'
        # Chercher dans formatted_data
        formatted_data = apartment.get('formatted_data', {})
        if formatted_data:
            hauteur_data = formatted_data.get('hauteur_plafond', {})
            if hauteur_data and hauteur_data.get('main_value'):
                return 'Oui'
        # Vérifier dans style_analysis (analyse des photos)
        style_analysis = apartment.get('style_analysis', {})
        if style_analysis:
            # Chercher dans les résultats d'analyse de photos
            photos_analysis = style_analysis.get('photos_analysis', [])
            for photo_analysis in photos_analysis:
                if isinstance(photo_analysis, dict):
                    hauteur = photo_analysis.get('hauteur_plafond')
                    if hauteur is not None:
                        return 'Oui'
        return 'Non'
    
    elif criterion == 'calme':
        calme_score = scores_detaille.get('calme', {})
        # Vérifier si le score existe (même si tier3)
        if calme_score and (calme_score.get('tier') or calme_score.get('score') is not None):
            return 'Oui'
        # Vérifier dans formatted_data
        formatted_data = apartment.get('formatted_data', {})
        if formatted_data and formatted_data.get('calme'):
            return 'Oui'
        return 'Non'
    
    return 'Non'


def generate_recap():
    """Génère le récapitulatif des 43 nouveaux appartements"""
    print("=" * 80)
    print("📊 RÉCAPITULATIF DES DONNÉES D'ANALYSE - 43 NOUVEAUX APPARTEMENTS")
    print("=" * 80)
    print()
    
    # 1. Identifier les 43 nouveaux appartements
    print("🔍 Identification des 43 nouveaux appartements...")
    new_apartment_ids = get_new_apartments()
    
    if len(new_apartment_ids) == 0:
        print("❌ Aucun nouvel appartement trouvé")
        return
    
    print(f"✅ {len(new_apartment_ids)} nouveaux appartements identifiés")
    print()
    
    # 2. Définir les 9 critères
    criteria = [
        'localisation',
        'prix',
        'haussmanien',
        'luminosite',
        'cuisine_ouverte',
        'ascenseur',
        'large_piece_vie',
        'hauteur_plafond',
        'calme'
    ]
    
    criteria_names = {
        'localisation': 'Localisation',
        'prix': 'Prix',
        'haussmanien': 'Haussmanien',
        'luminosite': 'Luminosité',
        'cuisine_ouverte': 'Cuisine ouverte',
        'ascenseur': 'Ascenseur',
        'large_piece_vie': 'Large pièce de vie',
        'hauteur_plafond': 'Hauteur plafond',
        'calme': 'Calme'
    }
    
    # 3. Analyser chaque appartement
    print("📋 Vérification de la présence des données d'analyse pour chaque critère...")
    results = []
    
    for apartment_id in new_apartment_ids:
        apartment_data = load_apartment_data(apartment_id)
        if not apartment_data:
            continue
        
        # Charger aussi les scores si disponibles
        score_data = load_score_data(apartment_id)
        if score_data:
            apartment_data.update(score_data)
        
        apartment_result = {
            'id': apartment_id,
            'criteria': {}
        }
        
        for criterion in criteria:
            result = check_criterion_data_exists(apartment_data, criterion)
            apartment_result['criteria'][criterion] = result
        
        results.append(apartment_result)
    
    # 4. Générer le récapitulatif
    print()
    print("=" * 80)
    print("📊 RÉCAPITULATIF PAR CRITÈRE - PRÉSENCE DES DONNÉES")
    print("=" * 80)
    print()
    
    # Tableau récapitulatif
    recap_table = []
    
    for criterion in criteria:
        oui_count = sum(1 for r in results if r['criteria'].get(criterion) == 'Oui')
        non_count = len(results) - oui_count
        oui_pct = (oui_count / len(results) * 100) if results else 0
        
        recap_table.append({
            'criterion': criteria_names[criterion],
            'oui': oui_count,
            'non': non_count,
            'oui_pct': oui_pct
        })
    
    # Afficher le tableau
    print(f"{'Critère':<30} {'Données existent':<20} {'Données manquantes':<20} {'% Avec données':<20}")
    print("-" * 90)
    for row in recap_table:
        print(f"{row['criterion']:<30} {row['oui']:<20} {row['non']:<20} {row['oui_pct']:.1f}%")
    
    print()
    print("=" * 80)
    print("📋 DÉTAIL PAR APPARTEMENT - PRÉSENCE DES DONNÉES")
    print("=" * 80)
    print()
    
    # Afficher le détail par appartement
    print(f"{'ID':<15} ", end='')
    for criterion in criteria:
        print(f"{criteria_names[criterion][:8]:<10}", end='')
    print()
    print("-" * 100)
    
    for result in results:
        print(f"{result['id']:<15} ", end='')
        for criterion in criteria:
            value = result['criteria'].get(criterion, 'Non')
            symbol = '✓' if value == 'Oui' else '✗'
            print(f"{symbol:<10}", end='')
        print()
    
    # Sauvegarder dans un fichier JSON
    output_file = 'data/recap_43_apartments.json'
    os.makedirs('data', exist_ok=True)
    
    recap_data = {
        'date': datetime.now().isoformat(),
        'total_apartments': len(results),
        'criteria_summary': recap_table,
        'apartments_detail': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recap_data, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"✅ Récapitulatif sauvegardé dans {output_file}")
    print()
    
    # Résumé final
    print("=" * 80)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"Total appartements analysés: {len(results)}")
    print()
    print("Critères avec le plus de données disponibles:")
    sorted_recap = sorted(recap_table, key=lambda x: x['oui_pct'], reverse=True)
    for i, row in enumerate(sorted_recap[:3], 1):
        print(f"{i}. {row['criterion']}: {row['oui']}/{len(results)} ({row['oui_pct']:.1f}%)")
    
    print()
    print("Critères avec le moins de données disponibles:")
    for i, row in enumerate(sorted_recap[-3:], 1):
        print(f"{i}. {row['criterion']}: {row['oui']}/{len(results)} ({row['oui_pct']:.1f}%)")


if __name__ == "__main__":
    generate_recap()

