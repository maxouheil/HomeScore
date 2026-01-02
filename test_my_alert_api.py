#!/usr/bin/env python3
"""
Récupère les derniers appartements d'une alerte
Sans lancer l'analyse IA, mais en affichant les données au bon format
"""

import asyncio
import json
from datetime import datetime
from scrape_jinka_api import JinkaAPIScraper


def format_apartment(apt, index):
    """Formate un appartement pour un affichage lisible"""
    lines = []
    lines.append("=" * 80)
    lines.append(f"🏠 APPARTEMENT {index}: {apt.get('id', 'N/A')}")
    lines.append("=" * 80)
    
    # Informations principales
    lines.append(f"\n📋 INFORMATIONS PRINCIPALES:")
    lines.append(f"   Titre: {apt.get('titre', 'N/A')}")
    lines.append(f"   Prix: {apt.get('prix', 'N/A')}")
    lines.append(f"   Prix/m²: {apt.get('prix_m2', 'N/A')}")
    lines.append(f"   Surface: {apt.get('surface', 'N/A')}")
    lines.append(f"   Pièces: {apt.get('pieces', 'N/A')}")
    lines.append(f"   Localisation: {apt.get('localisation', 'N/A')}")
    
    if apt.get('localisation_precise'):
        lines.append(f"   Localisation précise: {apt.get('localisation_precise')}")
    
    # Date
    if apt.get('date_creation_annonce'):
        lines.append(f"   Date création: {apt.get('date_creation_annonce')}")
    elif apt.get('scraped_at'):
        lines.append(f"   Scrapé le: {apt.get('scraped_at')}")
    
    # Transports
    if apt.get('transports'):
        lines.append(f"\n🚇 TRANSPORTS:")
        transports = apt.get('transports', [])
        if isinstance(transports, list):
            for transport in transports:
                if isinstance(transport, dict):
                    name = transport.get('name', transport.get('ligne', 'N/A'))
                    distance = transport.get('distance', transport.get('distance_m', 'N/A'))
                    lines.append(f"   - {name}: {distance}")
                else:
                    lines.append(f"   - {transport}")
        elif isinstance(transports, str):
            lines.append(f"   {transports}")
    
    # Description
    if apt.get('description'):
        desc = apt.get('description', '')
        if len(desc) > 300:
            desc = desc[:300] + "..."
        lines.append(f"\n📝 DESCRIPTION:")
        lines.append(f"   {desc}")
    
    # Caractéristiques
    if apt.get('caracteristiques'):
        lines.append(f"\n✨ CARACTÉRISTIQUES:")
        caracteristiques = apt.get('caracteristiques', [])
        if isinstance(caracteristiques, list):
            for carac in caracteristiques:
                lines.append(f"   - {carac}")
        elif isinstance(caracteristiques, str):
            lines.append(f"   {caracteristiques}")
    
    # Détails supplémentaires
    details = []
    if apt.get('etage'):
        details.append(f"Étage: {apt.get('etage')}")
    if apt.get('agence'):
        details.append(f"Agence: {apt.get('agence')}")
    if apt.get('coordinates'):
        coords = apt.get('coordinates', {})
        if isinstance(coords, dict):
            lat = coords.get('lat', coords.get('latitude'))
            lng = coords.get('lng', coords.get('longitude'))
            if lat and lng:
                details.append(f"Coordonnées: {lat}, {lng}")
    
    if details:
        lines.append(f"\n📍 DÉTAILS:")
        for detail in details:
            lines.append(f"   {detail}")
    
    # Photos
    photos = apt.get('photos', [])
    if photos:
        lines.append(f"\n📸 PHOTOS: {len(photos)} photo(s)")
        for i, photo in enumerate(photos[:3], 1):
            if isinstance(photo, dict):
                url = photo.get('url', 'N/A')
                local_path = photo.get('local_path', '')
                if local_path:
                    lines.append(f"   {i}. {local_path}")
                elif url:
                    lines.append(f"   {i}. {url[:80]}...")
            else:
                lines.append(f"   {i}. {photo}")
        if len(photos) > 3:
            lines.append(f"   ... et {len(photos) - 3} autre(s) photo(s)")
    
    # URL
    if apt.get('url'):
        lines.append(f"\n🔗 URL: {apt.get('url')}")
    
    lines.append("")
    return "\n".join(lines)


