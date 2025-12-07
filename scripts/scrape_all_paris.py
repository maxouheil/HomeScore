#!/usr/bin/env python3
"""
Script de scraping complet de tous les appartements Jinka à Paris
- Récupère toutes les alertes disponibles
- Scrape toutes les pages de chaque alerte
- Filtre les appartements Paris (code postal 75xxx)
- Télécharge les photos
- Sauvegarde dans data/paris_apartments.json

Coût : GRATUIT (API Jinka gratuite, stockage local)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinka_api_client import JinkaAPIClient
from scrape_jinka_api import JinkaAPIScraper
from api_data_adapter import adapt_api_to_scraped_format
from photo_manager import PhotoManager


def is_paris_apartment(apartment: Dict[str, Any]) -> bool:
    """
    Vérifie si un appartement est à Paris
    
    Args:
        apartment: Données de l'appartement
    
    Returns:
        True si l'appartement est à Paris, False sinon
    """
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
            print(f"   ⚠️  Doublon détecté: ID {apt_id}")
    
    return unique_apartments


def clean_apartment_data(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nettoie les données d'un appartement
    """
    cleaned = {}
    
    # Champs obligatoires
    required_fields = ['id', 'url', 'titre', 'prix', 'surface', 'localisation']
    for field in required_fields:
        if field in apartment and apartment[field]:
            cleaned[field] = apartment[field]
    
    # Champs optionnels
    optional_fields = [
        'prix_m2', 'pieces', 'date', 'transports', 'description',
        'caracteristiques', 'etage', 'agence', 'coordinates', 'map_info',
        'photos', 'scraped_at', '_api_data', 'exposition'
    ]
    
    for field in optional_fields:
        if field in apartment:
            value = apartment[field]
            if value is not None and value != '' and value != [] and value != {}:
                cleaned[field] = value
    
    # Nettoyer les photos : garder seulement celles avec URL valide
    if 'photos' in cleaned:
        cleaned_photos = []
        for photo in cleaned['photos']:
            if isinstance(photo, dict) and photo.get('url'):
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
    
    return cleaned


