#!/usr/bin/env python3
"""
Script pour rescraper des appartements spécifiques
"""

import asyncio
import json
from scrape_jinka import JinkaScraper

async def rescrape_specific_apartments(apartment_ids):
    """Rescrape des appartements spécifiques par leur ID"""
    print(f"🔄 RESCRAPING D'APPARTEMENTS SPÉCIFIQUES")
    print("=" * 60)
    print(f"📋 {len(apartment_ids)} appartements à rescraper: {', '.join(apartment_ids)}\n")
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # Login
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        print("✅ Connexion réussie\n")
        
        # Charger les données existantes pour obtenir les URLs
        apartments_data = []
        for apt_id in apartment_ids:
            try:
                with open(f"data/appartements/{apt_id}.json", 'r', encoding='utf-8') as f:
                    apt_data = json.load(f)
                    apartments_data.append(apt_data)
            except FileNotFoundError:
                print(f"⚠️ Fichier non trouvé pour {apt_id}")
                continue
        
        if not apartments_data:
            print("❌ Aucune donnée trouvée")
            return
        
        success_count = 0
        
        for i, apt_data in enumerate(apartments_data, 1):
            apt_id = apt_data.get('id')
            url = apt_data.get('url')
            
            print(f"\n🏠 [{i}/{len(apartments_data)}] Appartement {apt_id}")
            print(f"   📍 {apt_data.get('titre', 'N/A')}")
            print(f"   💰 {apt_data.get('prix', 'N/A')}")
            print(f"   URL: {url}")
            
            if not url:
                print(f"   ⚠️ Pas d'URL, skip")
                continue
            
            try:
                # Scraper l'appartement
                new_apt_data = await scraper.scrape_apartment(url)
                
                if new_apt_data:
                    photos_count = len(new_apt_data.get('photos', []))
                    
                    if photos_count > 0:
                        print(f"   ✅ {photos_count} photos trouvées !")
                        success_count += 1
                    else:
                        print(f"   ⚠️ Toujours aucune photo (peut-être vraiment pas de photos disponibles)")
                    
                    # Sauvegarder
                    await scraper.save_apartment(new_apt_data, skip_if_exists=False)
                else:
                    print(f"   ❌ Échec du scraping")
                
                # Pause entre les requêtes
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   ✅ Appartements avec photos récupérées: {success_count}/{len(apartments_data)}")
        
    except Exception as e:
        print(f"❌ Erreur globale: {e}")
    finally:
        await scraper.cleanup()

async def main():
    """Fonction principale"""
    # IDs des appartements à rescraper
    apartment_ids = [
        "92913102",  # 707k Pyrénées
        "92732956",  # 710k Rue des Boulets
    ]
    
    await rescrape_specific_apartments(apartment_ids)

if __name__ == "__main__":
    asyncio.run(main())





