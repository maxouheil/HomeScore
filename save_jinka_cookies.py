#!/usr/bin/env python3
"""
Script pour sauvegarder les cookies Jinka après une authentification manuelle
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from cookie_manager import CookieManager
from config_jinka import JINKA_DASHBOARD_URL


def save_cookies_interactive():
    """
    Ouvre le navigateur, attend que l'utilisateur se connecte, puis sauvegarde les cookies
    """
    print("=" * 80)
    print("🍪 SAUVEGARDE DES COOKIES JINKA")
    print("=" * 80)
    print()
    print("Instructions:")
    print("1. Le navigateur va s'ouvrir")
    print("2. Connectez-vous à Jinka avec votre compte")
    print("3. Une fois connecté et sur le dashboard, revenez ici")
    print()
    
    chrome_options = Options()
    # Ne pas utiliser headless pour permettre la connexion manuelle
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    driver = None
    manager = CookieManager()
    
    try:
        print("🌐 Ouverture du navigateur...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(JINKA_DASHBOARD_URL)
        
        print("\n✅ Navigateur ouvert !")
        print("📋 Connectez-vous à Jinka dans le navigateur")
        print("⏳ Le script attend que vous soyez connecté...")
        print("   (Il détectera automatiquement quand vous êtes sur le dashboard)")
        print()
        
        # Attendre que l'utilisateur soit connecté (détection automatique)
        max_wait = 300  # 5 minutes max
        wait_interval = 2  # Vérifier toutes les 2 secondes
        waited = 0
        
        while waited < max_wait:
            try:
                current_url = driver.current_url
                
                # Vérifier si on est sur le dashboard (connecté)
                if '/alert/dashboard' in current_url and '/sign/in' not in current_url:
                    # Vérifier aussi qu'il n'y a pas de redirection vers login
                    try:
                        # Attendre un peu pour voir si on reste sur le dashboard
                        time.sleep(2)
                        final_url = driver.current_url
                        if '/alert/dashboard' in final_url and '/sign/in' not in final_url:
                            print("✅ Connexion détectée ! Vous êtes sur le dashboard")
                            break
                    except:
                        pass
                
                # Si on est toujours sur la page de login, continuer à attendre
                if '/sign/in' in current_url:
                    if waited % 10 == 0:  # Afficher un message toutes les 10 secondes
                        print(f"   ⏳ En attente de connexion... ({waited}s)")
                else:
                    # URL différente, peut-être connecté
                    print(f"   🔍 Vérification de l'état de connexion...")
                
                time.sleep(wait_interval)
                waited += wait_interval
                
            except Exception as e:
                print(f"   ⚠️  Erreur lors de la vérification: {e}")
                time.sleep(wait_interval)
                waited += wait_interval
        
        # Vérification finale
        current_url = driver.current_url
        if '/sign/in' in current_url:
            print("\n⚠️  Vous semblez toujours sur la page de connexion")
            print("   Tentative de sauvegarde des cookies quand même...")
        else:
            print("\n✅ Vous êtes connecté !")
        
        # Récupérer les cookies
        cookies = driver.get_cookies()
        
        if not cookies:
            print("❌ Aucun cookie trouvé. Êtes-vous bien connecté ?")
            return False
        
        # Sauvegarder les cookies
        if manager.save_cookies(cookies, source='selenium'):
            print("\n✅ Cookies sauvegardés avec succès !")
            print("   Vous pouvez maintenant utiliser fetch_jinka_apartments.py")
            print("   Les cookies seront automatiquement réutilisés")
            return True
        else:
            print("\n❌ Erreur lors de la sauvegarde des cookies")
            return False
            
    except KeyboardInterrupt:
        print("\n\n❌ Interrompu par l'utilisateur")
        return False
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            print("\n🔒 Fermeture du navigateur...")
            driver.quit()


if __name__ == "__main__":
    save_cookies_interactive()

