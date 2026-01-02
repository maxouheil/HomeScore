#!/usr/bin/env python3
"""
Script pour récupérer les nouvelles données du 20e arrondissement uniquement
via l'API (appel unique pour toutes les pages)
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from scrape_jinka_api import JinkaAPIScraper
from photo_manager import PhotoManager
from api_data_adapter import adapt_api_to_scraped_format


def filter_20e_arrondissement(apartment: Dict[str, Any]) -> bool:
    """
    Filtre les appartements du 20e arrondissement
    
    Args:
        apartment: Données de l'appartement
    
    Returns:
        True si l'appartement est dans le 20e arrondissement
    """
    localisation = str(apartment.get('localisation', '')).lower()
    map_info = apartment.get('map_info', {}) or {}
    quartier = str(map_info.get('quartier', '')).lower()
    
    # Chercher des indices du 20e arrondissement
    indicators = ['20e', '20ème', '75020', '20e arrondissement', '20ème arrondissement']
    
    # Vérifier dans la localisation et le quartier
    for indicator in indicators:
        if indicator in localisation or indicator in quartier:
            return True
    
    # Vérifier aussi dans les métros (certains appartements peuvent être près de métros du 20e)
    metros = map_info.get('metros', []) or []
    for metro in metros:
        metro_str = str(metro).lower()
        # Métros typiques du 20e
        if any(m in metro_str for m in ['gambetta', 'père lachaise', 'ménilmontant', 'belleville', 'nation']):
            return True
    
    # Vérifier dans les données API brutes
    api_data = apartment.get('_api_data', {})
    postal_code = str(api_data.get('postal_code', ''))
    if '75020' in postal_code:
        return True
    
    city = str(api_data.get('city', '')).lower()
    if '20e' in city or '20ème' in city:
        return True
    
    return False


async def fetch_20e_apartments():
    """
    Récupère tous les appartements du 20e arrondissement via l'API
    """
    print("🚀 RÉCUPÉRATION DES APPARTEMENTS DU 20E ARRONDISSEMENT")
    print("=" * 60)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    alert_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
    
    scraper = JinkaAPIScraper()
    photo_manager = PhotoManager()
    
    try:
        # 1. Initialisation
        print("1️⃣ Initialisation du client API...")
        print("-" * 60)
        await scraper.setup()
        print("✅ Client API initialisé\n")
        
        # 2. Connexion
        print("\n2️⃣ Connexion à Jinka...")
        print("-" * 60)
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return None
        print("✅ Connexion réussie\n")
        
        # 3. Scraping de toutes les pages (appel unique via API)
        print("\n3️⃣ Récupération de toutes les pages de l'alerte via API...")
        print("-" * 60)
        print("📡 Utilisation de l'API pour récupérer tous les appartements en une fois")
        print()
        
        start_time = datetime.now()
        all_apartments = await scraper.scrape_alert_page(
            alert_url, 
            filter_type="all",
            max_pages=50  # Récupérer toutes les pages
        )
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n📊 RÉSULTATS BRUTS:")
        print(f"   {len(all_apartments)} appartements récupérés au total")
        print(f"   Temps: {elapsed_time:.1f} secondes")
        print()
        
        if not all_apartments:
            print("❌ Aucun appartement récupéré")
            return None
        
        # 4. Filtrage pour le 20e arrondissement
        print("\n4️⃣ Filtrage des appartements du 20e arrondissement...")
        print("-" * 60)
        
        apartments_20e = []
        for apt in all_apartments:
            if filter_20e_arrondissement(apt):
                apartments_20e.append(apt)
        
        print(f"✅ {len(apartments_20e)} appartements du 20e trouvés sur {len(all_apartments)} total")
        print()
        
        if not apartments_20e:
            print("❌ Aucun appartement du 20e trouvé")
            return None
        
        # 5. Téléchargement des photos via API
        print("\n5️⃣ Téléchargement des photos via API...")
        print("-" * 60)
        
        photos_downloaded = 0
        for i, apt in enumerate(apartments_20e, 1):
            apt_id = apt.get('id', 'unknown')
            photos_before = len(apt.get('photos', []))
            
            if photos_before > 0:
                print(f"   [{i}/{len(apartments_20e)}] Appartement {apt_id}: {photos_before} photos")
                
                # Télécharger les photos via le photo_manager
                apt_with_photos = photo_manager.download_apartment_photos(apt, max_photos=10)
                
                # Mettre à jour l'appartement avec les photos téléchargées
                apartments_20e[i-1] = apt_with_photos
                
                photos_after = len(apt_with_photos.get('photos', []))
                downloaded_count = sum(1 for p in apt_with_photos.get('photos', []) if p.get('local_path'))
                photos_downloaded += downloaded_count
                
                if downloaded_count > 0:
                    print(f"      ✅ {downloaded_count} photos téléchargées")
                else:
                    print(f"      ⚠️  Aucune photo téléchargée")
            else:
                print(f"   [{i}/{len(apartments_20e)}] Appartement {apt_id}: aucune photo")
        
        print(f"\n✅ Total photos téléchargées: {photos_downloaded}")
        print()
        
        # 6. Sauvegarder les données
        print("\n6️⃣ Sauvegarde des données...")
        print("-" * 60)
        
        os.makedirs('data', exist_ok=True)
        
        # Sauvegarder dans un fichier spécifique pour le 20e
        output_file = 'data/apartments_20e.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(apartments_20e, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Données sauvegardées dans {output_file}")
        print(f"   {len(apartments_20e)} appartements du 20e")
        print()
        
        # 7. Statistiques finales
        print("\n📊 STATISTIQUES FINALES")
        print("=" * 60)
        print(f"✅ Appartements du 20e récupérés: {len(apartments_20e)}")
        print(f"📸 Photos téléchargées: {photos_downloaded}")
        
        # Statistiques sur les prix et surfaces
        prices = []
        surfaces = []
        for apt in apartments_20e:
            # Prix
            prix_str = apt.get('prix', '').replace(' ', '').replace('€', '').strip()
            try:
                prix = int(prix_str)
                prices.append(prix)
            except:
                pass
            
            # Surface
            surface_str = apt.get('surface', '').replace('m²', '').strip()
            try:
                surface = int(surface_str)
                surfaces.append(surface)
            except:
                pass
        
        if prices:
            print(f"\n💰 Prix moyen: {sum(prices) / len(prices):,.0f} €")
            print(f"   Prix min: {min(prices):,} €")
            print(f"   Prix max: {max(prices):,} €")
        
        if surfaces:
            print(f"\n📐 Surface moyenne: {sum(surfaces) / len(surfaces):.1f} m²")
            print(f"   Surface min: {min(surfaces)} m²")
            print(f"   Surface max: {max(surfaces)} m²")
        
        # Afficher quelques exemples
        print(f"\n📋 Exemples d'appartements du 20e:")
        for i, apt in enumerate(apartments_20e[:5], 1):
            print(f"   {i}. ID: {apt.get('id')} - {apt.get('localisation', 'N/A')} - {apt.get('prix', 'N/A')}")
        
        print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return apartments_20e
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        print("\n🧹 Nettoyage...")
        await scraper.cleanup()
        print("✅ Terminé")


async def main():
    """Fonction principale"""
    apartments = await fetch_20e_apartments()
    
    if apartments:
        print(f"\n🎉 Récupération terminée avec succès!")
        print(f"   ✅ {len(apartments)} appartements du 20e récupérés")
        print(f"   📸 Photos téléchargées via API")
        print(f"\n💡 Prochaines étapes:")
        print(f"   1. Vérifier les données: python -c \"import json; d=json.load(open('data/apartments_20e.json')); print(len(d), 'appartements')\"")
        print(f"   2. Recalculer les scores si nécessaire")
    else:
        print("\n❌ Échec de la récupération")


if __name__ == "__main__":
    asyncio.run(main())


