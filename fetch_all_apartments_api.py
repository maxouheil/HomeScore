#!/usr/bin/env python3
"""
Script pour récupérer tous les appartements (42) via l'API, nettoyer les données et télécharger les photos
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set
from scrape_jinka_api import JinkaAPIScraper
from photo_manager import PhotoManager
from api_data_adapter import adapt_api_to_scraped_format


def clean_apartment_data(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nettoie les données d'un appartement
    
    - Supprime les champs vides ou None
    - Valide le format des données
    - Normalise les champs
    """
    cleaned = {}
    
    # Champs obligatoires
    required_fields = ['id', 'url', 'titre', 'prix', 'surface', 'localisation']
    for field in required_fields:
        if field in apartment and apartment[field]:
            cleaned[field] = apartment[field]
        else:
            print(f"⚠️  Appartement {apartment.get('id', 'unknown')}: champ '{field}' manquant")
    
    # Champs optionnels (seulement si non vides)
    optional_fields = [
        'prix_m2', 'pieces', 'date', 'transports', 'description',
        'caracteristiques', 'etage', 'agence', 'coordinates', 'map_info',
        'photos', 'scraped_at', 'date_creation_annonce', '_api_data'
    ]
    
    for field in optional_fields:
        if field in apartment:
            value = apartment[field]
            # Garder si non vide
            if value is not None and value != '' and value != [] and value != {}:
                cleaned[field] = value
    
    # Nettoyer les photos : garder seulement celles avec URL valide
    if 'photos' in cleaned:
        cleaned_photos = []
        for photo in cleaned['photos']:
            if isinstance(photo, dict) and photo.get('url'):
                # Nettoyer l'URL
                url = photo['url'].strip()
                if url and url.startswith('http'):
                    cleaned_photos.append({
                        'url': url,
                        'alt': photo.get('alt', 'Photo appartement'),
                        'selector': photo.get('selector', 'api_images'),
                        'width': photo.get('width'),
                        'height': photo.get('height')
                    })
        cleaned['photos'] = cleaned_photos
    
    # Normaliser le prix_m2
    if 'prix_m2' in cleaned and cleaned['prix_m2']:
        prix_m2_str = str(cleaned['prix_m2'])
        if '€' not in prix_m2_str and prix_m2_str.replace(' ', '').isdigit():
            cleaned['prix_m2'] = f"{prix_m2_str.replace(' ', '')} € / m²"
    
    return cleaned


