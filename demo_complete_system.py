#!/usr/bin/env python3
"""
Démonstration complète du système HomeScore
- Téléchargement des photos
- Génération du rapport HTML
- Statistiques finales
"""

import asyncio
import json
import os
from datetime import datetime
from download_apartment_photos import batch_download_photos
from generate_scorecard_html import main as generate_html

# Liste des URLs d'appartements
apartment_urls = [
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90129925&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=78267327&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92125826&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90466722&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=89529151&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92274287&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91005791&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=88404156&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92075365&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92008125&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91908884&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91658092&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=89473319&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=84210379&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91644200&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=85653922&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
    "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=75507606&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
]

def get_photo_statistics():
    """Calcule les statistiques des photos téléchargées"""
    photos_dir = "data/photos"
    if not os.path.exists(photos_dir):
        return {"total_apartments": 0, "total_photos": 0, "apartments_with_photos": 0}
    
    total_apartments = 0
    total_photos = 0
    apartments_with_photos = 0
    
    for apartment_id in os.listdir(photos_dir):
        apartment_path = os.path.join(photos_dir, apartment_id)
        if os.path.isdir(apartment_path):
            total_apartments += 1
            photo_count = len([f for f in os.listdir(apartment_path) if f.endswith(('.jpg', '.jpeg', '.png'))])
            if photo_count > 0:
                apartments_with_photos += 1
                total_photos += photo_count
    
    return {
        "total_apartments": total_apartments,
        "total_photos": total_photos,
        "apartments_with_photos": apartments_with_photos,
        "average_photos_per_apartment": round(total_photos / total_apartments, 1) if total_apartments > 0 else 0
    }

def get_file_sizes():
    """Calcule la taille totale des photos"""
    photos_dir = "data/photos"
    total_size = 0
    
    if os.path.exists(photos_dir):
        for apartment_id in os.listdir(photos_dir):
            apartment_path = os.path.join(photos_dir, apartment_id)
            if os.path.isdir(apartment_path):
                for filename in os.listdir(apartment_path):
                    if filename.endswith(('.jpg', '.jpeg', '.png')):
                        file_path = os.path.join(apartment_path, filename)
                        total_size += os.path.getsize(file_path)
    
    # Convertir en MB
    size_mb = total_size / (1024 * 1024)
    return round(size_mb, 2)

async def main():
    """Fonction principale de démonstration"""
    print("🏠 DÉMONSTRATION COMPLÈTE DU SYSTÈME HOMESCORE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    print()
    
    # 1. Statistiques des photos existantes
    print("📊 ÉTAT ACTUEL DES PHOTOS")
    print("-" * 30)
    stats = get_photo_statistics()
    print(f"   🏠 Appartements avec photos: {stats['apartments_with_photos']}/{stats['total_apartments']}")
    print(f"   📸 Total photos téléchargées: {stats['total_photos']}")
    print(f"   📊 Moyenne photos/appartement: {stats['average_photos_per_apartment']}")
    print(f"   💾 Taille totale: {get_file_sizes()} MB")
    print()
    
    # 2. Vérifier si on a besoin de télécharger plus de photos
    if stats['apartments_with_photos'] < len(apartment_urls):
        print("📥 TÉLÉCHARGEMENT DES PHOTOS MANQUANTES")
        print("-" * 40)
        print(f"   🎯 {len(apartment_urls)} appartements à traiter")
        print(f"   📸 3-4 photos par appartement maximum")
        print()
        
        # Télécharger les photos
        results = await batch_download_photos(apartment_urls)
        
        print(f"✅ Téléchargement terminé: {len(results)} appartements traités")
        print()
    else:
        print("✅ Toutes les photos sont déjà téléchargées")
        print()
    
    # 3. Générer le rapport HTML
    print("📄 GÉNÉRATION DU RAPPORT HTML")
    print("-" * 35)
    generate_html()
    print()
    
    # 4. Statistiques finales
    print("📊 STATISTIQUES FINALES")
    print("-" * 25)
    final_stats = get_photo_statistics()
    print(f"   🏠 Appartements traités: {final_stats['total_apartments']}")
    print(f"   📸 Photos téléchargées: {final_stats['total_photos']}")
    print(f"   📊 Moyenne photos/appartement: {final_stats['average_photos_per_apartment']}")
    print(f"   💾 Taille totale: {get_file_sizes()} MB")
    print()
    
    # 5. Informations sur les fichiers générés
    print("📁 FICHIERS GÉNÉRÉS")
    print("-" * 20)
    print(f"   📄 Rapport HTML: output/homepage.html")
    print(f"   📸 Photos: data/photos/")
    print(f"   📊 Métadonnées: data/photos_metadata/")
    print()
    
    print("🎉 DÉMONSTRATION TERMINÉE !")
    print("🌐 Ouvrez output/homepage.html dans votre navigateur")

if __name__ == "__main__":
    asyncio.run(main())