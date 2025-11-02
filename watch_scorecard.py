#!/usr/bin/env python3
"""
Script de watch amélioré pour régénérer automatiquement le scorecard HTML
quand les fichiers backend ou frontend changent.

Surveille:
- Fichiers de données JSON (scores, scraped_apartments)
- Fichiers Python backend (generate_scorecard_html.py, extract_baignoire.py, analyze_photos.py, etc.)
- Fichiers dans criteria/ (si utilisés)
- Fichiers de configuration (scoring_config.json, scoring_prompt.txt)
"""

import time
import os
import subprocess
from pathlib import Path
from datetime import datetime

class ScorecardWatcher:
    """Watcher intelligent pour le scorecard HTML"""
    
    def __init__(self, debounce_seconds=2):
        self.debounce_seconds = debounce_seconds
        self.last_regenerated = 0
        self.cache_file = '.watch_scorecard_cache.txt'
        self.files_to_watch = self._get_files_to_watch()
        self.init_cache()
    
    def _get_files_to_watch(self):
        """Détermine tous les fichiers à surveiller"""
        files = []
        
        # Fichiers de données JSON
        data_files = [
            'data/scores/all_apartments_scores.json',
            'data/scraped_apartments.json',
        ]
        
        # Vérifier si les fichiers existent
        for filepath in data_files:
            if os.path.exists(filepath):
                files.append(filepath)
        
        # Fichiers Python backend qui influencent la génération
        python_files = [
            'generate_scorecard_html.py',
            'scoring.py',  # Ajouté pour détecter les changements de règles de scoring
            'extract_baignoire.py',
            'analyze_photos.py',
            'analyze_apartment_style.py',
        ]
        
        for filepath in python_files:
            if os.path.exists(filepath):
                files.append(filepath)
        
        # Fichiers dans criteria/ si le dossier existe
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
        """Initialise le cache avec les temps de modification actuels"""
        cache = {}
        for filepath in self.files_to_watch:
            if os.path.exists(filepath):
                cache[filepath] = os.path.getmtime(filepath)
        
        self.save_cache(cache)
        return cache
    
    def load_cache(self):
        """Charge le cache depuis le fichier"""
        cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            filepath, mtime = line.split(':', 1)
                            cache[filepath] = float(mtime)
            except Exception as e:
                print(f"⚠️  Erreur lors du chargement du cache: {e}")
        return cache
    
    def save_cache(self, cache):
        """Sauvegarde le cache dans le fichier"""
        try:
            with open(self.cache_file, 'w') as f:
                for filepath, mtime in cache.items():
                    f.write(f"{filepath}:{mtime}\n")
        except Exception as e:
            print(f"⚠️  Erreur lors de la sauvegarde du cache: {e}")
    
    def get_file_mtime(self, filepath):
        """Récupère le temps de modification d'un fichier"""
        try:
            return os.path.getmtime(filepath)
        except:
            return 0
    
    def check_changes(self):
        """Vérifie si des fichiers ont changé"""
        cache = self.load_cache()
        changed_files = []
        
        # Vérifier tous les fichiers surveillés
        for filepath in self.files_to_watch:
            if not os.path.exists(filepath):
                continue
            
            current_mtime = self.get_file_mtime(filepath)
            cached_mtime = cache.get(filepath, 0)
            
            if current_mtime > cached_mtime:
                changed_files.append(filepath)
                cache[filepath] = current_mtime
        
        # Sauvegarder le cache mis à jour
        if changed_files:
            self.save_cache(cache)
        
        return changed_files
    
    def regenerate_html(self, changed_files=None):
        """Régénère le HTML, et recalcule les scores si nécessaire"""
        # Vérifier le debounce
        current_time = time.time()
        if current_time - self.last_regenerated < self.debounce_seconds:
            return False
        
        self.last_regenerated = current_time
        
        # Vérifier si scoring.py ou scoring_config.json ont changé
        needs_rescoring = False
        if changed_files:
            scoring_files = ['scoring.py', 'scoring_config.json']
            needs_rescoring = any(f in changed_files for f in scoring_files)
        
        # Recalculer les scores si nécessaire
        if needs_rescoring:
            print(f"\n{'='*60}")
            print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Recalcul des scores...")
            print(f"{'='*60}")
            
            try:
                # Utiliser homescore.py pour recalculer les scores
                result = subprocess.run(
                    ['python', 'homescore.py'],
                    capture_output=True,
                    text=True,
                    timeout=300  # Timeout de 5 minutes pour le scoring
                )
                
                if result.returncode == 0:
                    print("✅ Scores recalculés avec succès!")
                    # Afficher seulement les lignes importantes
                    for line in result.stdout.split('\n'):
                        if line.strip() and ('✅' in line or '📊' in line):
                            print(f"   {line}")
                else:
                    print("⚠️  Erreur lors du recalcul des scores (continuons quand même)")
                    error_lines = result.stderr.split('\n')[:5]
                    for line in error_lines:
                        if line.strip():
                            print(f"   {line}")
            except subprocess.TimeoutExpired:
                print("⚠️  Timeout lors du recalcul des scores (continuons quand même)")
            except Exception as e:
                print(f"⚠️  Erreur lors du recalcul: {e} (continuons quand même)")
        
        print(f"\n{'='*60}")
        print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Régénération du scorecard HTML...")
        print(f"{'='*60}")
        
        try:
            result = subprocess.run(
                ['python', 'generate_scorecard_html.py'],
                capture_output=True,
                text=True,
                timeout=120  # Timeout de 2 minutes
            )
            
            if result.returncode == 0:
                print("✅ HTML régénéré avec succès!")
                # Afficher seulement les lignes importantes
                for line in result.stdout.split('\n'):
                    if line.strip() and ('✅' in line or '📋' in line or '🏠' in line):
                        print(f"   {line}")
                return True
            else:
                print("❌ Erreur lors de la régénération:")
                error_lines = result.stderr.split('\n')[:10]  # Limiter à 10 lignes
                for line in error_lines:
                    if line.strip():
                        print(f"   {line}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Timeout: La régénération a pris trop de temps (>2min)")
            return False
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def watch(self, poll_interval=1):
        """Surveille les fichiers et régénère si nécessaire"""
        print("👀 SURVEILLANCE DU SCORECARD HTML")
        print("=" * 60)
        print("📁 Fichiers surveillés:")
        for filepath in sorted(self.files_to_watch):
            status = "✓" if os.path.exists(filepath) else "✗"
            print(f"   {status} {filepath}")
        print(f"\n⏱️  Intervalle de vérification: {poll_interval} seconde(s)")
        print(f"⏳ Debounce: {self.debounce_seconds} seconde(s)")
        print("\n💡 Le HTML sera régénéré automatiquement lors des modifications")
        print("   Appuyez sur Ctrl+C pour arrêter\n")
        
        try:
            while True:
                changed_files = self.check_changes()
                
                if changed_files:
                    print(f"\n📝 Fichiers modifiés:")
                    for filepath in changed_files:
                        print(f"   • {filepath}")
                    
                    self.regenerate_html(changed_files=changed_files)
                
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Arrêt de la surveillance...")
            # Nettoyer le cache
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            print("✅ Surveillance arrêtée")

def main():
    """Fonction principale"""
    watcher = ScorecardWatcher(debounce_seconds=2)
    watcher.watch(poll_interval=1)

if __name__ == "__main__":
    main()

