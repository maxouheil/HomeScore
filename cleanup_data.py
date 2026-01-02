#!/usr/bin/env python3
"""
Script de nettoyage des données d'appartements
Nettoie les doublons et archive les fichiers obsolètes
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

DATA_DIR = Path('data')
ARCHIVE_DIR = DATA_DIR / 'archive' / 'data_cleanup'
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

def load_json_file(file_path: Path) -> List[Dict]:
    """Charge un fichier JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"   ❌ Erreur lecture {file_path.name}: {e}")
        return []

def get_apartment_ids(apartments: List[Dict]) -> Set[str]:
    """Extrait les IDs des appartements"""
    return {str(apt.get('id')) for apt in apartments if apt.get('id')}

def archive_file(file_path: Path, reason: str):
    """Archive un fichier"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_name = f"{file_path.stem}_{reason}_{timestamp}{file_path.suffix}"
    archive_path = ARCHIVE_DIR / archive_name
    
    try:
        shutil.copy2(file_path, archive_path)
        print(f"   📦 Archivé: {file_path.name} → {archive_path.name}")
        return archive_path
    except Exception as e:
        print(f"   ❌ Erreur archivage {file_path.name}: {e}")
        return None

def cleanup_api_files():
    """Nettoie les anciens fichiers API (garde seulement le plus récent)"""
    print("\n🧹 Nettoyage des fichiers API...")
    
    api_files = sorted(
        DATA_DIR.glob('scraped_apartments_api_*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if len(api_files) <= 1:
        print("   ✅ Pas de nettoyage nécessaire (1 fichier ou moins)")
        return
    
    # Garder le plus récent
    keep_file = api_files[0]
    print(f"   ✅ Conservation: {keep_file.name}")
    
    # Archiver les autres
    for old_file in api_files[1:]:
        archive_file(old_file, 'old_api')
        old_file.unlink()
        print(f"   🗑️  Supprimé: {old_file.name}")

def cleanup_individual_files():
    """Archive les fichiers individuels dans data/appartements/"""
    print("\n🧹 Nettoyage des fichiers individuels...")
    
    appartements_dir = DATA_DIR / 'appartements'
    if not appartements_dir.exists():
        print("   ✅ Pas de fichiers individuels à nettoyer")
        return
    
    apartment_files = list(appartements_dir.glob('*.json'))
    
    if not apartment_files:
        print("   ✅ Pas de fichiers individuels à nettoyer")
        return
    
    print(f"   📦 Archivage de {len(apartment_files)} fichiers individuels...")
    
    # Créer une archive tar.gz de tous les fichiers
    archive_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_base = ARCHIVE_DIR / f'appartements_individual_{archive_timestamp}'
    
    # Copier tous les fichiers dans un sous-dossier d'archive
    archive_subdir = archive_base
    archive_subdir.mkdir(parents=True, exist_ok=True)
    
    for apt_file in apartment_files:
        shutil.copy2(apt_file, archive_subdir / apt_file.name)
    
    print(f"   ✅ {len(apartment_files)} fichiers archivés dans {archive_subdir.name}/")
    print(f"   💡 Les fichiers individuels peuvent être supprimés si all_apartments.json est à jour")

def analyze_duplicates():
    """Analyse les doublons entre fichiers principaux"""
    print("\n🔍 Analyse des doublons...")
    
    main_files = {
        'all_apartments.json': DATA_DIR / 'all_apartments.json',
        'scraped_apartments.json': DATA_DIR / 'scraped_apartments.json',
        'paris_apartments.json': DATA_DIR / 'paris_apartments.json',
        'jinka_apartments.json': DATA_DIR / 'jinka_apartments.json',
    }
    
    file_data = {}
    for name, path in main_files.items():
        if path.exists():
            apartments = load_json_file(path)
            file_data[name] = {
                'path': path,
                'apartments': apartments,
                'ids': get_apartment_ids(apartments)
            }
    
    # Comparer all_apartments.json avec les autres
    if 'all_apartments.json' not in file_data:
        print("   ⚠️  all_apartments.json n'existe pas - c'est le fichier principal!")
        return
    
    main_ids = file_data['all_apartments.json']['ids']
    
    print(f"\n   📊 Comparaison avec all_apartments.json ({len(main_ids)} appartements):")
    
    for name, data in file_data.items():
        if name == 'all_apartments.json':
            continue
        
        other_ids = data['ids']
        common = main_ids & other_ids
        only_in_other = other_ids - main_ids
        only_in_main = main_ids - other_ids
        
        print(f"\n   {name}:")
        print(f"      Total: {len(other_ids)} appartements")
        print(f"      En commun avec all_apartments.json: {len(common)}")
        print(f"      Seulement dans {name}: {len(only_in_other)}")
        print(f"      Seulement dans all_apartments.json: {len(only_in_main)}")
        
        if len(common) == len(main_ids) and len(only_in_other) == 0:
            print(f"      ✅ {name} est un sous-ensemble de all_apartments.json")
        elif len(common) > 0:
            print(f"      ⚠️  Doublons détectés: {len(common)} appartements")

def create_cleanup_report():
    """Crée un rapport de nettoyage"""
    print("\n📝 Création du rapport...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'actions': {
            'api_files_cleaned': False,
            'individual_files_archived': False,
        },
        'recommendations': []
    }
    
    # Vérifier les fichiers principaux
    main_file = DATA_DIR / 'all_apartments.json'
    if main_file.exists():
        apartments = load_json_file(main_file)
        report['main_file'] = {
            'path': str(main_file),
            'count': len(apartments),
            'size_mb': round(main_file.stat().st_size / (1024 * 1024), 2)
        }
        report['recommendations'].append(
            "✅ CONSERVER: data/all_apartments.json (fichier principal utilisé par le backend)"
        )
    else:
        report['recommendations'].append(
            "⚠️ CRÉER: data/all_apartments.json (requis par le backend)"
        )
    
    # Recommandations
    scraped_file = DATA_DIR / 'scraped_apartments.json'
    if scraped_file.exists():
        report['recommendations'].append(
            "❓ VÉRIFIER: data/scraped_apartments.json - utilisé par certains scripts mais doublon avec all_apartments.json"
        )
    
    paris_file = DATA_DIR / 'paris_apartments.json'
    if paris_file.exists():
        report['recommendations'].append(
            "❓ VÉRIFIER: data/paris_apartments.json - semble être un snapshot spécifique Paris (peut être archivé)"
        )
    
    jinka_file = DATA_DIR / 'jinka_apartments.json'
    if jinka_file.exists():
        report['recommendations'].append(
            "✅ CONSERVER: data/jinka_apartments.json - données spécifiques Jinka (47 appartements)"
        )
    
    # Sauvegarder le rapport
    report_file = DATA_DIR / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"   💾 Rapport sauvegardé: {report_file.name}")
    
    return report

def main():
    """Fonction principale"""
    print("=" * 80)
    print("🧹 NETTOYAGE DES DONNÉES")
    print("=" * 80)
    
    # Créer le répertoire d'archive
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📦 Répertoire d'archive: {ARCHIVE_DIR}")
    
    # Nettoyer les fichiers API
    cleanup_api_files()
    
    # Archiver les fichiers individuels
    cleanup_individual_files()
    
    # Analyser les doublons
    analyze_duplicates()
    
    # Créer le rapport
    report = create_cleanup_report()
    
    print("\n" + "=" * 80)
    print("✅ NETTOYAGE TERMINÉ")
    print("=" * 80)
    print("\n💡 RECOMMANDATIONS:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print(f"\n📦 Les fichiers archivés sont dans: {ARCHIVE_DIR}")

if __name__ == "__main__":
    main()