async def test_my_alert():
    """Récupère les derniers appartements de l'alerte et les affiche au bon format"""
    print("🚀 RÉCUPÉRATION DES DERNIERS APPARTEMENTS DE L'ALERTE")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # URL de l'alerte (token utilisé dans le backend)
    alert_url = "https://www.jinka.fr/asrenter/alert/dashboard/cebed5288c18eafafadb04e048a4e776"
    
    scraper = JinkaAPIScraper()
    
    try:
        print("1️⃣ Initialisation du client API...")
        print("-" * 80)
        await scraper.setup()
        print("✅ Client API initialisé\n")
        
        print("2️⃣ Connexion à Jinka...")
        print("-" * 80)
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        print("✅ Connexion réussie\n")
        
        print("3️⃣ Récupération des appartements de l'alerte...")
        print("-" * 80)
        print(f"   URL: {alert_url}")
        print()
        
        apartments = await scraper.scrape_alert_page(alert_url, filter_type="all", max_pages=50)
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   {len(apartments)} appartements récupérés")
        print()
        
        if not apartments:
            print("⚠️  Aucun appartement trouvé")
            return
        
        # Trier par date (plus récents en premier)
        def get_date(apt):
            date_str = apt.get('date_creation_annonce') or apt.get('scraped_at') or ''
            if date_str:
                try:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    try:
                        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    except:
                        pass
            return datetime.min
        
        sorted_apartments = sorted(apartments, key=get_date, reverse=True)
        
        # Afficher les derniers appartements (10 par défaut)
        print("4️⃣ AFFICHAGE DES DERNIERS APPARTEMENTS")
        print("=" * 80)
        print()
        
        apartments_to_show = sorted_apartments[:10]
        
        for i, apt in enumerate(apartments_to_show, 1):
            print(format_apartment(apt, i))
        
        # Sauvegarder les résultats
        import os
        from pathlib import Path
        
        os.makedirs('data', exist_ok=True)
        
        # Sauvegarder dans test_api_my_alert.json (backup)
        output_file = 'data/test_api_my_alert.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(apartments, f, ensure_ascii=False, indent=2, default=str)
        
        # Fusionner avec scraped_apartments.json (utilisé par le backend)
        scraped_file = Path('data/scraped_apartments.json')
        existing_apartments = {}
        
        if scraped_file.exists():
            try:
                with open(scraped_file, 'r', encoding='utf-8') as f:
                    existing_list = json.load(f)
                    for apt in existing_list:
                        apt_id = str(apt.get('id', ''))
                        if apt_id:
                            existing_apartments[apt_id] = apt
                print(f"\n📂 {len(existing_apartments)} appartements existants chargés")
            except Exception as e:
                print(f"⚠️  Erreur lors du chargement des données existantes: {e}")
        
        # Fusionner : mettre à jour les existants et ajouter les nouveaux
        merged_apartments = []
        updated_count = 0
        new_count = 0
        
        # Créer un dict des nouveaux par ID
        new_by_id = {str(apt.get('id', '')): apt for apt in apartments if apt.get('id')}
        
        # Traiter les appartements existants
        for apt_id, existing_apt in existing_apartments.items():
            if apt_id in new_by_id:
                # Mettre à jour avec les nouvelles données
                new_apt = new_by_id[apt_id]
                merged_apt = existing_apt.copy()
                
                # Mettre à jour les champs manquants ou vides
                fields_to_update = [
                    'prix_m2', 'transports', 'description', 'caracteristiques',
                    'etage', 'agence', 'coordinates', 'map_info', 'photos',
                    'date_creation_annonce', '_api_data', 'exposition',
                    'localisation', 'localisation_precise', 'prix', 'surface', 'pieces', 'titre', 'url'
                ]
                
                for field in fields_to_update:
                    existing_value = merged_apt.get(field)
                    new_value = new_apt.get(field)
                    
                    if not existing_value or existing_value == '' or existing_value == [] or existing_value == {}:
                        if new_value:
                            merged_apt[field] = new_value
                    elif field == 'photos' and new_value and len(new_value) > len(existing_value or []):
                        merged_apt[field] = new_value
                    elif field == '_api_data' and new_value:
                        merged_apt[field] = new_value
                    elif field == 'date_creation_annonce' and new_value:
                        merged_apt[field] = new_value
                
                merged_apartments.append(merged_apt)
                updated_count += 1
            else:
                # Garder l'appartement existant tel quel
                merged_apartments.append(existing_apt)
        
        # Ajouter les nouveaux appartements
        for apt_id, new_apt in new_by_id.items():
            if apt_id not in existing_apartments:
                merged_apartments.append(new_apt)
                new_count += 1
        
        # Sauvegarder dans scraped_apartments.json
        with open(scraped_file, 'w', encoding='utf-8') as f:
            json.dump(merged_apartments, f, ensure_ascii=False, indent=2, default=str)
        
        print("=" * 80)
        print("📊 STATISTIQUES")
        print("=" * 80)
        print(f"Total appartements récupérés: {len(apartments)}")
        print(f"Appartements affichés: {len(apartments_to_show)}")
        print(f"\n💾 Fusion avec scraped_apartments.json:")
        print(f"   ✅ {updated_count} appartements mis à jour")
        print(f"   ✅ {new_count} nouveaux appartements ajoutés")
        print(f"   ✅ {len(existing_apartments) - updated_count} appartements existants préservés")
        print(f"   📁 Total dans scraped_apartments.json: {len(merged_apartments)} appartements")
        print(f"\n💾 Backup sauvegardé dans {output_file}")
        print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🧹 Nettoyage...")
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(test_my_alert())

