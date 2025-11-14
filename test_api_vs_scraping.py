#!/usr/bin/env python3
"""
Script de test pour comparer les performances et résultats entre API et scraping HTML
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, List
from scrape_jinka import JinkaScraper
from scrape_jinka_api import JinkaAPIScraper


async def compare_scraping_methods(alert_url: str, max_apartments: int = 5):
    """
    Compare les deux méthodes de scraping sur un même ensemble d'appartements
    
    Args:
        alert_url: URL de l'alerte à tester
        max_apartments: Nombre maximum d'appartements à comparer
    """
    print("🔬 COMPARAISON API vs SCRAPING HTML")
    print("=" * 60)
    print(f"URL d'alerte: {alert_url}")
    print(f"Nombre d'appartements à comparer: {max_apartments}")
    print()
    
    results = {
        'api': {'time': 0, 'apartments': [], 'success': False},
        'scraping': {'time': 0, 'apartments': [], 'success': False}
    }
    
    # Test 1: Scraping via API
    print("📡 TEST 1: SCRAPING VIA API")
    print("-" * 60)
    api_scraper = JinkaAPIScraper()
    
    try:
        start_time = time.time()
        await api_scraper.setup()
        
        if await api_scraper.login():
            apartments = await api_scraper.scrape_alert_page(alert_url, max_pages=1)
            results['api']['apartments'] = apartments[:max_apartments]
            results['api']['time'] = time.time() - start_time
            results['api']['success'] = True
            print(f"✅ API: {len(apartments)} appartements en {results['api']['time']:.2f}s")
        else:
            print("❌ Échec de la connexion API")
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await api_scraper.cleanup()
    
    print()
    
    # Test 2: Scraping HTML
    print("🌐 TEST 2: SCRAPING HTML")
    print("-" * 60)
    html_scraper = JinkaScraper()
    
    try:
        start_time = time.time()
        await html_scraper.setup()
        
        if await html_scraper.login():
            await html_scraper.scrape_alert_page(alert_url)
            results['scraping']['apartments'] = html_scraper.apartments[:max_apartments]
            results['scraping']['time'] = time.time() - start_time
            results['scraping']['success'] = True
            print(f"✅ HTML: {len(html_scraper.apartments)} appartements en {results['scraping']['time']:.2f}s")
        else:
            print("❌ Échec de la connexion HTML")
    except Exception as e:
        print(f"❌ Erreur HTML: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await html_scraper.cleanup()
    
    # Comparaison
    print()
    print("📊 COMPARAISON DES RÉSULTATS")
    print("=" * 60)
    
    if results['api']['success'] and results['scraping']['success']:
        api_count = len(results['api']['apartments'])
        html_count = len(results['scraping']['apartments'])
        
        print(f"Appartements récupérés:")
        print(f"  API:   {api_count}")
        print(f"  HTML:  {html_count}")
        print()
        
        print(f"Temps d'exécution:")
        print(f"  API:   {results['api']['time']:.2f}s")
        print(f"  HTML:  {results['scraping']['time']:.2f}s")
        
        if results['scraping']['time'] > 0:
            speedup = results['scraping']['time'] / results['api']['time']
            print(f"  ⚡ API est {speedup:.2f}x plus rapide")
        print()
        
        # Comparer les données des appartements communs
        print("Comparaison des données:")
        api_ids = {apt['id'] for apt in results['api']['apartments']}
        html_ids = {apt['id'] for apt in results['scraping']['apartments']}
        common_ids = api_ids & html_ids
        
        print(f"  Appartements communs: {len(common_ids)}")
        
        if common_ids:
            # Comparer le premier appartement commun
            api_apt = next(apt for apt in results['api']['apartments'] if apt['id'] in common_ids)
            html_apt = next(apt for apt in results['scraping']['apartments'] if apt['id'] in common_ids)
            
            print(f"\n  Comparaison de l'appartement {api_apt['id']}:")
            
            # Comparer les champs principaux
            fields_to_compare = ['prix', 'surface', 'pieces', 'localisation']
            for field in fields_to_compare:
                api_val = api_apt.get(field, 'N/A')
                html_val = html_apt.get(field, 'N/A')
                match = "✅" if api_val == html_val else "⚠️"
                print(f"    {field}:")
                print(f"      API:   {api_val}")
                print(f"      HTML:  {html_val} {match}")
            
            # Comparer les photos
            api_photos = len(api_apt.get('photos', []))
            html_photos = len(html_apt.get('photos', []))
            print(f"    photos:")
            print(f"      API:   {api_photos}")
            print(f"      HTML:  {html_photos}")
    else:
        print("⚠️  Impossible de comparer (une des méthodes a échoué)")
        if not results['api']['success']:
            print("  ❌ API a échoué")
        if not results['scraping']['success']:
            print("  ❌ HTML a échoué")
    
    # Sauvegarder les résultats
    output_file = 'data/comparison_api_vs_scraping.json'
    os.makedirs('data', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 Résultats sauvegardés dans {output_file}")
    
    return results


async def main():
    """Fonction principale"""
    alert_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
    
    results = await compare_scraping_methods(alert_url, max_apartments=5)
    
    print("\n✅ Comparaison terminée!")


if __name__ == "__main__":
    import os
    asyncio.run(main())

