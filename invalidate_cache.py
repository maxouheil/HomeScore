#!/usr/bin/env python3
"""
Script pour invalider le cache du backend et forcer le rechargement des données
"""

import requests
import sys

def invalidate_backend_cache():
    """Invalide le cache du backend via l'API"""
    try:
        response = requests.post('http://localhost:8000/api/apartments/invalidate-cache')
        if response.status_code == 200:
            print("✅ Cache backend invalidé avec succès")
            return True
        else:
            print(f"⚠️ Erreur lors de l'invalidation du cache: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️ Le serveur backend n'est pas démarré sur le port 8000")
        print("   Démarrez-le avec: python3 -m backend.main")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Invalidation du cache backend...")
    success = invalidate_backend_cache()
    sys.exit(0 if success else 1)



