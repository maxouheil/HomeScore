#!/usr/bin/env python3
"""
Script pour extraire toutes les URLs depuis le dashboard
Version manuelle - tu dois être connecté dans Chrome
"""

import asyncio
import json
import os
import re
from scrape_jinka import JinkaScraper

async def extract_all_urls_manual():
    """Extrait toutes les URLs depuis le dashboard"""
    print("🔍 EXTRACTION MANUELLE DE TOUTES LES URLs")
    print("=" * 60)
    print("1. Ouvre Chrome manuellement")
    print("2. Va sur ton dashboard Jinka")
    print("3. Connecte-toi si nécessaire")
    print("4. Ce script va extraire toutes les URLs")
    print()
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Chrome ouvert")
        
        # Aller au dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        print(f"🌐 Navigation vers: {dashboard_url}")
        
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_timeout(5000)
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        if "sign/in" in current_url:
            print("❌ Redirection vers login")
            print("💡 Connecte-toi manuellement dans le navigateur qui s'est ouvert")
            print("⏳ J'attends que tu te connectes...")
            
            # Attendre que l'utilisateur se connecte
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                await scraper.page.wait_for_timeout(5000)
                current_url = scraper.page.url
                print(f"⏳ Attente... ({wait_time}s) - URL: {current_url[:80]}...")
                
                if "jinka.fr" in current_url and "sign/in" not in current_url:
                    print("🎉 CONNEXION DÉTECTÉE !")
                    break
                
                wait_time += 5
            
            if wait_time >= max_wait:
                print("⏰ Timeout - connexion non détectée")
                return False
        
        print("✅ Accès au dashboard réussi !")
        
        # Extraire le HTML de la page
        print("\n🔍 EXTRACTION DU HTML...")
        page_content = await scraper.page.content()
        print(f"📄 Taille du HTML: {len(page_content)} caractères")
        
        # Chercher toutes les URLs d'appartements avec regex
        print("\n🔍 RECHERCHE DES URLs D'APPARTEMENTS...")
        
        # Patterns pour trouver les URLs d'appartements
        patterns = [
            r'href="(/alert_result\?token=26c2ec3064303aa68ffa43f7c6518733&ad=\d+&[^"]*)"',
            r'href="(/alert_result\?token=26c2ec3064303aa68ffa43f7c6518733&ad=\d+)"',
            r'href="(/alert_result\?ad=\d+&[^"]*)"',
            r'href="(/alert_result\?ad=\d+)"'
        ]
        
        all_urls = []
        for pattern in patterns:
            urls = re.findall(pattern, page_content)
            all_urls.extend(urls)
            print(f"   Pattern '{pattern}': {len(urls)} URLs trouvées")
        
        # Dédupliquer
        unique_urls = list(set(all_urls))
        
        print(f"\n🏠 Total d'URLs uniques trouvées: {len(unique_urls)}")
        
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
            urls_file = "data/all_apartment_urls.json"
            
            with open(urls_file, 'w', encoding='utf-8') as f:
                json.dump(full_urls, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 URLs sauvegardées: {urls_file}")
            
            # Prendre un screenshot
            await scraper.page.screenshot(path="data/dashboard_all_urls.png")
            print(f"📸 Screenshot: data/dashboard_all_urls.png")
            
            print(f"\n🎉 EXTRACTION RÉUSSIE !")
            print(f"   {len(full_urls)} URLs d'appartements trouvées")
            print(f"   Prêt pour le scraping en batch !")
            
            return full_urls
        else:
            print("❌ Aucune URL d'appartement trouvée")
            print("💡 Vérifie que tu es bien sur la page du dashboard")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(extract_all_urls_manual())
