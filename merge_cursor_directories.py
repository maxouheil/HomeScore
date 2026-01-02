#!/usr/bin/env python3
"""
Script pour fusionner les données de deux dossiers CURSOR/HomeScore
- Source: /Users/sou/Desktop/CURSOR/HomeScore
- Destination: /Users/sou/Desktop/CURSOR/HomeScore
"""

import json
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

# Chemins
SOURCE_DIR = Path("/Users/sou/Desktop/CURSOR/HomeScore")
DEST_DIR = Path("/Users/sou/Desktop/CURSOR/HomeScore")

def merge_json_files(source_file: Path, dest_file: Path) -> Dict[str, Any]:
    """
    Fusionne deux fichiers JSON en évitant les doublons
    """
    result = {
        "merged": False,
        "source_count": 0,
        "dest_count": 0,
        "merged_count": 0,
        "added": 0,
        "skipped": 0
    }
    
    # Charger les fichiers
    source_data = None
    dest_data = None
    
    if source_file.exists():
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
                result["source_count"] = len(source_data) if isinstance(source_data, list) else 1
        except Exception as e:
            print(f"⚠️  Erreur lecture {source_file}: {e}")
            return result
    
    if dest_file.exists():
        try:
            with open(dest_file, 'r', encoding='utf-8') as f:
                dest_data = json.load(f)
                result["dest_count"] = len(dest_data) if isinstance(dest_data, list) else 1
        except Exception as e:
            print(f"⚠️  Erreur lecture {dest_file}: {e}")
            return result
    
    # Fusionner les données
    if isinstance(source_data, list) and isinstance(dest_data, list):
        # Fusionner deux listes
        dest_ids = {item.get('id') for item in dest_data if isinstance(item, dict) and 'id' in item}
        merged = dest_data.copy()
        
        for item in source_data:
            if isinstance(item, dict) and 'id' in item:
                if item['id'] not in dest_ids:
                    merged.append(item)
                    result["added"] += 1
                else:
                    result["skipped"] += 1
            else:
                merged.append(item)
                result["added"] += 1
        
        result["merged_count"] = len(merged)
        result["merged_data"] = merged
        result["merged"] = True
        
    elif isinstance(source_data, dict) and isinstance(dest_data, dict):
        # Fusionner deux dictionnaires
        merged = dest_data.copy()
        merged.update(source_data)
        result["merged_count"] = len(merged)
        result["merged_data"] = merged
        result["merged"] = True
        
    elif source_data is not None and dest_data is None:
        # Pas de fichier de destination, copier la source
        result["merged_data"] = source_data
        result["merged"] = True
        result["added"] = result["source_count"]
        
    return result


def copy_photos(source_photos_dir: Path, dest_photos_dir: Path) -> Dict[str, int]:
    """
    Copie les photos manquantes de source vers destination
    """
    stats = {
        "copied": 0,
        "skipped": 0,
        "errors": 0
    }
    
    if not source_photos_dir.exists():
        return stats
    
    dest_photos_dir.mkdir(parents=True, exist_ok=True)
    
    # Parcourir tous les fichiers photos dans la source
    for photo_file in source_photos_dir.rglob("*"):
        if photo_file.is_file() and photo_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            # Calculer le chemin relatif
            rel_path = photo_file.relative_to(source_photos_dir)
            dest_file = dest_photos_dir / rel_path
            
            # Copier seulement si le fichier n'existe pas déjà
            if not dest_file.exists():
                try:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(photo_file, dest_file)
                    stats["copied"] += 1
                except Exception as e:
                    print(f"⚠️  Erreur copie {photo_file} -> {dest_file}: {e}")
                    stats["errors"] += 1
            else:
                stats["skipped"] += 1
    
    return stats


def merge_all_data():
    """
    Fusionne toutes les données des deux dossiers
    """
    print("🔄 Début de la fusion des données...")
    print(f"📁 Source: {SOURCE_DIR}")
    print(f"📁 Destination: {DEST_DIR}")
    print()
    
    if not SOURCE_DIR.exists():
        print(f"❌ Le dossier source n'existe pas: {SOURCE_DIR}")
        return
    
    if not DEST_DIR.exists():
        print(f"❌ Le dossier destination n'existe pas: {DEST_DIR}")
        return
    
    # 1. Fusionner les fichiers JSON dans data/
    print("📄 Fusion des fichiers JSON...")
    source_data_dir = SOURCE_DIR / "data"
    dest_data_dir = DEST_DIR / "data"
    
    json_files_found = list(source_data_dir.rglob("*.json"))
    print(f"   Trouvé {len(json_files_found)} fichiers JSON dans la source")
    
    for source_json in json_files_found:
        # Ignorer les fichiers dans photos/ (on les gère séparément)
        if "photos" in str(source_json):
            continue
        
        rel_path = source_json.relative_to(source_data_dir)
        dest_json = dest_data_dir / rel_path
        
        print(f"\n   📄 {rel_path}")
        
        if dest_json.exists():
            # Fusionner
            merge_result = merge_json_files(source_json, dest_json)
            if merge_result["merged"]:
                # Sauvegarder le fichier fusionné
                dest_json.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_json, 'w', encoding='utf-8') as f:
                    json.dump(merge_result["merged_data"], f, indent=2, ensure_ascii=False)
                print(f"      ✅ Fusionné: {merge_result['added']} ajoutés, {merge_result['skipped']} ignorés")
            else:
                print(f"      ⚠️  Échec de la fusion")
        else:
            # Copier directement
            dest_json.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_json, dest_json)
            print(f"      ✅ Copié (nouveau fichier)")
    
    # 2. Copier les photos manquantes
    print("\n📸 Copie des photos manquantes...")
    source_photos_dir = SOURCE_DIR / "data" / "photos"
    dest_photos_dir = DEST_DIR / "data" / "photos"
    
    photo_stats = copy_photos(source_photos_dir, dest_photos_dir)
    print(f"   ✅ {photo_stats['copied']} photos copiées")
    print(f"   ⏭️  {photo_stats['skipped']} photos déjà présentes")
    if photo_stats['errors'] > 0:
        print(f"   ❌ {photo_stats['errors']} erreurs")
    
    # 3. Copier les autres fichiers/dossiers
    print("\n📦 Copie des autres fichiers...")
    
    # Cookies
    source_cookies = SOURCE_DIR / "data" / "cookies"
    dest_cookies = DEST_DIR / "data" / "cookies"
    if source_cookies.exists():
        for cookie_file in source_cookies.rglob("*"):
            if cookie_file.is_file():
                rel_path = cookie_file.relative_to(source_cookies)
                dest_file = dest_cookies / rel_path
                if not dest_file.exists():
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(cookie_file, dest_file)
                    print(f"   ✅ Cookie copié: {rel_path}")
    
    # Scores
    source_scores = SOURCE_DIR / "data" / "scores"
    dest_scores = DEST_DIR / "data" / "scores"
    if source_scores.exists():
        for score_file in source_scores.rglob("*"):
            if score_file.is_file():
                rel_path = score_file.relative_to(source_scores)
                dest_file = dest_scores / rel_path
                if not dest_file.exists():
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(score_file, dest_file)
                    print(f"   ✅ Score copié: {rel_path}")
    
    print("\n✅ Fusion terminée!")


if __name__ == "__main__":
    merge_all_data()
