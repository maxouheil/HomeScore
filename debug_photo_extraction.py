#!/usr/bin/env python3
"""
Script de debug pour comprendre pourquoi certaines photos ne sont pas trouvées
"""

import asyncio
import sys
from scrape_jinka import JinkaScraper
from dotenv import load_dotenv

load_dotenv()

async def debug_photo_extraction(apartment_id):
    """Debug l'extraction de photos pour un appartement spécifique"""
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        
        # Connexion
        print("🔐 Connexion à Jinka...")
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        print("✅ Connexion réussie\n")
        
        # Charger les appartements pour trouver l'URL
        import json
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        
        apartment = next((apt for apt in apartments if apt.get('id') == apartment_id), None)
        if not apartment:
            print(f"❌ Appartement {apartment_id} non trouvé")
            return
        
        apartment_url = apartment.get('url', '')
        if not apartment_url:
            print(f"❌ Pas d'URL pour l'appartement {apartment_id}")
            return
        
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG Appartement {apartment_id}")
        print(f"{'='*60}\n")
        
        # Naviguer vers l'appartement
        await scraper.page.goto(apartment_url)
        await scraper.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Scroller pour déclencher le lazy loading
        await scraper.page.evaluate('window.scrollTo(0, 200)')
        await asyncio.sleep(0.5)
        await scraper.page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(0.5)
        
        # Chercher la galerie
        gallery_selectors = [
            'div.sc-cJSrbW.juBoVb',
            'div.sc-gPEVay.jnWxBz',
            '[class*="sc-cJSrbW"][class*="juBoVb"]',
            '[class*="sc-gPEVay"][class*="jnWxBz"]'
        ]
        
        gallery_found = False
        for selector in gallery_selectors:
            try:
                gallery_div = scraper.page.locator(selector)
                if await gallery_div.count() > 0:
                    print(f"✅ Galerie trouvée: {selector}\n")
                    gallery_found = True
                    
                    # Chercher toutes les images dans la galerie
                    all_images = await gallery_div.locator('img').all()
                    print(f"📸 Total images dans la galerie: {len(all_images)}\n")
                    
                    for i, img in enumerate(all_images, 1):
                        try:
                            src = await img.get_attribute('src')
                            data_src = await img.get_attribute('data-src')
                            data_lazy = await img.get_attribute('data-lazy-src')
                            alt = await img.get_attribute('alt')
                            classes = await img.get_attribute('class')
                            parent_classes = await img.evaluate('el => el.parentElement ? el.parentElement.className : ""')
                            
                            display = await img.evaluate('el => window.getComputedStyle(el).display')
                            visibility = await img.evaluate('el => window.getComputedStyle(el).visibility')
                            width = await img.evaluate('el => el.naturalWidth || el.width || 0')
                            height = await img.evaluate('el => el.naturalHeight || el.height || 0')
                            
                            print(f"--- Image {i} ---")
                            print(f"  src: {src[:100] if src else 'None'}")
                            print(f"  data-src: {data_src[:100] if data_src else 'None'}")
                            print(f"  data-lazy-src: {data_lazy[:100] if data_lazy else 'None'}")
                            print(f"  alt: {alt}")
                            print(f"  classes: {classes}")
                            print(f"  parent classes: {parent_classes}")
                            print(f"  display: {display}")
                            print(f"  visibility: {visibility}")
                            print(f"  dimensions: {width}x{height}")
                            
                            # Vérifier pourquoi cette image serait filtrée
                            reasons = []
                            if alt and 'preloader' in alt.lower():
                                reasons.append("❌ ALT='preloader'")
                            if src and ('logo' in src.lower() or 'source_logos' in src.lower()):
                                reasons.append("❌ URL contient 'logo'")
                            if src and 'preloader' in src.lower():
                                reasons.append("❌ URL contient 'preloader'")
                            if width > 0 and height > 0 and (width < 200 or height < 200):
                                reasons.append(f"❌ Dimensions trop petites ({width}x{height})")
                            if display == 'none':
                                reasons.append("❌ display='none'")
                            if visibility == 'hidden':
                                reasons.append("❌ visibility='hidden'")
                            
                            # Vérifier si l'URL correspond aux patterns
                            src_to_check = src or data_src or data_lazy
                            photo_patterns = ['loueragile', 'upload_pro_ad', 'media.apimo.pro', 'studio-net.fr', 'images.century21.fr', 'biens', 'apartement', 'transopera', 'staticlbi']
                            if src_to_check:
                                matches_pattern = any(pattern in src_to_check.lower() for pattern in photo_patterns)
                                if not matches_pattern:
                                    reasons.append(f"❌ URL ne correspond à aucun pattern: {src_to_check[:60]}")
                                else:
                                    reasons.append(f"✅ URL correspond à un pattern")
                            
                            if reasons:
                                print(f"  Raisons de filtrage: {', '.join(reasons)}")
                            else:
                                print(f"  ✅ Cette image devrait être acceptée!")
                            print()
                            
                        except Exception as e:
                            print(f"  ❌ Erreur analyse image {i}: {e}\n")
                    
                    break  # On a trouvé une galerie, on s'arrête
            except:
                continue
        
        if not gallery_found:
            print("⚠️  Aucune galerie trouvée, recherche dans toute la page...\n")
            
            # Chercher toutes les images visibles
            all_visible = await scraper.page.locator('img:visible').all()
            print(f"📸 Total images visibles sur la page: {len(all_visible)}\n")
            
            for i, img in enumerate(all_visible[:10], 1):  # Limiter à 10 pour le debug
                try:
                    src = await img.get_attribute('src')
                    data_src = await img.get_attribute('data-src')
                    alt = await img.get_attribute('alt')
                    width = await img.evaluate('el => el.naturalWidth || el.width || 0')
                    height = await img.evaluate('el => el.naturalHeight || el.height || 0')
                    
                    print(f"--- Image visible {i} ---")
                    print(f"  src: {src[:100] if src else 'None'}")
                    print(f"  data-src: {data_src[:100] if data_src else 'None'}")
                    print(f"  alt: {alt}")
                    print(f"  dimensions: {width}x{height}")
                    print()
                except:
                    continue
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper.browser:
            await scraper.browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_photo_extraction.py <apartment_id>")
        print("\nAppartements sans photos:")
        print("  88404156, 92274287, 92075365, 91908884, 91658092, 89473319, 84210379")
        sys.exit(1)
    
    apartment_id = sys.argv[1]
    asyncio.run(debug_photo_extraction(apartment_id))


