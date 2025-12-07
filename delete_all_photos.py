#!/usr/bin/env python3
"""
Script pour supprimer toutes les photos existantes dans data/photos et data/photos_v2
"""

import os
import shutil

def delete_all_photos():
    """Supprime toutes les photos existantes"""
    print("🗑️  SUPPRESSION DE TOUTES LES PHOTOS EXISTANTES")
    print("=" * 60)
    
    # Dossiers à nettoyer
    photo_dirs = [
        "data/photos",
        "data/photos_v2"
    ]
    
    deleted_count = 0
    deleted_dirs = []
    
    for photo_dir in photo_dirs:
        if os.path.exists(photo_dir):
            print(f"\n📁 Nettoyage de {photo_dir}...")
            
            # Lister tous les fichiers et dossiers
            items = []
            for root, dirs, files in os.walk(photo_dir):
                for file in files:
                    items.append(os.path.join(root, file))
                for dir_name in dirs:
                    items.append(os.path.join(root, dir_name))
            
            # Compter les fichiers images
            image_files = [item for item in items if os.path.isfile(item) and item.lower().endswith(('.jpg', '.jpeg', '.png'))]
            deleted_count += len(image_files)
            
            # Supprimer le dossier entier
            try:
                shutil.rmtree(photo_dir)
                deleted_dirs.append(photo_dir)
                print(f"   ✅ {len(image_files)} fichiers supprimés")
            except Exception as e:
                print(f"   ❌ Erreur lors de la suppression: {e}")
        else:
            print(f"\n📁 {photo_dir} n'existe pas (déjà vide)")
    
    print(f"\n🎉 SUPPRESSION TERMINÉE")
    print(f"   📁 Dossiers supprimés: {len(deleted_dirs)}")
    print(f"   📸 Fichiers images supprimés: {deleted_count}")
    print(f"\n✅ Toutes les photos ont été supprimées avec succès!")
    
    return deleted_count

if __name__ == "__main__":
    # Demander confirmation seulement si exécuté directement
    print("⚠️  ATTENTION: Cette action va supprimer TOUTES les photos existantes!")
    print("   - data/photos/")
    print("   - data/photos_v2/")
    print()
    response = input("Continuer? (oui/non): ")
    
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        delete_all_photos()
    else:
        print("❌ Opération annulée")

