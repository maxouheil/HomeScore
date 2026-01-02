#!/usr/bin/env python3
"""
Script pour invalider le cache et forcer le recalcul des scores d'alertes
"""

import requests
import sys

def invalidate_cache():
    """Invalide le cache des appartements"""
    try:
        response = requests.post("http://localhost:8000/api/apartments/invalidate-cache")
        if response.status_code == 200:
            print("✅ Cache des appartements invalidé")
            return True
        else:
            print(f"❌ Erreur invalidation cache: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de l'invalidation du cache: {e}")
        print("   Assurez-vous que le backend est démarré sur http://localhost:8000")
        return False

def main():
    print("🔄 Invalidation du cache et recalcul des scores d'alertes...")
    print("=" * 60)
    
    if invalidate_cache():
        print("\n✅ Cache invalidé avec succès")
        print("💡 Les scores d'alertes seront recalculés automatiquement lors de la prochaine requête")
        print("💡 Rafraîchissez la page dans votre navigateur pour voir les nouveaux scores")
    else:
        print("\n❌ Échec de l'invalidation du cache")
        sys.exit(1)

if __name__ == "__main__":
    main()


