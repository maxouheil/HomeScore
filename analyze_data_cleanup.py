#!/usr/bin/env python3
"""
Script d'analyse et nettoyage des données d'appartements
Identifie les doublons, les fichiers utilisés/non utilisés, et propose un nettoyage
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Any
from datetime import datetime

# Fichiers principaux à analyser
DATA_DIR = Path('data')
MAIN_FILES = {
    'all_apartments.json': 'Backend principal (utilisé par backend/api/apartments.py)',
    'scraped_apartments.json': 'Données scrapées HTML (utilisé par plusieurs scripts)',
    'paris_apartments.json': 'Données spécifiques Paris',
    'jinka_apartments.json': 'Données Jinka',
}

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
    return {apt.get('id') for apt in apartments if apt.get('id')}

def analyze_file(file_path: Path, description: str) -> Dict[str, Any]:
    """Analyse un fichier de données"""
    print(f"\n📂 Analyse de {file_path.name}")
    print(f"   Description: {description}")
    
    if not file_path.exists():
        return {
            'exists': False,
            'size': 0,
            'count': 0,
            'ids': set(),
            'mtime': None
        }
    
    # Informations sur le fichier
    stat = file_path.stat()
    size_mb = stat.st_size / (1024 * 1024)
    mtime = datetime.fromtimestamp(stat.st_mtime)
    
    # Charger les données
    apartments = load_json_file(file_path)
    ids = get_apartment_ids(apartments)
    
    result = {
        'exists': True,
        'size_mb': round(size_mb, 2),
        'count': len(apartments),
        'ids': ids,
        'mtime': mtime,
        'description': description
    }
    
    print(f"   ✅ Existe: {size_mb:.2f} MB, {len(apartments)} appartements, {len(ids)} IDs uniques")
    print(f"   📅 Modifié: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return result

def analyze_api_files() -> Dict[str, Any]:
    """Analyse les fichiers API"""
    api_files = sorted(
        DATA_DIR.glob('scraped_apartments_api_*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not api_files:
        return {'files': [], 'all_ids': set()}
    
    print(f"\n📡 Analyse des fichiers API ({len(api_files)} fichiers)")
    all_ids = set()
    files_info = []
    
    for api_file in api_files[:5]:  # Limiter à 5 pour l'affichage
        stat = api_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        
        apartments = load_json_file(api_file)
        ids = get_apartment_ids(apartments)
        all_ids.update(ids)
        
        files_info.append({
            'name': api_file.name,
            'size_mb': round(size_mb, 2),
            'count': len(apartments),
            'ids': ids,
            'mtime': mtime
        })
        
        print(f"   📄 {api_file.name}: {size_mb:.2f} MB, {len(apartments)} appartements, {len(ids)} IDs")
    
    if len(api_files) > 5:
        print(f"   ... et {len(api_files) - 5} autres fichiers")
    
    return {'files': files_info, 'all_ids': all_ids}

def analyze_individual_files() -> Dict[str, Any]:
    """Analyse les fichiers individuels dans data/appartements/"""
    appartements_dir = DATA_DIR / 'appartements'
    
    if not appartements_dir.exists():
        return {'files': [], 'all_ids': set()}
    
    apartment_files = list(appartements_dir.glob('*.json'))
    
    if not apartment_files:
        return {'files': [], 'all_ids': set()}
    
    print(f"\n📁 Analyse des fichiers individuels ({len(apartment_files)} fichiers)")
    all_ids = set()
    
    for apt_file in apartment_files:
        apartments = load_json_file(apt_file)
        ids = get_apartment_ids(apartments)
        all_ids.update(ids)
    
    print(f"   ✅ {len(apartment_files)} fichiers, {len(all_ids)} IDs uniques")
    
    return {'files': apartment_files, 'all_ids': all_ids}

def find_duplicates(all_files_data: Dict[str, Dict]) -> Dict[str, Any]:
    """Trouve les doublons entre fichiers"""
    print("\n🔍 Recherche des doublons...")
    
    # Créer un mapping ID -> fichiers qui le contiennent
    id_to_files = defaultdict(list)
    
    for file_name, file_data in all_files_data.items():
        if file_data.get('exists') and file_data.get('ids'):
            for apt_id in file_data['ids']:
                id_to_files[apt_id].append(file_name)
    
    # Trouver les IDs présents dans plusieurs fichiers
    duplicates = {}
    for apt_id, files in id_to_files.items():
        if len(files) > 1:
            duplicates[apt_id] = files
    
    print(f"   📊 {len(duplicates)} appartements présents dans plusieurs fichiers")
    
    # Statistiques par paire de fichiers
    file_pairs = defaultdict(int)
    for apt_id, files in duplicates.items():
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                pair = tuple(sorted([file1, file2]))
                file_pairs[pair] += 1
    
    print(f"\n   📈 Doublons par paire de fichiers:")
    for (file1, file2), count in sorted(file_pairs.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"      {file1} ↔ {file2}: {count} doublons")
    
    return {
        'duplicate_ids': duplicates,
        'file_pairs': dict(file_pairs),
        'total_duplicates': len(duplicates)
    }

def check_usage_in_code() -> Dict[str, List[str]]:
    """Vérifie l'utilisation des fichiers dans le code"""
    print("\n🔍 Vérification de l'utilisation dans le code...")
    
    usage = defaultdict(list)
    
    # Chercher les références dans le code
    code_files = [
        'backend/api/apartments.py',
        'data_loader.py',
        'project_config.py',
    ]
    
    for code_file in code_files:
        code_path = Path(code_file)
        if not code_path.exists():
            continue
        
        try:
            with open(code_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for file_name in MAIN_FILES.keys():
                if file_name in content:
                    usage[file_name].append(code_file)
        except Exception as e:
            print(f"   ⚠️ Erreur lecture {code_file}: {e}")
    
    return dict(usage)

def generate_recommendations(all_files_data: Dict, duplicates: Dict, usage: Dict) -> List[str]:
    """Génère des recommandations de nettoyage"""
    recommendations = []
    
    print("\n💡 RECOMMANDATIONS:")
    print("=" * 80)
    
    # 1. Fichier principal utilisé par le backend
    if all_files_data.get('all_apartments.json', {}).get('exists'):
        recommendations.append("✅ CONSERVER: data/all_apartments.json (utilisé par le backend)")
    else:
        recommendations.append("⚠️ CRÉER: data/all_apartments.json (requis par le backend)")
    
    # 2. Fichiers API anciens
    api_files_count = len([f for f in Path(DATA_DIR).glob('scraped_apartments_api_*.json')])
    if api_files_count > 1:
        recommendations.append(f"🗑️ NETTOYER: {api_files_count} fichiers API (garder seulement le plus récent)")
    
    # 3. Fichiers individuels
    if Path(DATA_DIR / 'appartements').exists():
        individual_count = len(list((DATA_DIR / 'appartements').glob('*.json')))
        if individual_count > 0:
            recommendations.append(f"🗑️ ARCHIVER: {individual_count} fichiers individuels dans data/appartements/ (ancien format)")
    
    # 4. Doublons
    if duplicates.get('total_duplicates', 0) > 0:
        recommendations.append(f"⚠️ RÉSOUDRE: {duplicates['total_duplicates']} appartements en doublon entre fichiers")
    
    # 5. Fichiers non utilisés
    for file_name, file_data in all_files_data.items():
        if file_data.get('exists') and file_name not in usage:
            recommendations.append(f"❓ VÉRIFIER: {file_name} (non référencé dans le code analysé)")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    return recommendations

def main():
    """Fonction principale"""
    print("=" * 80)
    print("🧹 ANALYSE ET NETTOYAGE DES DONNÉES")
    print("=" * 80)
    
    # Analyser les fichiers principaux
    all_files_data = {}
    for file_name, description in MAIN_FILES.items():
        file_path = DATA_DIR / file_name
        all_files_data[file_name] = analyze_file(file_path, description)
    
    # Analyser les fichiers API
    api_data = analyze_api_files()
    
    # Analyser les fichiers individuels
    individual_data = analyze_individual_files()
    
    # Trouver les doublons
    duplicates = find_duplicates(all_files_data)
    
    # Vérifier l'utilisation dans le code
    usage = check_usage_in_code()
    
    print("\n📊 RÉSUMÉ:")
    print("=" * 80)
    print(f"Fichiers principaux analysés: {len([f for f in all_files_data.values() if f.get('exists')])}")
    print(f"Fichiers API: {len(api_data['files'])}")
    print(f"Fichiers individuels: {len(individual_data.get('files', []))}")
    print(f"Total doublons: {duplicates.get('total_duplicates', 0)}")
    
    # Générer les recommandations
    recommendations = generate_recommendations(all_files_data, duplicates, usage)
    
    # Sauvegarder le rapport
    report_file = DATA_DIR / f"data_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report = {
        'timestamp': datetime.now().isoformat(),
        'files_analyzed': {k: {
            'exists': v.get('exists'),
            'size_mb': v.get('size_mb'),
            'count': v.get('count'),
            'ids_count': len(v.get('ids', set())),
            'mtime': v.get('mtime').isoformat() if v.get('mtime') else None
        } for k, v in all_files_data.items()},
        'api_files': len(api_data['files']),
        'individual_files': len(individual_data.get('files', [])),
        'duplicates': {
            'total': duplicates.get('total_duplicates', 0),
            'file_pairs': {f"{k[0]} ↔ {k[1]}": v for k, v in duplicates.get('file_pairs', {}).items()}
        },
        'usage': usage,
        'recommendations': recommendations
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Rapport sauvegardé: {report_file.name}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
