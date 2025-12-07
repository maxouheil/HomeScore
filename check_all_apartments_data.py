#!/usr/bin/env python3
"""
Script pour vérifier toutes les données des appartements
Génère un récapitulatif détaillé des données présentes et manquantes
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Set
from datetime import datetime


def load_all_apartments() -> Dict[str, Dict[str, Any]]:
    """
    Charge tous les appartements depuis toutes les sources disponibles
    Retourne un dict {id: apartment_data}
    """
    apartments = {}
    data_dir = Path('data')
    
    # 1. Charger depuis scraped_apartments.json (fichier principal)
    main_file = data_dir / 'scraped_apartments.json'
    if main_file.exists():
        print(f"📂 Chargement depuis {main_file.name}...")
        with open(main_file, 'r', encoding='utf-8') as f:
            apts = json.load(f)
            for apt in apts:
                apt_id = apt.get('id')
                if apt_id:
                    apartments[apt_id] = apt
            print(f"   ✅ {len(apts)} appartements chargés")
    
    # 2. Charger depuis scraped_apartments_api_*.json (version API)
    api_files = sorted(data_dir.glob('scraped_apartments_api_*.json'), 
                       key=lambda p: p.stat().st_mtime, reverse=True)
    if api_files:
        print(f"📂 Chargement depuis {api_files[0].name}...")
        with open(api_files[0], 'r', encoding='utf-8') as f:
            apts = json.load(f)
            for apt in apts:
                apt_id = apt.get('id')
                if apt_id:
                    # Merger avec données existantes si nécessaire
                    if apt_id not in apartments:
                        apartments[apt_id] = apt
                    else:
                        # Merger les données (priorité aux données API plus récentes)
                        apartments[apt_id].update(apt)
            print(f"   ✅ {len(apts)} appartements chargés")
    
    # 3. Charger depuis data/appartements/ (fichiers individuels)
    apartments_dir = data_dir / 'appartements'
    if apartments_dir.exists():
        apt_files = list(apartments_dir.glob('*.json'))
        if apt_files:
            print(f"📂 Chargement depuis data/appartements/ ({len(apt_files)} fichiers)...")
            loaded = 0
            for apt_file in apt_files:
                try:
                    with open(apt_file, 'r', encoding='utf-8') as f:
                        apt = json.load(f)
                        apt_id = apt.get('id')
                        if apt_id:
                            if apt_id not in apartments:
                                apartments[apt_id] = apt
                                loaded += 1
                except Exception as e:
                    print(f"   ⚠️  Erreur lors du chargement de {apt_file.name}: {e}")
            print(f"   ✅ {loaded} nouveaux appartements chargés")
    
    # 4. Charger depuis all_apartments_scores.json (avec scores)
    scores_file = data_dir / 'scores' / 'all_apartments_scores.json'
    if scores_file.exists():
        print(f"📂 Chargement depuis {scores_file.name}...")
        with open(scores_file, 'r', encoding='utf-8') as f:
            apts = json.load(f)
            for apt in apts:
                apt_id = apt.get('id')
                if apt_id:
                    if apt_id not in apartments:
                        apartments[apt_id] = apt
                    else:
                        # Merger les scores si présents (sans écraser les photos)
                        if 'score' in apt:
                            apartments[apt_id]['score'] = apt['score']
                        # Préserver les photos existantes si elles ont downloaded=True
                        existing_photos = apartments[apt_id].get('photos', [])
                        new_photos = apt.get('photos', [])
                        if existing_photos and new_photos:
                            # Si les photos existantes ont downloaded=True, les garder
                            if any(p.get('downloaded') == True for p in existing_photos):
                                # Garder les photos existantes
                                pass
                            else:
                                # Sinon, utiliser les nouvelles photos
                                apartments[apt_id]['photos'] = new_photos
            print(f"   ✅ {len(apts)} appartements chargés")
    
    print(f"\n📊 Total: {len(apartments)} appartements uniques\n")
    return apartments


def check_field_presence(apartment: Dict[str, Any], field_path: str) -> bool:
    """
    Vérifie si un champ existe et n'est pas None/vide
    field_path peut être simple ('id') ou nested ('map_info.metros')
    """
    parts = field_path.split('.')
    value = apartment
    
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list):
            # Pour les listes, vérifier si elles ne sont pas vides
            return len(value) > 0
        else:
            return False
        
        if value is None:
            return False
    
    # Vérifier si la valeur n'est pas vide
    if isinstance(value, (str, list, dict)):
        return len(value) > 0 if value else False
    return value is not None


def check_photos_downloaded(apartment: Dict[str, Any]) -> tuple:
    """
    Vérifie les photos téléchargées
    Retourne (has_photos, has_downloaded_photos, total_photos, downloaded_count, files_exist_count)
    """
    photos = apartment.get('photos', [])
    if not photos:
        return (False, False, 0, 0, 0)
    
    total = len(photos)
    # Vérifier downloaded (peut être True, "true", 1, etc.)
    downloaded = sum(1 for p in photos if p.get('downloaded') in [True, 'true', 'True', 1, '1'])
    
    # Vérifier aussi si les fichiers existent réellement sur le disque
    files_exist = 0
    for p in photos:
        local_path = p.get('local_path')
        if local_path:
            # Résoudre le chemin (peut être relatif ou absolu)
            file_path = Path(local_path)
            if not file_path.is_absolute():
                # Si relatif, résoudre depuis le répertoire de travail
                file_path = Path.cwd() / file_path
            if file_path.exists():
                files_exist += 1
    
    # Considérer comme téléchargé si marqué downloaded OU si le fichier existe
    has_downloaded = downloaded > 0 or files_exist > 0
    
    return (True, has_downloaded, total, downloaded, files_exist)


def analyze_apartment_data(apartments: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyse toutes les données des appartements
    """
    total = len(apartments)
    
    # Champs à vérifier
    fields_to_check = {
        # Données de base
        'id': 'ID',
        'url': 'URL',
        'titre': 'Titre',
        'prix': 'Prix',
        'surface': 'Surface',
        'localisation': 'Localisation',
        'prix_m2': 'Prix/m²',
        'pieces': 'Pièces',
        'date': 'Date',
        'scraped_at': 'Date de scraping',
        
        # Caractéristiques
        'caracteristiques': 'Caractéristiques',
        'etage': 'Étage',
        'agence': 'Agence',
        'description': 'Description',
        'transports': 'Transports',
        
        # Localisation
        'coordinates': 'Coordonnées GPS',
        'coordinates.latitude': 'Latitude',
        'coordinates.longitude': 'Longitude',
        'localisation_precise': 'Localisation précise',
        'map_info': 'Map info',
        'map_info.metros': 'Métros',
        'map_info.quartier': 'Quartier',
        'map_info.streets': 'Rues',
        'map_info.screenshot': 'Screenshot carte',
        
        # Photos
        'photos': 'Photos',
        
        # Analyses
        'style_analysis': 'Analyse style',
        'style_analysis.style': 'Style détecté',
        'style_analysis.cuisine': 'Cuisine',
        'style_analysis.luminosite': 'Luminosité',
        'exposition': 'Exposition',
        'exposition.details': 'Détails exposition',
        
        # API data
        '_api_data': 'Données API',
        '_api_data.lat': 'API Lat',
        '_api_data.lng': 'API Lng',
        '_api_data.features': 'API Features',
        
        # Scores
        'score': 'Score',
    }
    
    # Statistiques par champ
    field_stats = {}
    for field_path, field_name in fields_to_check.items():
        present = sum(1 for apt in apartments.values() if check_field_presence(apt, field_path))
        field_stats[field_path] = {
            'name': field_name,
            'present': present,
            'missing': total - present,
            'percentage': round((present / total * 100) if total > 0 else 0, 1)
        }
    
    # Statistiques photos
    photos_stats = {
        'has_photos': 0,
        'has_downloaded_photos': 0,
        'total_photos': 0,
        'total_downloaded': 0,
        'total_files_exist': 0,
        'apartments_without_photos': 0,
        'apartments_without_downloaded_photos': 0,
    }
    
    # Statistiques cuisine et baignoire
    cuisine_stats = {
        'has_cuisine_data': 0,
        'cuisine_ouverte': 0,
        'cuisine_fermee': 0,
    }
    
    baignoire_stats = {
        'has_baignoire_caracteristiques': 0,
        'has_baignoire_description': 0,
        'has_baignoire_api': 0,
        'has_baignoire': 0,  # Au moins une source
        'has_douche_caracteristiques': 0,
        'has_douche_description': 0,
        'has_douche_api': 0,
        'has_douche': 0,  # Douche trouvée
        'has_baignoire_et_douche': 0,  # Les deux présents
        'ni_baignoire_ni_douche': 0,  # Aucun des deux trouvé
        'bath_explicitly_no': 0,  # Explicitement marqué comme non (bath=0)
        'shower_explicitly_no': 0,  # Explicitement marqué comme non (shower=0)
        'bath_none': 0,  # Information non disponible (bath=None)
        'shower_none': 0,  # Information non disponible (shower=None)
    }
    
    for apt in apartments.values():
        has_photos, has_downloaded, total_photos, downloaded, files_exist = check_photos_downloaded(apt)
        photos_stats['total_photos'] += total_photos
        photos_stats['total_downloaded'] += downloaded
        photos_stats['total_files_exist'] += files_exist
        
        if has_photos:
            photos_stats['has_photos'] += 1
        else:
            photos_stats['apartments_without_photos'] += 1
        
        if has_downloaded:
            photos_stats['has_downloaded_photos'] += 1
        else:
            photos_stats['apartments_without_downloaded_photos'] += 1
        
        # Statistiques cuisine
        cuisine_data = apt.get('style_analysis', {}).get('cuisine')
        if cuisine_data:
            cuisine_stats['has_cuisine_data'] += 1
            if cuisine_data.get('ouverte') == True:
                cuisine_stats['cuisine_ouverte'] += 1
            elif cuisine_data.get('ouverte') == False:
                cuisine_stats['cuisine_fermee'] += 1
        
        # Statistiques baignoire et douche
        caracteristiques = apt.get('caracteristiques', '')
        description = apt.get('description', '')
        desc_lower = description.lower() if description else ''
        
        # Chercher dans caractéristiques
        has_baignoire_carac = caracteristiques and 'Baignoire' in caracteristiques
        has_douche_carac = caracteristiques and 'Douche' in caracteristiques
        
        # Chercher dans description (avec regex pour éviter faux positifs)
        import re
        has_baignoire_desc = bool(re.search(r'\bbaignoire\b|\bsalle de bain\b', desc_lower))
        has_douche_desc = bool(re.search(r'\bdouche\b|\bdouches\b', desc_lower))
        
        # Vérifier dans API features
        has_baignoire_api = False
        has_douche_api = False
        bath_explicitly_no = False
        shower_explicitly_no = False
        
        api_data = apt.get('_api_data', {})
        if api_data:
            api_features = api_data.get('features')
            if api_features and isinstance(api_features, dict):
                bath = api_features.get('bath')
                shower = api_features.get('shower')
                if bath == 1:
                    has_baignoire_api = True
                elif bath == 0:
                    bath_explicitly_no = True
                if shower == 1:
                    has_douche_api = True
                elif shower == 0:
                    shower_explicitly_no = True
        
        # Déterminer l'état final (caractéristiques OU description OU API)
        has_baignoire = has_baignoire_carac or has_baignoire_desc or has_baignoire_api
        has_douche = has_douche_carac or has_douche_desc or has_douche_api
        
        # Compter les statistiques
        if has_baignoire_carac:
            baignoire_stats['has_baignoire_caracteristiques'] += 1
        if has_baignoire_desc:
            baignoire_stats['has_baignoire_description'] += 1
        if has_baignoire_api:
            baignoire_stats['has_baignoire_api'] += 1
        if has_baignoire:
            baignoire_stats['has_baignoire'] += 1
        
        if has_douche_carac:
            baignoire_stats['has_douche_caracteristiques'] += 1
        if has_douche_desc:
            baignoire_stats['has_douche_description'] += 1
        if has_douche_api:
            baignoire_stats['has_douche_api'] += 1
        if has_douche:
            baignoire_stats['has_douche'] += 1
        
        # Compter les cas explicites
        if bath_explicitly_no:
            baignoire_stats['bath_explicitly_no'] += 1
        if shower_explicitly_no:
            baignoire_stats['shower_explicitly_no'] += 1
        
        # Compter les None (information non disponible)
        api_data = apt.get('_api_data', {})
        if api_data:
            api_features = api_data.get('features')
            if api_features and isinstance(api_features, dict):
                if api_features.get('bath') is None:
                    baignoire_stats['bath_none'] += 1
                if api_features.get('shower') is None:
                    baignoire_stats['shower_none'] += 1
        
        # Cas combinés
        if has_baignoire and has_douche:
            baignoire_stats['has_baignoire_et_douche'] += 1
        elif not has_baignoire and not has_douche:
            baignoire_stats['ni_baignoire_ni_douche'] += 1
    
    # Appartements avec données complètes vs incomplètes
    critical_fields = ['id', 'url', 'titre', 'prix', 'surface', 'localisation', 'pieces']
    apartments_complete = 0
    apartments_incomplete = []
    
    for apt_id, apt in apartments.items():
        missing_critical = [f for f in critical_fields if not check_field_presence(apt, f)]
        if not missing_critical:
            apartments_complete += 1
        else:
            apartments_incomplete.append({
                'id': apt_id,
                'missing': missing_critical
            })
    
    return {
        'total_apartments': total,
        'field_stats': field_stats,
        'photos_stats': photos_stats,
        'cuisine_stats': cuisine_stats,
        'baignoire_stats': baignoire_stats,
        'apartments_complete': apartments_complete,
        'apartments_incomplete': apartments_incomplete,
        'completeness_percentage': round((apartments_complete / total * 100) if total > 0 else 0, 1)
    }


