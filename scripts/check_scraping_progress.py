#!/usr/bin/env python3
"""
Script pour vérifier la progression du scraping en cours
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime


def check_progress():
    """Vérifie la progression du scraping"""
    pid_file = Path('/tmp/scrape_paris_pid.txt')
    log_file = Path('/tmp/scrape_paris_live.log')
    data_file = Path('data/paris_apartments.json')
    
    print("📊 PROGRESSION DU SCRAPING PARIS")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Vérifier le processus
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Vérifier si le processus tourne
            if os.system(f'ps -p {pid} > /dev/null 2>&1') == 0:
                print(f"✅ Processus actif (PID: {pid})")
            else:
                print(f"⚠️  Processus terminé (PID: {pid})")
        except:
            print("⚠️  Impossible de vérifier le PID")
    else:
        print("⚠️  Aucun PID trouvé")
    
    # 2. Vérifier les logs récents
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"\n📄 Dernières lignes du log ({len(lines)} lignes):")
                    print("-" * 60)
                    # Afficher les 15 dernières lignes
                    for line in lines[-15:]:
                        print(line.rstrip())
                else:
                    print("\n📄 Log vide")
        except Exception as e:
            print(f"\n⚠️  Erreur lecture log: {e}")
    else:
        print("\n⚠️  Aucun log trouvé")
    
    # 3. Vérifier les données
    if data_file.exists():
        try:
            stat = data_file.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            # Compter les tokens uniques
            tokens = set()
            for apt in data:
                url = apt.get('url', '')
                if 'token=' in url:
                    import re
                    match = re.search(r'token=([a-f0-9]{32})', url)
                    if match:
                        tokens.add(match.group(1))
            
            print(f"\n📊 DONNÉES ACTUELLES:")
            print("-" * 60)
            print(f"   ✅ {len(data)} appartements")
            print(f"   🔑 {len(tokens)} alerte(s) utilisée(s)")
            print(f"   📅 Dernière modif: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📏 Taille: {stat.st_size / 1024:.1f} KB")
            
            # Calculer le temps depuis la dernière modif
            time_diff = (datetime.now() - mtime).total_seconds()
            if time_diff < 60:
                print(f"   ⚡ Modifié il y a {int(time_diff)} secondes")
            elif time_diff < 3600:
                print(f"   ⚡ Modifié il y a {int(time_diff/60)} minutes")
            else:
                print(f"   ⏸️  Modifié il y a {int(time_diff/3600)} heures")
            
        except Exception as e:
            print(f"\n⚠️  Erreur lecture données: {e}")
    else:
        print("\n⚠️  Fichier paris_apartments.json n'existe pas encore")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_progress()



