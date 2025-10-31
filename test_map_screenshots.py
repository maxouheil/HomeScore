#!/usr/bin/env python3
"""
Script de test pour vérifier que les screenshots de carte sont bien récupérés
avec l'ID de l'appartement dans le nom du fichier
"""

import asyncio
import os
import json
import sys
from scrape_jinka import JinkaScraper
from dotenv import load_dotenv

load_dotenv()

async def test_map_screenshots():
    """Test les screenshots de carte sur 2-3 appartements"""
    print("🗺️ TEST DES SCREENSHOTS DE CARTE")
    print("=" * 60)
    
    # Vérifier si des URLs d'appartements existent dans les données
    apartment_urls = []
    
    # Méthode 1: Depuis scraped_apartments.json
    scraped_file = "data/scraped_apartments.json"
    if os.path.exists(scraped_file):
        try:
            with open(scraped_file, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
            
            # Extraire les URLs uniques
            seen_urls = set()
            for apt in scraped_data[:10]:  # Prendre les 10 premiers
                url = apt.get('url', '')
                if url and url not in seen_urls:
                    apartment_urls.append(url)
                    seen_urls.add(url)
                    if len(apartment_urls) >= 3:  # Limiter à 3 pour le test
                        break
        except Exception as e:
            print(f"⚠️ Erreur lecture {scraped_file}: {e}")
    
    # Méthode 2: Si pas d'URLs trouvées, utiliser des URLs d'exemple ou demander à l'utilisateur
    if len(apartment_urls) == 0:
        print("⚠️ Aucune URL trouvée dans les données")
        print("📝 Usage: python test_map_screenshots.py <URL_ALERTE>")
        print("   ou fournir au moins une URL d'appartement")
        
        if len(sys.argv) > 1:
            # Si une URL d'alerte est fournie, extraire les appartements
            alert_url = sys.argv[1]
            print(f"\n🔍 Extraction des appartements depuis l'alerte: {alert_url}")
        else:
            print("\n❌ Pas d'URL fournie. Arrêt du test.")
            return False
    
    scraper = JinkaScraper()
    
    try:
        # Initialiser le scraper
        await scraper.setup()
        print("✅ Scraper initialisé\n")
        
        # Si une URL d'alerte est fournie, extraire les appartements
        if len(sys.argv) > 1 and len(apartment_urls) == 0:
            alert_url = sys.argv[1]
            print(f"🔍 Extraction des appartements depuis l'alerte...")
            
            if await scraper.login():
                # Extraire les URLs d'appartements depuis l'alerte
                await scraper.page.goto(alert_url)
                await scraper.page.wait_for_load_state('networkidle')
                await scraper.page.wait_for_timeout(3000)
                
                # Chercher les liens d'appartements
                selectors = [
                    'a[href*="alert_result"][href*="ad="]',
                    'a[href*="ad="]',
                    'a[href*="alert_result"]'
                ]
                
                for selector in selectors:
                    apartment_links = scraper.page.locator(selector)
                    count = await apartment_links.count()
                    if count > 0:
                        print(f"   📋 {count} appartements trouvés avec {selector}")
                        
                        for i in range(min(3, count)):
                            href = await apartment_links.nth(i).get_attribute('href')
                            if href:
                                if 'ad=' in href:
                                    import re
                                    match = re.search(r'ad=(\d+)', href)
                                    if match:
                                        apt_id = match.group(1)
                                        full_url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apt_id}&from=dashboard_card"
                                        if full_url not in apartment_urls:
                                            apartment_urls.append(full_url)
                        
                        if len(apartment_urls) >= 3:
                            break
        elif await scraper.login():
            print("✅ Connexion réussie\n")
        else:
            print("❌ Échec de la connexion")
            return False
        
        # Vérifier qu'on a des URLs à tester
        if len(apartment_urls) == 0:
            print("❌ Aucune URL d'appartement à tester")
            return False
        
        print(f"📋 {len(apartment_urls)} appartements à tester\n")
        
        # Lister les screenshots existants avant le test
        screenshots_dir = "data/screenshots"
        existing_screenshots = []
        if os.path.exists(screenshots_dir):
            existing_screenshots = [f for f in os.listdir(screenshots_dir) if f.startswith('map_') and f.endswith('.png')]
            print(f"📸 Screenshots existants: {len(existing_screenshots)}")
        
        # Tester chaque appartement
        test_results = []
        
        for i, url in enumerate(apartment_urls[:3], 1):  # Limiter à 3 pour le test
            print(f"\n{'='*60}")
            print(f"🏠 APPARTEMENT {i}/{min(3, len(apartment_urls))}")
            print(f"{'='*60}")
            print(f"📍 URL: {url}")
            
            try:
                # Scraper l'appartement
                apartment_data = await scraper.scrape_apartment(url)
                
                if apartment_data:
                    apt_id = apartment_data.get('id', 'unknown')
                    print(f"✅ Appartement {apt_id} scrapé")
                    
                    # Vérifier que le screenshot de carte a été créé
                    map_info = apartment_data.get('map_info', {})
                    screenshot_path = map_info.get('screenshot')
                    
                    if screenshot_path:
                        print(f"📸 Screenshot de carte: {screenshot_path}")
                        
                        # Vérifier que le fichier existe
                        if os.path.exists(screenshot_path):
                            file_size = os.path.getsize(screenshot_path)
                            print(f"   ✅ Fichier existe ({file_size} bytes)")
                            
                            # Vérifier que l'ID est dans le nom du fichier
                            if apt_id in screenshot_path:
                                print(f"   ✅ ID de l'appartement ({apt_id}) présent dans le nom du fichier")
                                test_results.append({
                                    'apartment_id': apt_id,
                                    'screenshot': screenshot_path,
                                    'exists': True,
                                    'has_id_in_name': True,
                                    'size': file_size
                                })
                            else:
                                print(f"   ⚠️ ID de l'appartement ({apt_id}) absent du nom du fichier")
                                test_results.append({
                                    'apartment_id': apt_id,
                                    'screenshot': screenshot_path,
                                    'exists': True,
                                    'has_id_in_name': False,
                                    'size': file_size
                                })
                        else:
                            print(f"   ❌ Fichier non trouvé: {screenshot_path}")
                            test_results.append({
                                'apartment_id': apt_id,
                                'screenshot': screenshot_path,
                                'exists': False,
                                'has_id_in_name': False
                            })
                    else:
                        print(f"   ⚠️ Aucun screenshot de carte dans map_info")
                        test_results.append({
                            'apartment_id': apt_id,
                            'screenshot': None,
                            'exists': False,
                            'has_id_in_name': False
                        })
                else:
                    print(f"❌ Échec du scraping")
                    test_results.append({
                        'apartment_id': None,
                        'screenshot': None,
                        'exists': False,
                        'has_id_in_name': False
                    })
                
                # Pause entre les appartements
                await scraper.page.wait_for_timeout(2000)
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
                test_results.append({
                    'apartment_id': None,
                    'screenshot': None,
                    'exists': False,
                    'has_id_in_name': False,
                    'error': str(e)
                })
        
        # Résumé des résultats
        print(f"\n{'='*60}")
        print("📊 RÉSUMÉ DES TESTS")
        print(f"{'='*60}")
        
        successful_tests = sum(1 for r in test_results if r.get('exists') and r.get('has_id_in_name'))
        total_tests = len(test_results)
        
        for i, result in enumerate(test_results, 1):
            apt_id = result.get('apartment_id', 'N/A')
            exists = result.get('exists', False)
            has_id = result.get('has_id_in_name', False)
            
            status = "✅" if (exists and has_id) else "❌"
            print(f"{status} Appartement {i} (ID: {apt_id})")
            if exists:
                print(f"   📸 Screenshot: {os.path.basename(result.get('screenshot', 'N/A'))}")
                print(f"   📏 Taille: {result.get('size', 0)} bytes")
            else:
                print(f"   ⚠️ Screenshot manquant")
        
        print(f"\n📈 Résultats: {successful_tests}/{total_tests} tests réussis")
        
        if successful_tests == total_tests:
            print("🎉 TOUS LES TESTS SONT RÉUSSIS !")
            return True
        else:
            print(f"⚠️ {total_tests - successful_tests} test(s) ont échoué")
            return False
        
    except Exception as e:
        print(f"\n❌ Erreur globale: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(test_map_screenshots())

