#!/usr/bin/env python3
"""
Script pour forcer le rechargement du backend en touchant les fichiers modifiés
"""

import os
import time

def touch_file(file_path):
    """Touche un fichier pour forcer le rechargement"""
    if os.path.exists(file_path):
        os.utime(file_path, None)
        print(f"✅ Touché: {file_path}")
        return True
    else:
        print(f"⚠️ Fichier non trouvé: {file_path}")
        return False

def main():
    print("🔄 Forçage du rechargement du backend...")
    print("=" * 60)
    
    # Toucher les fichiers modifiés pour forcer le rechargement avec --reload
    files_to_touch = [
        'alert_scoring.py',
        'backend/api/alerts.py',
        'backend/api/apartments.py',
        'backend/main.py'  # Toucher le main pour forcer le rechargement complet
    ]
    
    for file_path in files_to_touch:
        touch_file(file_path)
    
    print("\n✅ Fichiers touchés")
    print("💡 Le backend devrait se recharger automatiquement (si --reload est activé)")
    print("💡 Sinon, redémarrez manuellement le backend")
    print("\n📋 Pour redémarrer manuellement:")
    print("   1. Arrêtez le backend (Ctrl+C dans le terminal où il tourne)")
    print("   2. Relancez: python3 start_backend.py")

if __name__ == "__main__":
    main()


