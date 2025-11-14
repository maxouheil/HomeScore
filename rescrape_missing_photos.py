#!/usr/bin/env python3
"""
Script pour identifier les appartements sans photos et relancer le scraping
"""

import asyncio
import json
import os
from pathlib import Path
from scrape_jinka import JinkaScraper

def load_all_apartments():
    """Charge tous les appartements depuis data/appartements/"""
    apartments = []
    appartements_dir = Path("data/appartements")
    
    if not appartements_dir.exists():
        print("❌ Dossier data/appartements/ non trouvé")
        return []
    
    json_files = list(appartements_dir.glob("*.json"))
    print(f"📂 {len(json_files)} fichiers d'appartements trouvés")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                apartment_data = json.load(f)
                apartments.append(apartment_data)
        except Exception as e:
            print(f"⚠️ Erreur lecture {json_file.name}: {e}")
    
    return apartments

def check_apartment_photos(apartment_data):
    """Vérifie si un appartement a des photos"""
    apartment_id = apartment_data.get('id', 'unknown')
    
    # Ignorer les fichiers de test
    if apartment_id.startswith('test_') or apartment_id == 'unknown':
        return None
    
    # Vérifier les photos dans le JSON
    photos_json = apartment_data.get('photos', [])
    photos_count_json = len(photos_json) if photos_json else 0
    
    # Vérifier les photos téléchargées
    photos_dir = Path(f"data/photos/{apartment_id}")
    photos_downloaded = 0
    if photos_dir.exists():
        photos_downloaded = len(list(photos_dir.glob("*.jpg"))) + len(list(photos_dir.glob("*.jpeg"))) + len(list(photos_dir.glob("*.png")))
    
    # Vérifier d'autres données manquantes
    missing_data = []
    
    if not apartment_data.get('surface'):
        missing_data.append('surface')
    if not apartment_data.get('localisation') or apartment_data.get('localisation') == 'Localisation non trouvée':
        missing_data.append('localisation')
    if not apartment_data.get('description') or apartment_data.get('description') == 'Description non trouvée':
        missing_data.append('description')
    if not apartment_data.get('coordinates') or not apartment_data.get('coordinates', {}).get('latitude'):
        missing_data.append('coordinates')
    if not apartment_data.get('map_info') or not apartment_data.get('map_info', {}).get('quartier') or apartment_data.get('map_info', {}).get('quartier') == 'Quartier non identifié':
        missing_data.append('map_info')
    
    return {
        'id': apartment_id,
        'url': apartment_data.get('url', ''),
        'photos_json': photos_count_json,
        'photos_downloaded': photos_downloaded,
        'has_photos': photos_count_json > 0 or photos_downloaded > 0,
        'missing_data': missing_data,
        'apartment_data': apartment_data
    }

