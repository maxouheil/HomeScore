#!/usr/bin/env python3
"""
Scraping en batch avec les URLs connues
"""

import asyncio
import json
import os
from scrape_jinka import JinkaScraper

async def batch_scrape_known_urls():
    """Scrape en batch avec les URLs connues"""
    print("🏠 SCRAPING EN BATCH - URLs CONNUES")
    print("=" * 60)
    
    # URLs des appartements qu'on connaît
    known_urls = [
        # Première batch (7 appartements)
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90129925&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=78267327&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92125826&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90466722&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=89529151&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92274287&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91005791&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=88404156&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        
        # Deuxième batch (7 nouveaux appartements)
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92075365&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=92008125&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91908884&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91658092&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=89473319&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=84210379&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=91644200&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        
        # Troisième batch (2 nouveaux appartements)
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=85653922&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
        "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=75507606&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    ]
    
    print(f"📋 URLs connues: {len(known_urls)}")
    print("💡 Pour ajouter plus d'URLs, modifie la liste 'known_urls' dans le script")
    print()
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        scraped_apartments = []
        
        for i, url in enumerate(known_urls, 1):
            print(f"\n🏠 SCRAPING APPARTEMENT {i}/{len(known_urls)}")
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
                    
                    # Analyser le style avec les photos
                    try:
                        from analyze_apartment_style import ApartmentStyleAnalyzer
                        style_analyzer = ApartmentStyleAnalyzer()
                        style_analysis = style_analyzer.analyze_apartment_photos_from_data(apartment_data)
                        if style_analysis:
                            apartment_data['style_analysis'] = style_analysis
                            print(f"   🎨 Style: {style_analysis.get('style', {}).get('type', 'N/A')}")
                            print(f"   🍳 Cuisine: {'Ouverte' if style_analysis.get('cuisine', {}).get('ouverte', False) else 'Fermée'}")
                            print(f"   💡 Luminosité: {style_analysis.get('luminosite', {}).get('type', 'N/A')}")
                    except Exception as e:
                        print(f"   ⚠️ Erreur analyse style: {e}")
                    
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
            results_file = "data/batch_scraped_apartments.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(scraped_apartments, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Résultats sauvegardés: {results_file}")
            
            # Afficher le résumé
            print(f"\n📋 RÉSUMÉ DES APPARTEMENTS:")
            for i, apt in enumerate(scraped_apartments, 1):
                print(f"   {i}. {apt.get('titre', 'N/A')} - {apt.get('prix', 'N/A')}€")
                
                # Afficher l'analyse de style si disponible
                style_analysis = apt.get('style_analysis')
                if style_analysis:
                    style = style_analysis.get('style', {}).get('type', 'N/A')
                    cuisine = 'Ouverte' if style_analysis.get('cuisine', {}).get('ouverte', False) else 'Fermée'
                    luminosite = style_analysis.get('luminosite', {}).get('type', 'N/A')
                    print(f"      🎨 Style: {style}, 🍳 Cuisine: {cuisine}, 💡 Luminosité: {luminosite}")
            
            print(f"\n🎉 SCRAPING EN BATCH RÉUSSI !")
            print(f"   {len(scraped_apartments)} appartements scrapés")
            print(f"   Prêt pour le scoring !")
            
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
    asyncio.run(batch_scrape_known_urls())
