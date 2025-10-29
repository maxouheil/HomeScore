#!/usr/bin/env python3
"""
Script pour analyser le HTML et trouver le bon format des URLs
"""

import asyncio
import re
from scrape_jinka import JinkaScraper

async def debug_html():
    """Analyse le HTML pour trouver les URLs"""
    print("🔍 ANALYSE DU HTML POUR TROUVER LES URLs")
    print("=" * 60)
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Chrome ouvert")
        
        # Aller au dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(5000)
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        if "sign/in" in current_url:
            print("❌ Redirection vers login")
            print("💡 Connecte-toi manuellement dans le navigateur")
            print("⏳ J'attends que tu te connectes...")
            
            # Attendre la connexion
            max_wait = 300
            wait_time = 0
            
            while wait_time < max_wait:
                await scraper.page.wait_for_timeout(5000)
                current_url = scraper.page.url
                print(f"⏳ Attente... ({wait_time}s)")
                
                if "jinka.fr" in current_url and "sign/in" not in current_url:
                    print("🎉 CONNEXION DÉTECTÉE !")
                    break
                
                wait_time += 5
            
            if wait_time >= max_wait:
                print("⏰ Timeout")
                return False
        
        print("✅ Accès au dashboard réussi !")
        
        # Extraire le HTML
        page_content = await scraper.page.content()
        print(f"📄 Taille du HTML: {len(page_content)} caractères")
        
        # Chercher tous les liens href
        print("\n🔍 RECHERCHE DE TOUS LES LIENS HREF...")
        href_pattern = r'href="([^"]*)"'
        all_hrefs = re.findall(href_pattern, page_content)
        
        print(f"📋 Total de liens href trouvés: {len(all_hrefs)}")
        
        # Filtrer les liens d'appartements
        apartment_links = []
        for href in all_hrefs:
            if 'alert_result' in href or 'ad=' in href:
                apartment_links.append(href)
        
        print(f"🏠 Liens d'appartements trouvés: {len(apartment_links)}")
        
        if apartment_links:
            print("\n📋 LIENS D'APPARTEMENTS:")
            for i, link in enumerate(apartment_links[:20], 1):  # Afficher les 20 premiers
                print(f"   {i}. {link}")
            
            # Chercher les IDs d'appartements
            print("\n🔍 RECHERCHE DES IDs D'APPARTEMENTS...")
            id_pattern = r'ad=(\d+)'
            apartment_ids = re.findall(id_pattern, page_content)
            unique_ids = list(set(apartment_ids))
            
            print(f"🏠 IDs d'appartements trouvés: {len(unique_ids)}")
            for i, apt_id in enumerate(unique_ids[:10], 1):
                print(f"   {i}. ID: {apt_id}")
            
            # Construire les URLs complètes
            print("\n🔗 CONSTRUCTION DES URLs COMPLÈTES...")
            base_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
            
            full_urls = []
            for apt_id in unique_ids:
                full_url = base_url.format(apt_id)
                full_urls.append(full_url)
            
            print(f"✅ {len(full_urls)} URLs complètes construites")
            
            # Sauvegarder
            import json
            import os
            os.makedirs("data", exist_ok=True)
            
            with open("data/all_apartment_urls.json", 'w', encoding='utf-8') as f:
                json.dump(full_urls, f, indent=2, ensure_ascii=False)
            
            print(f"💾 URLs sauvegardées: data/all_apartment_urls.json")
            
            # Prendre un screenshot
            await scraper.page.screenshot(path="data/dashboard_debug.png")
            print(f"📸 Screenshot: data/dashboard_debug.png")
            
            return full_urls
        else:
            print("❌ Aucun lien d'appartement trouvé")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(debug_html())
