#!/usr/bin/env python3
"""
Script pour nettoyer les photos en doublon/triplon
Garde seulement les 4 photos les plus récentes par appartement
"""

import os
import glob
from pathlib import Path

def cleanup_duplicate_photos():
    """Nettoie les photos en doublon dans data/photos/"""
    photos_dir = "data/photos"
    
    if not os.path.exists(photos_dir):
        print("❌ Le dossier data/photos n'existe pas")
        return
    
    total_deleted = 0
    total_kept = 0
    
    # Parcourir tous les dossiers d'appartements
    for apartment_dir in Path(photos_dir).iterdir():
        if not apartment_dir.is_dir():
            continue
        
        apartment_id = apartment_dir.name
        photo_files = list(apartment_dir.glob("photo_*.jpg"))
        
        if len(photo_files) <= 4:
            # Pas de doublons, on garde tout
            total_kept += len(photo_files)
            continue
        
        # Trier par date de modification (plus récent en premier)
        photo_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Garder les 4 plus récentes
        files_to_keep = photo_files[:4]
        files_to_delete = photo_files[4:]
        
        print(f"🏠 Appartement {apartment_id}:")
        print(f"   📸 {len(photo_files)} photos trouvées")
        print(f"   ✅ Garde: {len(files_to_keep)} photos (les plus récentes)")
        print(f"   🗑️  Supprime: {len(files_to_delete)} photos (doublons)")
        
        # Supprimer les doublons
        for file_to_delete in files_to_delete:
            try:
                file_size = file_to_delete.stat().st_size
                os.remove(file_to_delete)
                total_deleted += 1
                print(f"      🗑️  Supprimé: {file_to_delete.name} ({file_size:,} bytes)")
            except Exception as e:
                print(f"      ❌ Erreur suppression {file_to_delete.name}: {e}")
        
        total_kept += len(files_to_keep)
    
    print(f"\n✅ Nettoyage terminé !")
    print(f"   📸 Photos gardées: {total_kept}")
    print(f"   🗑️  Photos supprimées: {total_deleted}")

if __name__ == "__main__":
    print("🧹 NETTOYAGE DES PHOTOS EN DOUBLON")
    print("=" * 50)
    cleanup_duplicate_photos()




