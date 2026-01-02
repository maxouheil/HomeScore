#!/usr/bin/env python3
"""
Script simple pour démarrer uniquement le backend API
"""

import subprocess
import sys
import os

def main():
    """Démarre le serveur backend FastAPI"""
    print("🚀 Démarrage du backend HomeScore API...")
    print("=" * 60)
    print("📊 Backend API: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("💡 Appuyez sur Ctrl+C pour arrêter")
    print("=" * 60)
    print()
    
    try:
        # Démarrer le serveur avec uvicorn
        # Le reload est désactivé par défaut pour éviter les rechargements constants
        # Activer avec RELOAD=true dans l'environnement si nécessaire
        reload_flag = ['--reload'] if os.getenv('RELOAD', 'false').lower() == 'true' else []
        subprocess.run(
            [
                sys.executable, 
                '-m', 
                'uvicorn', 
                'backend.main:app', 
                '--host', '0.0.0.0', 
                '--port', '8000'
            ] + reload_flag,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur backend...")
        print("✅ Serveur arrêté")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors du démarrage du serveur: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()