def remove_duplicates(apartments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Supprime les doublons basés sur l'ID
    Garde le plus récent en cas de doublon
    """
    seen_ids: Set[str] = set()
    unique_apartments = []
    
    for apt in apartments:
        apt_id = str(apt.get('id', ''))
        if apt_id and apt_id not in seen_ids:
            seen_ids.add(apt_id)
            unique_apartments.append(apt)
        elif apt_id:
            print(f"⚠️  Doublon détecté: ID {apt_id}")
    
    return unique_apartments


def load_existing_apartments() -> Dict[str, Dict[str, Any]]:
    """
    Charge les appartements existants depuis scraped_apartments.json
    
    Returns:
        Dictionnaire {apartment_id: apartment_data}
    """
    existing = {}
    scraped_file = Path('data/scraped_apartments.json')
    
    if scraped_file.exists():
        try:
            with open(scraped_file, 'r', encoding='utf-8') as f:
                apartments = json.load(f)
            
            for apt in apartments:
                apt_id = str(apt.get('id', ''))
                if apt_id:
                    existing[apt_id] = apt
            
            print(f"   ✅ {len(existing)} appartements existants chargés")
        except Exception as e:
            print(f"   ⚠️  Erreur lors du chargement des données existantes: {e}")
    
    return existing


def merge_apartment_data(existing: Dict[str, Dict[str, Any]], new_apartments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fusionne les nouveaux appartements avec les existants
    - Préserve les données existantes (scores, analyses, etc.)
    - Ajoute/mette à jour les données manquantes depuis l'API
    
    Args:
        existing: Dictionnaire des appartements existants {id: data}
        new_apartments: Liste des nouveaux appartements depuis l'API
    
    Returns:
        Liste de tous les appartements fusionnés
    """
    merged = []
    updated_count = 0
    new_count = 0
    
    # Créer un dict des nouveaux appartements par ID
    new_by_id = {str(apt.get('id', '')): apt for apt in new_apartments if apt.get('id')}
    
    # Traiter les appartements existants
    for apt_id, existing_apt in existing.items():
        if apt_id in new_by_id:
            # Appartement existant avec nouvelles données API
            new_apt = new_by_id[apt_id]
            merged_apt = existing_apt.copy()
            
            # Mettre à jour seulement les champs manquants ou vides
            fields_to_update = [
                'prix_m2', 'transports', 'description', 'caracteristiques',
                'etage', 'agence', 'coordinates', 'map_info', 'photos',
                'date_creation_annonce', '_api_data', 'exposition',
                'localisation', 'localisation_precise'
            ]
            
            for field in fields_to_update:
                # Si le champ est manquant ou vide dans l'existant, utiliser la nouvelle valeur
                existing_value = merged_apt.get(field)
                new_value = new_apt.get(field)
                
                if not existing_value or existing_value == '' or existing_value == [] or existing_value == {}:
                    if new_value:
                        merged_apt[field] = new_value
                # Pour les photos, toujours mettre à jour si nouvelles photos disponibles
                elif field == 'photos' and new_value and len(new_value) > len(existing_value or []):
                    merged_apt[field] = new_value
                # Pour _api_data, toujours mettre à jour avec les dernières données API
                elif field == '_api_data' and new_value:
                    merged_apt[field] = new_value
            
            # Mettre à jour les champs de base si manquants
            for field in ['prix', 'surface', 'pieces', 'titre', 'url']:
                if not merged_apt.get(field) and new_apt.get(field):
                    merged_apt[field] = new_apt[field]
            
            merged.append(merged_apt)
            updated_count += 1
        else:
            # Appartement existant sans nouvelles données API - garder tel quel
            merged.append(existing_apt)
    
    # Ajouter les nouveaux appartements qui n'existent pas encore
    for apt_id, new_apt in new_by_id.items():
        if apt_id not in existing:
            merged.append(new_apt)
            new_count += 1
    
    print(f"   ✅ {updated_count} appartements mis à jour")
    print(f"   ✅ {new_count} nouveaux appartements ajoutés")
    print(f"   ✅ {len(existing) - updated_count} appartements existants préservés")
    
    return merged


def validate_apartment(apartment: Dict[str, Any]) -> bool:
    """
    Valide qu'un appartement a les données minimales requises
    """
    required = ['id', 'url', 'titre', 'prix', 'surface']
    return all(apartment.get(field) for field in required)


def clean_old_data():
    """
    Supprime toutes les données du 5 novembre pour repartir à zéro
    """
    print("🧹 NETTOYAGE DES DONNÉES ANCIENNES (5 novembre)")
    print("=" * 60)
    
    data_dir = Path('data')
    files_deleted = 0
    dirs_deleted = 0
    
    # Fichiers à supprimer
    files_to_delete = [
        'scraped_apartments.json',
        'scores.json',
    ]
    
    # Dossiers à nettoyer
    dirs_to_clean = [
        'scores',
        'photos',
    ]
    
    # Supprimer les fichiers principaux
    for filename in files_to_delete:
        file_path = data_dir / filename
        if file_path.exists():
            file_path.unlink()
            print(f"   ✅ Supprimé: {filename}")
            files_deleted += 1
    
    # Supprimer le dossier scores (et son contenu)
    scores_dir = data_dir / 'scores'
    if scores_dir.exists():
        import shutil
        shutil.rmtree(scores_dir)
        print(f"   ✅ Supprimé: scores/")
        dirs_deleted += 1
    
    # Supprimer toutes les photos
    photos_dir = data_dir / 'photos'
    if photos_dir.exists():
        import shutil
        shutil.rmtree(photos_dir)
        print(f"   ✅ Supprimé: photos/")
        dirs_deleted += 1
    
    # Supprimer les fichiers de métadonnées de photos
    photos_metadata_dir = data_dir / 'photos_metadata'
    if photos_metadata_dir.exists():
        import shutil
        shutil.rmtree(photos_metadata_dir)
        print(f"   ✅ Supprimé: photos_metadata/")
        dirs_deleted += 1
    
    # Supprimer le dossier appartements (fichiers individuels du 5 novembre)
    appartements_dir = data_dir / 'appartements'
    if appartements_dir.exists():
        import shutil
        shutil.rmtree(appartements_dir)
        print(f"   ✅ Supprimé: appartements/")
        dirs_deleted += 1
    
    print(f"\n✅ Nettoyage terminé: {files_deleted} fichiers, {dirs_deleted} dossiers supprimés")
    print()


async def fetch_all_apartments_with_photos(merge_with_existing: bool = True):
    """
    Récupère tous les appartements via l'API, nettoie les données et télécharge les photos
    
    Args:
        merge_with_existing: Si True, fusionne avec les données existantes au lieu de les remplacer
    """
    print("🚀 RÉCUPÉRATION DE TOUS LES APPARTEMENTS VIA API")
    print("=" * 60)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 0. Charger les données existantes si fusion activée
    existing_apartments = {}
    if merge_with_existing:
        print("📂 Chargement des données existantes...")
        print("-" * 60)
        existing_apartments = load_existing_apartments()
        print()
    else:
        # Nettoyer les anciennes données seulement si pas de fusion
        clean_old_data()
    
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
        
        # 3. Scraping de toutes les pages
        print("\n3️⃣ Scraping de toutes les pages de l'alerte...")
        print("-" * 60)
        start_time = datetime.now()
        apartments = await scraper.scrape_alert_page(
            alert_url, 
            filter_type="all",
            max_pages=50  # Récupérer toutes les pages
        )
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n📊 RÉSULTATS BRUTS:")
        print(f"   {len(apartments)} appartements récupérés")
        print(f"   Temps: {elapsed_time:.1f} secondes")
        print()
        
        if not apartments:
            print("❌ Aucun appartement récupéré")
            return None
        
        # 4. Nettoyage des données
        print("\n4️⃣ Nettoyage et validation des données...")
        print("-" * 60)
        
        # Supprimer les doublons
        apartments = remove_duplicates(apartments)
        print(f"   Après déduplication: {len(apartments)} appartements")
        
        # Nettoyer chaque appartement
        cleaned_apartments = []
        invalid_count = 0
        
        for apt in apartments:
            if validate_apartment(apt):
                cleaned = clean_apartment_data(apt)
                cleaned_apartments.append(cleaned)
            else:
                invalid_count += 1
                print(f"   ⚠️  Appartement {apt.get('id', 'unknown')} invalide (données manquantes)")
        
        print(f"   Appartements valides: {len(cleaned_apartments)}")
        print(f"   Appartements invalides: {invalid_count}")
        print()
        
        # 4.5. Fusionner avec les données existantes si activé
        if merge_with_existing and existing_apartments:
            print("\n4.5️⃣ Fusion avec les données existantes...")
            print("-" * 60)
            cleaned_apartments = merge_apartment_data(existing_apartments, cleaned_apartments)
            print()
        
        # 5. Téléchargement des photos via API
        print("\n5️⃣ Téléchargement des photos via API...")
        print("-" * 60)
        
        photos_downloaded = 0
        for i, apt in enumerate(cleaned_apartments, 1):
            apt_id = apt.get('id', 'unknown')
            photos_before = len(apt.get('photos', []))
            
            if photos_before > 0:
                print(f"   [{i}/{len(cleaned_apartments)}] Appartement {apt_id}: {photos_before} photos")
                
                # Télécharger les photos via le photo_manager
                # download_apartment_photos modifie l'appartement en place et retourne l'appartement modifié
                apt_with_photos = photo_manager.download_apartment_photos(apt, max_photos=10)
                
                # Mettre à jour l'appartement avec les photos téléchargées
                cleaned_apartments[i-1] = apt_with_photos
                
                photos_after = len(apt_with_photos.get('photos', []))
                downloaded_count = sum(1 for p in apt_with_photos.get('photos', []) if p.get('local_path'))
                photos_downloaded += downloaded_count
                
                if downloaded_count > 0:
                    print(f"      ✅ {downloaded_count} photos téléchargées")
                else:
                    print(f"      ⚠️  Aucune photo téléchargée")
            else:
                print(f"   [{i}/{len(cleaned_apartments)}] Appartement {apt_id}: aucune photo")
        
        print(f"\n✅ Total photos téléchargées: {photos_downloaded}")
        print()
        
        # 6. Sauvegarder les données nettoyées
        print("\n6️⃣ Sauvegarde des données nettoyées...")
        print("-" * 60)
        
        from project_config import DATA_DIR
        
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder dans scraped_apartments.json (remplace l'ancien)
        output_file = DATA_DIR / 'scraped_apartments.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_apartments, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Données sauvegardées dans {output_file}")
        print(f"   {len(cleaned_apartments)} appartements")
        print()
        
        # 7. Statistiques finales
        print("\n📊 STATISTIQUES FINALES")
        print("=" * 60)
        print(f"✅ Appartements récupérés: {len(cleaned_apartments)}")
        print(f"📸 Photos téléchargées: {photos_downloaded}")
        
        # Statistiques sur les prix et surfaces
        prices = []
        surfaces = []
        for apt in cleaned_apartments:
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
            print(f"💰 Prix moyen: {sum(prices) / len(prices):,.0f} €")
            print(f"   Prix min: {min(prices):,} €")
            print(f"   Prix max: {max(prices):,} €")
        
        if surfaces:
            print(f"📐 Surface moyenne: {sum(surfaces) / len(surfaces):.1f} m²")
            print(f"   Surface min: {min(surfaces)} m²")
            print(f"   Surface max: {max(surfaces)} m²")
        
        print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return cleaned_apartments
        
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
    import sys
    
    # Par défaut, fusionner avec les données existantes pour préserver les scores/analyses
    merge = True
    if len(sys.argv) > 1 and sys.argv[1] == '--clean':
        merge = False
        print("⚠️  Mode nettoyage activé: toutes les données existantes seront supprimées")
        print()
    
    apartments = await fetch_all_apartments_with_photos(merge_with_existing=merge)
    
    if apartments:
        print(f"\n🎉 Récupération terminée avec succès!")
        print(f"   ✅ {len(apartments)} appartements récupérés et nettoyés")
        print(f"   📸 Photos téléchargées via API")
        if merge:
            print(f"   🔄 Fusion avec données existantes: activée")
        print(f"\n💡 Prochaines étapes:")
        print(f"   1. Recalculer les scores: python homescore.py")
        print(f"   2. Vérifier les données: python -c \"import json; d=json.load(open('data/scraped_apartments.json')); print(len(d), 'appartements')\"")
    else:
        print("\n❌ Échec de la récupération")


if __name__ == "__main__":
    asyncio.run(main())

