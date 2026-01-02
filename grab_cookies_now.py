#!/usr/bin/env python3
"""
Script pour récupérer les cookies depuis un navigateur Selenium déjà ouvert
OU ouvrir un nouveau navigateur et récupérer les cookies après connexion
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from cookie_manager import CookieManager
from config_jinka import JINKA_DASHBOARD_URL
import time

print("=" * 80)
print("🍪 RÉCUPÉRATION DES COOKIES")
print("=" * 80)
print()

manager = CookieManager()
chrome_options = Options()
chrome_options.add_argument('--window-size=1920,1080')
# Ne pas fermer automatiquement le navigateur
chrome_options.add_experimental_option("detach", True)

driver = None

try:
    print("🌐 Ouverture du navigateur...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(JINKA_DASHBOARD_URL)
    
    print("\n✅ Navigateur ouvert !")
    print(f"   URL: {driver.current_url}")
    print()
    print("📋 Si vous n'êtes pas encore connecté:")
    print("   1. Connectez-vous maintenant dans le navigateur")
    print("   2. Attendez d'être sur le dashboard (pas sur /sign/in)")
    print("   3. Revenez ici et appuyez sur ENTRÉE")
    print()
    print("📋 Si vous êtes déjà connecté:")
    print("   Appuyez sur ENTRÉE maintenant")
    print()
    
    input("👉 Appuyez sur ENTRÉE quand vous êtes prêt...")
    
    # Attendre un peu pour s'assurer que la page est chargée
    time.sleep(2)
    
    # Vérifier l'URL
    current_url = driver.current_url
    print(f"\n🔍 URL actuelle: {current_url}")
    
    if '/sign/in' in current_url:
        print("⚠️  Vous semblez sur la page de connexion")
        print("   Tentative de récupération des cookies quand même...")
    else:
        print("✅ Vous semblez être sur le dashboard")
    
    # Récupérer les cookies
    print("\n🍪 Récupération des cookies...")
    cookies = driver.get_cookies()
    
    if not cookies:
        print("❌ Aucun cookie trouvé")
        print("   Assurez-vous d'être bien connecté")
    else:
        print(f"✅ {len(cookies)} cookie(s) trouvé(s)")
        print(f"   Exemples: {[c.get('name') for c in cookies[:5]]}")
        
        # Sauvegarder
        if manager.save_cookies(cookies, source='selenium'):
            print("\n" + "="*80)
            print("🎉 SUCCÈS ! Cookies sauvegardés")
            print("="*80)
            print("\n✅ Vous pouvez maintenant utiliser:")
            print("   python3 fetch_jinka_apartments.py --test")
            print()
        else:
            print("\n❌ Erreur lors de la sauvegarde")
    
    print("\n🔒 Le navigateur reste ouvert (vous pouvez le fermer manuellement)")
    print("   Appuyez sur ENTRÉE pour terminer le script...")
    input()
    
except KeyboardInterrupt:
    print("\n\n❌ Interrompu")
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n✅ Terminé")

