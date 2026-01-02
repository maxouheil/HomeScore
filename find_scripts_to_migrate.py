#!/usr/bin/env python3
"""
Script pour identifier les fichiers qui utilisent encore les anciens fichiers de données
et doivent être migrés vers all_apartments.json
"""

import re
from pathlib import Path
from typing import List, Dict

# Fichiers à rechercher
OLD_FILES = [
    'scraped_apartments.json',
    'paris_apartments.json',
    'scraped_apartments_api_',
    'appartements/',
    'all_apartments_scores.json',  # Ancien format de scores
]

# Fichiers à ignorer
IGNORE_PATTERNS = [
    'analyze_data_cleanup.py',
    'cleanup_data.py',
    'find_scripts_to_migrate.py',
    '__pycache__',
    '.git',
    'node_modules',
    'archive',
    'backups',
    '.cursor',
]

def should_ignore_file(file_path: Path) -> bool:
    """Vérifie si un fichier doit être ignoré"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in IGNORE_PATTERNS)

def find_references(file_path: Path) -> List[Dict]:
    """Trouve les références aux anciens fichiers dans un fichier"""
    references = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for old_file in OLD_FILES:
                if old_file in line:
                    # Vérifier que ce n'est pas un commentaire ou une docstring
                    stripped = line.strip()
                    if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    
                    references.append({
                        'file': str(file_path),
                        'line': line_num,
                        'content': line.strip(),
                        'old_file': old_file
                    })
    except Exception as e:
        pass
    
    return references

def main():
    """Fonction principale"""
    print("=" * 80)
    print("🔍 RECHERCHE DES SCRIPTS À MIGRER")
    print("=" * 80)
    
    project_root = Path('.')
    
    # Chercher tous les fichiers Python
    python_files = []
    for ext in ['*.py', '*.jsx', '*.js']:
        python_files.extend(project_root.rglob(ext))
    
    # Filtrer les fichiers à ignorer
    python_files = [f for f in python_files if not should_ignore_file(f)]
    
    print(f"\n📂 Analyse de {len(python_files)} fichiers...\n")
    
    all_references = []
    files_with_refs = {}
    
    for file_path in python_files:
        refs = find_references(file_path)
        if refs:
            all_references.extend(refs)
            files_with_refs[str(file_path)] = refs
    
    # Grouper par ancien fichier
    by_old_file = {}
    for ref in all_references:
        old_file = ref['old_file']
        if old_file not in by_old_file:
            by_old_file[old_file] = []
        by_old_file[old_file].append(ref)
    
    # Afficher les résultats
    print("📊 RÉSULTATS PAR ANCIEN FICHIER:\n")
    
    for old_file, refs in sorted(by_old_file.items()):
        print(f"🔸 {old_file}: {len(refs)} références")
        
        # Grouper par fichier
        by_file = {}
        for ref in refs:
            file = ref['file']
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(ref)
        
        for file, file_refs in sorted(by_file.items()):
            print(f"   📄 {file}")
            for ref in file_refs[:3]:  # Limiter à 3 exemples
                print(f"      Ligne {ref['line']}: {ref['content'][:80]}")
            if len(file_refs) > 3:
                print(f"      ... et {len(file_refs) - 3} autres références")
        print()
    
    # Résumé
    print("=" * 80)
    print("📋 RÉSUMÉ")
    print("=" * 80)
    print(f"Total fichiers analysés: {len(python_files)}")
    print(f"Fichiers avec références: {len(files_with_refs)}")
    print(f"Total références trouvées: {len(all_references)}")
    
    print("\n💡 RECOMMANDATIONS:")
    print("   1. Migrer ces scripts vers data/all_apartments.json")
    print("   2. Utiliser load_apartments_data() depuis backend.api.apartments")
    print("   3. Ou charger directement depuis data/all_apartments.json")

if __name__ == "__main__":
    main()
