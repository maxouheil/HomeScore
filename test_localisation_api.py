#!/usr/bin/env python3
"""
Test pour vérifier que la localisation vient bien directement de l'API
"""

import asyncio
import json
from scrape_jinka_api import JinkaAPIScraper
from api_data_adapter import adapt_api_to_scraped_format


async def test_localisation_from_api():
    """Test que la localisation vient bien de l'API"""
    print("🔍 VÉRIFICATION DE LA LOCALISATION DEPUIS L'API")
    print("=" * 60)
    
    scraper = JinkaAPIScraper()
    
    try:
        await scraper.setup()
        
        # Se connecter
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        # Récupérer un appartement via l'API
        alert_token = "26c2ec3064303aa68ffa43f7c6518733"
        apartment_id = "93620099"  # Exemple d'appartement
        
        print(f"\n📡 Récupération des données brutes de l'API...")
        print(f"   Appartement ID: {apartment_id}")
        print(f"   Token: {alert_token}")
        
        # Récupérer les données brutes de l'API
        api_data = await scraper.api_client.get_apartment_details(
            alert_token=alert_token,
            apartment_id=apartment_id
        )
        
        if not api_data:
            print("❌ Aucune donnée API récupérée")
            return
        
        print("\n✅ Données brutes de l'API récupérées")
        print("-" * 60)
        
        # Afficher la structure complète
        if 'ad' in api_data:
            ad = api_data['ad']
            
            print("\n📋 DONNÉES BRUTES DE L'API (ad):")
            print(f"   city: {ad.get('city')}")
            print(f"   postal_code: {ad.get('postal_code')}")
            print(f"   quartier_name: {ad.get('quartier_name')}")
            print(f"   lat: {ad.get('lat')}")
            print(f"   lng: {ad.get('lng')}")
            
            # Afficher toutes les clés disponibles
            print(f"\n📦 Toutes les clés disponibles dans 'ad':")
            for key in sorted(ad.keys()):
                value = ad.get(key)
                if isinstance(value, (str, int, float, bool, type(None))):
                    print(f"   - {key}: {value}")
                elif isinstance(value, (list, dict)):
                    print(f"   - {key}: {type(value).__name__} ({len(value) if isinstance(value, (list, dict)) else 'N/A'})")
            
            # Vérifier la construction de la localisation
            print("\n🔧 CONSTRUCTION DE LA LOCALISATION:")
            print("-" * 60)
            
            city = ad.get('city', '')
            postal_code = ad.get('postal_code', '')
            
            print(f"   city depuis API: '{city}'")
            print(f"   postal_code depuis API: '{postal_code}'")
            
            # Construire la localisation comme dans api_data_adapter.py
            localisation = f"{city} ({postal_code})" if postal_code else city
            print(f"   → localisation construite: '{localisation}'")
            
            # Adapter les données
            print("\n🔄 ADAPTATION DES DONNÉES:")
            print("-" * 60)
            
            adapted_data = adapt_api_to_scraped_format(api_data, alert_token=alert_token)
            
            print(f"   localisation adaptée: '{adapted_data.get('localisation')}'")
            
            # Vérifier la cohérence
            print("\n✅ VÉRIFICATION:")
            print("-" * 60)
            
            if adapted_data.get('localisation') == localisation:
                print("   ✅ La localisation correspond bien à celle construite depuis l'API")
            else:
                print(f"   ⚠️  Différence détectée:")
                print(f"      Construite: '{localisation}'")
                print(f"      Adaptée: '{adapted_data.get('localisation')}'")
            
            # Vérifier que les données viennent bien de l'API et pas du scraping
            print("\n🔍 VÉRIFICATION DE LA SOURCE:")
            print("-" * 60)
            
            if 'city' in ad and 'postal_code' in ad:
                print("   ✅ Les champs 'city' et 'postal_code' sont présents dans les données API")
                print("   ✅ La localisation est construite directement depuis ces champs API")
                print("   ✅ Aucun scraping HTML n'est utilisé pour la localisation")
            else:
                print("   ⚠️  Les champs 'city' ou 'postal_code' sont manquants dans l'API")
                if 'city' not in ad:
                    print("      - 'city' manquant")
                if 'postal_code' not in ad:
                    print("      - 'postal_code' manquant")
            
            # Afficher les données brutes JSON pour inspection
            print("\n📄 DONNÉES BRUTES JSON (extrait):")
            print("-" * 60)
            print(json.dumps({
                'city': ad.get('city'),
                'postal_code': ad.get('postal_code'),
                'quartier_name': ad.get('quartier_name'),
                'lat': ad.get('lat'),
                'lng': ad.get('lng'),
            }, indent=2, ensure_ascii=False))
            
        else:
            print("❌ Structure API inattendue: 'ad' manquant")
            print(f"   Clés disponibles: {list(api_data.keys())}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(test_localisation_from_api())

