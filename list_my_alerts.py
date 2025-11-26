#!/usr/bin/env python3
"""
Liste toutes vos alertes pour identifier flobibi vs RP
"""

import asyncio
import json
from jinka_api_client import JinkaAPIClient


async def list_all_alerts():
    """Liste toutes les alertes disponibles"""
    print("🔍 LISTE DE VOS ALERTES")
    print("=" * 60)
    
    client = JinkaAPIClient()
    
    try:
        print("\n1️⃣ Connexion...")
        if not await client.login():
            print("❌ Échec de la connexion")
            return
        
        print("\n2️⃣ Récupération de la liste des alertes...")
        alerts = await client.get_alert_list()
        
        if alerts:
            print(f"\n✅ {len(alerts)} alerte(s) trouvée(s):\n")
            
            for i, alert in enumerate(alerts, 1):
                alert_id = alert.get('id', 'N/A')
                token = alert.get('token', 'N/A')
                user_name = alert.get('user_name', 'N/A')
                state = alert.get('state', 'N/A')
                price = alert.get('price', 'N/A')
                area_min = alert.get('area_min_used', 'N/A')
                
                print(f"{i}. Alerte: {user_name}")
                print(f"   ID: {alert_id}")
                print(f"   Token: {token}")
                print(f"   État: {state}")
                print(f"   Prix max: {price}€")
                print(f"   Surface min: {area_min}m²")
                print(f"   URL: https://www.jinka.fr/asrenter/alert/dashboard/{token}")
                print()
            
            # Sauvegarder
            output_file = 'data/my_alerts.json'
            import os
            os.makedirs('data', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 Liste sauvegardée dans {output_file}")
        else:
            print("⚠️  Aucune alerte trouvée")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(list_all_alerts())