def generate_report(analysis: Dict[str, Any]) -> str:
    """
    Génère un rapport textuel détaillé
    """
    report = []
    report.append("=" * 80)
    report.append("📊 RÉCAPITULATIF DES DONNÉES DES APPARTEMENTS")
    report.append("=" * 80)
    report.append(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"🏠 Total appartements: {analysis['total_apartments']}")
    report.append(f"✅ Appartements avec données complètes: {analysis['apartments_complete']} ({analysis['completeness_percentage']}%)")
    report.append(f"⚠️  Appartements avec données incomplètes: {len(analysis['apartments_incomplete'])}")
    
    # Statistiques par champ
    report.append("\n" + "=" * 80)
    report.append("📋 STATISTIQUES PAR CHAMP")
    report.append("=" * 80)
    
    # Grouper par catégorie
    categories = {
        'Données de base': ['id', 'url', 'titre', 'prix', 'surface', 'localisation', 'prix_m2', 'pieces', 'date', 'scraped_at'],
        'Caractéristiques': ['caracteristiques', 'etage', 'agence', 'description', 'transports'],
        'Localisation': ['coordinates', 'coordinates.latitude', 'coordinates.longitude', 'localisation_precise', 'map_info', 'map_info.metros', 'map_info.quartier', 'map_info.streets', 'map_info.screenshot'],
        'Photos': ['photos'],
        'Analyses': ['style_analysis', 'style_analysis.style', 'style_analysis.cuisine', 'style_analysis.luminosite', 'exposition', 'exposition.details'],
        'Données API': ['_api_data', '_api_data.lat', '_api_data.lng', '_api_data.features'],
        'Scores': ['score'],
    }
    
    for category, fields in categories.items():
        report.append(f"\n🔹 {category}")
        report.append("-" * 80)
        for field_path in fields:
            if field_path in analysis['field_stats']:
                stats = analysis['field_stats'][field_path]
                status = "✅" if stats['percentage'] == 100 else "⚠️ " if stats['percentage'] >= 50 else "❌"
                report.append(f"  {status} {stats['name']:30} {stats['present']:3}/{analysis['total_apartments']:3} ({stats['percentage']:5.1f}%)")
    
    # Statistiques photos détaillées
    report.append("\n" + "=" * 80)
    report.append("📸 STATISTIQUES PHOTOS")
    report.append("=" * 80)
    ps = analysis['photos_stats']
    report.append(f"  Appartements avec photos: {ps['has_photos']}/{analysis['total_apartments']} ({ps['has_photos']/analysis['total_apartments']*100:.1f}%)")
    report.append(f"  Appartements avec photos téléchargées: {ps['has_downloaded_photos']}/{analysis['total_apartments']} ({ps['has_downloaded_photos']/analysis['total_apartments']*100:.1f}%)")
    report.append(f"  Total photos: {ps['total_photos']}")
    report.append(f"  Total photos marquées 'downloaded': {ps['total_downloaded']}")
    report.append(f"  Total fichiers existants sur disque: {ps['total_files_exist']}")
    if ps['total_photos'] > 0:
        report.append(f"  Taux de téléchargement (marqué): {ps['total_downloaded']/ps['total_photos']*100:.1f}%")
        report.append(f"  Taux de fichiers existants: {ps['total_files_exist']/ps['total_photos']*100:.1f}%")
    report.append(f"  Appartements sans photos: {ps['apartments_without_photos']}")
    report.append(f"  Appartements sans photos téléchargées: {ps['apartments_without_downloaded_photos']}")
    
    # Statistiques cuisine
    report.append("\n" + "=" * 80)
    report.append("🍳 STATISTIQUES CUISINE")
    report.append("=" * 80)
    cs = analysis['cuisine_stats']
    total = analysis['total_apartments']
    report.append(f"  Appartements avec données cuisine: {cs['has_cuisine_data']}/{total} ({cs['has_cuisine_data']/total*100:.1f}%)")
    if cs['has_cuisine_data'] > 0:
        report.append(f"  Cuisine ouverte: {cs['cuisine_ouverte']}/{cs['has_cuisine_data']} ({cs['cuisine_ouverte']/cs['has_cuisine_data']*100:.1f}%)")
        report.append(f"  Cuisine fermée: {cs['cuisine_fermee']}/{cs['has_cuisine_data']} ({cs['cuisine_fermee']/cs['has_cuisine_data']*100:.1f}%)")
        report.append(f"  Cuisine ouverte (sur total): {cs['cuisine_ouverte']}/{total} ({cs['cuisine_ouverte']/total*100:.1f}%)")
        report.append(f"  Cuisine fermée (sur total): {cs['cuisine_fermee']}/{total} ({cs['cuisine_fermee']/total*100:.1f}%)")
    
    # Statistiques baignoire et douche
    report.append("\n" + "=" * 80)
    report.append("🛁 STATISTIQUES BAIGNOIRE / DOUCHE")
    report.append("=" * 80)
    bs = analysis['baignoire_stats']
    report.append(f"\n📊 Baignoire:")
    report.append(f"  Trouvée dans caractéristiques: {bs['has_baignoire_caracteristiques']}/{total} ({bs['has_baignoire_caracteristiques']/total*100:.1f}%)")
    report.append(f"  Trouvée dans description: {bs['has_baignoire_description']}/{total} ({bs['has_baignoire_description']/total*100:.1f}%)")
    report.append(f"  Trouvée dans API (bath=1): {bs['has_baignoire_api']}/{total} ({bs['has_baignoire_api']/total*100:.1f}%)")
    report.append(f"  TOTAL trouvée (au moins une source): {bs['has_baignoire']}/{total} ({bs['has_baignoire']/total*100:.1f}%)")
    report.append(f"  Explicitement non (bath=0): {bs['bath_explicitly_no']}/{total} ({bs['bath_explicitly_no']/total*100:.1f}%)")
    report.append(f"  Information non disponible (bath=None): {bs['bath_none']}/{total} ({bs['bath_none']/total*100:.1f}%)")
    
    report.append(f"\n🚿 Douche:")
    report.append(f"  Trouvée dans caractéristiques: {bs['has_douche_caracteristiques']}/{total} ({bs['has_douche_caracteristiques']/total*100:.1f}%)")
    report.append(f"  Trouvée dans description: {bs['has_douche_description']}/{total} ({bs['has_douche_description']/total*100:.1f}%)")
    report.append(f"  Trouvée dans API (shower=1): {bs['has_douche_api']}/{total} ({bs['has_douche_api']/total*100:.1f}%)")
    report.append(f"  TOTAL trouvée (au moins une source): {bs['has_douche']}/{total} ({bs['has_douche']/total*100:.1f}%)")
    report.append(f"  Explicitement non (shower=0): {bs['shower_explicitly_no']}/{total} ({bs['shower_explicitly_no']/total*100:.1f}%)")
    report.append(f"  Information non disponible (shower=None): {bs['shower_none']}/{total} ({bs['shower_none']/total*100:.1f}%)")
    
    report.append(f"\n📋 Résumé:")
    report.append(f"  Appartements avec baignoire ET douche: {bs['has_baignoire_et_douche']}/{total} ({bs['has_baignoire_et_douche']/total*100:.1f}%)")
    report.append(f"  Appartements avec douche uniquement: {bs['has_douche'] - bs['has_baignoire_et_douche']}/{total} ({(bs['has_douche'] - bs['has_baignoire_et_douche'])/total*100:.1f}%)")
    report.append(f"  Appartements avec baignoire uniquement: {bs['has_baignoire'] - bs['has_baignoire_et_douche']}/{total} ({(bs['has_baignoire'] - bs['has_baignoire_et_douche'])/total*100:.1f}%)")
    report.append(f"  ⚠️  Ni baignoire ni douche trouvée: {bs['ni_baignoire_ni_douche']}/{total} ({bs['ni_baignoire_ni_douche']/total*100:.1f}%)")
    report.append(f"     (Note: peut signifier information non disponible plutôt qu'absence réelle)")
    
    # Appartements incomplets
    if analysis['apartments_incomplete']:
        report.append("\n" + "=" * 80)
        report.append("⚠️  APPARTEMENTS AVEC DONNÉES MANQUANTES")
        report.append("=" * 80)
        for apt in analysis['apartments_incomplete'][:20]:  # Limiter à 20 pour la lisibilité
            report.append(f"  ❌ {apt['id']}: manque {', '.join(apt['missing'])}")
        if len(analysis['apartments_incomplete']) > 20:
            report.append(f"  ... et {len(analysis['apartments_incomplete']) - 20} autres")
    
    # Résumé des données critiques manquantes
    report.append("\n" + "=" * 80)
    report.append("📊 RÉSUMÉ DES DONNÉES CRITIQUES MANQUANTES")
    report.append("=" * 80)
    
    critical_missing = {}
    for apt in analysis['apartments_incomplete']:
        for field in apt['missing']:
            critical_missing[field] = critical_missing.get(field, 0) + 1
    
    for field, count in sorted(critical_missing.items(), key=lambda x: x[1], reverse=True):
        report.append(f"  ❌ {field:20} manquant pour {count:3} appartements")
    
    report.append("\n" + "=" * 80)
    
    return "\n".join(report)


def main():
    """Fonction principale"""
    print("🔍 Vérification de toutes les données des appartements...")
    print("=" * 80)
    
    # Charger tous les appartements
    apartments = load_all_apartments()
    
    if not apartments:
        print("❌ Aucun appartement trouvé!")
        return
    
    # Analyser les données
    print("\n📊 Analyse des données...")
    analysis = analyze_apartment_data(apartments)
    
    # Générer le rapport
    report = generate_report(analysis)
    print("\n" + report)
    
    # Sauvegarder le rapport
    output_file = Path('data') / f'apartments_data_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Sauvegarder aussi en JSON pour analyse ultérieure
    json_file = Path('data') / f'apartments_data_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Rapport sauvegardé dans: {output_file}")
    print(f"✅ Analyse JSON sauvegardée dans: {json_file}")


if __name__ == "__main__":
    main()

