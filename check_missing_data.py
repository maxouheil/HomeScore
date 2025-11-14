#!/usr/bin/env python3
"""
Script pour vérifier tous les appartements et identifier les données manquantes
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Any

# Structure de données attendue pour un appartement complet
EXPECTED_FIELDS = {
    'basic': ['id', 'url', 'scraped_at', 'titre', 'prix', 'localisation', 'surface', 'pieces', 'description'],
    'coordinates': ['latitude', 'longitude'],
    'map_info': ['quartier', 'metros', 'streets'],
    'photos': ['photos'],
    'analysis': ['exposition', 'baignoire', 'style_analysis', 'style_haussmannien'],
    'scoring': ['scores_detaille', 'score_total', 'tier']
}

def get_all_apartment_ids() -> Set[str]:
    """Récupère tous les IDs d'appartements depuis les différents fichiers"""
    apartment_ids = set()
    
    # Depuis data/appartements/
    appartements_dir = Path('data/appartements')
    if appartements_dir.exists():
        for file in appartements_dir.glob('*.json'):
            if file.stem not in ['test_001', 'test_no_photo', 'unknown']:
                apartment_ids.add(file.stem)
    
    # Depuis data/scraped_apartments.json
    scraped_file = Path('data/scraped_apartments.json')
    if scraped_file.exists():
        try:
            with open(scraped_file, 'r', encoding='utf-8') as f:
                apartments = json.load(f)
                for apt in apartments:
                    if 'id' in apt:
                        apartment_ids.add(str(apt['id']))
        except Exception as e:
            print(f"⚠️ Erreur lecture scraped_apartments.json: {e}")
    
    return apartment_ids

def check_field_exists(data: Dict, field_path: str) -> bool:
    """Vérifie si un champ existe dans les données (supporte les chemins imbriqués)"""
    parts = field_path.split('.')
    current = data
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False
    
    # Vérifier que la valeur n'est pas None ou vide
    if current is None:
        return False
    if isinstance(current, (list, str)) and len(current) == 0:
        return False
    if isinstance(current, str) and current.strip() == '':
        return False
    
    return True

def check_field_valid(data: Dict, field_path: str) -> bool:
    """Vérifie si un champ existe ET a une valeur valide (non-null, non-vide)"""
    if not check_field_exists(data, field_path):
        return False
    
    parts = field_path.split('.')
    current = data
    for part in parts:
        current = current[part]
    
    # Vérifications supplémentaires
    if current is None:
        return False
    if isinstance(current, (list, str)) and len(current) == 0:
        return False
    if isinstance(current, str) and current.strip() == '':
        return False
    if isinstance(current, dict) and len(current) == 0:
        return False
    
    return True

