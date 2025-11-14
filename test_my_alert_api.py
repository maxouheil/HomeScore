#!/usr/bin/env python3
"""
Test du scraper API avec votre alerte
"""

import asyncio
import json
from scrape_jinka_api import JinkaAPIScraper


async def test_my_alert():
    """Test du scraper API avec votre alerte"""
    print("🚀 TEST DU SCRAPER API AVEC VOTRE ALERTE")
    print("=" * 60)
    
    # URL de votre alerte (dashboard)
    alert_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
    
    scraper = JinkaAPIScraper()
    
    try:
        print("\n1️⃣ Initialisation du client API...")
        await scraper.setup()
        print("✅ Client API initialisé")
        
        print("\n2️⃣ Connexion à Jinka...")
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        print("\n3️⃣ Scraping de l'alerte (toutes les pages)...")
        apartments = await scraper.scrape_alert_page(alert_url, max_pages=10)  # Augmenter pour récupérer toutes les pages
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   {len(apartments)} appartements récupérés")
        
        if apartments:
            print(f"\n📋 Détails des appartements:")
            for i, apt in enumerate(apartments[:5], 1):  # Afficher les 5 premiers
                print(f"\n   {i}. Appartement {apt.get('id')}")
                print(f"      Titre: {apt.get('titre', 'N/A')}")
                print(f"      Prix: {apt.get('prix', 'N/A')}")
                print(f"      Surface: {apt.get('surface', 'N/A')}")
                print(f"      Pièces: {apt.get('pieces', 'N/A')}")
                print(f"      Localisation: {apt.get('localisation', 'N/A')}")
                print(f"      Photos: {len(apt.get('photos', []))} photos")
                print(f"      URL: {apt.get('url', 'N/A')[:80]}...")
            
            # Sauvegarder les résultats
            output_file = 'data/test_api_my_alert.json'
            import os
            os.makedirs('data', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(apartments, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n💾 Résultats sauvegardés dans {output_file}")
            
            # Tester le scraping d'un appartement en détail
            if apartments:
                print(f"\n4️⃣ Test du scraping détaillé d'un appartement...")
                first_apt_url = apartments[0].get('url')
                if first_apt_url:
                    print(f"   URL: {first_apt_url}")
                    detailed_apt = await scraper.scrape_apartment(first_apt_url)
                    if detailed_apt:
                        print(f"   ✅ Détails récupérés:")
                        print(f"      Description: {detailed_apt.get('description', 'N/A')[:100]}...")
                        print(f"      Caractéristiques: {detailed_apt.get('caracteristiques', 'N/A')[:100]}...")
                        print(f"      Étage: {detailed_apt.get('etage', 'N/A')}")
                        print(f"      Agence: {detailed_apt.get('agence', 'N/A')}")
        else:
            print("⚠️  Aucun appartement trouvé")
        
        print("\n✅ Test terminé avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🧹 Nettoyage...")
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(test_my_alert())

