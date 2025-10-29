#!/usr/bin/env python3
"""
Script qui reste ouvert et attend
"""

import asyncio
import time
from scrape_jinka import JinkaScraper

async def keep_open():
    """Garde Chrome ouvert et attend"""
    print("🔐 CONNEXION JINKA - MODE ATTENTE")
    print("=" * 50)
    print("1. Chrome va s'ouvrir")
    print("2. Connecte-toi manuellement")
    print("3. Le script restera ouvert")
    print()
    
    scraper = JinkaScraper()
    
    try:
        # 1. Initialiser
        await scraper.setup()
        print("✅ Chrome ouvert")
        
        # 2. Aller à Jinka
        print("🌐 Navigation vers Jinka...")
        await scraper.page.goto("https://www.jinka.fr/sign/in")
        await scraper.page.wait_for_timeout(5000)
        
        print()
        print("🔐 CONNEXION MANUELLE REQUISE")
        print("=" * 40)
        print("1. Clique sur 'Continuer avec Google'")
        print("2. Saisis ton email: souheil.medaghri@gmail.com")
        print("3. Saisis ton mot de passe: Lbooycz7")
        print("4. Complète toutes les étapes Google (2FA, etc.)")
        print("5. Attends d'être redirigé vers Jinka")
        print()
        print("⏳ Chrome reste ouvert... (ferme-le quand tu as fini)")
        
        # Attendre indéfiniment
        while True:
            await asyncio.sleep(10)
            print("⏳ J'attends... (ferme Chrome quand tu as fini)")
        
    except KeyboardInterrupt:
        print("\n👋 Script arrêté")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("✅ Script terminé")

if __name__ == "__main__":
    asyncio.run(keep_open())
