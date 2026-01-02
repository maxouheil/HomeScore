#!/usr/bin/env python3
"""
Script pour planifier l'exécution quotidienne de fetch_jinka_apartments.py
Peut être utilisé avec schedule Python ou comme wrapper pour cron
"""

import sys
import schedule
import time
from datetime import datetime
from fetch_jinka_apartments import fetch_new_apartments


def run_fetch():
    """Exécute la récupération des appartements"""
    print(f"\n{'='*80}")
    print(f"🕐 EXÉCUTION PLANIFIÉE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        result = fetch_new_apartments(download_photos=True)
        
        if result['success']:
            print(f"\n✅ Succès: {result['message']}")
            return 0
        else:
            print(f"\n⚠️  Avertissement: {result.get('message', 'Aucun appartement trouvé')}")
            return 0  # Ne pas échouer si aucun appartement trouvé
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Planifie l\'exécution quotidienne de fetch_jinka_apartments.py'
    )
    parser.add_argument(
        '--time',
        default='09:00',
        help='Heure d\'exécution quotidienne (format HH:MM, défaut: 09:00)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Exécuter une seule fois immédiatement (pour cron)'
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Exécuter en mode daemon avec schedule Python'
    )
    
    args = parser.parse_args()
    
    if args.once:
        # Mode cron: exécuter une fois et quitter
        sys.exit(run_fetch())
    
    elif args.daemon:
        # Mode daemon avec schedule Python
        print(f"🔄 Planification de l'exécution quotidienne à {args.time}")
        print("   Appuyez sur Ctrl+C pour arrêter")
        print()
        
        schedule.every().day.at(args.time).do(run_fetch)
        
        # Exécuter immédiatement au démarrage
        print("🚀 Exécution immédiate...")
        run_fetch()
        
        # Boucle principale
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier toutes les minutes
        except KeyboardInterrupt:
            print("\n\n👋 Arrêt du daemon")
            sys.exit(0)
    
    else:
        # Par défaut, exécuter une fois
        print("💡 Mode par défaut: exécution unique")
        print("   Utilisez --daemon pour un mode continu avec schedule")
        print("   Utilisez --once pour une exécution unique (recommandé pour cron)")
        print()
        sys.exit(run_fetch())


if __name__ == "__main__":
    main()

