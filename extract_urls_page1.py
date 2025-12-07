#!/usr/bin/env python3
"""
Script pour extraire toutes les URLs d'appartements visibles sur la page 1 du dashboard Jinka
Version simple sans pagination ni scroll - juste pour valider la méthode d'extraction
"""

import asyncio
import json
import os
import re
from scrape_jinka import JinkaScraper


async def extract_urls_from_page1():
    """
    Extrait toutes les URLs d'appartements visibles sur la page 1 du dashboard
    """
    print("🔍 EXTRACTION DES URLs - PAGE 1 DU DASHBOARD")
    print("=" * 60)
    
    scraper = JinkaScraper()
    
    try:
        # 1. Setup
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # 2. Aller directement au dashboard (sans login automatique)
        print("\n🌐 Navigation directe vers le dashboard...")
        print("   (Si tu n'es pas connecté, connecte-toi manuellement dans le navigateur)")
        
        # URL du dashboard
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        
        print(f"📍 Tentative de navigation vers: {dashboard_url}")
        
        # Aller au dashboard directement
        try:
            await scraper.page.goto(dashboard_url, wait_until='networkidle', timeout=30000)
            print("✅ Navigation réussie")
        except Exception as e:
            print(f"⚠️ Erreur lors de la navigation: {e}")
            print("   Tentative avec timeout plus long...")
            await scraper.page.goto(dashboard_url, timeout=60000)
        
        await asyncio.sleep(3000)  # Attendre le chargement complet
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        # Vérifier si on est déjà sur le dashboard
        is_on_dashboard = (
            "dashboard" in current_url.lower() or 
            "asrenter/alert/dashboard" in current_url.lower()
        )
        
        # Si on est redirigé vers login, attendre la connexion manuelle
        if not is_on_dashboard and ("sign/in" in current_url or "auth" in current_url or "couldn't sign" in current_url.lower()):
            print("⚠️ Redirection vers login détectée")
            print("   Connecte-toi manuellement dans le navigateur et va sur le dashboard...")
            print("   Le script attendra que tu navigues vers le dashboard...")
            
            # Attendre que l'utilisateur navigue vers le dashboard
            max_wait = 120  # 2 minutes max
            wait_time = 0
            
            while wait_time < max_wait:
                await asyncio.sleep(5)
                current_url = scraper.page.url
                wait_time += 5
                
                print(f"   ⏳ Vérification ({wait_time}s) - URL: {current_url[:100]}")
                
                # Vérifier plusieurs patterns pour détecter le dashboard
                if ("dashboard" in current_url.lower() or 
                    "asrenter/alert/dashboard" in current_url.lower()):
                    print(f"✅ Dashboard détecté après {wait_time}s!")
                    is_on_dashboard = True
                    break
                elif wait_time % 15 == 0:
                    print(f"   ⏳ Attente... ({wait_time}s)")
            
            if not is_on_dashboard:
                print("⏰ Timeout - le dashboard n'a pas été atteint")
                print("   Mais on continue quand même l'extraction...")
        
        # Afficher l'URL finale
        current_url = scraper.page.url
        print(f"\n📍 URL finale: {current_url}")
        
        # Attendre un peu pour s'assurer que la page est complètement chargée
        print("⏳ Attente du chargement complet de la page...")
        await asyncio.sleep(5000)  # 5 secondes pour s'assurer que tout est chargé
        
        if is_on_dashboard or "asrenter/alert" in current_url.lower():
            print("✅ Sur le dashboard - extraction des URLs...")
        else:
            print("⚠️ Pas sûr d'être sur le dashboard, mais on continue l'extraction...")
        
        # 4. Extraire les URLs avec plusieurs méthodes
        print("\n🔍 EXTRACTION DES URLs")
        print("-" * 40)
        print("Début de l'extraction...")
        
        all_urls = set()  # Utiliser un set pour éviter les doublons
        
        # Méthode 1: Sélecteurs Playwright
        print("\n📋 Méthode 1: Sélecteurs Playwright")
        try:
            selectors = [
                'a[href*="alert_result"][href*="ad="]',
                'a[href*="alert_result"]',
                'a[href*="ad="]',
            ]
            
            for selector in selectors:
                try:
                    links = scraper.page.locator(selector)
                    count = await links.count()
                    
                    if count > 0:
                        print(f"   ✅ {count} liens trouvés avec: {selector}")
                        
                        for i in range(count):
                            try:
                                href = await links.nth(i).get_attribute('href')
                                if href:
                                    # Construire l'URL complète si nécessaire
                                    if href.startswith('/'):
                                        full_url = f"https://www.jinka.fr{href}"
                                    elif href.startswith('http'):
                                        full_url = href
                                    elif href.startswith('loueragile://'):
                                        # Extraire l'ID depuis loueragile://
                                        match = re.search(r'id=(\d+)', href)
                                        if match:
                                            apt_id = match.group(1)
                                            full_url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apt_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
                                        else:
                                            continue
                                    else:
                                        continue
                                    
                                    # Vérifier que c'est bien une URL d'appartement
                                    if 'ad=' in full_url or 'alert_result' in full_url:
                                        all_urls.add(full_url)
                            except Exception as e:
                                continue
                    else:
                        print(f"   ⚠️  0 liens trouvés avec: {selector}")
                except Exception as e:
                    print(f"   ❌ Erreur avec sélecteur {selector}: {e}")
                    continue
        except Exception as e:
            print(f"   ❌ Erreur méthode sélecteurs: {e}")
        
        # Méthode 2: Regex sur le HTML brut (backup)
        print("\n📋 Méthode 2: Regex sur le HTML")
        try:
            page_content = await scraper.page.content()
            print(f"   📄 Taille du HTML: {len(page_content)} caractères")
            
            # Patterns pour trouver les URLs d'appartements
            url_patterns = [
                r'href="(/alert_result\?token=[^&]+&ad=\d+[^"]*)"',
                r'href="(https://www\.jinka\.fr/alert_result\?token=[^&]+&ad=\d+[^"]*)"',
            ]
            
            regex_urls_found = 0
            for pattern in url_patterns:
                matches = re.findall(pattern, page_content)
                for match in matches:
                    if match.startswith('/'):
                        full_url = f"https://www.jinka.fr{match}"
                    else:
                        full_url = match
                    
                    if 'ad=' in full_url:
                        all_urls.add(full_url)
                        regex_urls_found += 1
            
            print(f"   ✅ {regex_urls_found} URLs trouvées avec regex")
        except Exception as e:
            print(f"   ❌ Erreur méthode regex: {e}")
        
        # Méthode 3: Extraction des IDs depuis loueragile://
        print("\n📋 Méthode 3: Extraction depuis loueragile://")
        try:
            page_content = await scraper.page.content()
            
            # Chercher les liens loueragile://
            loueragile_pattern = r'loueragile://[^"]*id=(\d+)'
            matches = re.findall(loueragile_pattern, page_content)
            
            loueragile_ids_found = 0
            for apt_id in matches:
                full_url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apt_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
                all_urls.add(full_url)
                loueragile_ids_found += 1
            
            print(f"   ✅ {loueragile_ids_found} IDs trouvés depuis loueragile://")
        except Exception as e:
            print(f"   ❌ Erreur méthode loueragile: {e}")
        
        # Convertir en liste et trier
        unique_urls = sorted(list(all_urls))
        
        print(f"\n📊 RÉSULTATS")
        print("=" * 60)
        print(f"🏠 Total d'URLs uniques trouvées: {len(unique_urls)}")
        
        if unique_urls:
            # Afficher les premières URLs
            print(f"\n📋 Premières URLs trouvées:")
            for i, url in enumerate(unique_urls[:10], 1):
                print(f"   {i}. {url}")
            
            if len(unique_urls) > 10:
                print(f"   ... et {len(unique_urls) - 10} autres")
            
            # Sauvegarder les URLs
            os.makedirs("data", exist_ok=True)
            urls_file = "data/apartment_urls_page1.json"
            
            with open(urls_file, 'w', encoding='utf-8') as f:
                json.dump(unique_urls, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 URLs sauvegardées: {urls_file}")
            
            # Prendre un screenshot
            await scraper.page.screenshot(path="data/dashboard_page1_extraction.png")
            print(f"📸 Screenshot: data/dashboard_page1_extraction.png")
            
            return unique_urls
        else:
            print("❌ Aucune URL trouvée")
            return []
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")


async def main():
    """Fonction principale"""
    urls = await extract_urls_from_page1()
    
    if urls:
        print(f"\n🎉 SUCCÈS: {len(urls)} URLs d'appartements récupérées sur la page 1 !")
        print(f"📁 Fichier: data/apartment_urls_page1.json")
    else:
        print("\n❌ Aucune URL récupérée")


if __name__ == "__main__":
    asyncio.run(main())

