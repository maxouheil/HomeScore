#!/usr/bin/env python3
"""
Scrape directement depuis les URLs d'appartements
Sans ouvrir de nouveau navigateur
"""

import asyncio
import json
import os
from scrape_jinka import JinkaScraper

async def scrape_from_urls(urls_file=None):
    """
    Scrape directement depuis les URLs
    
    Args:
        urls_file: Chemin vers le fichier JSON contenant les URLs (optionnel)
                   Par défaut, essaie plusieurs sources dans l'ordre:
                   1. all_apartment_urls_merged.json (fusion de toutes les sources)
                   2. all_apartment_urls_from_email.json (depuis emails)
                   3. apartment_urls_page1.json (depuis dashboard)
                   4. all_apartments_scores.json (depuis scores existants)
    """
    print("🏠 SCRAPING DIRECT DEPUIS LES URLs")
    print("=" * 50)
    
    apartment_urls = []
    
    # Déterminer le fichier source
    if urls_file:
        source_files = [urls_file]
    else:
        # Ordre de priorité pour les fichiers sources
        source_files = [
            "data/all_apartment_urls_merged.json",
            "data/all_apartment_urls_from_email.json",
            "data/apartment_urls_page1.json",
            "data/scores/all_apartments_scores.json"
        ]
    
    # Charger depuis le premier fichier disponible
    for file_path in source_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Gérer différents formats
                if isinstance(data, list):
                    apartment_urls = [url if isinstance(url, str) else url.get('url', '') for url in data if url]
                elif isinstance(data, dict):
                    if 'urls' in data:
                        apartment_urls = data['urls']
                    else:
                        # Peut être un dict d'objets avec 'url'
                        apartment_urls = [item.get('url', '') for item in data.values() if isinstance(item, dict) and item.get('url')]
                
                # Filtrer les URLs vides
                apartment_urls = [url for url in apartment_urls if url and isinstance(url, str)]
                
                if apartment_urls:
                    print(f"✅ {len(apartment_urls)} URLs chargées depuis: {file_path}")
                    break
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement de {file_path}: {e}")
                continue
    
    if not apartment_urls:
        print("❌ Aucune URL trouvée dans les fichiers sources")
        print("   Fichiers essayés:")
        for f in source_files:
            exists = "✅" if os.path.exists(f) else "❌"
            print(f"   {exists} {f}")
        return False
    
    print()
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        scraped_apartments = []
        
        for i, url in enumerate(apartment_urls, 1):
            print(f"\n🏠 SCRAPING APPARTEMENT {i}/{len(apartment_urls)}")
            print(f"   URL: {url}")
            print("-" * 60)
            
            try:
                # Scraper l'appartement
                apartment_data = await scraper.scrape_apartment(url)
                
                if apartment_data:
                    print(f"   ✅ Appartement scrapé: {apartment_data.get('titre', 'N/A')}")
                    print(f"   💰 Prix: {apartment_data.get('prix', 'N/A')}")
                    print(f"   📐 Surface: {apartment_data.get('surface', 'N/A')}")
                    print(f"   📍 Localisation: {apartment_data.get('localisation', 'N/A')}")
                    
                    scraped_apartments.append(apartment_data)
                else:
                    print(f"   ❌ Échec du scraping")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   Appartements scrapés: {len(scraped_apartments)}")
        
        if scraped_apartments:
            # Sauvegarder les résultats
            os.makedirs("data", exist_ok=True)
            results_file = "data/scraped_apartments.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(scraped_apartments, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Résultats sauvegardés: {results_file}")
            
            # Afficher le résumé
            print(f"\n📋 RÉSUMÉ DES APPARTEMENTS:")
            for i, apt in enumerate(scraped_apartments, 1):
                print(f"   {i}. {apt.get('titre', 'N/A')} - {apt.get('prix', 'N/A')}€")
            
            print(f"\n🎉 SCRAPING RÉUSSI !")
            return True
        else:
            print("❌ Aucun appartement n'a pu être scrapé")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(scrape_from_urls())
