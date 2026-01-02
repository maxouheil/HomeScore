#!/usr/bin/env python3
"""
Script rapide pour sauvegarder les cookies - version simplifiée
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from cookie_manager import CookieManager
from config_jinka import JINKA_DASHBOARD_URL
import time

print("=" * 80)
print("🍪 SAUVEGARDE RAPIDE DES COOKIES")
print("=" * 80)
print()

chrome_options = Options()
chrome_options.add_argument('--window-size=1920,1080')

manager = CookieManager()
driver = None

try:
    print("🌐 Ouverture du navigateur...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(JINKA_DASHBOARD_URL)
    
    print("\n✅ Navigateur ouvert sur:", driver.current_url)
    print("\n" + "="*80)
    print("📋 INSTRUCTIONS IMPORTANTES:")
    print("="*80)
    print("   1. Le navigateur reste OUVERT - ne le fermez pas !")
    print("   2. Connectez-vous à Jinka dans le navigateur")
    print("   3. Une fois connecté et sur le dashboard, REVENEZ ICI")
    print("   4. Appuyez sur ENTRÉE dans ce terminal")
    print("="*80)
    print()
    print("⏳ Le script attend que vous appuyiez sur ENTRÉE...")
    print("   (Prenez votre temps pour vous connecter)")
    print()
    
    try:
        input("👉 Appuyez sur ENTRÉE une fois que vous êtes connecté sur le dashboard...")
    except (EOFError, KeyboardInterrupt):
        print("\n⚠️  Mode non-interactif - attente automatique de 120 secondes...")
        print("   Connectez-vous dans le navigateur, les cookies seront sauvegardés automatiquement")
        time.sleep(120)
    
    # Vérifier la connexion
    print("\n🔍 Vérification de la connexion...")
    time.sleep(2)  # Laisser le temps à la page de se charger
    current_url = driver.current_url
    print(f"   URL actuelle: {current_url[:80]}...")
    
    if '/sign/in' in current_url:
        print("⚠️  Vous semblez toujours sur la page de connexion")
        print("   Tentative de sauvegarde quand même...")
    else:
        print("✅ Vous semblez être connecté !")
    
    # Récupérer les cookies
    print("\n🍪 Récupération des cookies...")
    cookies = driver.get_cookies()
    
    if not cookies:
        print("❌ Aucun cookie trouvé")
        print("   Le navigateur reste ouvert - réessayez de vous connecter")
        print("   Puis relancez ce script")
        input("\n👉 Appuyez sur ENTRÉE pour fermer le navigateur...")
    else:
        print(f"✅ {len(cookies)} cookie(s) trouvé(s)")
        
        if manager.save_cookies(cookies, source='selenium'):
            print("\n" + "="*80)
            print("🎉 SUCCÈS ! Cookies sauvegardés")
            print("="*80)
            print("   Vous pouvez maintenant utiliser:")
            print("   python3 fetch_jinka_apartments.py --test")
            print("="*80)
        else:
            print("\n❌ Erreur lors de la sauvegarde")
        
        print("\n🔒 Fermeture du navigateur dans 3 secondes...")
        time.sleep(3)
    
except KeyboardInterrupt:
    print("\n\n❌ Interrompu")
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    if driver:
        driver.quit()
        print("✅ Navigateur fermé")

