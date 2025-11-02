#!/usr/bin/env python3
"""
Serveur HTTP avec auto-reload pour visualiser le scorecard HTML en temps réel.

Fonctionnalités:
- Serve un serveur HTTP local sur http://localhost:8000
- Surveille les fichiers et régénère automatiquement le HTML
- Auto-refresh du navigateur quand le HTML change (via WebSocket ou polling)
- Interface simple pour voir les changements en direct
"""

import time
import os
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    print("⚠️  watchdog non installé, utilisation du polling simple")
    print("   Installez avec: pip install watchdog")

class ScorecardHTTPHandler(SimpleHTTPRequestHandler):
    """Handler HTTP personnalisé avec auto-refresh"""
    
    def __init__(self, *args, watcher=None, **kwargs):
        self.watcher = watcher
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        """Ajoute les headers pour éviter le cache"""
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_GET(self):
        """Gère les requêtes GET"""
        if self.path == '/' or self.path == '/homepage.html':
            # Rediriger vers le fichier HTML
            self.path = '/output/homepage.html'
        
        # Servir les fichiers statiques
        return super().do_GET()
    
    def log_message(self, format, *args):
        """Désactive les logs verbeux"""
        pass

class ScorecardWatcherServer:
    """Serveur de watch avec HTTP"""
    
    def __init__(self, port=8000, debounce_seconds=2):
        self.port = port
        self.debounce_seconds = debounce_seconds
        self.last_regenerated = 0
        self.cache_file = '.watch_scorecard_cache.txt'
        self.files_to_watch = self._get_files_to_watch()
        self.http_server = None
        self.watcher_thread = None
        self.init_cache()
    
    def _get_files_to_watch(self):
        """Détermine tous les fichiers à surveiller"""
        files = []
        
        # Fichiers de données JSON
        data_files = [
            'data/scores/all_apartments_scores.json',
            'data/scraped_apartments.json',
        ]
        
        for filepath in data_files:
            if os.path.exists(filepath):
                files.append(filepath)
        
        # Fichiers Python backend
        python_files = [
            'generate_scorecard_html.py',
            'extract_baignoire.py',
            'analyze_photos.py',
            'analyze_apartment_style.py',
        ]
        
        for filepath in python_files:
            if os.path.exists(filepath):
                files.append(filepath)
        
        # Fichiers dans criteria/
        criteria_dir = Path('criteria')
        if criteria_dir.exists():
            for py_file in criteria_dir.glob('*.py'):
                files.append(str(py_file))
        
        # Fichiers de configuration
        config_files = [
            'scoring_config.json',
            'scoring_prompt.txt',
        ]
        
        for filepath in config_files:
            if os.path.exists(filepath):
                files.append(filepath)
        
        return files
    
    def init_cache(self):
        """Initialise le cache"""
        cache = {}
        for filepath in self.files_to_watch:
            if os.path.exists(filepath):
                cache[filepath] = os.path.getmtime(filepath)
        self.save_cache(cache)
    
    def load_cache(self):
        """Charge le cache"""
        cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            filepath, mtime = line.split(':', 1)
                            cache[filepath] = float(mtime)
            except:
                pass
        return cache
    
    def save_cache(self, cache):
        """Sauvegarde le cache"""
        try:
            with open(self.cache_file, 'w') as f:
                for filepath, mtime in cache.items():
                    f.write(f"{filepath}:{mtime}\n")
        except:
            pass
    
    def check_changes(self):
        """Vérifie si des fichiers ont changé"""
        cache = self.load_cache()
        changed_files = []
        
        for filepath in self.files_to_watch:
            if not os.path.exists(filepath):
                continue
            
            current_mtime = os.path.getmtime(filepath)
            cached_mtime = cache.get(filepath, 0)
            
            if current_mtime > cached_mtime:
                changed_files.append(filepath)
                cache[filepath] = current_mtime
        
        if changed_files:
            self.save_cache(cache)
        
        return changed_files
    
    def regenerate_html(self):
        """Régénère le HTML"""
        current_time = time.time()
        if current_time - self.last_regenerated < self.debounce_seconds:
            return False
        
        self.last_regenerated = current_time
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] 🔄 Régénération du HTML...", end=' ')
        
        try:
            result = subprocess.run(
                ['python', 'generate_scorecard_html.py'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✅")
                return True
            else:
                print("❌")
                print(f"   Erreur: {result.stderr[:200]}")
                return False
        except Exception as e:
            print(f"❌ ({e})")
            return False
    
    def watch_loop(self):
        """Boucle de surveillance"""
        while True:
            changed_files = self.check_changes()
            if changed_files:
                self.regenerate_html()
            time.sleep(1)
    
    def start_http_server(self):
        """Démarre le serveur HTTP"""
        os.chdir(Path(__file__).parent)
        
        handler = lambda *args, **kwargs: ScorecardHTTPHandler(*args, watcher=self, **kwargs)
        self.http_server = HTTPServer(('localhost', self.port), handler)
        
        print(f"🌐 Serveur HTTP démarré sur http://localhost:{self.port}")
        print(f"   Ouvrez http://localhost:{self.port}/output/homepage.html dans votre navigateur")
        
        # Ouvrir automatiquement le navigateur après 1 seconde
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{self.port}/output/homepage.html')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            self.http_server.serve_forever()
        except KeyboardInterrupt:
            pass
    
    def start(self):
        """Démarre le serveur et la surveillance"""
        print("🚀 SERVEUR DE DÉVELOPPEMENT SCORECARD")
        print("=" * 60)
        print("📁 Fichiers surveillés:")
        for filepath in sorted(self.files_to_watch):
            status = "✓" if os.path.exists(filepath) else "✗"
            print(f"   {status} {filepath}")
        print(f"\n⏱️  Régénération automatique activée")
        print(f"🌐 Serveur HTTP sur le port {self.port}")
        print("\n💡 Modifiez les fichiers pour voir les changements en direct")
        print("   Appuyez sur Ctrl+C pour arrêter\n")
        
        # Démarrer le thread de surveillance
        self.watcher_thread = threading.Thread(target=self.watch_loop, daemon=True)
        self.watcher_thread.start()
        
        # Démarrer le serveur HTTP (bloquant)
        self.start_http_server()
    
    def stop(self):
        """Arrête le serveur"""
        if self.http_server:
            self.http_server.shutdown()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

def main():
    """Fonction principale"""
    server = ScorecardWatcherServer(port=8000, debounce_seconds=2)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur...")
        server.stop()
        print("✅ Serveur arrêté")

if __name__ == "__main__":
    main()

