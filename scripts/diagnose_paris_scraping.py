#!/usr/bin/env python3
"""
Script de diagnostic pour comprendre pourquoi seulement 42 appartements sont récupérés
au lieu de tous les appartements Paris disponibles
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from jinka_api_client import JinkaAPIClient
from scrape_jinka_api import JinkaAPIScraper


def is_paris_apartment(apartment: Dict[str, Any]) -> bool:
    """Vérifie si un appartement est à Paris"""
    api_data = apartment.get('_api_data', {})
    postal_code = api_data.get('postal_code', '')
    
    if postal_code and postal_code.startswith('75'):
        return True
    
    localisation = apartment.get('localisation', '').lower()
    city = api_data.get('city', '').lower()
    
    if 'paris' in localisation or 'paris' in city:
        return True
    
    titre = apartment.get('titre', '').lower()
    if 'paris' in titre:
        return True
    
    return False


async def diagnose_alert(alert: Dict[str, Any], scraper: JinkaAPIScraper) -> Dict[str, Any]:
    """
    Diagnostique une alerte pour voir combien d'appartements Paris elle contient
    
    Returns:
        Dict avec les statistiques de l'alerte
    """
    alert_token = alert.get('token') or alert.get('id') or ''
    alert_name = alert.get('name') or alert.get('title') or alert.get('label') or 'Alerte inconnue'
    
    if not alert_token:
        return {
            'name': alert_name,
            'token': 'N/A',
            'error': 'Token manquant',
            'total_apartments': 0,
            'paris_apartments': 0
        }
    
    print(f"\n🔍 Diagnostic de l'alerte: {alert_name}")
    print(f"   Token: {alert_token}")
    
    alert_url = f"https://www.jinka.fr/asrenter/alert/dashboard/{alert_token}"
    
    try:
        # Scraper seulement la première page pour le diagnostic
        apartments = await scraper.scrape_alert_page(
            alert_url,
            filter_type="all",
            max_pages=1  # Seulement la première page pour le diagnostic
        )
        
        total = len(apartments)
        paris_count = sum(1 for apt in apartments if is_paris_apartment(apt))
        
        # Vérifier aussi via l'API directement pour avoir le total réel
        dashboard_data = await scraper.api_client.get_alert_dashboard(
            alert_token=alert_token,
            filter_type="all",
            page=1
        )
        
        total_from_api = 0
        if dashboard_data:
            pagination = dashboard_data.get('pagination', {})
            total_from_api = pagination.get('total', 0)
        
        result = {
            'name': alert_name,
            'token': alert_token,
            'total_apartments_page1': total,
            'paris_apartments_page1': paris_count,
            'total_from_api': total_from_api,
            'success': True
        }
        
        print(f"   ✅ Page 1: {total} appartements ({paris_count} Paris)")
        if total_from_api > 0:
            print(f"   📊 Total API: {total_from_api} appartements")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return {
            'name': alert_name,
            'token': alert_token,
            'error': str(e),
            'total_apartments': 0,
            'paris_apartments': 0,
            'success': False
        }


async def main():
    """Fonction principale de diagnostic"""
    print("🔍 DIAGNOSTIC DU SCRAPING PARIS")
    print("=" * 60)
    print()
    
    scraper = JinkaAPIScraper()
    
    try:
        # 1. Initialisation
        print("1️⃣ Initialisation...")
        await scraper.setup()
        
        # 2. Connexion
        print("\n2️⃣ Connexion à Jinka...")
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        print("✅ Connexion réussie\n")
        
        # 3. Récupérer toutes les alertes
        print("3️⃣ Récupération des alertes...")
        print("-" * 60)
        
        alerts = await scraper.api_client.get_alert_list()
        
        if not alerts or not isinstance(alerts, list) or len(alerts) == 0:
            print("❌ Aucune alerte trouvée")
            return
        
        print(f"✅ {len(alerts)} alertes trouvées\n")
        
        # 4. Diagnostiquer chaque alerte
        print("4️⃣ Diagnostic de chaque alerte...")
        print("=" * 60)
        
        results = []
        for i, alert in enumerate(alerts, 1):
            print(f"\n[{i}/{len(alerts)}]")
            result = await diagnose_alert(alert, scraper)
            results.append(result)
            
            # Petit délai entre les alertes
            await asyncio.sleep(0.5)
        
        # 5. Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DU DIAGNOSTIC")
        print("=" * 60)
        
        total_paris_page1 = sum(r.get('paris_apartments_page1', 0) for r in results)
        total_from_all_alerts = sum(r.get('total_from_api', 0) for r in results)
        successful_alerts = sum(1 for r in results if r.get('success', False))
        
        print(f"\n✅ Alertes analysées: {len(results)}")
        print(f"✅ Alertes réussies: {successful_alerts}")
        print(f"📊 Total appartements (page 1): {sum(r.get('total_apartments_page1', 0) for r in results)}")
        print(f"🏙️  Appartements Paris (page 1): {total_paris_page1}")
        print(f"📈 Total estimé depuis API: {total_from_all_alerts}")
        
        print("\n📋 Détail par alerte:")
        for r in results:
            name = r.get('name', 'N/A')
            paris = r.get('paris_apartments_page1', 0)
            total_api = r.get('total_from_api', 0)
            status = "✅" if r.get('success') else "❌"
            print(f"   {status} {name}: {paris} Paris (total API: {total_api})")
        
        # 6. Sauvegarder les résultats
        output_file = Path('data/diagnostic_paris_scraping.json')
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_alerts': len(results),
                    'successful_alerts': successful_alerts,
                    'total_paris_page1': total_paris_page1,
                    'total_from_api': total_from_all_alerts
                },
                'alerts': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats sauvegardés: {output_file}")
        
        # 7. Recommandations
        print("\n💡 RECOMMANDATIONS:")
        print("-" * 60)
        
        if total_paris_page1 < 100:
            print("⚠️  Peu d'appartements Paris trouvés sur la page 1")
            print("   → Il faut scraper TOUTES les pages de chaque alerte")
            print("   → Le script scrape_all_paris.py devrait le faire automatiquement")
        
        if successful_alerts < len(results):
            print(f"⚠️  {len(results) - successful_alerts} alertes ont échoué")
            print("   → Vérifier les tokens et les permissions")
        
        if total_from_all_alerts > 0:
            print(f"✅ Potentiel de {total_from_all_alerts} appartements au total")
            print("   → Il faut scraper toutes les pages de toutes les alertes")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(main())



