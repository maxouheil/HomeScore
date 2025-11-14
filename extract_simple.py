#!/usr/bin/env python3
"""
Script simple: ouvre le navigateur, attend que tu sois sur le dashboard, puis extrait
"""

import asyncio
import json
import re
import os
from scrape_jinka import JinkaScraper

async def main():
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("=" * 60)
        print("🔍 EXTRACTION DES URLs DU DASHBOARD")
        print("=" * 60)
        print("\n✅ Navigateur ouvert")
        
        # Aller au dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        print(f"\n🌐 Navigation vers le dashboard...")
        await scraper.page.goto(dashboard_url, timeout=60000)
        await asyncio.sleep(3000)
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        # Si redirigé vers login, attendre
        if "sign/in" in current_url or "auth" in current_url:
            print("\n⚠️ Redirection vers login détectée")
            print("   Connecte-toi manuellement et va sur le dashboard")
            print("   Le script attendra 60 secondes...")
            
            for i in range(12):  # 12 x 5s = 60s
                await asyncio.sleep(5)
                current_url = scraper.page.url
                if "dashboard" in current_url.lower():
                    print(f"✅ Dashboard détecté après {i*5}s!")
                    break
                if i % 3 == 0:
                    print(f"   ⏳ Attente... ({i*5}s) - URL: {current_url[:70]}")
        
        # Attendre un peu pour le chargement
        print("\n⏳ Attente du chargement complet...")
        await asyncio.sleep(5000)
        
        current_url = scraper.page.url
        print(f"📍 URL finale: {current_url}")
        
        # EXTRACTION
        print("\n" + "=" * 60)
        print("🔍 EXTRACTION DES URLs")
        print("=" * 60)
        
        urls_set = set()
        
        # Méthode 1: Sélecteurs
        print("\n📋 Méthode 1: Sélecteurs Playwright")
        try:
            links = scraper.page.locator('a[href*="ad="]')
            count = await links.count()
            print(f"   Trouvé {count} liens avec 'ad='")
            
            for i in range(count):
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
                            urls_set.add(full_url)
                except:
                    continue
            print(f"   ✅ {len(urls_set)} URLs extraites avec sélecteurs")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Méthode 2: Regex
        print("\n📋 Méthode 2: Regex sur HTML")
        try:
            page_content = await scraper.page.content()
            ids = re.findall(r'ad=(\d+)', page_content)
            unique_ids = list(set(ids))
            print(f"   Trouvé {len(unique_ids)} IDs uniques")
            
            for apt_id in unique_ids:
                url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apt_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
                urls_set.add(url)
            
            print(f"   ✅ Total après regex: {len(urls_set)} URLs")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Résultats
        all_urls = sorted(list(urls_set))
        
        print("\n" + "=" * 60)
        print(f"📊 RÉSULTATS FINAUX: {len(all_urls)} URLs trouvées")
        print("=" * 60)
        
        if all_urls:
            print("\n📋 Liste complète des URLs:")
            for i, url in enumerate(all_urls, 1):
                print(f"   {i}. {url}")
            
            # Sauvegarder
            os.makedirs("data", exist_ok=True)
            output_file = "data/apartment_urls_page1.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_urls, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Sauvegardé dans: {output_file}")
            print(f"✅ TERMINÉ AVEC SUCCÈS!")
        else:
            print("\n❌ Aucune URL trouvée")
            print("   Vérifie que tu es bien sur le dashboard avec des appartements")
        
        return all_urls
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        print("\n⚠️ Le navigateur restera ouvert")

if __name__ == "__main__":
    asyncio.run(main())