async def scrape_all_paris_apartments(
    alert_tokens: Optional[List[str]] = None,
    max_pages_per_alert: int = 50,
    use_existing_scraper: bool = False
) -> List[Dict[str, Any]]:
    """
    Scrape tous les appartements Paris depuis toutes les alertes
    
    Args:
        alert_tokens: Liste des tokens d'alertes à scraper (si None, récupère toutes les alertes)
        max_pages_per_alert: Nombre maximum de pages par alerte
    
    Returns:
        Liste de tous les appartements Paris
    """
    print("🏙️  SCRAPING COMPLET PARIS")
    print("=" * 60)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    scraper = JinkaAPIScraper()
    
    try:
        # 1. Initialisation
        print("1️⃣ Initialisation...")
        print("-" * 60)
        await scraper.setup()
        
        # 2. Connexion
        print("\n2️⃣ Connexion à Jinka...")
        print("-" * 60)
        if not await scraper.login():
            print("❌ Échec de la connexion automatique")
            print("💡 Vous pouvez essayer de vous connecter manuellement d'abord avec:")
            print("   python wait_for_login.py")
            print("   puis relancer ce script")
            return []
        print("✅ Connexion réussie\n")
        
        # 3. Récupérer les alertes
        print("3️⃣ Récupération des alertes...")
        print("-" * 60)
        
        if alert_tokens:
            # Utiliser les tokens fournis
            alerts = [{'token': token, 'id': token} for token in alert_tokens if token]
            print(f"✅ {len(alerts)} alertes fournies depuis fichier/config")
        else:
            # Récupérer toutes les alertes via l'API du scraper (qui est déjà connecté)
            print("🔍 Récupération automatique des alertes via l'API...")
            try:
                # Utiliser le client API du scraper qui est déjà connecté
                if scraper.api_client:
                    alerts_data = await scraper.api_client.get_alert_list()
                    
                    if alerts_data and isinstance(alerts_data, list) and len(alerts_data) > 0:
                        alerts = alerts_data
                        print(f"✅ {len(alerts)} alertes trouvées automatiquement via l'API")
                        for i, alert in enumerate(alerts[:10], 1):  # Afficher les 10 premières
                            alert_name = alert.get('name') or alert.get('title') or alert.get('label') or f'Alerte {i}'
                            alert_token = alert.get('token') or alert.get('id') or 'N/A'
                            print(f"   {i}. {alert_name} (token: {alert_token[:8]}...)")
                        if len(alerts) > 10:
                            print(f"   ... et {len(alerts) - 10} autres alertes")
                    else:
                        # Fallback : utiliser l'alerte connue par défaut
                        alerts = [{'token': '26c2ec3064303aa68ffa43f7c6518733', 'name': 'Alerte principale'}]
                        print(f"⚠️  Aucune alerte trouvée via l'API, utilisation de l'alerte par défaut")
                else:
                    # Fallback si pas de client API
                    alerts = [{'token': '26c2ec3064303aa68ffa43f7c6518733', 'name': 'Alerte principale'}]
                    print(f"⚠️  Client API non disponible, utilisation de l'alerte par défaut")
            except Exception as e:
                print(f"⚠️  Erreur lors de la récupération des alertes: {e}")
                import traceback
                traceback.print_exc()
                # Fallback : utiliser l'alerte connue par défaut
                alerts = [{'token': '26c2ec3064303aa68ffa43f7c6518733', 'name': 'Alerte principale'}]
                print(f"⚠️  Utilisation de l'alerte par défaut")
        
        if not alerts:
            print("❌ Aucune alerte trouvée")
            return []
        
        print()
        
        # 4. Scraper toutes les alertes
        print("3️⃣ Scraping de toutes les alertes...")
        print("-" * 60)
        
        all_apartments = []
        
        for i, alert in enumerate(alerts, 1):
            # Gérer différents formats d'alertes
            # L'API retourne 'id' comme token pour les alertes
            alert_token = alert.get('token') or alert.get('id') or alert.get('alert_token', '')
            if not alert_token:
                print(f"⚠️  Alerte {i}: Token manquant, skip")
                print(f"   Données: {alert}")
                continue
            
            alert_name = alert.get('name') or alert.get('title') or alert.get('label') or f'Alerte {i}'
            print(f"\n📋 Alerte {i}/{len(alerts)}: {alert_name}")
            print(f"   Token: {alert_token}")
            
            # Construire l'URL de l'alerte
            alert_url = f"https://www.jinka.fr/asrenter/alert/dashboard/{alert_token}"
            
            try:
                # Scraper cette alerte
                apartments = await scraper.scrape_alert_page(
                    alert_url,
                    filter_type="all",
                    max_pages=max_pages_per_alert
                )
                
                print(f"   ✅ {len(apartments)} appartements récupérés")
                all_apartments.extend(apartments)
                
            except Exception as e:
                print(f"   ❌ Erreur lors du scraping de l'alerte: {e}")
                continue
        
        print(f"\n📊 Total brut: {len(all_apartments)} appartements")
        
        if not all_apartments:
            print("\n⚠️  Aucun appartement récupéré. Vérifiez votre connexion.")
            return []
        
        # 5. Filtrer Paris
        print("\n5️⃣ Filtrage Paris (code postal 75xxx)...")
        print("-" * 60)
        
        paris_apartments = []
        for apt in all_apartments:
            if is_paris_apartment(apt):
                paris_apartments.append(apt)
        
        print(f"✅ {len(paris_apartments)} appartements Paris trouvés")
        
        # 6. Supprimer les doublons
        print("\n6️⃣ Déduplication...")
        print("-" * 60)
        paris_apartments = remove_duplicates(paris_apartments)
        print(f"✅ {len(paris_apartments)} appartements uniques")
        
        # 7. Nettoyer les données
        print("\n7️⃣ Nettoyage des données...")
        print("-" * 60)
        
        cleaned_apartments = []
        for apt in paris_apartments:
            cleaned = clean_apartment_data(apt)
            if cleaned.get('id'):
                cleaned_apartments.append(cleaned)
        
        print(f"✅ {len(cleaned_apartments)} appartements nettoyés")
        
        # 8. Télécharger les photos
        print("\n8️⃣ Téléchargement des photos...")
        print("-" * 60)
        
        photo_manager = PhotoManager()
        photos_downloaded = 0
        
        for i, apt in enumerate(cleaned_apartments, 1):
            apt_id = apt.get('id', 'unknown')
            photos_count = len(apt.get('photos', []))
            
            if photos_count > 0:
                if i % 10 == 0:
                    print(f"   [{i}/{len(cleaned_apartments)}] Appartement {apt_id}: {photos_count} photos")
                
                # Télécharger les photos (max 10)
                apt_with_photos = photo_manager.download_apartment_photos(apt, max_photos=10)
                cleaned_apartments[i-1] = apt_with_photos
                
                downloaded_count = sum(1 for p in apt_with_photos.get('photos', []) if p.get('local_path'))
                photos_downloaded += downloaded_count
        
        print(f"✅ {photos_downloaded} photos téléchargées")
        
        # 9. Sauvegarder
        print("\n9️⃣ Sauvegarde...")
        print("-" * 60)
        
        os.makedirs('data', exist_ok=True)
        output_file = 'data/paris_apartments.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_apartments, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Données sauvegardées: {output_file}")
        
        # 9. Statistiques finales
        print("\n📊 STATISTIQUES FINALES")
        print("=" * 60)
        print(f"✅ Appartements Paris: {len(cleaned_apartments)}")
        print(f"📸 Photos téléchargées: {photos_downloaded}")
        
        # Statistiques sur les prix et surfaces
        prices = []
        surfaces = []
        arrondissements = {}
        
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
            
            # Arrondissement
            postal_code = apt.get('_api_data', {}).get('postal_code', '')
            if postal_code and postal_code.startswith('75'):
                arr = postal_code[-2:] if len(postal_code) >= 2 else 'unknown'
                arrondissements[arr] = arrondissements.get(arr, 0) + 1
        
        if prices:
            print(f"\n💰 Prix:")
            print(f"   Moyen: {sum(prices) / len(prices):,.0f} €")
            print(f"   Min: {min(prices):,} €")
            print(f"   Max: {max(prices):,} €")
        
        if surfaces:
            print(f"\n📐 Surface:")
            print(f"   Moyenne: {sum(surfaces) / len(surfaces):.1f} m²")
            print(f"   Min: {min(surfaces)} m²")
            print(f"   Max: {max(surfaces)} m²")
        
        if arrondissements:
            print(f"\n🏙️  Arrondissements:")
            for arr, count in sorted(arrondissements.items()):
                print(f"   {arr}: {count} appartements")
        
        print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return cleaned_apartments
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        await scraper.cleanup()


