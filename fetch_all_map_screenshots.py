#!/usr/bin/env python3
"""
Script pour récupérer les screenshots de carte pour tous les appartements
"""

import asyncio
import json
import os
import re
from datetime import datetime
from scrape_jinka import JinkaScraper
from dotenv import load_dotenv

load_dotenv()

async def fetch_map_screenshot(scraper, apartment_data):
    """Récupère uniquement le screenshot de carte pour un appartement"""
    url = apartment_data.get('url')
    apt_id = apartment_data.get('id')
    
    if not url or not apt_id:
        return None
    
    try:
        print(f"   🗺️ Récupération du screenshot pour l'appartement {apt_id}...")
        
        # Naviguer vers la page de l'appartement
        await scraper.page.goto(url)
        await scraper.page.wait_for_load_state('networkidle')
        await scraper.page.wait_for_timeout(2000)
        
        # Extraire uniquement le screenshot de la carte
        screenshot_path = await scraper.extract_map_info(apartment_id=apt_id)
        
        return screenshot_path
        
    except Exception as e:
        print(f"   ❌ Erreur pour l'appartement {apt_id}: {e}")
        return None

async def fetch_all_map_screenshots():
    """Récupère les screenshots de carte pour tous les appartements"""
    print("🗺️ RÉCUPÉRATION DES SCREENSHOTS DE CARTE")
    print("=" * 70)
    
    # Charger tous les appartements
    scraped_file = "data/scraped_apartments.json"
    if not os.path.exists(scraped_file):
        print(f"❌ Fichier {scraped_file} non trouvé")
        return
    
    print(f"📋 Chargement des appartements depuis {scraped_file}...")
    with open(scraped_file, 'r', encoding='utf-8') as f:
        all_apartments = json.load(f)
    
    print(f"✅ {len(all_apartments)} appartements chargés\n")
    
    # Identifier les appartements qui ont besoin d'un screenshot
    apartments_needing_screenshot = []
    
    for apt in all_apartments:
        apt_id = apt.get('id')
        screenshot_path = apt.get('map_info', {}).get('screenshot')
        
        needs_screenshot = False
        
        if not screenshot_path or screenshot_path == 'N/A':
            needs_screenshot = True
            reason = "Screenshot manquant"
        else:
            # Vérifier si c'est l'ancien format (sans ID)
            screenshot_filename = os.path.basename(screenshot_path)
            if re.match(r'map_\d{8}_\d{6}\.png$', screenshot_filename):
                # Ancien format : map_YYYYMMDD_HHMMSS.png
                needs_screenshot = True
                reason = "Ancien format (sans ID)"
            elif not re.match(r'map_\d+_\d{8}_\d{6}\.png$', screenshot_filename):
                # Format invalide
                needs_screenshot = True
                reason = "Format invalide"
            else:
                # Vérifier que l'ID correspond
                match = re.match(r'map_(\d+)_(\d{8}_\d{6})\.png$', screenshot_filename)
                if match:
                    screenshot_id = match.group(1)
                    if apt_id != screenshot_id:
                        needs_screenshot = True
                        reason = f"ID mismatch (appartement={apt_id}, screenshot={screenshot_id})"
        
        if needs_screenshot:
            apartments_needing_screenshot.append({
                'apartment': apt,
                'reason': reason
            })
    
    print(f"📊 RÉSUMÉ:")
    print(f"   Total d'appartements: {len(all_apartments)}")
    print(f"   Appartements avec screenshot valide: {len(all_apartments) - len(apartments_needing_screenshot)}")
    print(f"   Appartements nécessitant un screenshot: {len(apartments_needing_screenshot)}\n")
    
    if len(apartments_needing_screenshot) == 0:
        print("✅ Tous les appartements ont déjà un screenshot valide !")
        return
    
    print(f"📋 Appartements nécessitant un screenshot:")
    for i, item in enumerate(apartments_needing_screenshot[:10], 1):
        apt_id = item['apartment'].get('id', 'N/A')
        print(f"   {i}. Appartement {apt_id} - {item['reason']}")
    if len(apartments_needing_screenshot) > 10:
        print(f"   ... et {len(apartments_needing_screenshot) - 10} autres\n")
    
    # Initialiser le scraper
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        print("✅ Scraper initialisé\n")
        
        # Se connecter
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        print("✅ Connexion réussie\n")
        print("=" * 70)
        
        # Récupérer les screenshots
        successful = 0
        failed = 0
        
        for i, item in enumerate(apartments_needing_screenshot, 1):
            apt = item['apartment']
            apt_id = apt.get('id', 'N/A')
            url = apt.get('url')
            
            print(f"\n🏠 APPARTEMENT {i}/{len(apartments_needing_screenshot)}")
            print(f"   ID: {apt_id}")
            print(f"   URL: {url}")
            print(f"   Raison: {item['reason']}")
            
            if not url:
                print(f"   ❌ Pas d'URL pour l'appartement {apt_id}")
                failed += 1
                continue
            
            try:
                # Naviguer vers la page de l'appartement
                await scraper.page.goto(url)
                await scraper.page.wait_for_load_state('networkidle')
                await scraper.page.wait_for_timeout(2000)
                
                # Extraire le screenshot de la carte avec l'ID
                # Si map_info existe déjà, on le met à jour, sinon on en crée un nouveau
                existing_map_info = apt.get('map_info', {})
                
                map_info = await scraper.extract_map_info(apartment_id=apt_id)
                
                screenshot_path = map_info.get('screenshot')
                
                if screenshot_path and os.path.exists(screenshot_path):
                    # Vérifier que le screenshot contient bien l'ID
                    screenshot_filename = os.path.basename(screenshot_path)
                    if apt_id in screenshot_filename:
                        print(f"   ✅ Screenshot récupéré: {screenshot_filename}")
                        
                        # Mettre à jour les données de l'appartement
                        apt['map_info'] = map_info
                        
                        # Sauvegarder l'appartement individuellement
                        apt_file = f"data/appartements/{apt_id}.json"
                        os.makedirs("data/appartements", exist_ok=True)
                        with open(apt_file, 'w', encoding='utf-8') as f:
                            json.dump(apt, f, ensure_ascii=False, indent=2)
                        
                        successful += 1
                    else:
                        print(f"   ⚠️ Screenshot créé mais l'ID n'est pas dans le nom: {screenshot_filename}")
                        failed += 1
                else:
                    print(f"   ⚠️ Screenshot non créé ou non trouvé")
                    failed += 1
                
                # Pause entre les appartements
                await scraper.page.wait_for_timeout(2000)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        # Sauvegarder tous les appartements mis à jour
        print(f"\n{'='*70}")
        print(f"💾 Sauvegarde de tous les appartements mis à jour...")
        with open(scraped_file, 'w', encoding='utf-8') as f:
            json.dump(all_apartments, f, ensure_ascii=False, indent=2)
        print(f"✅ Tous les appartements sauvegardés dans {scraped_file}")
        
        # Résumé
        print(f"\n{'='*70}")
        print(f"📊 RÉSUMÉ")
        print(f"{'='*70}")
        print(f"Total: {len(apartments_needing_screenshot)}")
        print(f"✅ Réussis: {successful}")
        print(f"❌ Échecs: {failed}")
        print(f"📈 Taux de réussite: {100*successful/len(apartments_needing_screenshot):.1f}%")
        
        if successful == len(apartments_needing_screenshot):
            print("\n🎉 TOUS LES SCREENSHOTS ONT ÉTÉ RÉCUPÉRÉS AVEC SUCCÈS !")
        elif successful > 0:
            print(f"\n✅ {successful} screenshots récupérés avec succès")
            if failed > 0:
                print(f"⚠️ {failed} screenshots n'ont pas pu être récupérés")
        
    except Exception as e:
        print(f"\n❌ Erreur globale: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n⚠️ Le navigateur restera ouvert")
        print("Ferme-le manuellement quand tu as fini")

if __name__ == "__main__":
    asyncio.run(fetch_all_map_screenshots())

