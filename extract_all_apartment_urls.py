#!/usr/bin/env python3
"""
Script pour extraire TOUTES les URLs d'appartements depuis le dashboard Jinka
Gère le scroll infini, la pagination et les boutons "Voir plus"
"""

import asyncio
import json
import os
import re
from scrape_jinka import JinkaScraper


async def scroll_to_load_all_apartments(page, max_scrolls=50):
    """
    Scroll progressivement pour charger tous les appartements (lazy loading)
    
    Args:
        page: Page Playwright
        max_scrolls: Nombre maximum de scrolls à effectuer
    
    Returns:
        Nombre d'appartements chargés
    """
    print("   📜 Début du scroll pour charger tous les appartements...")
    
    last_count = 0
    stable_count = 0
    max_stable = 3  # Si le nombre ne change pas 3 fois, on arrête
    scroll_count = 0
    
    while scroll_count < max_scrolls and stable_count < max_stable:
        # Compter les appartements avant le scroll
        before_count = await page.locator('a[href*="ad="], a[href*="alert_result"]').count()
        
        # Scroller progressivement
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)  # Attendre le chargement lazy
        
        # Petit scroll supplémentaire pour déclencher le chargement
        await page.evaluate('window.scrollBy(0, -100)')
        await asyncio.sleep(0.5)
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1.5)
        
        # Compter les appartements après le scroll
        after_count = await page.locator('a[href*="ad="], a[href*="alert_result"]').count()
        
        scroll_count += 1
        
        if after_count == before_count:
            stable_count += 1
            print(f"   ⏸️  Scroll {scroll_count}: {after_count} appartements (stable {stable_count}/{max_stable})")
        else:
            stable_count = 0
            print(f"   📊 Scroll {scroll_count}: {before_count} → {after_count} appartements (+{after_count - before_count})")
        
        last_count = after_count
        
        # Sécurité: limite max (ex: 500 appartements)
        if after_count > 500:
            print(f"   🛑 Limite de sécurité atteinte ({after_count} appartements)")
            break
    
    print(f"   ✅ Scroll terminé: {last_count} appartements chargés après {scroll_count} scrolls")
    return last_count


async def click_load_more_until_done(page, max_clicks=100):
    """
    Clique sur 'Voir plus' / 'Load more' jusqu'à ce qu'il n'y en ait plus
    
    Args:
        page: Page Playwright
        max_clicks: Nombre maximum de clics
    
    Returns:
        Nombre de clics effectués
    """
    print("   🔘 Recherche de bouton 'Voir plus'...")
    
    click_count = 0
    
    while click_count < max_clicks:
        # Chercher le bouton avec différents sélecteurs
        load_more_selectors = [
            'button:has-text("Voir plus")',
            'button:has-text("Charger plus")',
            'button:has-text("Load more")',
            'a:has-text("Voir plus")',
            'a:has-text("Charger plus")',
            '[data-testid="load-more"]',
            '[data-testid="loadMore"]',
            '.load-more',
            'button[class*="load"]',
            'button[class*="more"]',
            'a[class*="load"]',
            'a[class*="more"]'
        ]
        
        button_found = False
        for selector in load_more_selectors:
            try:
                button = page.locator(selector).first
                if await button.count() > 0:
                    # Vérifier si visible et cliquable
                    is_visible = await button.is_visible()
                    if is_visible:
                        # Compter avant le clic
                        before_count = await page.locator('a[href*="ad="]').count()
                        
                        # Cliquer
                        await button.click()
                        await asyncio.sleep(3)  # Attendre le chargement
                        
                        # Compter après le clic
                        after_count = await page.locator('a[href*="ad="]').count()
                        
                        click_count += 1
                        button_found = True
                        print(f"   🔘 Clic {click_count}: {before_count} → {after_count} appartements (+{after_count - before_count})")
                        break
            except Exception as e:
                continue
        
        if not button_found:
            print(f"   ✅ Plus de bouton 'Voir plus' trouvé après {click_count} clics")
            break
    
    return click_count


