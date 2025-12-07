#!/usr/bin/env python3
"""
Script pour récupérer régulièrement les annonces manquantes depuis le dashboard Jinka
- Se connecte au dashboard
- Extrait toutes les URLs d'appartements disponibles
- Compare avec les appartements déjà scrapés
- Scrape uniquement les appartements manquants
"""

import asyncio
import json
import os
import re
from datetime import datetime
from scrape_jinka import JinkaScraper
from extract_all_apartment_urls import (
    extract_all_apartment_urls,
    scroll_to_load_all_apartments,
    click_load_more_until_done,
    extract_urls_from_page
)


def load_existing_apartments():
    """Charge la liste des IDs d'appartements déjà scrapés"""
    apartments_dir = 'data/appartements'
    if not os.path.exists(apartments_dir):
        return set()
    
    apartment_files = [f for f in os.listdir(apartments_dir) if f.endswith('.json')]
    return {f.replace('.json', '') for f in apartment_files}


def extract_apartment_id_from_url(url):
    """Extrait l'ID d'appartement depuis une URL"""
    match = re.search(r'ad=(\d+)', url)
    return match.group(1) if match else None


def find_missing_apartments(dashboard_urls, existing_ids):
    """Trouve les appartements manquants"""
    missing_urls = []
    missing_ids = []
    
    for url in dashboard_urls:
        apt_id = extract_apartment_id_from_url(url)
        if apt_id and apt_id not in existing_ids:
            missing_urls.append(url)
            missing_ids.append(apt_id)
    
    return missing_urls, missing_ids


async def scrape_missing_apartments(scraper, missing_urls, skip_if_exists=True):
    """Scrape les appartements manquants"""
    scraped_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, url in enumerate(missing_urls, 1):
        print(f"\n🏠 SCRAPING APPARTEMENT MANQUANT {i}/{len(missing_urls)}")
        print(f"   URL: {url}")
        print("-" * 60)
        
        try:
            # Scraper l'appartement
            apartment_data = await scraper.scrape_apartment(url)
            
            if apartment_data:
                apt_id = apartment_data.get('id')
                
                # Sauvegarder l'appartement
                saved = await scraper.save_apartment(apartment_data, skip_if_exists=skip_if_exists)
                
                if saved:
                    scraped_count += 1
                    print(f"   ✅ Appartement {apt_id} scrapé et sauvegardé")
                    print(f"   💰 Prix: {apartment_data.get('prix', 'N/A')}")
                    print(f"   📐 Surface: {apartment_data.get('surface', 'N/A')}")
                    print(f"   📍 Localisation: {apartment_data.get('localisation', 'N/A')}")
                else:
                    skipped_count += 1
                    print(f"   ⏭️  Appartement {apt_id} déjà existant - SKIP")
            else:
                error_count += 1
                print(f"   ❌ Échec du scraping")
                
        except Exception as e:
            error_count += 1
            print(f"   ❌ Erreur: {e}")
        
        # Pause entre les requêtes pour éviter la surcharge
        if i < len(missing_urls):
            await asyncio.sleep(1)
    
    return scraped_count, skipped_count, error_count


