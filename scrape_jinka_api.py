#!/usr/bin/env python3
"""
Scraper Jinka utilisant l'API au lieu du scraping HTML
Plus rapide, plus stable et moins fragile aux changements CSS
"""

import asyncio
import json
import re
import os
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from jinka_api_client import JinkaAPIClient
from api_data_adapter import adapt_api_to_scraped_format, adapt_dashboard_to_apartment_list
from extract_exposition import ExpositionExtractor
from analyze_apartment_style import ApartmentStyleAnalyzer
from extract_baignoire import BaignoireExtractor


class JinkaAPIScraper:
    """
    Scraper utilisant l'API Jinka au lieu du scraping HTML
    
    Avantages:
    - Plus rapide (pas de rendu HTML)
    - Plus stable (moins fragile aux changements CSS)
    - Moins de ressources (pas de navigateur)
    - Plus facile à déboguer
    """
    
    def __init__(self):
        """Initialise le scraper API"""
        self.api_client: Optional[JinkaAPIClient] = None
        self.apartments: List[Dict[str, Any]] = []
        self.exposition_extractor = ExpositionExtractor()
        self.style_analyzer = ApartmentStyleAnalyzer()
        self.baignoire_extractor = BaignoireExtractor()
        self.alert_token: Optional[str] = None
    
    async def setup(self):
        """Initialise le client API"""
        print("🔧 Initialisation du client API...")
        self.api_client = JinkaAPIClient(enable_cache=True)
        print("✅ Client API initialisé")
    
    async def login(self) -> bool:
        """
        Se connecte à Jinka via email code et récupère le token API
        
        Réutilise la logique de login du scraper HTML pour obtenir le token
        """
        if not self.api_client:
            await self.setup()
        
        print("🔐 Connexion à Jinka via API...")
        success = await self.api_client.login()
        
        if success:
            print("✅ Connexion réussie")
        else:
            print("❌ Échec de la connexion")
        
        return success
    
    def _extract_alert_token_from_url(self, alert_url: str) -> Optional[str]:
        """
        Extrait le token d'alerte depuis l'URL
        
        Args:
            alert_url: URL de l'alerte (ex: "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733")
        
        Returns:
            Token d'alerte ou None
        """
        # Pattern 1: /alert/dashboard/{token}
        match = re.search(r'/alert/dashboard/([a-f0-9]{32})', alert_url)
        if match:
            return match.group(1)
        
        # Pattern 2: ?token={token}
        parsed = urlparse(alert_url)
        params = parse_qs(parsed.query)
        if 'token' in params:
            token = params['token'][0]
            if len(token) == 32:  # Token Jinka fait 32 caractères hex
                return token
        
        return None
    
    async def scrape_alert_page(
        self, 
        alert_url: str, 
        filter_type: str = "all",
        max_pages: int = 50  # Augmenté par défaut pour récupérer toutes les pages
    ) -> List[Dict[str, Any]]:
        """
        Scrape toutes les pages d'une alerte via l'API
        
        Args:
            alert_url: URL de l'alerte
            filter_type: Type de filtre ("all", "seen", "unseen", etc.)
            max_pages: Nombre maximum de pages à scraper
        
        Returns:
            Liste des appartements trouvés
        """
        if not self.api_client:
            raise RuntimeError("Client API non initialisé. Appelez setup() d'abord.")
        
        print(f"\n🏠 SCRAPING DE L'ALERTE VIA API")
        print("=" * 60)
        print(f"URL: {alert_url}")
        
        # Extraire le token d'alerte
        self.alert_token = self._extract_alert_token_from_url(alert_url)
        if not self.alert_token:
            print("❌ Impossible d'extraire le token d'alerte depuis l'URL")
            return []
        
        print(f"✅ Token d'alerte: {self.alert_token}")
        
        all_apartments = []
        page = 1
        has_more = True
        
        while has_more and page <= max_pages:
            print(f"\n📄 Page {page}/{max_pages}...")
            
            # Récupérer le dashboard de la page
            dashboard_data = await self.api_client.get_alert_dashboard(
                alert_token=self.alert_token,
                filter_type=filter_type,
                page=page
            )
            
            if not dashboard_data:
                print(f"⚠️  Aucune donnée pour la page {page}")
                break
            
            # Extraire les appartements de cette page
            page_apartments = adapt_dashboard_to_apartment_list(dashboard_data)
            
            if not page_apartments:
                print(f"✅ Fin des résultats (page {page})")
                has_more = False
                break
            
            print(f"   {len(page_apartments)} appartements trouvés sur cette page")
            
            # Vérifier la pagination dans la réponse API
            pagination_info = dashboard_data.get('pagination', {})
            if pagination_info:
                total = pagination_info.get('total', 0)
                current_page = pagination_info.get('page', page)
                per_page = pagination_info.get('per_page', len(page_apartments))
                has_more_pages = pagination_info.get('has_more', None)
                
                if total > 0:
                    print(f"   📊 Total: {total} appartements | Page {current_page} | {per_page} par page")
                
                # Si has_more est explicitement False, on arrête
                if has_more_pages is False:
                    has_more = False
            
            # Scraper les détails de chaque appartement
            for apt_info in page_apartments:
                apartment_id = apt_info['id']
                apartment_data = await self.scrape_apartment(apt_info['url'])
                
                if apartment_data:
                    all_apartments.append(apartment_data)
                    print(f"   ✅ {apartment_id}: {apartment_data.get('titre', 'N/A')[:50]}")
                else:
                    print(f"   ⚠️  {apartment_id}: Échec du scraping")
            
            # Si on n'a pas d'info de pagination explicite, on continue tant qu'on a des résultats
            # et qu'on n'a pas atteint max_pages
            if len(page_apartments) == 0:
                has_more = False
            
            page += 1
        
        self.apartments = all_apartments
        print(f"\n✅ Scraping terminé: {len(all_apartments)} appartements au total")
        
        return all_apartments
    
    async def scrape_apartment(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape les détails d'un appartement via l'API
        
        Args:
            url: URL de l'appartement (ex: "https://www.jinka.fr/alert_result?token=...&ad=90931157")
        
        Returns:
            Données de l'appartement au format scraping ou None
        """
        if not self.api_client:
            raise RuntimeError("Client API non initialisé. Appelez setup() d'abord.")
        
        # Extraire l'ID de l'appartement depuis l'URL
        apartment_id = self._extract_apartment_id_from_url(url)
        if not apartment_id:
            print(f"❌ Impossible d'extraire l'ID depuis l'URL: {url}")
            return None
        
        # Si on n'a pas le token d'alerte, essayer de l'extraire de l'URL
        if not self.alert_token:
            self.alert_token = self._extract_alert_token_from_url(url)
        
        if not self.alert_token:
            print(f"❌ Token d'alerte manquant pour l'appartement {apartment_id}")
            return None
        
        # Récupérer les détails via l'API
        api_data = await self.api_client.get_apartment_details(
            alert_token=self.alert_token,
            apartment_id=apartment_id
        )
        
        if not api_data:
            print(f"❌ Aucune donnée API pour l'appartement {apartment_id}")
            return None
        
        # Ajouter le token d'alerte aux données si pas déjà présent
        if self.alert_token and 'token' not in api_data:
            api_data['token'] = self.alert_token
        
        # Adapter les données API vers le format scraping
        try:
            apartment_data = adapt_api_to_scraped_format(api_data, alert_token=self.alert_token)
            
            # Ajouter l'extraction d'exposition si nécessaire
            # (l'API peut déjà fournir certaines données d'exposition)
            if 'description' in apartment_data:
                # L'extraction d'exposition peut être faite ici si nécessaire
                pass
            
            # Analyser le style et la cuisine depuis les photos (DÉSACTIVÉ pour scraping rapide)
            # L'analyse IA sera faite plus tard avec batch_analyze_paris.py
            # try:
            #     style_analysis = self.style_analyzer.analyze_apartment_photos_from_data(apartment_data)
            #     if style_analysis:
            #         apartment_data['style_analysis'] = style_analysis
            # except Exception as e:
            #     print(f"   ⚠️ Erreur analyse style/cuisine: {e}")
            
            # Analyser la baignoire (DÉSACTIVÉ pour scraping rapide)
            # try:
            #     baignoire_data = self.baignoire_extractor.extract_baignoire_ultimate(apartment_data)
            #     if baignoire_data:
            #         apartment_data['baignoire'] = baignoire_data
            # except Exception as e:
            #     print(f"   ⚠️ Erreur analyse baignoire: {e}")
            
            return apartment_data
            
        except Exception as e:
            print(f"❌ Erreur lors de l'adaptation des données: {e}")
            return None
    
    def _extract_apartment_id_from_url(self, url: str) -> Optional[str]:
        """
        Extrait l'ID de l'appartement depuis l'URL
        
        Args:
            url: URL de l'appartement
        
        Returns:
            ID de l'appartement ou None
        """
        # Pattern 1: ?ad=12345678
        match = re.search(r'[?&]ad=(\d+)', url)
        if match:
            return match.group(1)
        
        # Pattern 2: /ad/12345678
        match = re.search(r'/ad/(\d+)', url)
        if match:
            return match.group(1)
        
        return None
    
    async def scrape_apartment_details(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Alias pour scrape_apartment (compatibilité avec l'ancien scraper)
        """
        return await self.scrape_apartment(url)
    
    async def cleanup(self):
        """Ferme les ressources"""
        if self.api_client:
            await self.api_client.close()
            self.api_client = None
        print("✅ Nettoyage terminé")
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.cleanup()


async def main():
    """Test du scraper API"""
    print("🚀 TEST DU SCRAPER API JINKA")
    print("=" * 60)
    
    scraper = JinkaAPIScraper()
    
    try:
        await scraper.setup()
        
        # Se connecter
        if not await scraper.login():
            print("❌ Échec de la connexion")
            return
        
        # Tester le scraping d'une alerte
        alert_url = "https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733"
        apartments = await scraper.scrape_alert_page(alert_url, max_pages=1)
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   {len(apartments)} appartements scrapés")
        
        if apartments:
            print(f"\n📋 Premier appartement:")
            apt = apartments[0]
            print(f"   ID: {apt.get('id')}")
            print(f"   Titre: {apt.get('titre')}")
            print(f"   Prix: {apt.get('prix')}")
            print(f"   Surface: {apt.get('surface')}")
            print(f"   Localisation: {apt.get('localisation')}")
            print(f"   Photos: {len(apt.get('photos', []))} photos")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

