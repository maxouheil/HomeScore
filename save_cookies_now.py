#!/usr/bin/env python3
"""
Script rapide pour sauvegarder les cookies depuis un navigateur Selenium ouvert
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from cookie_manager import CookieManager
from config_jinka import JINKA_DASHBOARD_URL
import time

def save_cookies_from_browser():
    """Sauvegarde les cookies depuis un navigateur ouvert"""
    print("=" * 80)
    print("🍪 SAUVEGARDE DES COOKIES")
    print("=" * 80)
    print()
    
    chrome_options = Options()
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_experimental_option("detach", True)  # Garder le navigateur ouvert
    
    manager = CookieManager()
    driver = None
    
    try:
        print("🌐 Ouverture du navigateur...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(JINKA_DASHBOARD_URL)
        
        print("\n✅ Navigateur ouvert !")
        print("📋 Si vous n'êtes pas encore connecté, connectez-vous maintenant")
        print("⏳ Attente de 10 secondes pour que vous puissiez vous connecter...")
        print()
        
        time.sleep(10)
        
        # Récupérer les cookies
        print("🍪 Récupération des cookies...")
        cookies = driver.get_cookies()
        
        if not cookies:
            print("❌ Aucun cookie trouvé. Êtes-vous bien connecté ?")
            print("   Le navigateur reste ouvert, vous pouvez vous connecter et relancer ce script")
            return False
        
        print(f"✅ {len(cookies)} cookie(s) trouvé(s)")
        
        # Sauvegarder
        if manager.save_cookies(cookies, source='selenium'):
            print("\n✅ Cookies sauvegardés avec succès !")
            print("   Vous pouvez maintenant utiliser fetch_jinka_apartments.py")
            print("\n🔒 Fermeture du navigateur dans 3 secondes...")
            time.sleep(3)
            driver.quit()
            return True
        else:
            print("\n❌ Erreur lors de la sauvegarde")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            print("\n⚠️  Le navigateur reste ouvert pour que vous puissiez réessayer")
        return False

if __name__ == "__main__":
    save_cookies_from_browser()

