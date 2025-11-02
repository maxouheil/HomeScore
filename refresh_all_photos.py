#!/usr/bin/env python3
"""
Script maître pour supprimer toutes les photos existantes et re-télécharger
toutes les photos avec numérotation correcte (photo_1.jpg, photo_2.jpg, etc.)
"""

import asyncio
import sys
from delete_all_photos import delete_all_photos
from redownload_all_photos import redownload_all_photos

async def main():
    """Fonction principale qui effectue les deux opérations"""
    print("🔄 REFRESH COMPLET DES PHOTOS")
    print("=" * 60)
    print("Cette opération va:")
    print("1. Supprimer toutes les photos existantes dans data/photos et data/photos_v2")
    print("2. Re-télécharger toutes les photos depuis all_apartments_scores.json")
    print("3. Numéroter correctement les photos (photo_1.jpg, photo_2.jpg, etc.)")
    print()
    
    # Étape 1: Supprimer toutes les photos existantes
    print("📋 ÉTAPE 1: SUPPRESSION DES PHOTOS EXISTANTES")
    print("-" * 60)
    try:
        deleted_count = delete_all_photos()
        print(f"✅ {deleted_count} fichiers supprimés\n")
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        sys.exit(1)
    
    # Étape 2: Re-télécharger toutes les photos
    print("📋 ÉTAPE 2: RE-TÉLÉCHARGEMENT DES PHOTOS")
    print("-" * 60)
    try:
        await redownload_all_photos()
        print("\n✅ Re-téléchargement terminé avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors du re-téléchargement: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 REFRESH COMPLET TERMINÉ AVEC SUCCÈS!")
    print("=" * 60)

if __name__ == "__main__":
    # Exécuter automatiquement sans confirmation (script batch)
    asyncio.run(main())


