#!/usr/bin/env python3
"""
Script pour scraper les prix médians par arrondissement depuis MeilleursAgents
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time
from pathlib import Path

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'prix_medians'
OUTPUT_FILE = OUTPUT_DIR / 'arrondissements.json'
CACHE_DIR = OUTPUT_DIR / 'cache_meilleursagents'

# Arrondissements de Paris
ARRONDISSEMENTS = {
    '75001': '1er',
    '75002': '2e',
    '75003': '3e',
    '75004': '4e',
    '75005': '5e',
    '75006': '6e',
    '75007': '7e',
    '75008': '8e',
    '75009': '9e',
    '75010': '10e',
    '75011': '11e',
    '75012': '12e',
    '75013': '13e',
    '75014': '14e',
    '75015': '15e',
    '75016': '16e',
    '75017': '17e',
    '75018': '18e',
    '75019': '19e',
    '75020': '20e',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def ensure_dirs():
    """Crée les répertoires nécessaires"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def scrape_meilleursagents_median(postal_code: str) -> dict:
    """
    Scrape le prix médian depuis MeilleursAgents pour un arrondissement
    
    Args:
        postal_code: Code postal (ex: "75010")
        
    Returns:
        Dict avec prix_median_m2 et autres infos, ou None si erreur
    """
    url = f"https://www.meilleursagents.com/prix-immobilier/paris-{postal_code}/"
    
    # Vérifier le cache
    cache_file = CACHE_DIR / f"{postal_code}.html"
    if cache_file.exists():
        print(f"  📦 Utilisation du cache pour {postal_code}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    else:
        print(f"  🌐 Scraping {url}...")
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            # Sauvegarder dans le cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Rate limiting
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ Erreur pour {postal_code}: {e}")
            return None
    
    # Parser le HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Chercher le prix médian
    # Structure HTML peut varier, essayer plusieurs sélecteurs
    prix_median = None
    
    # Méthode 1: Chercher dans les métadonnées JSON-LD
    json_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and 'offers' in data:
                if 'price' in data['offers']:
                    prix_median = data['offers']['price']
                    break
        except:
            pass
    
    # Méthode 2: Chercher dans le texte avec regex
    if prix_median is None:
        # Chercher pattern "X XXX €/m²" ou "X,XXX €/m²"
        prix_patterns = [
            r'(\d+[\s,\.]?\d+)\s*€\s*/?\s*m[²2]',
            r'prix[:\s]+(\d+[\s,\.]?\d+)\s*€',
            r'médian[:\s]+(\d+[\s,\.]?\d+)\s*€',
        ]
        
        page_text = soup.get_text()
        for pattern in prix_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                # Prendre le premier match qui ressemble à un prix médian (entre 5000 et 20000)
                for match in matches:
                    prix_str = match.replace(' ', '').replace(',', '').replace('.', '')
                    try:
                        prix_num = int(prix_str)
                        if 5000 <= prix_num <= 20000:
                            prix_median = prix_num
                            break
                    except:
                        pass
                if prix_median:
                    break
    
    # Méthode 3: Chercher dans les classes CSS spécifiques
    if prix_median is None:
        # Sélecteurs possibles (à adapter selon la structure réelle)
        selectors = [
            '.prix-median',
            '.price-median',
            '[data-price-median]',
            '.stat-price',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text()
                match = re.search(r'(\d+[\s,\.]?\d+)', text)
                if match:
                    prix_str = match.group(1).replace(' ', '').replace(',', '').replace('.', '')
                    try:
                        prix_num = int(prix_str)
                        if 5000 <= prix_num <= 20000:
                            prix_median = prix_num
                            break
                    except:
                        pass
                if prix_median:
                    break
            if prix_median:
                break
    
    if prix_median:
        return {
            'prix_median_m2': prix_median,
            'source': 'meilleursagents',
            'url': url
        }
    
    return None


def load_existing_medians() -> dict:
    """Charge les médians existants depuis le fichier JSON"""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_medians(medians: dict):
    """Sauvegarde les médians dans le fichier JSON"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(medians, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Médians sauvegardés dans {OUTPUT_FILE}")


def main():
    """Fonction principale"""
    print("=" * 60)
    print("📊 SCRAPING PRIX MÉDIANS MEILLEURSAGENTS")
    print("=" * 60)
    
    ensure_dirs()
    
    # Charger les médians existants
    medians = load_existing_medians()
    
    # Scraper chaque arrondissement
    for postal_code, arr in ARRONDISSEMENTS.items():
        print(f"\n🏙️  {arr} arrondissement ({postal_code})")
        
        # Skip si déjà présent et récent (optionnel)
        if postal_code in medians:
            print(f"  ✅ Déjà présent: {medians[postal_code].get('prix_median_m2')} €/m²")
            continue
        
        # Scraper
        result = scrape_meilleursagents_median(postal_code)
        
        if result:
            medians[postal_code] = {
                'arrondissement': arr,
                **result,
                'last_updated': time.strftime('%Y-%m-%d')
            }
            print(f"  ✅ Prix médian: {result['prix_median_m2']} €/m²")
        else:
            print(f"  ⚠️  Impossible de récupérer le prix médian")
    
    # Sauvegarder
    save_medians(medians)
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"Arrondissements traités: {len(medians)}")
    for postal_code, data in sorted(medians.items()):
        arr = data.get('arrondissement', '?')
        prix = data.get('prix_median_m2', 'N/A')
        print(f"  {arr:3s} ({postal_code}): {prix} €/m²")


if __name__ == "__main__":
    main()

