#!/usr/bin/env python3
"""
Version ultra-simple: extrait les URLs MAINTENANT depuis la page ouverte
"""

import asyncio
import json
import re
import os
from scrape_jinka import JinkaScraper

async def extract_now():
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé")
        print("⚠️ Assure-toi d'être sur le dashboard dans le navigateur qui va s'ouvrir")
        print("   Attente de 5 secondes...")
        await asyncio.sleep(5)
        
        # Lire l'URL actuelle (tu es déjà sur le dashboard)
        current_url = scraper.page.url
        print(f"📍 URL actuelle dans le navigateur: {current_url}")
        
        # Si ce n'est pas le dashboard, aller dessus
        if "dashboard" not in current_url.lower():
            dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
            print(f"🌐 Navigation vers le dashboard...")
            await scraper.page.goto(dashboard_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3000)
            current_url = scraper.page.url
            print(f"📍 URL après navigation: {current_url}")
        
        print("\n🔍 EXTRACTION EN COURS...")
        print("-" * 50)
        
        # Méthode 1: Sélecteurs
        print("\n1️⃣ Méthode sélecteurs Playwright...")
        urls_set = set()
        
        try:
            # Chercher tous les liens avec ad=
            links = scraper.page.locator('a[href*="ad="]')
            count = await links.count()
            print(f"   ✅ {count} liens trouvés")
            
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
                        
                        if 'ad=' in full_url:
                            urls_set.add(full_url)
                            if i < 5:  # Afficher les 5 premiers
                                print(f"      {i+1}. {full_url[:80]}...")
                except:
                    continue
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Méthode 2: Regex sur HTML
        print(f"\n2️⃣ Méthode regex sur HTML...")
        try:
            page_content = await scraper.page.content()
            # Chercher tous les IDs d'appartements
            ids_found = re.findall(r'ad=(\d+)', page_content)
            unique_ids = list(set(ids_found))
            print(f"   ✅ {len(unique_ids)} IDs uniques trouvés")
            
            for apt_id in unique_ids:
                url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apt_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
                urls_set.add(url)
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Résultats finaux
        all_urls = sorted(list(urls_set))
        
        print(f"\n{'='*50}")
        print(f"📊 RÉSULTATS FINAUX")
        print(f"{'='*50}")
        print(f"🏠 Total: {len(all_urls)} URLs uniques trouvées")
        
        if all_urls:
            print(f"\n📋 Liste complète:")
            for i, url in enumerate(all_urls, 1):
                print(f"   {i}. {url}")
            
            # Sauvegarder
            os.makedirs("data", exist_ok=True)
            output_file = "data/apartment_urls_page1.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_urls, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 URLs sauvegardées dans: {output_file}")
            print(f"✅ TERMINÉ!")
        else:
            print(f"\n❌ Aucune URL trouvée")
            print(f"   Vérifie que tu es bien sur le dashboard avec des appartements visibles")
        
        return all_urls
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        print("\n⚠️ Le navigateur restera ouvert - ferme-le manuellement")

if __name__ == "__main__":
    asyncio.run(extract_now())

