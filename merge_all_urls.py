#!/usr/bin/env python3
"""
Script pour fusionner toutes les sources d'URLs d'appartements:
- URLs depuis emails (all_apartment_urls_from_email.json)
- URLs depuis dashboard page 1 (apartment_urls_page1.json)
- URLs existantes dans all_apartments_scores.json
"""

import json
import os
import re
from collections import defaultdict

JINKA_TOKEN = "26c2ec3064303aa68ffa43f7c6518733"

def extract_apartment_id(url):
    """Extrait l'ID d'appartement depuis une URL"""
    match = re.search(r'ad=(\d+)', url)
    return match.group(1) if match else None

def normalize_url(url):
    """Normalise une URL pour la déduplication"""
    if not url:
        return None
    
    # Si c'est juste un ID
    if url.isdigit():
        return f"https://www.jinka.fr/alert_result?token={JINKA_TOKEN}&ad={url}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    
    # Si c'est un lien relatif
    if url.startswith('/'):
        return f"https://www.jinka.fr{url}"
    
    # Si c'est déjà une URL complète
    if url.startswith('http'):
        return url
    
    return None

def load_urls_from_file(filepath, source_name):
    """Charge les URLs depuis un fichier"""
    if not os.path.exists(filepath):
        print(f"⚠️  {source_name}: Fichier non trouvé ({filepath})")
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Gérer différents formats
        if isinstance(data, list):
            urls = data
        elif isinstance(data, dict):
            # Peut être un dictionnaire avec une clé 'urls' ou des objets avec 'url'
            if 'urls' in data:
                urls = data['urls']
            elif 'url' in str(data.values()):
                urls = [item.get('url', '') for item in data.values() if isinstance(item, dict)]
            else:
                urls = []
        else:
            urls = []
        
        # Filtrer et normaliser
        normalized_urls = []
        for url in urls:
            if isinstance(url, dict):
                url = url.get('url', '')
            if url:
                normalized = normalize_url(url)
                if normalized:
                    normalized_urls.append(normalized)
        
        print(f"✅ {source_name}: {len(normalized_urls)} URLs chargées")
        return normalized_urls
        
    except Exception as e:
        print(f"❌ {source_name}: Erreur lors du chargement ({e})")
        return []

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🔗 FUSION DE TOUTES LES SOURCES D'URLs")
    print("=" * 70)
    print()
    
    # Charger depuis toutes les sources
    sources = {
        'Emails': 'data/all_apartment_urls_from_email.json',
        'Dashboard Page 1': 'data/apartment_urls_page1.json',
        'Scores existants': 'data/scores/all_apartments_scores.json'
    }
    
    all_urls_dict = {}  # ID -> URL pour déduplication
    
    for source_name, filepath in sources.items():
        urls = load_urls_from_file(filepath, source_name)
        for url in urls:
            apt_id = extract_apartment_id(url)
            if apt_id:
                # Garder la première URL trouvée pour chaque ID
                if apt_id not in all_urls_dict:
                    all_urls_dict[apt_id] = url
    
    # Convertir en liste triée
    all_urls = sorted(all_urls_dict.values(), key=lambda x: extract_apartment_id(x) or '0')
    
    print("\n" + "=" * 70)
    print(f"📊 RÉSULTATS DE LA FUSION")
    print("=" * 70)
    print(f"🏠 Total URLs uniques: {len(all_urls)}")
    
    # Statistiques par source
    print("\n📈 URLs par source:")
    for source_name, filepath in sources.items():
        urls = load_urls_from_file(filepath, source_name)
        count = sum(1 for url in urls if extract_apartment_id(url) in all_urls_dict)
        print(f"   {source_name}: {count} URLs")
    
    # Sauvegarder
    os.makedirs("data", exist_ok=True)
    output_file = "data/all_apartment_urls_merged.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_urls, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 URLs fusionnées sauvegardées: {output_file}")
    
    # Afficher quelques exemples
    print(f"\n📋 Premières URLs (exemples):")
    for i, url in enumerate(all_urls[:10], 1):
        apt_id = extract_apartment_id(url)
        print(f"   {i}. ID: {apt_id} - {url[:70]}...")
    
    if len(all_urls) > 10:
        print(f"   ... et {len(all_urls) - 10} autres")
    
    print(f"\n✅ TERMINÉ!")
    return all_urls

if __name__ == "__main__":
    main()






