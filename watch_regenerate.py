#!/usr/bin/env python3
"""
Script de watch pour régénérer automatiquement le HTML
quand les données changent.
"""

import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class RegenerateHandler(FileSystemEventHandler):
    """Handler qui régénère le HTML quand les fichiers changent"""
    
    def __init__(self):
        self.last_regenerated = 0
        self.debounce_seconds = 2  # Attendre 2 secondes avant de régénérer
    
    def on_modified(self, event):
        """Appelé quand un fichier est modifié"""
        if event.is_directory:
            return
        
        # Vérifier si c'est un fichier de données ou le script de génération
        if event.src_path.endswith(('.json', '.py')):
            # Éviter les régénérations trop fréquentes (debounce)
            current_time = time.time()
            if current_time - self.last_regenerated < self.debounce_seconds:
                return
            
            self.last_regenerated = current_time
            print(f"\n🔄 Fichier modifié: {event.src_path}")
            print("📝 Régénération du HTML...")
            
            try:
                # Exécuter le script de génération
                result = subprocess.run(
                    ['python', 'generate_scorecard_html.py'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    print("✅ HTML régénéré avec succès!")
                    if result.stdout:
                        print(result.stdout)
                else:
                    print("❌ Erreur lors de la régénération:")
                    print(result.stderr)
            except Exception as e:
                print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("👀 Surveillance des fichiers...")
    print("📁 Fichiers surveillés:")
    print("   - data/scores/all_apartments_scores.json")
    print("   - data/scraped_apartments.json")
    print("   - generate_scorecard_html.py")
    print("\n💡 Le HTML sera régénéré automatiquement lors des modifications")
    print("   Appuyez sur Ctrl+C pour arrêter\n")
    
    event_handler = RegenerateHandler()
    observer = Observer()
    
    # Surveiller les fichiers de données et le script
    paths_to_watch = [
        'data/scores',
        'data',
        '.'
    ]
    
    for path in paths_to_watch:
        if os.path.exists(path):
            observer.schedule(event_handler, path, recursive=False)
            print(f"✓ Surveillance de: {path}")
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt de la surveillance...")
        observer.stop()
    
    observer.join()
    print("✅ Surveillance arrêtée")

if __name__ == "__main__":
    main()










