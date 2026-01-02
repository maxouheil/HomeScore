#!/usr/bin/env python3
"""
Script de debug pour inspecter le dashboard Jinka et trouver où sont les appartements
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from cookie_manager import CookieManager
from config_jinka import JINKA_DASHBOARD_URL
import time
import json

print("=" * 80)
print("🔍 DEBUG DU DASHBOARD JINKA")
print("=" * 80)
print()

chrome_options = Options()
# Ne pas utiliser headless pour voir ce qui se passe
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_experimental_option("detach", True)

manager = CookieManager()
driver = None

try:
    driver = webdriver.Chrome(options=chrome_options)
    
    # Charger les cookies
    saved_cookies = manager.load_cookies()
    if saved_cookies:
        print("🍪 Chargement des cookies...")
        manager.add_cookies_to_driver(driver, saved_cookies)
    
    driver.get(JINKA_DASHBOARD_URL)
    print(f"📡 Accès à {JINKA_DASHBOARD_URL}")
    print()
    
    print("⏳ Attente du chargement (20 secondes)...")
    time.sleep(20)
    
    # Faire défiler pour déclencher le chargement lazy
    print("📜 Défilement de la page pour déclencher le chargement...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    print("\n" + "="*80)
    print("📄 INFORMATIONS DE LA PAGE")
    print("="*80)
    print(f"Titre: {driver.title}")
    print(f"URL: {driver.current_url}")
    print()
    
    # Vérifier si on est connecté
    if '/sign/in' in driver.current_url:
        print("⚠️  Vous êtes sur la page de connexion")
        print("   Connectez-vous dans le navigateur et relancez ce script")
    else:
        print("✅ Vous semblez être connecté")
    print()
    
    # Chercher tous les liens
    print("="*80)
    print("🔗 LIENS TROUVÉS")
    print("="*80)
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"Total: {len(links)} liens")
    
    alert_links = []
    all_hrefs = []
    for link in links:
        href = link.get_attribute('href')
        text = link.text.strip()[:50]
        if href:
            all_hrefs.append(href)
            if 'alert_result' in href or 'ad=' in href or '/ad/' in href:
                alert_links.append({'href': href, 'text': text})
                print(f"  ✅ {href[:80]}")
                if text:
                    print(f"     Texte: {text}")
    
    if not alert_links:
        print("  ⚠️  Aucun lien vers des annonces trouvé")
        print(f"  📋 Exemples de liens trouvés:")
        for href in all_hrefs[:10]:
            print(f"     - {href[:70]}")
    print()
    
    # Chercher des boutons ou éléments cliquables qui pourraient charger les résultats
    print("="*80)
    print("🔘 BOUTONS ET ÉLÉMENTS ACTIONNABLES")
    print("="*80)
    buttons = driver.find_elements(By.TAG_NAME, "button")
    clickables = driver.find_elements(By.CSS_SELECTOR, "[role='button'], [onclick], .btn, button")
    print(f"Total: {len(buttons)} boutons, {len(clickables)} éléments cliquables")
    
    # Chercher des textes qui pourraient indiquer des résultats
    result_texts = ['résultat', 'annonce', 'appartement', 'voir', 'afficher', 'charger']
    for text in result_texts:
        elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
        if elements:
            print(f"  '{text}': {len(elements)} élément(s)")
            for elem in elements[:3]:
                print(f"     - {elem.text[:50]} ({elem.tag_name})")
    print()
    
    # Chercher dans le HTML source
    print("="*80)
    print("📋 RECHERCHE DANS LE HTML")
    print("="*80)
    html = driver.page_source
    
    # Chercher des IDs d'appartements dans le HTML
    import re
    ad_ids = re.findall(r'ad=(\d+)', html)
    if ad_ids:
        unique_ids = list(set(ad_ids))
        print(f"✅ {len(unique_ids)} ID(s) d'appartement trouvé(s) dans le HTML:")
        for apt_id in unique_ids[:10]:
            print(f"   - {apt_id}")
    else:
        print("⚠️  Aucun ID d'appartement trouvé dans le HTML")
    print()
    
    # Chercher dans les scripts JSON
    print("="*80)
    print("📜 SCRIPTS JSON")
    print("="*80)
    scripts = driver.find_elements(By.CSS_SELECTOR, "script[type='application/json']")
    print(f"Total: {len(scripts)} scripts JSON")
    for i, script in enumerate(scripts):
        try:
            content = script.get_attribute('innerHTML')
            if content:
                data = json.loads(content)
                print(f"  Script #{i+1}: {len(str(data))} caractères")
                print(f"    Clés: {list(data.keys())[:10] if isinstance(data, dict) else 'Liste'}")
        except:
            pass
    print()
    
    # Chercher dans window
    print("="*80)
    print("🌐 VARIABLES WINDOW")
    print("="*80)
    window_vars = driver.execute_script("""
        const vars = {};
        for (let key in window) {
            if (key.startsWith('__') || key.includes('REACT') || key.includes('REDUX') || key.includes('STATE') || key.includes('NEXT')) {
                try {
                    const value = window[key];
                    if (value && typeof value === 'object') {
                        vars[key] = typeof value;
                    }
                } catch(e) {}
            }
        }
        return vars;
    """)
    print(f"Variables trouvées: {list(window_vars.keys())}")
    print()
    
    # Chercher des éléments avec des classes ou IDs intéressants
    print("="*80)
    print("🏷️  ÉLÉMENTS INTÉRESSANTS")
    print("="*80)
    
    # Chercher des classes qui pourraient contenir des listings
    interesting_classes = ['card', 'item', 'listing', 'apartment', 'ad', 'result', 'match']
    for class_name in interesting_classes:
        elements = driver.find_elements(By.CSS_SELECTOR, f"[class*='{class_name}']")
        if elements:
            print(f"  {class_name}: {len(elements)} élément(s)")
    
    # Chercher des boutons ou liens "Voir", "Afficher", etc.
    action_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Voir') or contains(text(), 'Afficher') or contains(text(), 'Résultats')]")
    if action_elements:
        print(f"  Boutons/liens d'action: {len(action_elements)}")
        for elem in action_elements[:5]:
            print(f"    - {elem.text[:50]}")
    print()
    
    # Prendre une capture d'écran pour debug
    try:
        screenshot_path = "data/debug_dashboard.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Capture d'écran sauvegardée: {screenshot_path}")
    except:
        pass
    
    print("\n" + "="*80)
    print("✅ DEBUG TERMINÉ")
    print("="*80)
    print("Le navigateur reste ouvert pour inspection manuelle")
    print("Appuyez sur ENTRÉE pour fermer...")
    
    try:
        input()
    except:
        pass
    
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    if driver:
        driver.quit()

