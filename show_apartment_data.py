#!/usr/bin/env python3
"""
Affiche toutes les données clés d'un appartement pour le projet
"""

import json
import os
from pathlib import Path


def show_apartment_data(apartment_id: str = None):
    """Affiche toutes les données clés d'un appartement"""
    
    # Trouver le fichier le plus récent
    data_dir = Path('data')
    json_files = list(data_dir.glob('scraped_apartments_api_*.json'))
    
    if not json_files:
        print("❌ Aucun fichier de données trouvé")
        return
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Fichier: {latest_file}\n")
    
    # Charger les données
    with open(latest_file, 'r', encoding='utf-8') as f:
        apartments = json.load(f)
    
    if not apartments:
        print("❌ Aucun appartement dans le fichier")
        return
    
    # Sélectionner un appartement
    if apartment_id:
        apartment = next((apt for apt in apartments if apt['id'] == apartment_id), None)
        if not apartment:
            print(f"❌ Appartement {apartment_id} non trouvé")
            return
    else:
        # Prendre le premier appartement avec le plus de données
        apartment = max(apartments, key=lambda apt: len(apt.get('photos', [])) + len(apt.get('description', '')))
    
    print("=" * 80)
    print("🏠 DONNÉES CLÉS D'UN APPARTEMENT")
    print("=" * 80)
    print()
    
    # IDENTIFICATION
    print("📋 IDENTIFICATION")
    print("-" * 80)
    print(f"ID:                    {apartment.get('id')}")
    print(f"URL:                   {apartment.get('url')}")
    print(f"Titre:                 {apartment.get('titre')}")
    print(f"Date de scraping:      {apartment.get('scraped_at')}")
    print()
    
    # PRIX ET SURFACE
    print("💰 PRIX ET SURFACE")
    print("-" * 80)
    print(f"Prix:                  {apartment.get('prix')}")
    print(f"Prix au m²:            {apartment.get('prix_m2')}")
    print(f"Surface:               {apartment.get('surface')}")
    print(f"Pièces:                {apartment.get('pieces')}")
    
    api_data = apartment.get('_api_data', {})
    if api_data:
        print(f"Chambres:              {api_data.get('bedroom', 'N/A')}")
        print(f"Prix secteur:          {api_data.get('price_sector', 'N/A'):,.0f} €/m²" if api_data.get('price_sector') else "Prix secteur:          N/A")
    print()
    
    # LOCALISATION
    print("📍 LOCALISATION")
    print("-" * 80)
    print(f"Localisation:           {apartment.get('localisation')}")
    
    map_info = apartment.get('map_info', {})
    if map_info:
        print(f"Quartier:              {map_info.get('quartier', 'N/A')}")
        metros = map_info.get('metros', [])
        if metros:
            print(f"Métros:                {', '.join(metros)}")
        else:
            print(f"Métros:                N/A")
    
    coordinates = apartment.get('coordinates')
    if coordinates:
        print(f"Coordonnées GPS:        {coordinates.get('latitude')}, {coordinates.get('longitude')}")
    else:
        print(f"Coordonnées GPS:        N/A")
    
    if api_data:
        print(f"Ville:                 {api_data.get('city', 'N/A')}")
        print(f"Code postal:            {api_data.get('postal_code', 'N/A')}")
    print()
    
    # CARACTÉRISTIQUES
    print("🏗️  CARACTÉRISTIQUES")
    print("-" * 80)
    print(f"Étage:                 {apartment.get('etage', 'N/A')}")
    print(f"Caractéristiques:      {apartment.get('caracteristiques', 'N/A')}")
    
    features = api_data.get('features', {}) if api_data else {}
    if features:
        print(f"\nDétails des features:")
        print(f"  Ascenseur:           {'✅' if features.get('lift') == 1 else '❌'}")
        print(f"  Baignoire:           {'✅' if features.get('bath') == 1 else '❌'}")
        print(f"  Douche:              {'✅' if features.get('shower') == 1 else '❌'}")
        print(f"  Parking:             {'✅' if features.get('parking') == 1 else '❌'}")
        print(f"  Box:                 {'✅' if features.get('box') == 1 else '❌'}")
        print(f"  Balcon:              {'✅' if features.get('balcony') == 1 else '❌'}")
        print(f"  Terrasse:            {'✅' if features.get('terracy') == 1 else '❌'}")
        print(f"  Cave:                {'✅' if features.get('cave') == 1 else '❌'}")
        print(f"  Jardin:              {'✅' if features.get('garden') == 1 else '❌'}")
        if features.get('year'):
            print(f"  Année:                {features.get('year')}")
    
    if api_data:
        print(f"\nType de bien:          {api_data.get('type', 'N/A')}")
        print(f"Meublé:                {'✅' if api_data.get('furnished') == 1 else '❌'}")
        print(f"Type d'achat:          {api_data.get('buy_type', 'N/A')}")
    print()
    
    # AGENCE
    print("🏢 AGENCE")
    print("-" * 80)
    print(f"Agence:                {apartment.get('agence', 'N/A')}")
    if api_data:
        print(f"Source:                {api_data.get('source', 'N/A')}")
        print(f"Type propriétaire:     {api_data.get('owner_type', 'N/A')}")
        if api_data.get('source_logo'):
            print(f"Logo:                  {api_data.get('source_logo')}")
    print()
    
    # PHOTOS
    print("📸 PHOTOS")
    print("-" * 80)
    photos = apartment.get('photos', [])
    print(f"Nombre de photos:      {len(photos)}")
    if photos:
        print(f"\nPremières photos:")
        for i, photo in enumerate(photos[:5], 1):
            print(f"  {i}. {photo.get('url', 'N/A')[:80]}...")
            print(f"     Alt: {photo.get('alt', 'N/A')}")
        if len(photos) > 5:
            print(f"  ... et {len(photos) - 5} autres photos")
    print()
    
    # DESCRIPTION
    print("📝 DESCRIPTION")
    print("-" * 80)
    description = apartment.get('description', '')
    if description:
        # Limiter à 500 caractères
        desc_preview = description[:500] + "..." if len(description) > 500 else description
        print(desc_preview)
    else:
        print("Aucune description disponible")
    print()
    
    # DONNÉES API BRUTES (pour référence)
    print("🔧 DONNÉES API BRUTES (pour référence)")
    print("-" * 80)
    if api_data:
        print(f"Rent (prix):           {api_data.get('rent', 'N/A')} €")
        print(f"Area (surface):        {api_data.get('area', 'N/A')} m²")
        print(f"Room (pièces):         {api_data.get('room', 'N/A')}")
        print(f"Bedroom (chambres):   {api_data.get('bedroom', 'N/A')}")
        print(f"Floor (étage):         {api_data.get('floor', 'N/A')}")
        print(f"Created at:           {api_data.get('created_at', 'N/A')}")
        print(f"Expired at:           {api_data.get('expired_at', 'N/A')}")
        print(f"Favorite:             {api_data.get('favorite', False)}")
    print()
    
    # TRANSPORTS
    print("🚇 TRANSPORTS")
    print("-" * 80)
    transports = apartment.get('transports', [])
    if transports:
        print(f"Stations:              {', '.join(transports)}")
    else:
        print("Aucune information de transport disponible")
    print()
    
    print("=" * 80)
    print(f"✅ Données complètes de l'appartement {apartment.get('id')}")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    apartment_id = None
    if len(sys.argv) > 1:
        apartment_id = sys.argv[1]
    
    show_apartment_data(apartment_id)

