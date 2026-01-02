#!/usr/bin/env python3
"""
Script AUTOMATIQUE pour sauvegarder les cookies - détection automatique de la connexion
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from cookie_manager import CookieManager
from config_jinka import JINKA_DASHBOARD_URL
import time

print("=" * 80)
print("🍪 SAUVEGARDE AUTOMATIQUE DES COOKIES")
print("=" * 80)
print()
print("🌐 Ouverture du navigateur...")
print("   Le script va détecter automatiquement quand vous serez connecté")
print("   Vous avez 5 minutes pour vous connecter")
print()

chrome_options = Options()
chrome_options.add_argument('--window-size=1920,1080')
# Garder le navigateur ouvert même après
chrome_options.add_experimental_option("detach", True)

manager = CookieManager()
driver = None

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(JINKA_DASHBOARD_URL)
    
    print("✅ Navigateur ouvert !")
    print(f"   URL: {driver.current_url}")
    print()
    print("📋 INSTRUCTIONS:")
    print("   1. Connectez-vous à Jinka dans le navigateur qui vient de s'ouvrir")
    print("   2. Le script détectera automatiquement votre connexion")
    print("   3. Les cookies seront sauvegardés automatiquement")
    print()
    print("⏳ Détection en cours... (vérification toutes les 3 secondes)")
    print()
    
    # Attendre jusqu'à 5 minutes (300 secondes)
    max_wait = 300
    check_interval = 3
    waited = 0
    last_url = ""
    
    while waited < max_wait:
        try:
            current_url = driver.current_url
            
            # Si l'URL a changé, l'afficher
            if current_url != last_url:
                print(f"   📍 URL: {current_url[:70]}...")
                last_url = current_url
            
            # Vérifier si on est connecté (sur le dashboard, pas sur /sign/in)
            if '/alert/dashboard' in current_url and '/sign/in' not in current_url:
                # Attendre un peu pour s'assurer qu'on reste sur le dashboard
                time.sleep(2)
                final_check = driver.current_url
                if '/alert/dashboard' in final_check and '/sign/in' not in final_check:
                    print("\n✅ Connexion détectée ! Vous êtes sur le dashboard")
                    break
            
            # Si on est sur la page de login, continuer à attendre
            if '/sign/in' in current_url:
                if waited % 15 == 0:  # Afficher toutes les 15 secondes
                    print(f"   ⏳ En attente de connexion... ({waited}s / {max_wait}s)")
            else:
                # URL différente, peut-être en train de se connecter
                if waited % 9 == 0:  # Afficher toutes les 9 secondes
                    print(f"   🔍 Vérification... ({waited}s)")
            
            time.sleep(check_interval)
            waited += check_interval
            
        except Exception as e:
            print(f"   ⚠️  Erreur lors de la vérification: {e}")
            time.sleep(check_interval)
            waited += check_interval
    
    # Vérification finale
    print("\n🔍 Vérification finale...")
    time.sleep(2)
    current_url = driver.current_url
    
    if '/sign/in' in current_url:
        print("⚠️  Vous semblez toujours sur la page de connexion")
        print("   Tentative de sauvegarde des cookies quand même...")
    else:
        print("✅ Vous êtes connecté !")
    
    # Récupérer les cookies
    print("\n🍪 Récupération des cookies...")
    cookies = driver.get_cookies()
    
    if not cookies:
        print("❌ Aucun cookie trouvé")
        print("   Le navigateur reste ouvert - vous pouvez réessayer")
    else:
        print(f"✅ {len(cookies)} cookie(s) trouvé(s)")
        
        if manager.save_cookies(cookies, source='selenium'):
            print("\n" + "="*80)
            print("🎉 SUCCÈS ! Cookies sauvegardés")
            print("="*80)
            print("\n✅ Vous pouvez maintenant utiliser:")
            print("   python3 fetch_jinka_apartments.py --test")
            print("="*80)
        else:
            print("\n❌ Erreur lors de la sauvegarde")
    
    print("\n🔒 Le navigateur reste ouvert (vous pouvez le fermer manuellement)")
    print("✅ Script terminé")
    
except KeyboardInterrupt:
    print("\n\n❌ Interrompu par l'utilisateur")
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n✅ Terminé")

