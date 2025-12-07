#!/usr/bin/env python3
"""
Script de lancement du batch scraper
Configuration facile pour scraper 40+ appartements
"""

import asyncio
from batch_scraper import BatchScraper

async def main():
    """Configuration et lancement du batch scraper"""
    
    print("🚀 BATCH SCRAPER HOMESCORE")
    print("=" * 50)
    print("Configuration optimisée pour 40+ appartements")
    print()
    
    # Configuration
    config = {
        # URL de ton dashboard d'alertes Jinka
        'alert_url': "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733",
        
        # Paramètres de scraping
        'pages_to_scrape': 1,         # Juste la page 1 pour commencer
        'max_apartments': 50,         # Maximum d'appartements
        'max_concurrent': 3,          # Appartements en parallèle
        'delay_between_pages': 2,     # Délai entre pages (secondes)
        'delay_between_apartments': 1 # Délai entre appartements (secondes)
    }
    
    print("📋 CONFIGURATION:")
    for key, value in config.items():
        print(f"   {key}: {value}")
    print()
    
    # Créer le batch scraper
    batch_scraper = BatchScraper(
        max_concurrent=config['max_concurrent'],
        max_apartments=config['max_apartments']
    )
    
    # Lancer le scraping
    try:
        await batch_scraper.scrape_alert_batch(
            config['alert_url'], 
            config['pages_to_scrape']
        )
        print("\n🎉 BATCH SCRAPING TERMINÉ AVEC SUCCÈS !")
        
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        print("\n📊 Vérifiez les résultats dans data/batch_results/")

if __name__ == "__main__":
    asyncio.run(main())
