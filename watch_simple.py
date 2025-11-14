#!/usr/bin/env python3
"""
Script simple de watch pour régénérer automatiquement le HTML
Quand les fichiers de données changent.
Utilise un polling simple (pas de dépendances externes).
"""

import time
import os
import subprocess
from pathlib import Path

def get_file_mtime(filepath):
    """Récupère le temps de modification d'un fichier"""
    try:
        return os.path.getmtime(filepath)
    except:
        return 0

def should_regenerate():
    """Vérifie si le HTML doit être régénéré"""
    files_to_watch = [
        'data/scores/all_apartments_scores.json',
        'data/scraped_apartments.json',
        'generate_scorecard_html.py'
    ]
    
    # Créer un fichier de cache pour stocker les derniers temps de modification
    cache_file = '.watch_cache.txt'
    
    # Lire le cache
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                for line in f:
                    if ':' in line:
                        filepath, mtime = line.strip().split(':', 1)
                        cache[filepath] = float(mtime)
        except:
            pass
    
    # Vérifier les fichiers
    regenerated = False
    for filepath in files_to_watch:
        if os.path.exists(filepath):
            current_mtime = get_file_mtime(filepath)
            cached_mtime = cache.get(filepath, 0)
            
            if current_mtime > cached_mtime:
                cache[filepath] = current_mtime
                regenerated = True
    
    # Sauvegarder le cache
    if regenerated:
        with open(cache_file, 'w') as f:
            for filepath, mtime in cache.items():
                f.write(f"{filepath}:{mtime}\n")
    
    return regenerated

def regenerate_html():
    """Régénère le HTML"""
    print("\n🔄 Régénération du HTML...")
    try:
        result = subprocess.run(
            ['python', 'generate_scorecard_html.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ HTML régénéré avec succès!")
            # Afficher seulement les lignes importantes
            for line in result.stdout.split('\n'):
                if line.strip() and ('✅' in line or '📋' in line):
                    print(line)
        else:
            print("❌ Erreur lors de la régénération:")
            print(result.stderr[:500])  # Limiter la sortie
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("👀 Surveillance des fichiers (polling toutes les 2 secondes)...")
    print("📁 Fichiers surveillés:")
    print("   - data/scores/all_apartments_scores.json")
    print("   - data/scraped_apartments.json")
    print("   - generate_scorecard_html.py")
    print("\n💡 Le HTML sera régénéré automatiquement lors des modifications")
    print("   Appuyez sur Ctrl+C pour arrêter\n")
    
    # Initialiser le cache avec les temps actuels
    files_to_watch = [
        'data/scores/all_apartments_scores.json',
        'data/scraped_apartments.json',
        'generate_scorecard_html.py'
    ]
    
    cache_file = '.watch_cache.txt'
    with open(cache_file, 'w') as f:
        for filepath in files_to_watch:
            if os.path.exists(filepath):
                mtime = get_file_mtime(filepath)
                f.write(f"{filepath}:{mtime}\n")
    
    try:
        while True:
            if should_regenerate():
                regenerate_html()
            time.sleep(2)  # Vérifier toutes les 2 secondes
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt de la surveillance...")
        # Nettoyer le cache
        if os.path.exists('.watch_cache.txt'):
            os.remove('.watch_cache.txt')
        print("✅ Surveillance arrêtée")

if __name__ == "__main__":
    main()







