#!/usr/bin/env python3
"""
Script pour récupérer et scraper les nouveaux appartements depuis Jinka
Compare avec les appartements déjà scrapés pour ne scraper que les nouveaux
"""

import asyncio
import json
import os
import re
from scrape_jinka import JinkaScraper
from extract_all_apartment_urls import extract_urls_from_page, scroll_to_load_all_apartments, click_load_more_until_done


def load_existing_apartment_ids():
    """Charge la liste des IDs d'appartements déjà scrapés"""
    apartments_dir = 'data/appartements'
    if not os.path.exists(apartments_dir):
        return set()
    
    apartment_files = [f for f in os.listdir(apartments_dir) if f.endswith('.json')]
    # Enlever les fichiers de test
    apartment_ids = {f.replace('.json', '') for f in apartment_files if not f.startswith('test_')}
    return apartment_ids


def extract_apartment_id_from_url(url):
    """Extrait l'ID d'appartement depuis une URL"""
    match = re.search(r'ad=(\d+)', url)
    return match.group(1) if match else None


def filter_new_apartments(all_urls, existing_ids):
    """Filtre les URLs pour ne garder que les nouveaux appartements"""
    new_urls = []
    new_ids = set()
    
    for url in all_urls:
        apartment_id = extract_apartment_id_from_url(url)
        if apartment_id and apartment_id not in existing_ids:
            if apartment_id not in new_ids:  # Éviter les doublons
                new_urls.append(url)
                new_ids.add(apartment_id)
    
    return new_urls