async def main():
    """Fonction principale"""
    print("🚀 SCRAPING COMPLET PARIS - JINKA")
    print("=" * 60)
    print()
    print("Ce script va:")
    print("1. Se connecter à l'API Jinka")
    print("2. Scraper toutes les alertes fournies")
    print("3. Scraper toutes les pages de chaque alerte")
    print("4. Filtrer les appartements Paris (75xxx)")
    print("5. Télécharger les photos")
    print("6. Sauvegarder dans data/paris_apartments.json")
    print()
    print("Coût: GRATUIT (API Jinka gratuite)")
    print()
    
    # Par défaut, récupérer automatiquement toutes les alertes via l'API
    # Pour forcer des tokens spécifiques, créez data/alert_tokens.json
    alert_tokens_file = Path('data/alert_tokens.json')
    alert_tokens_auto_file = Path('data/alert_tokens_auto.json')
    alert_tokens = None
    
    # Vérifier si un fichier de tokens existe (pour override manuel)
    if alert_tokens_file.exists():
        try:
            with open(alert_tokens_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'paris_alerts' in data:
                    alert_tokens = [alert['token'] for alert in data['paris_alerts']]
                    print(f"✅ {len(alert_tokens)} alertes chargées depuis data/alert_tokens.json")
                elif isinstance(data, list):
                    alert_tokens = data
                    print(f"✅ {len(alert_tokens)} alertes chargées depuis data/alert_tokens.json")
        except Exception as e:
            print(f"⚠️  Erreur lecture alert_tokens.json: {e}")
    
    # Si pas de fichier manuel, utiliser le fichier auto généré par check_alerts.py
    if not alert_tokens and alert_tokens_auto_file.exists():
        try:
            with open(alert_tokens_auto_file, 'r', encoding='utf-8') as f:
                alerts_data = json.load(f)
                if isinstance(alerts_data, list) and len(alerts_data) > 0:
                    # Extraire les tokens depuis les alertes (le token est l'id)
                    alert_tokens = [alert.get('token') or alert.get('id') for alert in alerts_data if alert.get('token') or alert.get('id')]
                    print(f"✅ {len(alert_tokens)} alertes chargées depuis data/alert_tokens_auto.json")
                    print(f"   (Généré automatiquement par check_alerts.py)")
        except Exception as e:
            print(f"⚠️  Erreur lecture alert_tokens_auto.json: {e}")
    
    # Si pas de fichier, récupération automatique via l'API (dans la fonction scrape_all_paris_apartments)
    if not alert_tokens:
        print("💡 Récupération automatique de toutes les alertes via l'API")
        print("   (Pour forcer des tokens spécifiques, créez data/alert_tokens.json)")
        print("   (Ou exécutez d'abord: python scripts/check_alerts.py)")
    
    apartments = await scrape_all_paris_apartments(
        alert_tokens=alert_tokens,
        max_pages_per_alert=50
    )
    
    if apartments:
        print(f"\n🎉 Scraping terminé avec succès!")
        print(f"   ✅ {len(apartments)} appartements Paris récupérés")
        print(f"   💾 Données sauvegardées: data/paris_apartments.json")
        print(f"\n💡 Prochaine étape:")
        print(f"   python batch_analyze_paris.py")
    else:
        print("\n❌ Échec du scraping")


if __name__ == "__main__":
    asyncio.run(main())

