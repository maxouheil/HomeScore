#!/usr/bin/env python3
"""
Script principal pour récupérer automatiquement les nouveaux appartements Jinka
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

from config_jinka import (
    APARTMENTS_FILE,
    JINKA_APARTMENTS_FILE,
    DATA_DIR
)
from jinka_scraper import JinkaScraper
from photo_downloader import PhotoDownloader


def load_existing_apartments() -> Dict[str, Dict]:
    """
    Charge les appartements existants depuis le fichier
    
    Returns:
        Dictionnaire {apartment_id: apartment_data}
    """
    existing = {}
    
    # Charger depuis all_apartments_scores.json
    if APARTMENTS_FILE.exists():
        try:
            with open(APARTMENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Gérer différents formats
            if isinstance(data, list):
                for apt in data:
                    apt_id = str(apt.get('id', ''))
                    if apt_id:
                        existing[apt_id] = apt
            elif isinstance(data, dict):
                for key, apt in data.items():
                    apt_id = str(apt.get('id', key))
                    if apt_id:
                        existing[apt_id] = apt
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement de {APARTMENTS_FILE}: {e}")
    
    # Charger aussi depuis jinka_apartments.json si il existe
    if JINKA_APARTMENTS_FILE.exists():
        try:
            with open(JINKA_APARTMENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for apt in data:
                    apt_id = str(apt.get('id', ''))
                    if apt_id:
                        existing[apt_id] = apt
            elif isinstance(data, dict):
                existing.update(data)
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement de {JINKA_APARTMENTS_FILE}: {e}")
    
    return existing


def save_apartments(apartments: List[Dict], file_path: Path):
    """
    Sauvegarde les appartements dans un fichier JSON
    
    Args:
        apartments: Liste des appartements
        file_path: Chemin du fichier
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, indent=2, ensure_ascii=False)
    
    print(f"💾 {len(apartments)} appartement(s) sauvegardé(s) dans {file_path}")


def merge_with_existing(new_apartments: List[Dict], existing: Dict[str, Dict]) -> List[Dict]:
    """
    Fusionne les nouveaux appartements avec les existants
    
    Args:
        new_apartments: Liste des nouveaux appartements
        existing: Dictionnaire des appartements existants
        
    Returns:
        Liste de tous les appartements (nouveaux + existants)
    """
    all_apartments = list(existing.values())
    new_count = 0
    
    for apt in new_apartments:
        apt_id = str(apt.get('id', ''))
        if not apt_id or apt_id == 'unknown':
            continue
        
        if apt_id not in existing:
            # Nouvel appartement
            all_apartments.append(apt)
            existing[apt_id] = apt
            new_count += 1
            print(f"  ✅ Nouvel appartement: {apt_id} - {apt.get('titre', 'N/A')}")
        else:
            # Appartement existant - mettre à jour si nécessaire
            existing_apt = existing[apt_id]
            # Mettre à jour la date de dernière mise à jour
            existing_apt['date_derniere_maj'] = datetime.now().isoformat()
            # Mettre à jour les photos si de nouvelles sont disponibles
            if apt.get('photos') and len(apt['photos']) > len(existing_apt.get('photos', [])):
                existing_apt['photos'] = apt['photos']
    
    return all_apartments, new_count


