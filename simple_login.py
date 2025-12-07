#!/usr/bin/env python3
"""
Script simple qui ouvre Chrome et reste ouvert
"""

import asyncio
from scrape_jinka import JinkaScraper

async def simple_login():
    """Ouvre Chrome et reste ouvert"""
    print("🔐 CONNEXION SIMPLE JINKA")
    print("=" * 40)
    print("Chrome va s'ouvrir et rester ouvert")
    print("Connecte-toi manuellement, puis ferme Chrome quand fini")
    print()
    
    scraper = JinkaScraper()
    
    try:
        # 1. Initialiser
        await scraper.setup()
        print("✅ Chrome ouvert")
        
        # 2. Aller à Jinka
        print("🌐 Navigation vers Jinka...")
        await scraper.page.goto("https://www.jinka.fr/sign/in")
        await scraper.page.wait_for_timeout(3000)
        
        # 3. Cliquer sur Google
        print("🔍 Recherche du bouton Google...")
        google_button = await scraper.page.query_selector('button:has-text("Continuer avec Google")')
        if not google_button:
            print("❌ Bouton Google non trouvé")
            return False
        
        print("🖱️ Clic sur Google...")
        await google_button.click()
        await scraper.page.wait_for_timeout(5000)
        
        print("✅ Redirection vers Google réussie")
        print()
        print("🔐 CONNEXION MANUELLE REQUISE")
        print("=" * 40)
        print("1. Saisis ton email: souheil.medaghri@gmail.com")
        print("2. Saisis ton mot de passe: Lbooycz7")
        print("3. Complète toutes les étapes Google (2FA, etc.)")
        print("4. Attends d'être redirigé vers Jinka")
        print("5. Une fois sur Jinka, ferme Chrome")
        print()
        print("⏳ Chrome reste ouvert... (ferme-le quand tu as fini)")
        
        # Attendre indéfiniment que l'utilisateur ferme Chrome
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Script arrêté")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        print("✅ Script terminé")

if __name__ == "__main__":
    asyncio.run(simple_login())
