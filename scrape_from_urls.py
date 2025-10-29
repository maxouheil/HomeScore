#!/usr/bin/env python3
"""
Scrape directement depuis les URLs d'appartements
Sans ouvrir de nouveau navigateur
"""

import asyncio
import json
import os
from scrape_jinka import JinkaScraper

async def scrape_from_urls():
    """Scrape directement depuis les URLs"""
    print("🏠 SCRAPING DIRECT DEPUIS LES URLs")
    print("=" * 50)
    print("24 appartements détectés !")
    print()
    
    # URLs d'appartements (tu peux en ajouter d'autres)
    apartment_urls = [
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90129925&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        # Ajoute d'autres URLs d'appartements ici si tu en as
    ]
    
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
