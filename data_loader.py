#!/usr/bin/env python3
"""
Chargeur unifié de données d'appartements
Supporte à la fois le format API et HTML (avec préférence pour l'API)
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional


def load_apartments(prefer_api: bool = True) -> List[Dict]:
    """
    Charge les appartements depuis API ou HTML
    
    Args:
        prefer_api: Préférer les données API si disponibles (défaut: True)
    
    Returns:
        Liste des appartements au format unifié
    """
    data_dir = Path('data')
    
    # Chercher les fichiers API récents
    if prefer_api:
        api_files = sorted(
            data_dir.glob('scraped_apartments_api_*.json'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        if api_files:
            print(f"📡 Chargement depuis API: {api_files[0].name}")
            with open(api_files[0], 'r', encoding='utf-8') as f:
                apartments = json.load(f)
                print(f"✅ {len(apartments)} appartements chargés depuis l'API")
                return apartments
    
    # Fallback sur HTML scraping
    html_file = data_dir / 'scraped_apartments.json'
    if html_file.exists():
        print(f"🌐 Chargement depuis HTML scraping: {html_file.name}")
        with open(html_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
            print(f"✅ {len(apartments)} appartements chargés depuis HTML")
            return apartments
    
    # Chercher dans data/appartements/ (ancien format)
    apartments_dir = data_dir / 'appartements'
    if apartments_dir.exists():
        apartment_files = list(apartments_dir.glob('*.json'))
        if apartment_files:
            print(f"📁 Chargement depuis data/appartements/ ({len(apartment_files)} fichiers)")
            apartments = []
            for apt_file in apartment_files:
                try:
                    with open(apt_file, 'r', encoding='utf-8') as f:
                        apt_data = json.load(f)
                        apartments.append(apt_data)
                except:
                    continue
            if apartments:
                print(f"✅ {len(apartments)} appartements chargés")
                return apartments
    
    print("⚠️  Aucune donnée d'appartement trouvée")
    return []


def load_apartment_by_id(apartment_id: str, prefer_api: bool = True) -> Optional[Dict]:
    """
    Charge un appartement spécifique par son ID
    
    Args:
        apartment_id: ID de l'appartement
        prefer_api: Préférer les données API
    
    Returns:
        Données de l'appartement ou None
    """
    apartments = load_apartments(prefer_api=prefer_api)
    return next((apt for apt in apartments if apt.get('id') == apartment_id), None)


def get_latest_data_source() -> str:
    """
    Retourne la source de données la plus récente
    
    Returns:
        'api', 'html', ou 'none'
    """
    data_dir = Path('data')
    
    # Vérifier API
    api_files = sorted(
        data_dir.glob('scraped_apartments_api_*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if api_files:
        return 'api'
    
    # Vérifier HTML
    html_file = data_dir / 'scraped_apartments.json'
    if html_file.exists():
        return 'html'
    
    return 'none'


if __name__ == "__main__":
    """Test du chargeur"""
    print("🧪 TEST DU CHARGEUR DE DONNÉES")
    print("=" * 60)
    
    apartments = load_apartments()
    
    if apartments:
        print(f"\n✅ {len(apartments)} appartements chargés")
        print(f"\n📊 Source: {get_latest_data_source()}")
        print(f"\n📋 Premier appartement:")
        apt = apartments[0]
        print(f"   ID: {apt.get('id')}")
        print(f"   Titre: {apt.get('titre')}")
        print(f"   Prix: {apt.get('prix')}")
        print(f"   Surface: {apt.get('surface')}")
    else:
        print("\n❌ Aucun appartement trouvé")