async def scrape_new_apartments():
    """
    Fonction principale pour récupérer et scraper les nouveaux appartements
    """
    print("🏠 RÉCUPÉRATION DES NOUVEAUX APPARTEMENTS JINKA")
    print("=" * 60)
    
    # 1. Charger les appartements déjà scrapés
    print("\n📋 ÉTAPE 1: Vérification des appartements existants")
    print("-" * 40)
    existing_ids = load_existing_apartment_ids()
    print(f"✅ {len(existing_ids)} appartements déjà scrapés")
    
    # 2. Extraire toutes les URLs depuis le dashboard
    print("\n🔍 ÉTAPE 2: Extraction des URLs depuis le dashboard")
    print("-" * 40)
    
    # URL du dashboard
    dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
    
    scraper = JinkaScraper()
    
    try:
        # Setup
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # Aller directement à la page de login et attendre connexion manuelle
        print("\n🔐 CONNEXION MANUELLE REQUISE")
        print("=" * 40)
        print("1. Le navigateur va s'ouvrir sur la page de login Jinka")
        print("2. Connecte-toi manuellement avec Google")
        print("3. Le script attendra que tu sois connecté")
        print("4. Une fois connecté, le scraping continuera automatiquement")
        print()
        
        # Aller à la page de login
        print("🌐 Navigation vers la page de login...")
        await scraper.page.goto('https://www.jinka.fr/sign/in')
        await scraper.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Cliquer sur Google pour faciliter la connexion
        try:
            google_button = scraper.page.locator('button:has-text("Continuer avec Google")').first
            if await google_button.count() > 0:
                await google_button.click()
                await asyncio.sleep(2)
                print("✅ Redirection vers Google")
        except:
            pass
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        # Attendre la connexion manuelle (toujours)
        # Attendre la connexion manuelle SANS rafraîchir la page
        print("⏸️  Le script attend que tu te connectes...")
        print("   (Pas de rafraîchissement automatique - tu peux te connecter tranquillement)")
        print()
        
        max_wait = 600  # 10 minutes max
        wait_time = 0
        login_success = False
        
        while wait_time < max_wait:
            # Vérifier l'URL actuelle SANS changer de page
            current_url = scraper.page.url
            
            if wait_time % 10 == 0:  # Afficher seulement toutes les 10 secondes
                print(f"⏳ Attente connexion... ({wait_time}s) - URL: {current_url[:80]}...")
                print("   (Continue ta connexion, je ne vais pas rafraîchir)")
            
            # Vérifier si on est connecté (pas de redirection vers sign/in ou Google)
            if "jinka.fr" in current_url and "sign/in" not in current_url and "accounts.google.com" not in current_url:
                print("🎉 CONNEXION DÉTECTÉE !")
                login_success = True
                break
            
            await asyncio.sleep(2)  # Vérifier toutes les 2 secondes
            wait_time += 2
        
        if not login_success:
            print("⏰ Timeout - connexion non détectée")
            print("💡 Tu peux te reconnecter manuellement et relancer le script")
            return False
        
        # Maintenant qu'on est connecté, aller au dashboard UNE SEULE FOIS
        print("\n🌐 Navigation vers le dashboard...")
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Fermer les popups de cookies si présents
        try:
            cookie_selectors = [
                'button:has-text("Accepter")',
                'button:has-text("Accept")',
                'button:has-text("OK")',
                '[id*="cookie"] button',
                '[class*="cookie"] button',
                '.cookie-consent button',
                '#cookieConsent button'
            ]
            for selector in cookie_selectors:
                cookie_button = scraper.page.locator(selector).first
                if await cookie_button.count() > 0:
                    await cookie_button.click()
                    print("✅ Popup cookies fermée")
                    await asyncio.sleep(1)
                    break
        except:
            pass  # Pas de popup cookies, on continue
        
        current_url = scraper.page.url
        print(f"📍 URL dashboard: {current_url}")
        
        if "sign/in" in current_url:
            print("❌ Redirection vers login détectée - connexion perdue")
            return False
        
        print("✅ Connexion réussie et vérifiée")
        print("✅ Accès au dashboard réussi !")
        
        # Scroll pour charger tous les appartements
        print("\n📜 Chargement de tous les appartements (scroll)...")
        await scroll_to_load_all_apartments(scraper.page)
        
        # Cliquer sur "Voir plus" si disponible
        print("\n🔘 Recherche de bouton 'Voir plus'...")
        await click_load_more_until_done(scraper.page)
        
        # Extraire toutes les URLs
        print("\n🔍 Extraction des URLs...")
        all_urls = await extract_urls_from_page(scraper.page)
        print(f"✅ {len(all_urls)} URLs trouvées au total")
        
        # 3. Filtrer pour ne garder que les nouveaux
        print("\n🔍 ÉTAPE 3: Filtrage des nouveaux appartements")
        print("-" * 40)
        new_urls = filter_new_apartments(all_urls, existing_ids)
        print(f"✅ {len(new_urls)} nouveaux appartements trouvés")
        
        if not new_urls:
            print("\n🎉 Aucun nouvel appartement à scraper !")
            return True
        
        # Afficher les nouveaux appartements
        print(f"\n📋 Nouveaux appartements à scraper:")
        for i, url in enumerate(new_urls[:10], 1):
            apt_id = extract_apartment_id_from_url(url)
            print(f"   {i}. Appartement {apt_id}")
        
        if len(new_urls) > 10:
            print(f"   ... et {len(new_urls) - 10} autres")
        
        # 4. Scraper les nouveaux appartements
        print(f"\n🏠 ÉTAPE 4: Scraping des {len(new_urls)} nouveaux appartements")
        print("-" * 40)
        
        # Vérifier à nouveau les IDs existants AVANT de scraper (sécurité supplémentaire)
        current_existing_ids = load_existing_apartment_ids()
        
        scraped_count = 0
        skipped_count = 0
        
        for i, url in enumerate(new_urls, 1):
            apt_id = extract_apartment_id_from_url(url)
            
            # Double vérification : ne pas scraper si l'appartement existe déjà
            if apt_id in current_existing_ids:
                print(f"\n⏭️  Appartement {apt_id} déjà existant - SKIP")
                skipped_count += 1
                continue
            
            print(f"\n🏠 Scraping {i}/{len(new_urls)}: Appartement {apt_id}")
            print(f"   URL: {url[:80]}...")
            
            try:
                apartment_data = await scraper.scrape_apartment(url)
                
                if apartment_data:
                    apt_id_scraped = apartment_data.get('id')
                    
                    # Vérifier une dernière fois avant de sauvegarder
                    final_check_ids = load_existing_apartment_ids()
                    if apt_id_scraped in final_check_ids:
                        print(f"   ⚠️  Appartement {apt_id_scraped} créé entre-temps - SKIP sauvegarde")
                        skipped_count += 1
                    else:
                        # Sauvegarder avec protection contre les doublons
                        saved = await scraper.save_apartment(apartment_data, skip_if_exists=True)
                        if saved:
                            print(f"   ✅ Appartement scrapé: {apartment_data.get('titre', 'N/A')}")
                            print(f"   💰 Prix: {apartment_data.get('prix', 'N/A')}")
                            print(f"   📐 Surface: {apartment_data.get('surface', 'N/A')}")
                            scraped_count += 1
                        else:
                            print(f"   ⏭️  Appartement déjà sauvegardé - SKIP")
                            skipped_count += 1
                else:
                    print(f"   ❌ Échec du scraping")
                
                # Pause entre les requêtes
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                continue
        
        # Résumé final
        print(f"\n📊 RÉSULTATS FINAUX")
        print("=" * 60)
        print(f"✅ {scraped_count} nouveaux appartements scrapés avec succès")
        if skipped_count > 0:
            print(f"⏭️  {skipped_count} appartements ignorés (déjà existants)")
        print(f"📋 Total URLs analysées: {len(new_urls)}")
        
        # Vérification finale : aucun doublon créé
        final_existing_ids = load_existing_apartment_ids()
        print(f"\n🔍 Vérification finale:")
        print(f"   Total appartements après scraping: {len(final_existing_ids)}")
        
        if scraped_count > 0:
            print(f"\n🎉 SUCCÈS ! {scraped_count} nouveaux appartements récupérés et scrapés.")
            print(f"✅ Aucun doublon créé.")
        elif skipped_count > 0:
            print(f"\n✅ Aucun nouvel appartement à scraper.")
            print(f"   Tous les appartements trouvés existaient déjà.")
        else:
            print(f"\n⚠️ Aucun appartement n'a pu être scrapé.")
        
        return scraped_count > 0
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")


if __name__ == "__main__":
    asyncio.run(scrape_new_apartments())

