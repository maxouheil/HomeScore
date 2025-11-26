#!/usr/bin/env python3
"""
Script de monitoring pour surveiller le scraping en cours
"""

import time
import os
import json
from pathlib import Path


def check_scraping_status():
    """Vérifie l'état du scraping"""
    print("🔍 ÉTAT DU SCRAPING PARIS")
    print("=" * 60)
    
    # 1. Vérifier si le processus tourne
    pid_file = Path('/tmp/scrape_paris_pid.txt')
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Vérifier si le processus existe
            if os.path.exists(f'/proc/{pid}'):  # Linux
                print(f"✅ Processus actif (PID: {pid})")
            elif os.system(f'ps -p {pid} > /dev/null 2>&1') == 0:  # macOS/Unix
                print(f"✅ Processus actif (PID: {pid})")
            else:
                print(f"⚠️  Processus terminé (PID: {pid})")
        except:
            print("⚠️  Impossible de vérifier le PID")
    else:
        print("⚠️  Aucun PID trouvé")
    
    # 2. Vérifier les logs
    log_file = Path('/tmp/scrape_paris_output.log')
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"\n📄 Dernières lignes du log ({len(lines)} lignes total):")
                    print("-" * 60)
                    for line in lines[-10:]:
                        print(line.rstrip())
                else:
                    print("\n📄 Log vide")
        except Exception as e:
            print(f"\n⚠️  Erreur lecture log: {e}")
    else:
        print("\n⚠️  Aucun log trouvé")
    
    # 3. Vérifier les données récupérées
    paris_file = Path('data/paris_apartments.json')
    if paris_file.exists():
        try:
            with open(paris_file, 'r') as f:
                data = json.load(f)
                print(f"\n📊 Données actuelles:")
                print(f"   ✅ {len(data)} appartements dans paris_apartments.json")
                
                # Compter les tokens uniques
                tokens = set()
                for apt in data:
                    url = apt.get('url', '')
                    if 'token=' in url:
                        import re
                        match = re.search(r'token=([a-f0-9]{32})', url)
                        if match:
                            tokens.add(match.group(1))
                
                print(f"   🔑 {len(tokens)} alerte(s) utilisée(s)")
                
                # Vérifier la date de modification
                mtime = paris_file.stat().st_mtime
                import datetime
                mod_time = datetime.datetime.fromtimestamp(mtime)
                print(f"   📅 Dernière modification: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
        except Exception as e:
            print(f"\n⚠️  Erreur lecture données: {e}")
    else:
        print("\n⚠️  Fichier paris_apartments.json n'existe pas encore")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_scraping_status()



