#!/usr/bin/env python3
"""
Script d'automatisation quotidienne pour HomeScore
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from scrape_jinka import JinkaScraper
from score_appartement import score_all_apartments
from generate_html_report import generate_html_report

def load_config():
    """Charge la configuration"""
    config_file = 'config.json'
    default_config = {
        'alert_url': 'https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1',
        'min_score_threshold': 75,
        'notification_email': None,
        'max_apartments_per_run': 50
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return {**default_config, **config}
        except:
            pass
    
    return default_config

def save_config(config):
    """Sauvegarde la configuration"""
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_existing_apartments():
    """Charge la liste des appartements déjà scrapés"""
    apartments_dir = 'data/appartements'
    if not os.path.exists(apartments_dir):
        return set()
    
    apartment_files = [f for f in os.listdir(apartments_dir) if f.endswith('.json')]
    return {f.replace('.json', '') for f in apartment_files}

def find_new_apartments():
    """Trouve les nouveaux appartements depuis le dernier run"""
    existing = load_existing_apartments()
    
    # Charger la liste des appartements du dernier run
    last_run_file = 'data/last_run_apartments.json'
    if os.path.exists(last_run_file):
        try:
            with open(last_run_file, 'r', encoding='utf-8') as f:
                last_run_apartments = json.load(f)
        except:
            last_run_apartments = []
    else:
        last_run_apartments = []
    
    # Trouver les nouveaux
    new_apartments = existing - set(last_run_apartments)
    return list(new_apartments)

def save_last_run_apartments(apartment_ids):
    """Sauvegarde la liste des appartements du dernier run"""
    os.makedirs('data', exist_ok=True)
    with open('data/last_run_apartments.json', 'w', encoding='utf-8') as f:
        json.dump(apartment_ids, f, ensure_ascii=False, indent=2)

def log_message(message):
    """Log un message avec timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    
    # Sauvegarder dans un fichier de log
    os.makedirs('logs', exist_ok=True)
    log_file = f"logs/homescore_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

async def run_daily_scrape():
    """Exécute le scraping quotidien"""
    log_message("🚀 Début du scraping quotidien HomeScore")
    
    # Charger la configuration
    config = load_config()
    alert_url = config['alert_url']
    min_score_threshold = config['min_score_threshold']
    
    log_message(f"📋 Configuration: seuil score {min_score_threshold}, max {config['max_apartments_per_run']} appartements")
    
    # Phase 1: Scraping
    log_message("🏠 Phase 1: Scraping des appartements")
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        
        if await scraper.login():
            await scraper.scrape_alert_page(alert_url)
            log_message(f"✅ Scraping terminé: {len(scraper.apartments)} appartements")
            
            # Sauvegarder la liste des appartements
            apartment_ids = [apt['id'] for apt in scraper.apartments]
            save_last_run_apartments(apartment_ids)
        else:
            log_message("❌ Échec de la connexion Jinka")
            return False
    
    except Exception as e:
        log_message(f"❌ Erreur scraping: {e}")
        return False
    
    finally:
        await scraper.cleanup()
    
    # Phase 2: Scoring
    log_message("🤖 Phase 2: Scoring des appartements")
    try:
        if score_all_apartments():
            log_message("✅ Scoring terminé")
        else:
            log_message("❌ Erreur lors du scoring")
            return False
    except Exception as e:
        log_message(f"❌ Erreur scoring: {e}")
        return False
    
    # Phase 3: Génération du rapport
    log_message("📊 Phase 3: Génération du rapport")
    try:
        if generate_html_report():
            log_message("✅ Rapport généré")
        else:
            log_message("❌ Erreur génération rapport")
            return False
    except Exception as e:
        log_message(f"❌ Erreur rapport: {e}")
        return False
    
    # Phase 4: Détection des nouveaux appartements intéressants
    log_message("🔍 Phase 4: Analyse des nouveaux appartements")
    try:
        new_apartments = find_new_apartments()
        if new_apartments:
            log_message(f"🆕 {len(new_apartments)} nouveaux appartements détectés")
            
            # Analyser les scores des nouveaux appartements
            high_score_apartments = []
            for apartment_id in new_apartments:
                score_file = f"data/scores/{apartment_id}_score.json"
                if os.path.exists(score_file):
                    try:
                        with open(score_file, 'r', encoding='utf-8') as f:
                            score_data = json.load(f)
                        score_global = score_data.get('score_global', 0)
                        if score_global >= min_score_threshold:
                            high_score_apartments.append({
                                'id': apartment_id,
                                'score': score_global,
                                'url': f"https://www.jinka.fr/alert_result?ad={apartment_id}"
                            })
                    except:
                        pass
            
            if high_score_apartments:
                log_message(f"⭐️ {len(high_score_apartments)} appartements avec score ≥ {min_score_threshold}")
                for apt in sorted(high_score_apartments, key=lambda x: x['score'], reverse=True):
                    log_message(f"   🏠 {apt['id']}: {apt['score']}/100 - {apt['url']}")
            else:
                log_message("ℹ️ Aucun nouvel appartement avec score élevé")
        else:
            log_message("ℹ️ Aucun nouvel appartement détecté")
    
    except Exception as e:
        log_message(f"❌ Erreur analyse nouveaux appartements: {e}")
    
    log_message("✅ Scraping quotidien terminé avec succès")
    return True

def main():
    """Fonction principale"""
    if len(sys.argv) > 1 and sys.argv[1] == '--config':
        # Mode configuration
        config = load_config()
        print("Configuration actuelle:")
        print(json.dumps(config, ensure_ascii=False, indent=2))
        
        print("\nPour modifier la configuration, éditez le fichier config.json")
        return
    
    # Mode exécution normale
    try:
        success = asyncio.run(run_daily_scrape())
        if success:
            print("✅ HomeScore terminé avec succès")
            sys.exit(0)
        else:
            print("❌ HomeScore terminé avec des erreurs")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ HomeScore interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
