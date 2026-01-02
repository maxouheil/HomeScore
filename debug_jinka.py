#!/usr/bin/env python3
"""
Script de debug pour inspecter ce qui se passe sur le dashboard Jinka
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json
import time

def debug_dashboard():
    """Debug le dashboard Jinka"""
    chrome_options = Options()
    # Ne pas utiliser headless pour voir ce qui se passe
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        print(f"📡 Accès à {url}")
        driver.get(url)
        
        print("⏳ Attente 10 secondes...")
        time.sleep(10)
        
        print("\n" + "="*80)
        print("📄 TITRE DE LA PAGE")
        print("="*80)
        print(driver.title)
        
        print("\n" + "="*80)
        print("🔍 URL ACTUELLE")
        print("="*80)
        print(driver.current_url)
        
        print("\n" + "="*80)
        print("📋 SCRIPTS JSON TROUVÉS")
        print("="*80)
        scripts = driver.find_elements(By.TAG_NAME, "script")
        json_scripts = []
        for i, script in enumerate(scripts):
            script_type = script.get_attribute("type")
            if script_type == "application/json":
                try:
                    content = script.get_attribute("innerHTML")
                    if content:
                        data = json.loads(content)
                        json_scripts.append({
                            'index': i,
                            'data': data
                        })
                        print(f"Script #{i}: {len(str(data))} caractères")
                        print(f"  Clés: {list(data.keys()) if isinstance(data, dict) else 'Liste'}")
                except:
                    pass
        
        print(f"\nTotal: {len(json_scripts)} scripts JSON trouvés")
        
        print("\n" + "="*80)
        print("🌐 VARIABLES GLOBALES")
        print("="*80)
        globals_to_check = [
            '__NEXT_DATA__',
            '__INITIAL_STATE__',
            '__APOLLO_STATE__',
            '__REDUX_STATE__'
        ]
        for var in globals_to_check:
            try:
                value = driver.execute_script(f"return window.{var} || null;")
                if value:
                    print(f"{var}: {type(value)}")
                    if isinstance(value, dict):
                        print(f"  Clés: {list(value.keys())[:10]}")
            except:
                pass
        
        print("\n" + "="*80)
        print("🔗 LIENS VERS LES ANNONCES")
        print("="*80)
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='alert_result'], a[href*='ad=']")
        print(f"Total: {len(links)} liens trouvés")
        for i, link in enumerate(links[:10]):
            href = link.get_attribute("href")
            text = link.text[:50] if link.text else ""
            print(f"{i+1}. {href}")
            if text:
                print(f"   Texte: {text}")
        
        print("\n" + "="*80)
        print("📊 ÉLÉMENTS AVEC DATA-ATTRIBUTES")
        print("="*80)
        data_elements = driver.find_elements(By.CSS_SELECTOR, "[data-ad-id], [data-id], [data-apartment-id]")
        print(f"Total: {len(data_elements)} éléments trouvés")
        for i, elem in enumerate(data_elements[:10]):
            attrs = {}
            for attr in ['data-ad-id', 'data-id', 'data-apartment-id']:
                val = elem.get_attribute(attr)
                if val:
                    attrs[attr] = val
            if attrs:
                print(f"{i+1}. {attrs}")
        
        print("\n" + "="*80)
        print("💾 LOCALSTORAGE/SESSIONSTORAGE")
        print("="*80)
        storage = driver.execute_script("""
            return {
                localStorage: Object.keys(localStorage),
                sessionStorage: Object.keys(sessionStorage)
            };
        """)
        print(f"localStorage: {storage.get('localStorage', [])}")
        print(f"sessionStorage: {storage.get('sessionStorage', [])}")
        
        print("\n" + "="*80)
        print("⏸️  PAUSE - Appuyez sur Entrée pour fermer le navigateur...")
        print("="*80)
        input()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_dashboard()

