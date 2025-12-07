#!/usr/bin/env python3
"""
Script de développement unifié pour lancer backend et frontend
"""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Vérifie que les dépendances sont installées"""
    print("🔍 Vérification des dépendances...")
    
    # Vérifier FastAPI
    try:
        import fastapi
        print("  ✅ FastAPI installé")
    except ImportError:
        print("  ❌ FastAPI non installé")
        print("  💡 Exécutez: pip install -r requirements.txt")
        return False
    
    # Vérifier que Node.js est installé
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Node.js installé ({result.stdout.strip()})")
        else:
            print("  ❌ Node.js non installé")
            return False
    except FileNotFoundError:
        print("  ❌ Node.js non installé")
        print("  💡 Installez Node.js depuis https://nodejs.org/")
        return False
    
    # Vérifier que npm est installé
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ npm installé ({result.stdout.strip()})")
        else:
            print("  ❌ npm non installé")
            return False
    except FileNotFoundError:
        print("  ❌ npm non installé")
        return False
    
    return True

def install_frontend_dependencies():
    """Installe les dépendances du frontend si nécessaire"""
    frontend_dir = Path(__file__).parent / 'frontend'
    node_modules = frontend_dir / 'node_modules'
    
    if not node_modules.exists():
        print("📦 Installation des dépendances frontend...")
        try:
            subprocess.run(
                ['npm', 'install'],
                cwd=frontend_dir,
                check=True
            )
            print("  ✅ Dépendances frontend installées")
        except subprocess.CalledProcessError:
            print("  ❌ Erreur lors de l'installation des dépendances frontend")
            return False
    else:
        print("  ✅ Dépendances frontend déjà installées")
    
    return True

def start_backend():
    """Démarre le serveur backend FastAPI"""
    print("\n🚀 Démarrage du backend (port 8000)...")
    backend_process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    return backend_process

def start_frontend():
    """Démarre le serveur frontend Vite"""
    print("🚀 Démarrage du frontend (port 5173)...")
    frontend_dir = Path(__file__).parent / 'frontend'
    frontend_process = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    return frontend_process

def print_output(process, prefix):
    """Affiche la sortie d'un processus avec un préfixe"""
    for line in process.stdout:
        print(f"[{prefix}] {line}", end='')

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🏠 HomeScore - Serveur de développement")
    print("=" * 60)
    
    # Vérifier les dépendances
    if not check_dependencies():
        sys.exit(1)
    
    # Installer les dépendances frontend si nécessaire
    if not install_frontend_dependencies():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🚀 Démarrage des serveurs...")
    print("=" * 60)
    
    # Démarrer le backend
    backend_process = start_backend()
    
    # Attendre un peu pour que le backend démarre
    time.sleep(2)
    
    # Démarrer le frontend
    frontend_process = start_frontend()
    
    # Attendre un peu pour que le frontend démarre
    time.sleep(3)
    
    # Ouvrir le navigateur
    print("\n🌐 Ouverture du navigateur...")
    webbrowser.open('http://localhost:5173')
    
    print("\n" + "=" * 60)
    print("✅ Serveurs démarrés!")
    print("=" * 60)
    print("📊 Backend API: http://localhost:8000")
    print("🎨 Frontend: http://localhost:5173")
    print("\n💡 Appuyez sur Ctrl+C pour arrêter les serveurs\n")
    
    try:
        # Afficher les logs des deux processus
        import threading
        
        def log_backend():
            for line in backend_process.stdout:
                print(f"[BACKEND] {line}", end='')
        
        def log_frontend():
            for line in frontend_process.stdout:
                print(f"[FRONTEND] {line}", end='')
        
        backend_thread = threading.Thread(target=log_backend, daemon=True)
        frontend_thread = threading.Thread(target=log_frontend, daemon=True)
        
        backend_thread.start()
        frontend_thread.start()
        
        # Attendre que les processus se terminent
        backend_process.wait()
        frontend_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt des serveurs...")
        backend_process.terminate()
        frontend_process.terminate()
        
        # Attendre la fin propre
        backend_process.wait(timeout=5)
        frontend_process.wait(timeout=5)
        
        print("✅ Serveurs arrêtés")

if __name__ == "__main__":
    main()