def check_apartment_data(apartment_id: str) -> Dict[str, Any]:
    """Vérifie les données d'un appartement et retourne les manquantes"""
    missing = defaultdict(list)
    issues = []
    
    # 1. Vérifier le fichier appartement
    apt_file = Path(f'data/appartements/{apartment_id}.json')
    if not apt_file.exists():
        missing['files'].append('appartement.json')
        return {'missing': dict(missing), 'issues': issues, 'exists': False}
    
    try:
        with open(apt_file, 'r', encoding='utf-8') as f:
            apt_data = json.load(f)
    except Exception as e:
        issues.append(f"Erreur lecture JSON: {e}")
        return {'missing': dict(missing), 'issues': issues, 'exists': True}
    
    # 2. Vérifier les champs de base
    for field in EXPECTED_FIELDS['basic']:
        if not check_field_valid(apt_data, field):
            missing['basic'].append(field)
    
    # 3. Vérifier les coordonnées
    if not check_field_exists(apt_data, 'coordinates'):
        missing['coordinates'].append('coordinates')
    elif not check_field_valid(apt_data, 'coordinates.latitude') or not check_field_valid(apt_data, 'coordinates.longitude'):
        missing['coordinates'].append('coordinates (invalides)')
    
    # 4. Vérifier map_info
    if not check_field_exists(apt_data, 'map_info'):
        missing['map_info'].append('map_info')
    else:
        if not check_field_valid(apt_data, 'map_info.quartier'):
            missing['map_info'].append('quartier')
        if not check_field_valid(apt_data, 'map_info.metros'):
            missing['map_info'].append('metros (vide)')
    
    # 5. Vérifier les photos
    if not check_field_valid(apt_data, 'photos'):
        missing['photos'].append('photos (aucune photo)')
    else:
        photos = apt_data.get('photos', [])
        if len(photos) == 0:
            missing['photos'].append('photos (liste vide)')
        else:
            # Vérifier si les photos sont téléchargées
            photos_dir = Path(f'data/photos/{apartment_id}')
            if not photos_dir.exists():
                missing['photos'].append('photos_dir (non téléchargées)')
            else:
                downloaded_photos = list(photos_dir.glob('*.jpg'))
                if len(downloaded_photos) == 0:
                    missing['photos'].append('photos_dir (vide)')
                elif len(downloaded_photos) < len(photos):
                    missing['photos'].append(f'photos_dir (partiel: {len(downloaded_photos)}/{len(photos)})')
    
    # 6. Vérifier prix_m2
    if not check_field_valid(apt_data, 'prix_m2'):
        missing['basic'].append('prix_m2')
    
    # 7. Vérifier l'exposition
    if not check_field_exists(apt_data, 'exposition'):
        missing['analysis'].append('exposition')
    elif not check_field_valid(apt_data, 'exposition.exposition'):
        missing['analysis'].append('exposition.exposition')
    
    # 8. Vérifier baignoire
    if not check_field_exists(apt_data, 'baignoire'):
        missing['analysis'].append('baignoire')
    
    # 9. Vérifier style_analysis
    if not check_field_exists(apt_data, 'style_analysis'):
        missing['analysis'].append('style_analysis')
    elif not check_field_valid(apt_data, 'style_analysis.style'):
        missing['analysis'].append('style_analysis.style')
    
    # 10. Vérifier style_haussmannien
    if not check_field_exists(apt_data, 'style_haussmannien'):
        missing['analysis'].append('style_haussmannien')
    
    # 11. Vérifier les scores
    if not check_field_exists(apt_data, 'scores_detaille'):
        missing['scoring'].append('scores_detaille')
    if not check_field_valid(apt_data, 'score_total'):
        missing['scoring'].append('score_total')
    if not check_field_valid(apt_data, 'tier'):
        missing['scoring'].append('tier')
    
    # 12. Vérifier le fichier de score séparé
    score_file = Path(f'data/scores/apartment_{apartment_id}_score.json')
    if not score_file.exists():
        missing['files'].append('score.json')
    
    # 13. Vérifier le screenshot de map
    if check_field_exists(apt_data, 'map_info.screenshot'):
        screenshot_path = apt_data.get('map_info', {}).get('screenshot', '')
        if screenshot_path and not Path(screenshot_path).exists():
            missing['files'].append('map_screenshot')
    
    return {'missing': dict(missing), 'issues': issues, 'exists': True, 'apt_data': apt_data}

def generate_report() -> Dict[str, Any]:
    """Génère un rapport complet sur les données manquantes"""
    print("🔍 Vérification de tous les appartements...")
    
    apartment_ids = get_all_apartment_ids()
    print(f"📊 {len(apartment_ids)} appartements trouvés\n")
    
    all_missing = defaultdict(lambda: defaultdict(int))
    apartments_by_issue = defaultdict(list)
    total_stats = {
        'total': len(apartment_ids),
        'complete': 0,
        'incomplete': 0,
        'missing_files': 0,
        'missing_photos': 0,
        'missing_analysis': 0,
        'missing_scoring': 0
    }
    
    for apt_id in sorted(apartment_ids):
        result = check_apartment_data(apt_id)
        
        if not result['exists']:
            total_stats['missing_files'] += 1
            apartments_by_issue['missing_file'].append(apt_id)
            continue
        
        missing = result['missing']
        
        if len(missing) == 0:
            total_stats['complete'] += 1
        else:
            total_stats['incomplete'] += 1
            
            # Compter les problèmes par catégorie
            if 'files' in missing:
                total_stats['missing_files'] += 1
            if 'photos' in missing:
                total_stats['missing_photos'] += 1
            if 'analysis' in missing:
                total_stats['missing_analysis'] += 1
            if 'scoring' in missing:
                total_stats['missing_scoring'] += 1
            
            # Enregistrer les problèmes
            for category, fields in missing.items():
                for field in fields:
                    all_missing[category][field] += 1
                    apartments_by_issue[f"{category}.{field}"].append(apt_id)
    
    return {
        'stats': total_stats,
        'missing_summary': dict(all_missing),
        'apartments_by_issue': dict(apartments_by_issue)
    }

