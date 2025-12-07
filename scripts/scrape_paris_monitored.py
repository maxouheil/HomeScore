#!/usr/bin/env python3
"""
Version surveillée du scraping Paris avec timeout et monitoring
"""

import asyncio
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.scrape_all_paris import scrape_all_paris_apartments
import json


# Flag pour arrêter proprement
stop_requested = False


def signal_handler(sig, frame):
    """Gère l'interruption (Ctrl+C)"""
    global stop_requested
    print("\n\n⚠️  INTERRUPTION DEMANDÉE")
    print("Arrêt en cours...")
    stop_requested = True
    sys.exit(0)


async def monitored_scrape():
    """Scraping surveillé avec timeout"""
    global stop_requested
    
    # Enregistrer le handler pour Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 SCRAPING PARIS - VERSION SURVEILLÉE")
    print("=" * 60)
    print("⏱️  Timeout: 30 minutes maximum")
    print("📊 Mise à jour toutes les 30 secondes")
    print("⚠️  Appuyez sur Ctrl+C pour arrêter proprement")
    print()
    
    # Charger les tokens depuis alert_tokens_auto.json
    alert_tokens_auto_file = Path('data/alert_tokens_auto.json')
    alert_tokens = None
    
    if alert_tokens_auto_file.exists():
        try:
            with open(alert_tokens_auto_file, 'r', encoding='utf-8') as f:
                alerts_data = json.load(f)
                if isinstance(alerts_data, list) and len(alerts_data) > 0:
                    alert_tokens = [alert.get('token') or alert.get('id') for alert in alerts_data if alert.get('token') or alert.get('id')]
                    print(f"✅ {len(alert_tokens)} alertes chargées depuis alert_tokens_auto.json")
        except Exception as e:
            print(f"⚠️  Erreur lecture alert_tokens_auto.json: {e}")
    
    if not alert_tokens:
        print("❌ Aucune alerte trouvée. Exécutez d'abord: python scripts/check_alerts.py")
        return
    
    print(f"\n📋 {len(alert_tokens)} alertes à scraper")
    print("=" * 60)
    print()
    
    try:
        # Lancer le scraping avec timeout de 30 minutes
        apartments = await asyncio.wait_for(
            scrape_all_paris_apartments(
                alert_tokens=alert_tokens,
                max_pages_per_alert=50
            ),
            timeout=1800  # 30 minutes
        )
        
        if apartments:
            print(f"\n🎉 SCRAPING TERMINÉ AVEC SUCCÈS!")
            print(f"   ✅ {len(apartments)} appartements Paris récupérés")
            print(f"   💾 Données sauvegardées: data/paris_apartments.json")
        else:
            print("\n⚠️  Aucun appartement récupéré")
            
    except asyncio.TimeoutError:
        print("\n⏱️  TIMEOUT: Le scraping a pris plus de 30 minutes")
        print("   Le script a été arrêté pour éviter un blocage")
        print("   Les données partiellement récupérées sont sauvegardées")
        
    except KeyboardInterrupt:
        print("\n⚠️  INTERRUPTION PAR L'UTILISATEUR")
        print("   Arrêt propre du script")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(monitored_scrape())
    except KeyboardInterrupt:
        print("\n\n⚠️  Script arrêté par l'utilisateur")
        sys.exit(0)



