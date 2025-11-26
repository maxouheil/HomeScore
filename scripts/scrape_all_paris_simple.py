#!/usr/bin/env python3
"""
Version simplifiée du scraping Paris - Utilise fetch_all_apartments_api.py comme base
Puis filtre pour Paris
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrape_jinka_api import JinkaAPIScraper
from photo_manager import PhotoManager


def is_paris_apartment(apartment: Dict) -> bool:
    """Vérifie si un appartement est à Paris"""
    # Vérifier le code postal depuis _api_data
    api_data = apartment.get('_api_data', {})
    postal_code = api_data.get('postal_code', '')
    
    if postal_code and postal_code.startswith('75'):
        return True
    
    # Vérifier la localisation
    localisation = apartment.get('localisation', '').lower()
    city = api_data.get('city', '').lower()
    
    if 'paris' in localisation or 'paris' in city:
        return True
    
    # Vérifier le titre
    titre = apartment.get('titre', '').lower()
    if 'paris' in titre:
        return True
    
    return False


async def main():
    """Fonction principale"""
    print("🏙️  SCRAPING COMPLET PARIS - VERSION SIMPLIFIÉE")
    print("=" * 60)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    alert_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
    
    scraper = JinkaAPIScraper()
    photo_manager = PhotoManager()
    
    try:
        # 1. Initialisation
        print("1️⃣ Initialisation...")
        await scraper.setup()
        print("✅ Client API initialisé\n")
        
        # 2. Connexion
        print("2️⃣ Connexion à Jinka...")
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        print("✅ Connexion réussie\n")
        
        # 3. Scraping de toutes les pages
        print("3️⃣ Scraping de toutes les pages...")
        print("-" * 60)
        start_time = datetime.now()
        
        apartments = await scraper.scrape_alert_page(
            alert_url,
            filter_type="all",
            max_pages=50
        )
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"\n📊 {len(apartments)} appartements récupérés en {elapsed_time:.1f}s")
        
        if not apartments:
            print("❌ Aucun appartement récupéré")
            return
        
        # 4. Filtrer Paris
        print("\n4️⃣ Filtrage Paris (75xxx)...")
        print("-" * 60)
        
        paris_apartments = [apt for apt in apartments if is_paris_apartment(apt)]
        print(f"✅ {len(paris_apartments)} appartements Paris trouvés")
        
        # 5. Télécharger les photos
        print("\n5️⃣ Téléchargement des photos...")
        print("-" * 60)
        
        photos_downloaded = 0
        for i, apt in enumerate(paris_apartments, 1):
            if i % 10 == 0:
                print(f"   [{i}/{len(paris_apartments)}] Traitement...")
            
            apt_with_photos = photo_manager.download_apartment_photos(apt, max_photos=10)
            paris_apartments[i-1] = apt_with_photos
            
            downloaded_count = sum(1 for p in apt_with_photos.get('photos', []) if p.get('local_path'))
            photos_downloaded += downloaded_count
        
        print(f"✅ {photos_downloaded} photos téléchargées")
        
        # 6. Sauvegarder
        print("\n6️⃣ Sauvegarde...")
        print("-" * 60)
        
        os.makedirs('data', exist_ok=True)
        output_file = 'data/paris_apartments.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(paris_apartments, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Données sauvegardées: {output_file}")
        
        # 7. Statistiques
        print("\n📊 STATISTIQUES FINALES")
        print("=" * 60)
        print(f"✅ Appartements Paris: {len(paris_apartments)}")
        print(f"📸 Photos téléchargées: {photos_downloaded}")
        print(f"⏰ Durée totale: {elapsed_time:.1f}s")
        print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n🎉 Scraping terminé avec succès!")
        print(f"   💾 Données: {output_file}")
        print(f"\n💡 Prochaine étape:")
        print(f"   python batch_analyze_paris.py")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