async def fetch_missing_from_dashboard(dashboard_url=None, max_missing=None, skip_if_exists=True):
    """
    Récupère les annonces manquantes depuis le dashboard Jinka
    
    Args:
        dashboard_url: URL du dashboard (optionnel, utilise config.json sinon)
        max_missing: Nombre maximum d'appartements manquants à scraper (None = tous)
        skip_if_exists: Si True, ne pas écraser les fichiers existants
    
    Returns:
        Tuple (success, stats_dict)
    """
    print("🔍 RÉCUPÉRATION DES ANNONCES MANQUANTES")
    print("=" * 60)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Charger les appartements déjà scrapés
    print("📋 PHASE 1: Analyse des appartements existants")
    print("-" * 60)
    existing_ids = load_existing_apartments()
    print(f"✅ {len(existing_ids)} appartements déjà scrapés")
    print()
    
    # 2. Extraire toutes les URLs du dashboard
    print("🌐 PHASE 2: Extraction des URLs depuis le dashboard")
    print("-" * 60)
    
    scraper = JinkaScraper()
    
    try:
        # Setup
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # Login
        print("\n🔐 Connexion à Jinka...")
        print("   (Cette étape peut prendre quelques secondes...)")
        try:
            # Timeout plus long pour la connexion par email (peut prendre du temps pour récupérer le code Gmail)
            login_success = await asyncio.wait_for(scraper.login(), timeout=120.0)
            if not login_success:
                print("❌ Échec de la connexion")
                return False, {}
        except asyncio.TimeoutError:
            print("❌ Timeout lors de la connexion (120s)")
            return False, {}
        
        print("✅ Connexion réussie")
        
        # Attendre un peu après le login pour que la redirection se fasse
        print("   Attente de la redirection...")
        await asyncio.sleep(1000)
        
        # Vérifier où on se trouve après le login
        current_url_after_login = scraper.page.url
        print(f"📍 URL après login: {current_url_after_login}")
        
        # Si on est sur une page d'appartement ou autre, on doit aller au dashboard
        if "alert_result" in current_url_after_login or "ad=" in current_url_after_login:
            print("⚠️  Redirection vers un appartement détectée après login")
            print("   Navigation vers le dashboard...")
        
        # Charger l'URL du dashboard
        if not dashboard_url:
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    dashboard_url = config.get('dashboard_url') or config.get('alert_url')
                    # Si alert_url pointe vers un appartement, extraire le token pour le dashboard
                    if dashboard_url and 'alert_result' in dashboard_url:
                        # Extraire le token depuis l'URL
                        token_match = re.search(r'token=([^&]+)', dashboard_url)
                        if token_match:
                            token = token_match.group(1)
                            dashboard_url = f"https://www.jinka.fr/asrenter/alert/dashboard/{token}"
            except:
                pass
        
        if not dashboard_url:
            dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        
        print(f"\n🌐 Navigation vers le dashboard...")
        print(f"   URL: {dashboard_url}")
        try:
            await asyncio.wait_for(
                scraper.page.goto(dashboard_url, wait_until='domcontentloaded', timeout=15000),
                timeout=15.0
            )
            print("   Page chargée, attente du contenu...")
            await asyncio.sleep(1500)
        except asyncio.TimeoutError:
            print("⚠️  Timeout lors du chargement du dashboard, continuons quand même...")
            await asyncio.sleep(1000)
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle après navigation: {current_url}")
        
        if "sign/in" in current_url:
            print("❌ Redirection vers login détectée")
            return False, {}
        
        # Vérifier qu'on est bien sur le dashboard (pas sur un appartement)
        is_on_dashboard = "dashboard" in current_url or ("asrenter/alert" in current_url and "alert_result" not in current_url)
        
        if not is_on_dashboard:
            print("⚠️  Pas sur le dashboard détecté")
            print("   Essayons différentes méthodes pour accéder au dashboard...")
            
            # Méthode 1: Chercher un lien vers le dashboard dans le menu
            dashboard_links = await scraper.page.locator('a[href*="dashboard"], a:has-text("Dashboard"), a:has-text("Mes alertes"), nav a[href*="alert"]').all()
            if dashboard_links:
                print(f"   Méthode 1: Trouvé {len(dashboard_links)} lien(s) vers le dashboard")
                try:
                    await dashboard_links[0].click()
                    await asyncio.sleep(1500)
                    current_url = scraper.page.url
                    print(f"   URL après clic: {current_url}")
                    is_on_dashboard = "dashboard" in current_url or ("asrenter/alert" in current_url and "alert_result" not in current_url)
                except Exception as e:
                    print(f"   Erreur lors du clic: {e}")
            
            # Méthode 2: Si toujours pas sur le dashboard, essayer d'aller directement
            if not is_on_dashboard:
                print("   Méthode 2: Navigation directe vers le dashboard...")
                try:
                    await asyncio.wait_for(
                        scraper.page.goto(dashboard_url, wait_until='domcontentloaded', timeout=15000),
                        timeout=15.0
                    )
                    await asyncio.sleep(1500)
                    current_url = scraper.page.url
                    print(f"   URL après navigation directe: {current_url}")
                    is_on_dashboard = "dashboard" in current_url or ("asrenter/alert" in current_url and "alert_result" not in current_url)
                except asyncio.TimeoutError:
                    print("   ⚠️  Timeout lors de la navigation directe")
                    # Vérifier quand même l'URL actuelle
                    current_url = scraper.page.url
                    is_on_dashboard = "dashboard" in current_url or ("asrenter/alert" in current_url and "alert_result" not in current_url)
        
        if not is_on_dashboard:
            print("❌ Impossible d'accéder au dashboard")
            print(f"   URL actuelle: {current_url}")
            print("   Peut-être que l'URL du dashboard est incorrecte ou que vous n'avez pas accès")
            return False, {}
        
        print("✅ Accès au dashboard réussi !")
        
        # Scroll pour charger tous les appartements
        print("\n📜 Chargement de tous les appartements (scroll)...")
        print("   (Cela peut prendre 15-30 secondes selon le nombre d'appartements...)")
        try:
            await asyncio.wait_for(scroll_to_load_all_apartments(scraper.page), timeout=60.0)
        except asyncio.TimeoutError:
            print("⚠️  Timeout lors du scroll, continuons avec ce qui est chargé...")
        
        # Cliquer sur "Voir plus" si nécessaire
        print("\n🔘 Recherche de bouton 'Voir plus'...")
        try:
            await asyncio.wait_for(click_load_more_until_done(scraper.page), timeout=30.0)
        except asyncio.TimeoutError:
            print("⚠️  Timeout lors de la recherche du bouton 'Voir plus', continuons...")
        
        # Extraire toutes les URLs
        print("\n🔍 Extraction des URLs...")
        dashboard_urls = await extract_urls_from_page(scraper.page)
        print(f"✅ {len(dashboard_urls)} URLs trouvées sur le dashboard")
        print()
        
        # 3. Trouver les appartements manquants
        print("🔍 PHASE 3: Identification des appartements manquants")
        print("-" * 60)
        missing_urls, missing_ids = find_missing_apartments(dashboard_urls, existing_ids)
        
        print(f"📊 Statistiques:")
        print(f"   Total sur le dashboard: {len(dashboard_urls)}")
        print(f"   Déjà scrapés: {len(existing_ids)}")
        print(f"   Manquants: {len(missing_urls)}")
        print()
        
        if not missing_urls:
            print("✅ Aucun appartement manquant ! Tous les appartements sont déjà scrapés.")
            return True, {
                'total_dashboard': len(dashboard_urls),
                'existing': len(existing_ids),
                'missing': 0,
                'scraped': 0,
                'skipped': 0,
                'errors': 0
            }
        
        # Limiter le nombre si demandé
        if max_missing and len(missing_urls) > max_missing:
            print(f"⚠️  Limitation à {max_missing} appartements manquants (sur {len(missing_urls)})")
            missing_urls = missing_urls[:max_missing]
            missing_ids = missing_ids[:max_missing]
        
        # Afficher les premiers appartements manquants
        print(f"📋 Premiers appartements manquants:")
        for i, (url, apt_id) in enumerate(zip(missing_urls[:10], missing_ids[:10]), 1):
            print(f"   {i}. ID: {apt_id}")
        if len(missing_urls) > 10:
            print(f"   ... et {len(missing_urls) - 10} autres")
        print()
        
        # 4. Scraper les appartements manquants
        print("🏠 PHASE 4: Scraping des appartements manquants")
        print("-" * 60)
        scraped_count, skipped_count, error_count = await scrape_missing_apartments(
            scraper, missing_urls, skip_if_exists=skip_if_exists
        )
        
        # 5. Résumé final
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ FINAL")
        print("=" * 60)
        print(f"✅ Appartements scrapés: {scraped_count}")
        print(f"⏭️  Appartements déjà existants (skip): {skipped_count}")
        print(f"❌ Erreurs: {error_count}")
        print(f"📈 Total manquants traités: {scraped_count + skipped_count + error_count}")
        print()
        print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Sauvegarder un log
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'total_dashboard': len(dashboard_urls),
            'existing': len(existing_ids),
            'missing': len(missing_urls),
            'scraped': scraped_count,
            'skipped': skipped_count,
            'errors': error_count
        }
        
        os.makedirs('data/logs', exist_ok=True)
        log_file = f"data/logs/fetch_missing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Log sauvegardé: {log_file}")
        
        return True, log_data
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False, {}
    
    finally:
        await scraper.cleanup()


async def main():
    """Fonction principale"""
    import sys
    
    # Paramètres depuis la ligne de commande
    max_missing = None
    dashboard_url = None
    
    if len(sys.argv) > 1:
        try:
            max_missing = int(sys.argv[1])
        except ValueError:
            dashboard_url = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            max_missing = int(sys.argv[2])
        except ValueError:
            pass
    
    success, stats = await fetch_missing_from_dashboard(
        dashboard_url=dashboard_url,
        max_missing=max_missing,
        skip_if_exists=True
    )
    
    if success:
        print("\n🎉 Récupération terminée avec succès !")
        if stats.get('scraped', 0) > 0:
            print(f"   ✅ {stats['scraped']} nouveaux appartements ajoutés")
    else:
        print("\n❌ Erreur lors de la récupération")


if __name__ == "__main__":
    asyncio.run(main())

