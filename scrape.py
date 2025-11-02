#!/usr/bin/env python3
"""
Scraping simplifié - Scraping + analyse images IA
Utilise scrape_jinka.py pour le scraping et analyze_apartment_style.py pour l'analyse IA
"""

import json
import os
import asyncio
from scrape_jinka import JinkaScraper
from analyze_apartment_style import ApartmentStyleAnalyzer


async def scrape_and_analyze(urls=None, alert_url=None):
    """
    Scrape les appartements et analyse avec IA images
    
    Args:
        urls: List d'URLs d'appartements à scraper (optionnel)
        alert_url: URL de l'alerte Jinka à scraper (optionnel)
        
    Returns:
        List de dicts avec données scrapées + analyses IA
    """
    scraper = JinkaScraper()
    style_analyzer = ApartmentStyleAnalyzer()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # Login
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return []
        
        apartments = []
        
        # Scraper depuis alert_url ou urls
        if alert_url:
            await scraper.scrape_alert_page(alert_url)
            apartment_urls = [apt.get('url') for apt in scraper.apartments if apt.get('url')]
        elif urls:
            apartment_urls = urls
        else:
            print("❌ Aucune URL fournie")
            return []
        
        print(f"📋 {len(apartment_urls)} appartements à traiter")
        
        # Scraper chaque appartement
        for i, url in enumerate(apartment_urls, 1):
            print(f"\n🏠 Scraping {i}/{len(apartment_urls)}: {url}")
            
            apartment_data = await scraper.scrape_apartment(url)
            if not apartment_data:
                continue
            
            # Analyser le style avec IA images (style, cuisine, luminosité)
            print("   🎨 Analyse IA des photos...")
            try:
                style_analysis = style_analyzer.analyze_apartment_photos_from_data(apartment_data)
                if style_analysis:
                    apartment_data['style_analysis'] = style_analysis
                    print(f"   ✅ Style: {style_analysis.get('style', {}).get('type', 'N/A')}")
                    print(f"   ✅ Cuisine: {'Ouverte' if style_analysis.get('cuisine', {}).get('ouverte', False) else 'Fermée'}")
                    print(f"   ✅ Luminosité: {style_analysis.get('luminosite', {}).get('type', 'N/A')}")
            except Exception as e:
                print(f"   ⚠️ Erreur analyse style: {e}")
            
            apartments.append(apartment_data)
        
        return apartments
        
    finally:
        await scraper.cleanup()


def save_scraped_apartments(apartments):
    """Sauvegarde les appartements scrapés dans data/scraped_apartments.json"""
    os.makedirs('data', exist_ok=True)
    with open('data/scraped_apartments.json', 'w', encoding='utf-8') as f:
        json.dump(apartments, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Données sauvegardées: data/scraped_apartments.json ({len(apartments)} appartements)")


async def main():
    """Fonction principale"""
    print("🏠 Scraping + Analyse IA")
    print("=" * 50)
    
    # Charger URLs depuis config ou utiliser alert_url
    import sys
    alert_url = None
    if len(sys.argv) > 1:
        alert_url = sys.argv[1]
    else:
        # Essayer de charger depuis config.json
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                alert_url = config.get('alert_url')
        except:
            pass
    
    if not alert_url:
        print("❌ Aucune URL d'alerte fournie")
        print("Usage: python scrape.py <alert_url>")
        return
    
    # Scraper et analyser
    apartments = await scrape_and_analyze(alert_url=alert_url)
    
    if apartments:
        save_scraped_apartments(apartments)
        print(f"\n🎉 {len(apartments)} appartements scrapés et analysés!")
    else:
        print("\n❌ Aucun appartement scrapé")


if __name__ == "__main__":
    asyncio.run(main())


