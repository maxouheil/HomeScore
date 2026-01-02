#!/usr/bin/env python3
"""
Script de migration pour fusionner Desktop/HomeScore vers CURSOR/HomeScore
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

SOURCE_DIR = Path('/Users/sou/Desktop/HomeScore')
TARGET_DIR = Path('/Users/sou/Desktop/CURSOR/HomeScore')

def get_file_info(file_path):
    """Retourne les infos d'un fichier (taille, date modif)"""
    try:
        stat = file_path.stat()
        return {
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'exists': True
        }
    except:
        return {'exists': False}

def should_copy(source_file, target_file):
    """Détermine si on doit copier le fichier source vers la cible"""
    source_info = get_file_info(source_file)
    target_info = get_file_info(target_file)
    
    if not source_info['exists']:
        return False
    
    if not target_info['exists']:
        return True  # Le fichier n'existe pas dans la cible
    
    # Si le fichier source est plus récent, on le copie
    if source_info['mtime'] > target_info['mtime']:
        return True
    
    # Si les dates sont identiques mais les tailles différentes, on copie
    if source_info['mtime'] == target_info['mtime'] and source_info['size'] != target_info['size']:
        return True
    
    return False

def migrate_file(source_file, target_file):
    """Migre un fichier en préservant les métadonnées"""
    try:
        # Créer le répertoire parent si nécessaire
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Copier le fichier
        shutil.copy2(source_file, target_file)
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def migrate_directory(source_dir, target_dir, relative_path=Path('')):
    """Migre récursivement un répertoire"""
    source_path = source_dir / relative_path
    target_path = target_dir / relative_path
    
    if not source_path.exists():
        return
    
    if source_path.is_file():
        if should_copy(source_path, target_path):
            print(f"   📄 {relative_path}")
            migrate_file(source_path, target_path)
        else:
            print(f"   ⏭️  {relative_path} (déjà à jour ou plus récent dans CURSOR)")
        return
    
    if source_path.is_dir():
        # Ignorer certains répertoires
        if source_path.name in ['__pycache__', '.git', '.DS_Store', 'node_modules']:
            return
        
        # Créer le répertoire cible
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Parcourir les fichiers et sous-répertoires
        for item in source_path.iterdir():
            migrate_directory(source_dir, target_dir, relative_path / item.name)

def main():
    print("=" * 80)
    print("🔄 MIGRATION DE HomeScore VERS CURSOR/HomeScore")
    print("=" * 80)
    print()
    print(f"Source: {SOURCE_DIR}")
    print(f"Cible:  {TARGET_DIR}")
    print()
    
    if not SOURCE_DIR.exists():
        print(f"❌ Le répertoire source n'existe pas: {SOURCE_DIR}")
        return
    
    if not TARGET_DIR.exists():
        print(f"❌ Le répertoire cible n'existe pas: {TARGET_DIR}")
        print(f"   Création du répertoire...")
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    print("📋 Migration en cours...")
    print()
    
    # Compter les fichiers
    source_files = list(SOURCE_DIR.rglob('*'))
    source_files = [f for f in source_files if f.is_file() and '__pycache__' not in str(f)]
    
    print(f"📊 {len(source_files)} fichiers à vérifier")
    print()
    
    # Migrer
    migrated = 0
    skipped = 0
    errors = 0
    
    for source_file in source_files:
        relative_path = source_file.relative_to(SOURCE_DIR)
        target_file = TARGET_DIR / relative_path
        
        if should_copy(source_file, target_file):
            if migrate_file(source_file, target_file):
                migrated += 1
            else:
                errors += 1
        else:
            skipped += 1
    
    print()
    print("=" * 80)
    print("✅ MIGRATION TERMINÉE")
    print("=" * 80)
    print(f"📄 Fichiers copiés: {migrated}")
    print(f"⏭️  Fichiers ignorés (déjà à jour): {skipped}")
    print(f"❌ Erreurs: {errors}")
    print()
    print(f"💡 Tous les fichiers sont maintenant dans: {TARGET_DIR}")
    print()
    print("⚠️  Vous pouvez maintenant supprimer l'ancien dossier:")
    print(f"   rm -rf {SOURCE_DIR}")

if __name__ == "__main__":
    main()