def print_report(report: Dict[str, Any]):
    """Affiche le rapport de manière lisible"""
    stats = report['stats']
    missing_summary = report['missing_summary']
    apartments_by_issue = report['apartments_by_issue']
    
    print("=" * 80)
    print("📊 RAPPORT DE VÉRIFICATION DES DONNÉES")
    print("=" * 80)
    print()
    
    print("📈 STATISTIQUES GLOBALES")
    print("-" * 80)
    print(f"Total d'appartements: {stats['total']}")
    print(f"✅ Complets: {stats['complete']}")
    print(f"⚠️  Incomplets: {stats['incomplete']}")
    print(f"📁 Manquants fichiers: {stats['missing_files']}")
    print(f"📸 Manquantes photos: {stats['missing_photos']}")
    print(f"🔬 Manquantes analyses: {stats['missing_analysis']}")
    print(f"📊 Manquants scores: {stats['missing_scoring']}")
    print()
    
    print("📋 RÉSUMÉ DES DONNÉES MANQUANTES")
    print("-" * 80)
    
    for category in ['files', 'basic', 'coordinates', 'map_info', 'photos', 'analysis', 'scoring']:
        if category in missing_summary:
            print(f"\n🔹 {category.upper()}:")
            for field, count in sorted(missing_summary[category].items(), key=lambda x: -x[1]):
                percentage = (count / stats['total']) * 100
                print(f"   - {field}: {count} ({percentage:.1f}%)")
    
    print()
    print("=" * 80)
    print("📝 DÉTAILS PAR APPARTEMENT")
    print("=" * 80)
    print()
    
    # Afficher les appartements avec problèmes par catégorie
    for issue_key, apt_ids in sorted(apartments_by_issue.items()):
        if len(apt_ids) > 0:
            print(f"\n🔸 {issue_key}: {len(apt_ids)} appartements")
            if len(apt_ids) <= 10:
                print(f"   IDs: {', '.join(apt_ids)}")
            else:
                print(f"   IDs (10 premiers): {', '.join(apt_ids[:10])}... (+{len(apt_ids)-10} autres)")

def generate_detailed_report() -> Dict[str, Any]:
    """Génère un rapport détaillé par appartement"""
    apartment_ids = get_all_apartment_ids()
    detailed = {}
    
    for apt_id in sorted(apartment_ids):
        result = check_apartment_data(apt_id)
        detailed[apt_id] = {
            'missing_count': sum(len(v) for v in result['missing'].values()),
            'missing_by_category': {k: len(v) for k, v in result['missing'].items()},
            'missing_details': result['missing'],
            'issues': result['issues']
        }
    
    return detailed

def print_detailed_summary(report: Dict[str, Any]):
    """Affiche un résumé détaillé par appartement"""
    detailed = generate_detailed_report()
    
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ DÉTAILLÉ PAR APPARTEMENT")
    print("=" * 80)
    print()
    
    # Trier par nombre de problèmes
    sorted_apts = sorted(detailed.items(), key=lambda x: -x[1]['missing_count'])
    
    print("🔴 APPARTEMENTS AVEC LE PLUS DE PROBLÈMES:")
    print("-" * 80)
    for apt_id, info in sorted_apts[:10]:
        print(f"\n🏠 {apt_id}: {info['missing_count']} problèmes")
        for category, count in info['missing_by_category'].items():
            if count > 0:
                print(f"   - {category}: {count} champs manquants")
                for field in info['missing_details'].get(category, []):
                    print(f"     • {field}")
    
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES PAR PRIORITÉ")
    print("=" * 80)
    
    # Catégoriser par priorité
    critical = []  # Pas de photos ou pas de scoring
    high = []      # Manque analyses importantes
    medium = []    # Manque données secondaires
    
    for apt_id, info in detailed.items():
        if info['missing_details'].get('photos') or info['missing_details'].get('scoring'):
            critical.append((apt_id, info))
        elif info['missing_details'].get('analysis'):
            high.append((apt_id, info))
        else:
            medium.append((apt_id, info))
    
    print(f"\n🔴 CRITIQUE ({len(critical)} appartements): Manque photos ou scoring")
    for apt_id, info in critical[:5]:
        print(f"   - {apt_id}: {info['missing_count']} problèmes")
    
    print(f"\n🟡 ÉLEVÉE ({len(high)} appartements): Manque analyses importantes")
    for apt_id, info in high[:5]:
        print(f"   - {apt_id}: {info['missing_count']} problèmes")
    
    print(f"\n🟢 MOYENNE ({len(medium)} appartements): Manque données secondaires")
    for apt_id, info in medium[:5]:
        print(f"   - {apt_id}: {info['missing_count']} problèmes")

def save_report(report: Dict[str, Any], filename: str = 'data/missing_data_report.json'):
    """Sauvegarde le rapport en JSON"""
    os.makedirs('data', exist_ok=True)
    
    # Ajouter le rapport détaillé
    report['detailed'] = generate_detailed_report()
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Rapport sauvegardé dans {filename}")

if __name__ == '__main__':
    report = generate_report()
    print_report(report)
    print_detailed_summary(report)
    save_report(report)
    
    print("\n✅ Vérification terminée!")

