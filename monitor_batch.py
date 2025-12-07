#!/usr/bin/env python3
"""
Script de monitoring du batch scraper
Affiche le progrès en temps réel
"""

import json
import os
import time
from datetime import datetime

def monitor_batch_progress():
    """Surveille le progrès du batch scraper"""
    print("📊 MONITORING DU BATCH SCRAPER")
    print("=" * 50)
    
    # Dossiers à surveiller
    apartments_dir = "data/appartements"
    batch_results_dir = "data/batch_results"
    
    print(f"📁 Dossier appartements: {apartments_dir}")
    print(f"📁 Dossier résultats: {batch_results_dir}")
    print()
    
    # Compter les appartements scrapés
    if os.path.exists(apartments_dir):
        apartment_files = [f for f in os.listdir(apartments_dir) if f.endswith('.json')]
        print(f"🏠 Appartements scrapés: {len(apartment_files)}")
        
        # Analyser les derniers appartements
        if apartment_files:
            print(f"\n📈 DERNIERS APPARTEMENTS:")
            apartment_files.sort(key=lambda x: os.path.getmtime(os.path.join(apartments_dir, x)), reverse=True)
            
            for i, file in enumerate(apartment_files[:5], 1):
                file_path = os.path.join(apartments_dir, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"   {i}. {data.get('id', 'N/A')} - {data.get('titre', 'N/A')}")
                    print(f"      Prix: {data.get('prix', 'N/A')}€")
                    print(f"      Surface: {data.get('surface', 'N/A')}")
                    
                    # Vérifier l'analyse de style
                    style_analysis = data.get('style_analysis')
                    if style_analysis:
                        style = style_analysis.get('style', {}).get('type', 'N/A')
                        cuisine = style_analysis.get('cuisine', {}).get('ouverte', False)
                        luminosite = style_analysis.get('luminosite', {}).get('type', 'N/A')
                        print(f"      Style: {style}, Cuisine: {'Ouverte' if cuisine else 'Fermée'}, Luminosité: {luminosite}")
                    else:
                        print(f"      Style: Non analysé")
                    print()
                    
                except Exception as e:
                    print(f"   {i}. {file} - Erreur lecture: {e}")
    else:
        print("❌ Dossier appartements non trouvé")
    
    # Vérifier les résultats de batch
    if os.path.exists(batch_results_dir):
        summary_files = [f for f in os.listdir(batch_results_dir) if f.startswith('summary_')]
        if summary_files:
            latest_summary = max(summary_files, key=lambda x: os.path.getmtime(os.path.join(batch_results_dir, x)))
            summary_path = os.path.join(batch_results_dir, latest_summary)
            
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                print(f"📊 RÉSUMÉ BATCH (dernier):")
                print(f"   Timestamp: {summary.get('timestamp', 'N/A')}")
                print(f"   Total appartements: {summary.get('total_apartments', 0)}")
                print(f"   Succès: {summary.get('successful', 0)}")
                print(f"   Erreurs: {summary.get('errors', 0)}")
                
                # Statistiques des styles
                apartments = summary.get('apartments', [])
                if apartments:
                    styles = {}
                    cuisines_ouvertes = 0
                    luminosites = {}
                    
                    for apt in apartments:
                        style_analysis = apt.get('style_analysis', {})
                        if style_analysis:
                            style = style_analysis.get('style', {}).get('type', 'inconnu')
                            styles[style] = styles.get(style, 0) + 1
                            
                            if style_analysis.get('cuisine', {}).get('ouverte', False):
                                cuisines_ouvertes += 1
                            
                            luminosite = style_analysis.get('luminosite', {}).get('type', 'inconnue')
                            luminosites[luminosite] = luminosites.get(luminosite, 0) + 1
                    
                    print(f"\n📈 STATISTIQUES:")
                    print(f"   Styles: {styles}")
                    print(f"   Cuisines ouvertes: {cuisines_ouvertes}/{len(apartments)} ({cuisines_ouvertes/len(apartments)*100:.1f}%)")
                    print(f"   Luminosités: {luminosites}")
                
            except Exception as e:
                print(f"❌ Erreur lecture résumé: {e}")
        else:
            print("📊 Aucun résumé de batch trouvé")
    else:
        print("❌ Dossier résultats non trouvé")

def watch_mode():
    """Mode surveillance continue"""
    print("👀 MODE SURVEILLANCE CONTINUE")
    print("Appuyez sur Ctrl+C pour arrêter")
    print()
    
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            monitor_batch_progress()
            print(f"\n⏰ Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")
            print("Appuyez sur Ctrl+C pour arrêter...")
            time.sleep(10)  # Mise à jour toutes les 10 secondes
            
    except KeyboardInterrupt:
        print("\n👋 Surveillance arrêtée")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        watch_mode()
    else:
        monitor_batch_progress()
