#!/usr/bin/env python3
"""
Scraper en batch pour traiter toutes les annonces d'une alerte Jinka
Optimisé pour traiter 40+ appartements efficacement
"""

import asyncio
import json
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from scrape_jinka import JinkaScraper
from analyze_apartment_style import ApartmentStyleAnalyzer

class BatchScraper:
    """Scraper en batch optimisé"""
    
    def __init__(self, max_concurrent=3, max_apartments=50):
        self.max_concurrent = max_concurrent  # Nombre d'appartements en parallèle
        self.max_apartments = max_apartments  # Limite d'appartements
        self.scraper = JinkaScraper()
        self.style_analyzer = ApartmentStyleAnalyzer()
        self.results = []
        self.errors = []
        
    async def scrape_alert_batch(self, alert_url, pages_to_scrape=5):
        """Scrape toutes les annonces d'une alerte Jinka"""
        print(f"🚀 DÉMARRAGE DU SCRAPING EN BATCH")
        print(f"=" * 60)
        print(f"URL d'alerte: {alert_url}")
        print(f"Pages à scraper: {pages_to_scrape}")
        print(f"Appartements max: {self.max_apartments}")
        print(f"Concurrent: {self.max_concurrent}")
        print()
        
        start_time = time.time()
        
        try:
            # 1. Initialiser le scraper
            await self.scraper.setup()
            
            # 2. Connexion à Jinka
            if not await self.scraper.login():
                print("❌ Échec de la connexion")
                return
            
            # 2. Scraper toutes les pages de l'alerte
            all_apartments = await self.scrape_all_pages(alert_url, pages_to_scrape)
            
            if not all_apartments:
                print("❌ Aucun appartement trouvé")
                return
            
            print(f"✅ {len(all_apartments)} appartements trouvés au total")
            
            # 3. Traiter les appartements en batch
            processed_apartments = await self.process_apartments_batch(all_apartments)
            
            # 4. Sauvegarder les résultats
            await self.save_batch_results(processed_apartments)
            
            # 5. Statistiques finales
            elapsed_time = time.time() - start_time
            self.print_final_stats(processed_apartments, elapsed_time)
            
        except Exception as e:
            print(f"❌ Erreur globale: {e}")
        finally:
            if hasattr(self.scraper, 'browser') and self.scraper.browser:
                await self.scraper.browser.close()
    
    async def scrape_all_pages(self, alert_url, pages_to_scrape):
        """Scrape toutes les pages de l'alerte"""
        print(f"📄 SCRAPING DE TOUTES LES PAGES")
        print("-" * 40)
        
        all_apartments = []
        
        for page in range(1, pages_to_scrape + 1):
            print(f"📄 Page {page}/{pages_to_scrape}")
            
            # Construire l'URL de la page
            if '?' in alert_url:
                page_url = f"{alert_url}&page={page}"
            else:
                page_url = f"{alert_url}?page={page}"
            
            try:
                # Scraper la page
                apartments = await self.scraper.scrape_alert_page(page_url)
                
                if apartments:
                    all_apartments.extend(apartments)
                    print(f"   ✅ {len(apartments)} appartements trouvés sur la page {page}")
                else:
                    print(f"   ⚠️ Aucun appartement sur la page {page}")
                    # Si pas d'appartements, on peut arrêter
                    if page > 1:
                        break
                
                # Limiter le nombre total
                if len(all_apartments) >= self.max_apartments:
                    all_apartments = all_apartments[:self.max_apartments]
                    print(f"   🛑 Limite de {self.max_apartments} appartements atteinte")
                    break
                
                # Pause entre les pages pour éviter la surcharge
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Erreur page {page}: {e}")
                continue
        
        return all_apartments
    
    async def process_apartments_batch(self, apartments):
        """Traite les appartements en batch avec concurrence limitée"""
        print(f"\n🏠 TRAITEMENT EN BATCH DE {len(apartments)} APPARTEMENTS")
        print("-" * 50)
        
        processed = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_single_apartment(apartment_url, index):
            async with semaphore:
                try:
                    print(f"🏠 Appartement {index+1}/{len(apartments)}")
                    
                    # Scraper les détails de l'appartement
                    apartment_data = await self.scraper.scrape_apartment_details(apartment_url)
                    
                    if apartment_data:
                        # Analyser le style avec les photos
                        style_analysis = await self.analyze_apartment_style_async(apartment_data)
                        if style_analysis:
                            apartment_data['style_analysis'] = style_analysis
                        
                        # Sauvegarder l'appartement individuellement
                        await self.scraper.save_apartment(apartment_data)
                        
                        processed.append(apartment_data)
                        print(f"   ✅ Appartement {index+1} traité")
                    else:
                        print(f"   ❌ Échec appartement {index+1}")
                        self.errors.append(f"Appartement {index+1}: {apartment_url}")
                    
                except Exception as e:
                    print(f"   ❌ Erreur appartement {index+1}: {e}")
                    self.errors.append(f"Appartement {index+1}: {e}")
        
        # Traiter tous les appartements avec concurrence limitée
        tasks = [process_single_apartment(url, i) for i, url in enumerate(apartments)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return processed
    
    async def analyze_apartment_style_async(self, apartment_data):
        """Analyse le style de l'appartement de manière asynchrone"""
        try:
            photos = apartment_data.get('photos', [])
            if not photos:
                return None
            
            # Prendre seulement les 3 premières photos pour économiser
            photos_to_analyze = photos[:3]
            
            # Analyser les photos
            analysis = self.style_analyzer.analyze_apartment_photos_from_data(apartment_data)
            return analysis
            
        except Exception as e:
            print(f"   ⚠️ Erreur analyse style: {e}")
            return None
    
    async def save_batch_results(self, apartments):
        """Sauvegarde les résultats du batch"""
        print(f"\n💾 SAUVEGARDE DES RÉSULTATS")
        print("-" * 40)
        
        # Créer le dossier de résultats
        os.makedirs("data/batch_results", exist_ok=True)
        
        # Sauvegarder le résumé
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary = {
            'timestamp': timestamp,
            'total_apartments': len(apartments),
            'successful': len(apartments),
            'errors': len(self.errors),
            'apartments': []
        }
        
        for apt in apartments:
            summary['apartments'].append({
                'id': apt.get('id'),
                'titre': apt.get('titre'),
                'prix': apt.get('prix'),
                'surface': apt.get('surface'),
                'localisation': apt.get('localisation'),
                'style_analysis': apt.get('style_analysis', {}),
                'exposition': apt.get('exposition', {})
            })
        
        # Sauvegarder le résumé
        summary_file = f"data/batch_results/summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Résumé sauvegardé: {summary_file}")
        
        # Sauvegarder les erreurs si il y en a
        if self.errors:
            errors_file = f"data/batch_results/errors_{timestamp}.json"
            with open(errors_file, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, indent=2, ensure_ascii=False)
            print(f"⚠️ Erreurs sauvegardées: {errors_file}")
    
    def print_final_stats(self, apartments, elapsed_time):
        """Affiche les statistiques finales"""
        print(f"\n📊 STATISTIQUES FINALES")
        print("=" * 60)
        print(f"⏱️ Temps total: {elapsed_time:.1f} secondes")
        print(f"🏠 Appartements traités: {len(apartments)}")
        print(f"❌ Erreurs: {len(self.errors)}")
        print(f"⚡ Vitesse: {len(apartments)/elapsed_time:.1f} appartements/seconde")
        
        if apartments:
            # Statistiques des styles
            styles = {}
            cuisines_ouvertes = 0
            luminosites = {}
            
            for apt in apartments:
                style_analysis = apt.get('style_analysis', {})
                if style_analysis:
                    style = style_analysis.get('style', {}).get('type', 'inconnu')
                    styles[style] = styles.get(style, 0) + 1
                    
                    if style_analysis.get('cuisine', {}).get('ouverte', False):
                        cuisines_ouvertes += 1
                    
                    luminosite = style_analysis.get('luminosite', {}).get('type', 'inconnue')
                    luminosites[luminosite] = luminosites.get(luminosite, 0) + 1
            
            print(f"\n📈 ANALYSE DES RÉSULTATS:")
            print(f"   Styles détectés: {styles}")
            print(f"   Cuisines ouvertes: {cuisines_ouvertes}/{len(apartments)} ({cuisines_ouvertes/len(apartments)*100:.1f}%)")
            print(f"   Luminosités: {luminosites}")

async def main():
    """Fonction principale"""
    # URL de ton alerte Jinka (remplace par la tienne)
    alert_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    
    # Configuration du batch scraper
    batch_scraper = BatchScraper(
        max_concurrent=3,  # 3 appartements en parallèle
        max_apartments=50  # Maximum 50 appartements
    )
    
    # Lancer le scraping en batch
    await batch_scraper.scrape_alert_batch(alert_url, pages_to_scrape=10)

if __name__ == "__main__":
    asyncio.run(main())