def identify_missing_photos():
    """Identifie tous les appartements sans photos ou avec données manquantes"""
    print("🔍 IDENTIFICATION DES APPARTEMENTS SANS PHOTOS")
    print("=" * 60)
    
    apartments = load_all_apartments()
    
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return []
    
    print(f"\n📊 Analyse de {len(apartments)} appartements...\n")
    
    missing_photos = []
    missing_data_only = []
    complete_apartments = []
    
    for apartment in apartments:
        check_result = check_apartment_photos(apartment)
        
        # Ignorer les fichiers de test
        if check_result is None:
            continue
        
        if not check_result['has_photos']:
            missing_photos.append(check_result)
            print(f"❌ {check_result['id']}: Aucune photo (JSON: {check_result['photos_json']}, Téléchargées: {check_result['photos_downloaded']})")
        elif check_result['missing_data']:
            missing_data_only.append(check_result)
            print(f"⚠️ {check_result['id']}: Photos OK mais données manquantes: {', '.join(check_result['missing_data'])}")
        else:
            complete_apartments.append(check_result)
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"   ✅ Appartements complets: {len(complete_apartments)}")
    print(f"   ❌ Appartements sans photos: {len(missing_photos)}")
    print(f"   ⚠️ Appartements avec données manquantes: {len(missing_data_only)}")
    
    if missing_photos:
        print(f"\n📋 Liste des appartements sans photos:")
        for apt in missing_photos:
            url_display = apt.get('url', 'Pas d\'URL')
            print(f"   - {apt['id']}: {url_display[:80]}...")
    
    # Sauvegarder le rapport
    report = {
        'total_apartments': len(apartments),
        'complete': len(complete_apartments),
        'missing_photos': len(missing_photos),
        'missing_data': len(missing_data_only),
        'apartments_missing_photos': [
            {
                'id': apt['id'],
                'url': apt['url'],
                'photos_json': apt['photos_json'],
                'photos_downloaded': apt['photos_downloaded']
            }
            for apt in missing_photos
        ],
        'apartments_missing_data': [
            {
                'id': apt['id'],
                'url': apt['url'],
                'missing_data': apt['missing_data']
            }
            for apt in missing_data_only
        ]
    }
    
    report_file = "data/missing_photos_report.json"
    os.makedirs("data", exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Rapport sauvegardé: {report_file}")
    
    # Retourner les appartements à rescraper (sans photos + données manquantes)
    to_rescrape = missing_photos + missing_data_only
    
    return to_rescrape

async def rescrape_apartments(apartments_to_rescrape):
    """Relance le scraping pour les appartements sans photos"""
    if not apartments_to_rescrape:
        print("\n✅ Aucun appartement à rescraper")
        return
    
    print(f"\n🔄 RELANCE DU SCRAPING")
    print("=" * 60)
    print(f"📋 {len(apartments_to_rescrape)} appartements à rescraper\n")
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # Login
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        print("✅ Connexion réussie\n")
        
        success_count = 0
        error_count = 0
        
        for i, apt_check in enumerate(apartments_to_rescrape, 1):
            apartment_id = apt_check['id']
            url = apt_check['url']
            
            print(f"\n🏠 [{i}/{len(apartments_to_rescrape)}] Appartement {apartment_id}")
            print(f"   URL: {url}")
            
            if not url:
                print(f"   ⚠️ Pas d'URL, skip")
                error_count += 1
                continue
            
            try:
                # Scraper l'appartement
                apartment_data = await scraper.scrape_apartment(url)
                
                if apartment_data:
                    # Vérifier si des photos ont été trouvées
                    photos_count = len(apartment_data.get('photos', []))
                    
                    if photos_count > 0:
                        print(f"   ✅ Scraping réussi: {photos_count} photos trouvées")
                        success_count += 1
                    else:
                        print(f"   ⚠️ Scraping réussi mais toujours aucune photo")
                        success_count += 1  # On compte quand même comme succès
                    
                    # Sauvegarder l'appartement (écrase l'ancien)
                    await scraper.save_apartment(apartment_data, skip_if_exists=False)
                else:
                    print(f"   ❌ Échec du scraping")
                    error_count += 1
                
                # Pause entre les requêtes
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                error_count += 1
        
        print(f"\n📊 RÉSULTATS FINAUX:")
        print(f"   ✅ Succès: {success_count}")
        print(f"   ❌ Erreurs: {error_count}")
        print(f"   📈 Taux de succès: {success_count/len(apartments_to_rescrape)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Erreur globale: {e}")
    finally:
        await scraper.cleanup()

async def main():
    """Fonction principale"""
    print("🏠 RELANCE DU SCRAPING POUR APPARTEMENTS SANS PHOTOS")
    print("=" * 60)
    print()
    
    # 1. Identifier les appartements sans photos
    apartments_to_rescrape = identify_missing_photos()
    
    if not apartments_to_rescrape:
        print("\n✅ Tous les appartements ont des photos !")
        return
    
    # 2. Afficher les détails et continuer automatiquement
    print(f"\n⚠️ {len(apartments_to_rescrape)} appartements nécessitent un rescraping")
    print("   Démarrage automatique du rescraping...")
    
    # 3. Relancer le scraping
    await rescrape_apartments(apartments_to_rescrape)
    
    # 4. Ré-analyser après le rescraping
    print("\n🔍 Ré-analyse après rescraping...")
    apartments_after = identify_missing_photos()
    
    if len(apartments_after) < len(apartments_to_rescrape):
        improvement = len(apartments_to_rescrape) - len(apartments_after)
        print(f"\n✅ Amélioration: {improvement} appartements récupérés")
    else:
        print(f"\n⚠️ Aucune amélioration détectée")

if __name__ == "__main__":
    asyncio.run(main())

