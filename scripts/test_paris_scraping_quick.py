#!/usr/bin/env python3
"""
Test rapide pour vérifier pourquoi seulement 42 appartements sont récupérés
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from jinka_api_client import JinkaAPIClient
from scrape_jinka_api import JinkaAPIScraper


async def quick_test():
    """Test rapide de la récupération des alertes"""
    print("🔍 TEST RAPIDE - SCRAPING PARIS")
    print("=" * 60)
    
    scraper = JinkaAPIScraper()
    
    try:
        # 1. Connexion
        print("\n1️⃣ Connexion...")
        await scraper.setup()
        if not await scraper.login():
            print("❌ Échec connexion")
            return
        print("✅ Connecté\n")
        
        # 2. Récupérer les alertes
        print("2️⃣ Récupération des alertes...")
        alerts = await scraper.api_client.get_alert_list()
        
        if not alerts or not isinstance(alerts, list):
            print("❌ Aucune alerte trouvée")
            return
        
        print(f"✅ {len(alerts)} alertes trouvées\n")
        
        # Afficher les noms des alertes
        print("📋 Liste des alertes:")
        for i, alert in enumerate(alerts[:15], 1):
            name = alert.get('name') or alert.get('title') or alert.get('label') or f'Alerte {i}'
            token = alert.get('token') or alert.get('id') or 'N/A'
            print(f"   {i}. {name} (token: {token[:8]}...)")
        
        # 3. Tester le scraping d'une seule alerte (la première)
        if alerts:
            first_alert = alerts[0]
            alert_token = first_alert.get('token') or first_alert.get('id') or ''
            alert_name = first_alert.get('name') or first_alert.get('title') or 'Alerte test'
            
            if alert_token:
                print(f"\n3️⃣ Test scraping de l'alerte: {alert_name}")
                print(f"   Token: {alert_token}")
                
                alert_url = f"https://www.jinka.fr/asrenter/alert/dashboard/{alert_token}"
                
                # Scraper seulement la première page pour le test
                apartments = await scraper.scrape_alert_page(
                    alert_url,
                    filter_type="all",
                    max_pages=1  # Seulement page 1 pour le test rapide
                )
                
                print(f"   ✅ {len(apartments)} appartements trouvés (page 1)")
                
                # Compter les appartements Paris
                paris_count = 0
                for apt in apartments:
                    api_data = apt.get('_api_data', {})
                    postal_code = api_data.get('postal_code', '')
                    if postal_code and postal_code.startswith('75'):
                        paris_count += 1
                
                print(f"   🏙️  {paris_count} appartements Paris (page 1)")
                
                # Vérifier le total depuis l'API
                dashboard_data = await scraper.api_client.get_alert_dashboard(
                    alert_token=alert_token,
                    filter_type="all",
                    page=1
                )
                
                if dashboard_data:
                    pagination = dashboard_data.get('pagination', {})
                    total = pagination.get('total', 0)
                    print(f"   📊 Total API: {total} appartements")
                    
                    if total > len(apartments):
                        print(f"   ⚠️  Il y a {total - len(apartments)} appartements supplémentaires sur les autres pages")
        
        # 4. Vérifier le fichier existant
        print("\n4️⃣ Vérification du fichier existant...")
        paris_file = Path('data/paris_apartments.json')
        if paris_file.exists():
            with open(paris_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            print(f"   📄 {len(existing)} appartements dans paris_apartments.json")
            
            # Vérifier les tokens des alertes utilisées
            alert_tokens_used = set()
            for apt in existing:
                url = apt.get('url', '')
                if 'token=' in url:
                    import re
                    match = re.search(r'token=([a-f0-9]{32})', url)
                    if match:
                        alert_tokens_used.add(match.group(1))
            
            print(f"   🔑 {len(alert_tokens_used)} token(s) d'alerte utilisé(s)")
            if alert_tokens_used:
                print(f"   Tokens: {', '.join(list(alert_tokens_used)[:3])}...")
        else:
            print("   ⚠️  Fichier paris_apartments.json n'existe pas")
        
        print("\n💡 CONCLUSION:")
        print("-" * 60)
        print(f"✅ {len(alerts)} alertes disponibles")
        print("⚠️  Pour récupérer tous les appartements Paris:")
        print("   1. Le script doit scraper TOUTES les alertes")
        print("   2. Le script doit scraper TOUTES les pages de chaque alerte")
        print("   3. Le script doit filtrer les appartements Paris (75xxx)")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(quick_test())



