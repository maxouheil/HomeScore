#!/usr/bin/env python3
"""
Script qui reste ouvert indéfiniment
"""

import asyncio
import time
from scrape_jinka import JinkaScraper

async def stay_open():
    """Reste ouvert indéfiniment"""
    print("🔐 CONNEXION JINKA - MODE PERMANENT")
    print("=" * 50)
    print("1. Chrome va s'ouvrir")
    print("2. Connecte-toi manuellement")
    print("3. Le script restera ouvert indéfiniment")
    print("4. Appuie sur Ctrl+C pour arrêter")
    print()
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Chrome ouvert")
        
        # Aller au dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(3000)
        
        print()
        print("🔐 CONNEXION MANUELLE REQUISE")
        print("=" * 40)
        print("1. Connecte-toi manuellement dans le navigateur")
        print("2. Une fois connecté, dis-moi 'OK'")
        print("3. Le script restera ouvert")
        print()
        
        # Attendre indéfiniment
        while True:
            await asyncio.sleep(30)
            current_url = scraper.page.url
            print(f"⏳ Script actif... URL: {current_url[:80]}...")
            print("   Appuie sur Ctrl+C pour arrêter")
        
    except KeyboardInterrupt:
        print("\n👋 Script arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("✅ Script terminé")

if __name__ == "__main__":
    asyncio.run(stay_open())
