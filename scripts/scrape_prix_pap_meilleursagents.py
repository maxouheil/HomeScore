#!/usr/bin/env python3
"""
Script pour scraper les prix médians depuis PAP.fr ou MeilleursAgents
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from pathlib import Path
from typing import Dict, Optional

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'prix_medians'
OUTPUT_FILE_QUARTIERS = OUTPUT_DIR / 'quartiers_pap.json'
OUTPUT_FILE_STATIONS = OUTPUT_DIR / 'stations_metro.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
}


def scrape_pap_quartier(quartier_code: str, quartier_name: str) -> Optional[Dict]:
    """
    Scrape le prix médian depuis PAP.fr pour un quartier
    
    Format URL : https://www.pap.fr/vendeur/prix-m2/paris-75-g439
    où g439 est le code du quartier
    
    Args:
        quartier_code: Code quartier (ex: "g439")
        quartier_name: Nom du quartier (ex: "Sainte-Marguerite")
        
    Returns:
        Dict avec prix_median_m2 ou None si erreur
    """
    url = f"https://www.pap.fr/vendeur/prix-m2/paris-75-{quartier_code}"
    
    print(f"  🌐 Scraping {quartier_name} ({quartier_code})...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher le prix médian dans la page
        # Structure HTML peut varier, essayer plusieurs sélecteurs
        prix_median = None
        
        # Méthode 1: Chercher dans les métadonnées ou données structurées
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                # Chercher prix dans les données structurées
                if isinstance(data, dict):
                    if 'offers' in data and 'price' in data['offers']:
                        prix_median = data['offers']['price']
                        break
            except:
                pass
        
        # Méthode 2: Chercher dans le texte avec regex
        if prix_median is None:
            page_text = soup.get_text()
            
            # Patterns possibles pour trouver le prix
            patterns = [
                r'(\d+[\s,\.]?\d+)\s*€\s*/?\s*m[²2]',  # "9 012 €/m²"
                r'prix[:\s]+(\d+[\s,\.]?\d+)\s*€',      # "Prix: 9012 €"
                r'médian[:\s]+(\d+[\s,\.]?\d+)\s*€',    # "Médian: 9012 €"
                r'appartements[:\s]+(\d+[\s,\.]?\d+)\s*€',  # "Appartements: 9012 €"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    # Prendre le premier match qui ressemble à un prix médian
                    for match in matches:
                        prix_str = match.replace(' ', '').replace(',', '').replace('.', '')
                        try:
                            prix_num = int(prix_str)
                            if 5000 <= prix_num <= 20000:  # Prix raisonnable pour Paris
                                prix_median = prix_num
                                break
                        except:
                            pass
                    if prix_median:
                        break
        
        # Méthode 3: Chercher dans des classes CSS spécifiques
        if prix_median is None:
            selectors = [
                '.prix-median',
                '.price-median',
                '[data-price-median]',
                '.stat-price',
                '.prix-m2',
                '.price-m2',
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
            print(f"  ✅ Prix trouvé: {prix_median} €/m²")
            return {
                'quartier': quartier_name,
                'code': quartier_code,
                'prix_median_m2': prix_median,
                'source': 'pap.fr',
                'url': url
            }
        else:
            print(f"  ⚠️  Prix non trouvé")
            return None
            
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return None


def scrape_meilleursagents_quartier(quartier_name: str, arrondissement: str) -> Optional[Dict]:
    """
    Scrape le prix médian depuis MeilleursAgents pour un quartier
    
    Format URL : https://www.meilleursagents.com/prix-immobilier/paris-75011/sainte-marguerite/
    
    Args:
        quartier_name: Nom du quartier (ex: "Sainte-Marguerite")
        arrondissement: Code arrondissement (ex: "75011")
        
    Returns:
        Dict avec prix_median_m2 ou None si erreur
    """
    # Normaliser le nom du quartier pour l'URL
    quartier_url = quartier_name.lower().replace(' ', '-').replace("'", '-')
    url = f"https://www.meilleursagents.com/prix-immobilier/paris-{arrondissement}/{quartier_url}/"
    
    print(f"  🌐 Scraping MeilleursAgents {quartier_name} ({arrondissement})...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher le prix médian
        prix_median = None
        
        # Méthode 1: Chercher dans les données structurées JSON-LD
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if 'offers' in data and 'price' in data['offers']:
                        prix_median = data['offers']['price']
                        break
            except:
                pass
        
        # Méthode 2: Chercher dans le texte
        if prix_median is None:
            page_text = soup.get_text()
            patterns = [
                r'appartements[:\s]+(\d+[\s,\.]?\d+)\s*€\s*/?\s*m[²2]',
                r'prix[:\s]+(\d+[\s,\.]?\d+)\s*€\s*/?\s*m[²2]',
                r'(\d+[\s,\.]?\d+)\s*€\s*/?\s*m[²2]',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
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
        
        # Méthode 3: Chercher dans des éléments spécifiques
        if prix_median is None:
            # Chercher des éléments avec classes communes pour prix
            price_elements = soup.find_all(['span', 'div', 'p'], class_=re.compile(r'price|prix|median|m2', re.I))
            for elem in price_elements:
                text = elem.get_text()
                match = re.search(r'(\d+[\s,\.]?\d+)\s*€', text)
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
            print(f"  ✅ Prix trouvé: {prix_median} €/m²")
            return {
                'quartier': quartier_name,
                'arrondissement': arrondissement,
                'prix_median_m2': prix_median,
                'source': 'meilleursagents',
                'url': url
            }
        else:
            print(f"  ⚠️  Prix non trouvé")
            return None
            
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return None


def main():
    """Fonction principale"""
    print("=" * 60)
    print("📊 SCRAPING PRIX MÉDIANS - PAP.fr / MeilleursAgents")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Liste des quartiers à scraper (exemples)
    # Format: (code_pap, nom_quartier, arrondissement, station_proche)
    quartiers = [
        # Exemples basés sur vos captures d'écran
        ("g439", "Sainte-Marguerite", "75011", "Alexandre Dumas"),
        ("gXXX", "Hôpital Saint-Louis", "75010", "Goncourt"),  # Code à trouver
        # Ajouter d'autres quartiers ici
    ]
    
    results = {}
    
    print("\n🏙️  Scraping des quartiers...\n")
    
    for code, nom, arr, station in quartiers:
        print(f"\n📍 {nom} ({arr}) - Station proche: {station}")
        
        # Essayer PAP.fr d'abord
        result_pap = scrape_pap_quartier(code, nom)
        if result_pap:
            results[nom] = {
                **result_pap,
                'station_proche': station,
                'arrondissement': arr
            }
            time.sleep(2)  # Rate limiting
            continue
        
        # Fallback: MeilleursAgents
        result_ma = scrape_meilleursagents_quartier(nom, arr)
        if result_ma:
            results[nom] = {
                **result_ma,
                'station_proche': station
            }
        
        time.sleep(2)  # Rate limiting
    
    # Sauvegarder les résultats
    if results:
        with open(OUTPUT_FILE_QUARTIERS, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvegardés dans {OUTPUT_FILE_QUARTIERS}")
        print(f"   {len(results)} quartiers traités")
    else:
        print("\n⚠️  Aucun résultat trouvé")


if __name__ == "__main__":
    main()

