#!/usr/bin/env python3
"""
Script pour extraire toutes les URLs d'appartements depuis le dashboard
"""

import asyncio
import json
import os
import re
from scrape_jinka import JinkaScraper

async def extract_all_urls():
    """Extrait toutes les URLs d'appartements"""
    print("🔍 EXTRACTION DE TOUTES LES URLs D'APPARTEMENTS")
    print("=" * 60)
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # Aller au dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        print(f"🌐 Navigation vers: {dashboard_url}")
        
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(5000)
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        if "sign/in" in current_url:
            print("❌ Redirection vers login - tu dois te connecter")
            return False
        
        print("✅ Accès au dashboard réussi !")
        
        # Extraire le HTML de la page
        print("\n🔍 EXTRACTION DU HTML...")
        page_content = await scraper.page.content()
        print(f"📄 Taille du HTML: {len(page_content)} caractères")
        
        # Chercher toutes les URLs d'appartements avec regex
        print("\n🔍 RECHERCHE DES URLs D'APPARTEMENTS...")
        
        # Pattern pour trouver les URLs d'appartements
        url_pattern = r'href="(/alert_result\?token=26c2ec3064303aa68ffa43f7c6518733&ad=\d+&[^"]*)"'
        
        # Trouver toutes les URLs
        urls = re.findall(url_pattern, page_content)
        
        # Dédupliquer
        unique_urls = list(set(urls))
        
        print(f"🏠 URLs trouvées: {len(unique_urls)}")
        
        if unique_urls:
            # Construire les URLs complètes
            full_urls = []
            for url in unique_urls:
                if url.startswith('/'):
                    full_url = f"https://www.jinka.fr{url}"
                else:
                    full_url = url
                full_urls.append(full_url)
            
            print(f"\n📋 LISTE DES URLs D'APPARTEMENTS:")
            for i, url in enumerate(full_urls, 1):
                print(f"   {i}. {url}")
            
            # Sauvegarder les URLs
            os.makedirs("data", exist_ok=True)
            urls_file = "data/apartment_urls.json"
            
            with open(urls_file, 'w', encoding='utf-8') as f:
                json.dump(full_urls, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 URLs sauvegardées: {urls_file}")
            
            # Prendre un screenshot
            await scraper.page.screenshot(path="data/dashboard_extraction.png")
            print(f"📸 Screenshot: data/dashboard_extraction.png")
            
            return full_urls
        else:
            print("❌ Aucune URL d'appartement trouvée")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(extract_all_urls())
