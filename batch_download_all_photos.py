#!/usr/bin/env python3
"""
Téléchargement en batch de toutes les photos d'appartements
"""

import asyncio
from download_apartment_photos import batch_download_photos

# Liste des URLs d'appartements à traiter
apartment_urls = [
    # Première batch (7 appartements)
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90129925&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=78267327&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92125826&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90466722&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=89529151&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92274287&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91005791&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=88404156&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    
    # Deuxième batch (7 nouveaux appartements)
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92075365&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92008125&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91908884&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91658092&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=89473319&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=84210379&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91644200&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    
    # Troisième batch (2 nouveaux appartements)
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=85653922&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=75507606&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
]

async def main():
    """Fonction principale"""
    print(f"🚀 DÉMARRAGE DU TÉLÉCHARGEMENT BATCH")
    print(f"📊 {len(apartment_urls)} appartements à traiter")
    print(f"📸 3-4 photos par appartement maximum")
    print(f"💾 Sauvegarde dans data/photos/")
    
    # Lancer le téléchargement batch
    results = await batch_download_photos(apartment_urls)
    
    # Résumé final
    print(f"\n🎉 TÉLÉCHARGEMENT TERMINÉ !")
    print(f"✅ {len(results)} appartements traités avec succès")
    
    total_photos = sum(result['downloaded_photos'] for result in results)
    print(f"📸 {total_photos} photos téléchargées au total")
    
    # Afficher le détail par appartement
    for result in results:
        print(f"   🏠 Appartement {result['apartment_id']}: {result['downloaded_photos']} photos")

if __name__ == "__main__":
    asyncio.run(main())
