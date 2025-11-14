#!/usr/bin/env python3
"""
Script de scraping utilisant l'API Jinka (plus rapide et stable)
"""

import asyncio
import json
import os
from datetime import datetime
from scrape_jinka_api import JinkaAPIScraper
from photo_manager import download_photos_for_apartments


async def scrape_alert_with_api(alert_url: str, filter_type: str = "all"):
    """
    Scrape une alerte complète avec l'API
    
    Args:
        alert_url: URL de l'alerte (dashboard)
        filter_type: Type de filtre ("all", "seen", "unseen", etc.)
    """
    print("🚀 SCRAPING AVEC L'API JINKA")
    print("=" * 60)
    print(f"URL: {alert_url}")
    print(f"Filtre: {filter_type}")
    print()
    
    scraper = JinkaAPIScraper()
    
    try:
        # Initialisation
        print("1️⃣ Initialisation du client API...")
        await scraper.setup()
        print("✅ Client API initialisé\n")
        
        # Connexion
        print("2️⃣ Connexion à Jinka...")
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return None
        print("✅ Connexion réussie\n")
        
        # Scraping
        print("3️⃣ Scraping de l'alerte...")
        start_time = datetime.now()
        apartments = await scraper.scrape_alert_page(alert_url, filter_type=filter_type)
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   {len(apartments)} appartements récupérés")
        print(f"   Temps total: {elapsed_time:.1f} secondes")
        print(f"   Vitesse: {len(apartments) / elapsed_time:.1f} appartements/seconde")
        
        # Phase 4: Télécharger les photos en local
        if apartments:
            print("\n📸 Phase 4: Téléchargement des photos en local...")
            apartments = download_photos_for_apartments(apartments, max_photos=10)
            print(f"✅ Photos téléchargées pour {len(apartments)} appartements")
        
        # Sauvegarder les résultats
        if apartments:
            os.makedirs('data', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'data/scraped_apartments_api_{timestamp}.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(apartments, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n💾 Résultats sauvegardés dans {output_file}")
            
            # Afficher quelques statistiques
            print(f"\n📈 STATISTIQUES:")
            prices = []
            surfaces = []
            for apt in apartments:
                # Extraire le prix (format: "745 000 €")
                prix_str = apt.get('prix', '').replace(' ', '').replace('€', '').strip()
                try:
                    prix = int(prix_str)
                    prices.append(prix)
                except:
                    pass
                
                # Extraire la surface (format: "65 m²")
                surface_str = apt.get('surface', '').replace('m²', '').strip()
                try:
                    surface = int(surface_str)
                    surfaces.append(surface)
                except:
                    pass
            
            if prices:
                print(f"   Prix moyen: {sum(prices) / len(prices):,.0f} €")
                print(f"   Prix min: {min(prices):,} €")
                print(f"   Prix max: {max(prices):,} €")
            
            if surfaces:
                print(f"   Surface moyenne: {sum(surfaces) / len(surfaces):.1f} m²")
                print(f"   Surface min: {min(surfaces)} m²")
                print(f"   Surface max: {max(surfaces)} m²")
            
            # Compter les photos
            total_photos = sum(len(apt.get('photos', [])) for apt in apartments)
            print(f"   Photos totales: {total_photos}")
            print(f"   Photos moyennes par appartement: {total_photos / len(apartments):.1f}")
        
        return apartments
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        print("\n🧹 Nettoyage...")
        await scraper.cleanup()
        print("✅ Terminé")


async def main():
    """Fonction principale"""
    # URL de votre alerte RP
    alert_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
    
    # Vous pouvez changer le filtre si besoin
    # filter_type = "all"      # Tous les appartements
    # filter_type = "seen"     # Déjà vus
    # filter_type = "unseen"   # Pas encore vus
    
    apartments = await scrape_alert_with_api(alert_url, filter_type="all")
    
    if apartments:
        print(f"\n✅ Scraping terminé avec succès: {len(apartments)} appartements")
    else:
        print("\n❌ Scraping échoué")


if __name__ == "__main__":
    asyncio.run(main())