async def extract_urls_from_page(page):
    """
    Extrait toutes les URLs d'appartements de la page actuelle
    
    Args:
        page: Page Playwright
    
    Returns:
        Liste d'URLs (dédupliquée)
    """
    urls = set()  # Utiliser un set pour éviter les doublons
    
    # Méthode 1: Sélecteurs Playwright
    try:
        links = page.locator('a[href*="alert_result"][href*="ad="], a[href*="ad="]')
        count = await links.count()
        
        for i in range(count):
            try:
                href = await links.nth(i).get_attribute('href')
                if href:
                    # Construire l'URL complète si nécessaire
                    if href.startswith('/'):
                        href = f"https://www.jinka.fr{href}"
                    elif not href.startswith('http'):
                        continue
                    
                    # Vérifier que c'est bien une URL d'appartement
                    if 'ad=' in href and 'alert_result' in href:
                        urls.add(href)
            except:
                continue
    except Exception as e:
        print(f"      ⚠️ Erreur méthode sélecteurs: {e}")
    
    # Méthode 2: Regex sur le HTML (backup)
    try:
        page_content = await page.content()
        
        # Pattern pour trouver les URLs d'appartements
        url_patterns = [
            r'href="(/alert_result\?token=[^&]+&ad=\d+[^"]*)"',
            r'href="(https://www\.jinka\.fr/alert_result\?token=[^&]+&ad=\d+[^"]*)"',
            r'ad=(\d+)',
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else None
                
                if match:
                    # Si c'est juste un ID, construire l'URL complète
                    if match.isdigit():
                        url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={match}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
                    elif match.startswith('/'):
                        url = f"https://www.jinka.fr{match}"
                    elif match.startswith('http'):
                        url = match
                    else:
                        continue
                    
                    if 'ad=' in url:
                        urls.add(url)
    except Exception as e:
        print(f"      ⚠️ Erreur méthode regex: {e}")
    
    # Méthode 3: JavaScript injection (backup)
    try:
        js_urls = await page.evaluate('''
            () => {
                const links = Array.from(document.querySelectorAll('a[href*="ad="]'));
                return links.map(link => {
                    let href = link.href || link.getAttribute('href');
                    if (href && !href.startsWith('http') && href.startsWith('/')) {
                        href = 'https://www.jinka.fr' + href;
                    }
                    return href;
                }).filter(href => href && href.includes('alert_result') && href.includes('ad='));
            }
        ''')
        
        for url in js_urls:
            if url:
                urls.add(url)
    except Exception as e:
        print(f"      ⚠️ Erreur méthode JavaScript: {e}")
    
    return list(urls)


async def extract_urls_from_all_pages(scraper, dashboard_url, max_pages=50):
    """
    Extrait les URLs de toutes les pages (si pagination par URL)
    
    Args:
        scraper: JinkaScraper instance
        dashboard_url: URL du dashboard
        max_pages: Nombre maximum de pages à tester
    
    Returns:
        Liste de toutes les URLs trouvées
    """
    print("   📄 Tentative d'extraction par pagination...")
    
    all_urls = []
    page = 1
    
    while page <= max_pages:
        # Construire l'URL de la page
        if '?' in dashboard_url:
            page_url = f"{dashboard_url}&page={page}"
        else:
            page_url = f"{dashboard_url}?page={page}"
        
        try:
            await scraper.page.goto(page_url)
            await scraper.page.wait_for_timeout(3000)
            
            # Extraire les URLs de cette page
            page_urls = await extract_urls_from_page(scraper.page)
            
            if not page_urls:
                print(f"   ⏹️  Page {page}: vide, arrêt de la pagination")
                break  # Plus d'appartements
            
            all_urls.extend(page_urls)
            print(f"   📄 Page {page}: {len(page_urls)} appartements trouvés")
            
            # Si moins d'appartements que d'habitude, peut-être la dernière page
            if page > 1 and len(page_urls) < 10:
                print(f"   ⚠️  Page {page} a peu d'appartements, peut être la dernière")
            
            page += 1
            await asyncio.sleep(1)  # Pause entre les pages
            
        except Exception as e:
            print(f"   ❌ Erreur page {page}: {e}")
            break
    
    if all_urls:
        print(f"   ✅ Pagination: {len(all_urls)} URLs trouvées sur {page-1} pages")
    else:
        print(f"   ⚠️  Pagination: aucune URL trouvée (peut-être pas de pagination par URL)")
    
    return all_urls


async def extract_all_apartment_urls(dashboard_url=None):
    """
    Extrait TOUTES les URLs d'appartements depuis le dashboard Jinka
    Utilise plusieurs stratégies combinées: scroll, bouton "Voir plus", pagination
    
    Args:
        dashboard_url: URL du dashboard (optionnel, utilise config.json sinon)
    
    Returns:
        Liste de toutes les URLs trouvées (dédupliquée)
    """
    print("🔍 EXTRACTION DE TOUTES LES URLs D'APPARTEMENTS")
    print("=" * 60)
    
    # Charger l'URL du dashboard
    if not dashboard_url:
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                dashboard_url = config.get('alert_url') or config.get('dashboard_url')
        except:
            pass
    
    if not dashboard_url:
        # URL par défaut
        dashboard_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
    
    print(f"📍 Dashboard URL: {dashboard_url}")
    
    scraper = JinkaScraper()
    
    try:
        # 1. Setup
        await scraper.setup()
        print("✅ Scraper initialisé")
        
        # 2. Login
        print("\n🔐 Connexion à Jinka...")
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return []
        
        print("✅ Connexion réussie")
        
        # 3. Aller au dashboard
        print(f"\n🌐 Navigation vers le dashboard...")
        await scraper.page.goto(dashboard_url)
        await scraper.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3000)
        
        current_url = scraper.page.url
        print(f"📍 URL actuelle: {current_url}")
        
        if "sign/in" in current_url:
            print("❌ Redirection vers login détectée")
            return []
        
        print("✅ Accès au dashboard réussi !")
        
        # 4. Stratégie 1: Scroll infini
        print("\n📜 STRATÉGIE 1: Scroll infini")
        print("-" * 40)
        await scroll_to_load_all_apartments(scraper.page)
        
        # 5. Stratégie 2: Bouton "Voir plus"
        print("\n🔘 STRATÉGIE 2: Bouton 'Voir plus'")
        print("-" * 40)
        await click_load_more_until_done(scraper.page)
        
        # 6. Extraire toutes les URLs de la page actuelle
        print("\n🔍 EXTRACTION DES URLs")
        print("-" * 40)
        all_urls = await extract_urls_from_page(scraper.page)
        print(f"✅ {len(all_urls)} URLs trouvées sur la page actuelle")
        
        # 7. Stratégie 3: Pagination (test optionnel)
        print("\n📄 STRATÉGIE 3: Pagination par URL (test)")
        print("-" * 40)
        pagination_urls = await extract_urls_from_all_pages(scraper, dashboard_url, max_pages=5)
        
        # Combiner toutes les URLs et dédupliquer
        all_urls.extend(pagination_urls)
        unique_urls = list(set(all_urls))  # Dédupliquer
        
        print(f"\n📊 RÉSULTATS FINAUX")
        print("=" * 60)
        print(f"🏠 Total d'URLs uniques trouvées: {len(unique_urls)}")
        
        if unique_urls:
            # Sauvegarder les URLs
            os.makedirs("data", exist_ok=True)
            urls_file = "data/all_apartment_urls.json"
            
            with open(urls_file, 'w', encoding='utf-8') as f:
                json.dump(unique_urls, f, indent=2, ensure_ascii=False)
            
            print(f"💾 URLs sauvegardées: {urls_file}")
            
            # Afficher les 10 premières URLs
            print(f"\n📋 Premières URLs trouvées:")
            for i, url in enumerate(unique_urls[:10], 1):
                print(f"   {i}. {url}")
            
            if len(unique_urls) > 10:
                print(f"   ... et {len(unique_urls) - 10} autres")
            
            # Prendre un screenshot
            await scraper.page.screenshot(path="data/dashboard_all_urls.png")
            print(f"\n📸 Screenshot: data/dashboard_all_urls.png")
            
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
    import sys
    
    dashboard_url = None
    if len(sys.argv) > 1:
        dashboard_url = sys.argv[1]
    
    urls = await extract_all_apartment_urls(dashboard_url)
    
    if urls:
        print(f"\n🎉 SUCCÈS: {len(urls)} URLs d'appartements récupérées !")
        print(f"📁 Fichier: data/all_apartment_urls.json")
    else:
        print("\n❌ Aucune URL récupérée")


if __name__ == "__main__":
    asyncio.run(main())









