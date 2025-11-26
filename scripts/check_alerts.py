#!/usr/bin/env python3
"""
Script rapide pour vérifier les alertes disponibles
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from jinka_api_client import JinkaAPIClient


async def main():
    print("🔍 VÉRIFICATION DES ALERTES DISPONIBLES")
    print("=" * 60)
    
    client = JinkaAPIClient()
    
    try:
        print("\n1️⃣ Connexion...")
        if not await client.login():
            print("❌ Échec de la connexion")
            return
        
        print("✅ Connecté\n")
        
        print("2️⃣ Récupération des alertes...")
        alerts = await client.get_alert_list()
        
        if alerts and isinstance(alerts, list) and len(alerts) > 0:
            print(f"\n✅ {len(alerts)} alertes trouvées:\n")
            
            for i, alert in enumerate(alerts, 1):
                name = alert.get('name') or alert.get('title') or alert.get('label') or f'Alerte {i}'
                token = alert.get('token') or alert.get('id') or 'N/A'
                print(f"{i}. {name}")
                print(f"   Token: {token}")
            
            # Sauvegarder dans un fichier
            output_file = Path('data/alert_tokens_auto.json')
            output_file.parent.mkdir(exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Alertes sauvegardées dans {output_file}")
            print(f"\n💡 Le script scrape_all_paris.py utilisera automatiquement ces alertes")
        else:
            print("❌ Aucune alerte trouvée")
            print("   Vérifiez que vous avez créé des alertes sur Jinka")
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())



