#!/usr/bin/env python3
"""
Script pour invalider directement le cache des appartements
"""

import os
import sys

# Ajouter le chemin pour importer les modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def invalidate_cache_direct():
    """Invalide directement le cache Python"""
    try:
        # Importer le module apartments pour accéder au cache
        from backend.api import apartments
        
        # Invalider le cache
        apartments.invalidate_cache()
        print("✅ Cache invalidé directement dans le code Python")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'invalidation du cache: {e}")
        import traceback
        traceback.print_exc()
        return False

def touch_files():
    """Touche les fichiers pour forcer le rechargement"""
    try:
        scores_file = 'data/scores/all_apartments_scores.json'
        scraped_file = 'data/scraped_apartments.json'
        
        # Toucher les fichiers pour forcer le rechargement
        for file_path in [scores_file, scraped_file]:
            if os.path.exists(file_path):
                # Modifier le temps d'accès pour forcer le rechargement
                os.utime(file_path, None)
                print(f"✅ Fichier touché: {file_path}")
        
        return True
    except Exception as e:
        print(f"⚠️ Erreur lors du touch des fichiers: {e}")
        return False

def main():
    print("🔄 Invalidation du cache des appartements...")
    print("=" * 60)
    
    success = True
    
    # Invalider le cache Python
    if not invalidate_cache_direct():
        success = False
    
    # Toucher les fichiers
    if not touch_files():
        success = False
    
    if success:
        print("\n✅ Cache invalidé avec succès")
        print("💡 Redémarrez le backend pour que les changements prennent effet")
        print("💡 Ou attendez que le cache expire naturellement")
    else:
        print("\n⚠️ Certaines opérations ont échoué")
        sys.exit(1)

if __name__ == "__main__":
    main()


