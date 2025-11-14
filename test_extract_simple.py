#!/usr/bin/env python3
"""
Version de test simple pour extraire les URLs directement depuis le dashboard
"""

import asyncio
import json
import re
from scrape_jinka import JinkaScraper

async def test_extract():
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # Aller directement au dashboard (tu es déjà connecté)
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        print(f"🌐 Navigation vers: {dashboard_url}")
        
        await scraper.page.goto(dashboard_url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(5000)  # Attendre le chargement
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        # Méthode 1: Sélecteurs simples
        print("\n🔍 Méthode 1: Sélecteurs Playwright")
        links = scraper.page.locator('a[href*="ad="]')
        count = await links.count()
        print(f"   Trouvé {count} liens avec ad=")
        
        urls = set()
        for i in range(min(count, 100)):  # Limiter à 100 pour le test
            try:
                href = await links.nth(i).get_attribute('href')
                if href:
                    if href.startswith('/'):
                        full_url = f"https://www.jinka.fr{href}"
                    elif href.startswith('http'):
                        full_url = href
                    elif 'loueragile://' in href:
                        match = re.search(r'id=(\d+)', href)
                        if match:
                            apt_id = match.group(1)
                            full_url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apt_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
                        else:
                            continue
                    else:
                        continue
                    
                    if 'ad=' in full_url or 'alert_result' in full_url:
                        urls.add(full_url)
                        print(f"   {i+1}. {full_url}")
            except Exception as e:
                print(f"   Erreur lien {i+1}: {e}")
                continue
        
        # Méthode 2: Regex sur HTML
        print(f"\n🔍 Méthode 2: Regex sur HTML")
        page_content = await scraper.page.content()
        matches = re.findall(r'ad=(\d+)', page_content)
        unique_ids = list(set(matches))
        print(f"   Trouvé {len(unique_ids)} IDs uniques")
        
        for apt_id in unique_ids[:20]:  # Afficher les 20 premiers
            url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apt_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
            urls.add(url)
        
        # Résultats
        all_urls = sorted(list(urls))
        print(f"\n📊 TOTAL: {len(all_urls)} URLs uniques trouvées")
        
        # Sauvegarder
        import os
        os.makedirs("data", exist_ok=True)
        with open("data/apartment_urls_page1.json", 'w', encoding='utf-8') as f:
            json.dump(all_urls, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Sauvegardé dans data/apartment_urls_page1.json")
        
        return all_urls
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        print("\n⚠️ Le navigateur restera ouvert")

if __name__ == "__main__":
    asyncio.run(test_extract())