def fetch_new_apartments(download_photos: bool = True) -> Dict:
    """
    Récupère les nouveaux appartements depuis Jinka
    
    Args:
        download_photos: Si True, télécharge les photos
        
    Returns:
        Dictionnaire avec les statistiques
    """
    print("=" * 80)
    print("🏠 RÉCUPÉRATION DES APPARTEMENTS JINKA")
    print("=" * 80)
    print()
    
    # Charger les appartements existants
    print("📂 Chargement des appartements existants...")
    existing = load_existing_apartments()
    print(f"   {len(existing)} appartement(s) existant(s)")
    print()
    
    # Récupérer les appartements depuis Jinka
    scraper = JinkaScraper()
    new_apartments = scraper.get_all_apartments()
    
    if not new_apartments:
        print("⚠️  Aucun appartement trouvé")
        return {
            'success': False,
            'new_count': 0,
            'total_count': len(existing),
            'message': 'Aucun appartement trouvé'
        }
    
    print()
    print(f"📊 {len(new_apartments)} appartement(s) récupéré(s) depuis Jinka")
    print()
    
    # Identifier les nouveaux appartements
    new_apartments_list = []
    for apt in new_apartments:
        apt_id = str(apt.get('id', ''))
        if apt_id and apt_id != 'unknown' and apt_id not in existing:
            new_apartments_list.append(apt)
    
    print(f"🆕 {len(new_apartments_list)} nouveau(x) appartement(s) détecté(s)")
    print()
    
    # Télécharger les photos pour les nouveaux appartements
    if download_photos and new_apartments_list:
        print("📸 Téléchargement des photos...")
        downloader = PhotoDownloader()
        
        for apt in new_apartments_list:
            apt_id = str(apt.get('id', ''))
            photo_urls = []
            
            # Extraire les URLs des photos
            for photo in apt.get('photos', []):
                if isinstance(photo, dict):
                    url = photo.get('url', '')
                elif isinstance(photo, str):
                    url = photo
                else:
                    continue
                
                if url:
                    photo_urls.append(url)
            
            if photo_urls:
                downloaded_photos = downloader.download_apartment_photos(apt_id, photo_urls)
                # Mettre à jour les photos avec les chemins locaux
                apt['photos'] = downloaded_photos
            else:
                print(f"   ⚠️  Aucune photo pour l'appartement {apt_id}")
        
        print()
    
    # Fusionner avec les existants
    all_apartments, new_count = merge_with_existing(new_apartments, existing)
    
    # Sauvegarder dans jinka_apartments.json
    save_apartments(all_apartments, JINKA_APARTMENTS_FILE)
    
    # Sauvegarder aussi dans all_apartments_scores.json si le fichier existe
    if APARTMENTS_FILE.exists():
        # Charger le fichier existant pour préserver sa structure
        try:
            with open(APARTMENTS_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # Ajouter les nouveaux appartements Jinka
            if isinstance(existing_data, list):
                # Ajouter les nouveaux à la liste existante
                existing_ids = {str(apt.get('id', '')) for apt in existing_data}
                for apt in new_apartments_list:
                    apt_id = str(apt.get('id', ''))
                    if apt_id and apt_id not in existing_ids:
                        existing_data.append(apt)
                        existing_ids.add(apt_id)
                
                save_apartments(existing_data, APARTMENTS_FILE)
        except Exception as e:
            print(f"⚠️  Erreur lors de la mise à jour de {APARTMENTS_FILE}: {e}")
    
    print()
    print("=" * 80)
    print("✅ RÉCUPÉRATION TERMINÉE")
    print("=" * 80)
    print(f"   Nouveaux appartements: {new_count}")
    print(f"   Total: {len(all_apartments)}")
    print()
    
    return {
        'success': True,
        'new_count': new_count,
        'total_count': len(all_apartments),
        'fetched_count': len(new_apartments),
        'message': f'{new_count} nouveau(x) appartement(s) ajouté(s)'
    }


def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Récupère les nouveaux appartements Jinka')
    parser.add_argument(
        '--no-photos',
        action='store_true',
        help='Ne pas télécharger les photos'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Mode test (affiche les informations sans sauvegarder)'
    )
    
    args = parser.parse_args()
    
    download_photos = not args.no_photos
    
    if args.test:
        print("🧪 MODE TEST")
        print()
        # Juste tester l'API et le scraper
        scraper = JinkaScraper()
        apartments = scraper.get_all_apartments()
        print(f"\n📊 {len(apartments)} appartement(s) trouvé(s)")
        if apartments:
            print("\nPremier appartement:")
            apt = apartments[0]
            for key, value in apt.items():
                if key != 'raw_data':
                    print(f"  {key}: {value}")
    else:
        result = fetch_new_apartments(download_photos=download_photos)
        
        if result['success']:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()

