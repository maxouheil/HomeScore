#!/usr/bin/env python3
"""
Scraper SeLoger utilisant l'API reverse engineered
Avec fallback sur scraping HTML si l'API échoue
"""

import asyncio
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from seloger_api_client import SeLogerAPIClient
from api_client_base import PropertyData, BaseAPIClient
from playwright.async_api import async_playwright


class SeLogerScraper:
    """Scraper SeLoger avec support API et fallback HTML"""
    
    def __init__(self, use_api: bool = True, fallback_to_html: bool = True):
        """
        Initialise le scraper
        
        Args:
            use_api: Utiliser l'API si disponible
            fallback_to_html: Utiliser le scraping HTML si l'API échoue
        """
        self.use_api = use_api
        self.fallback_to_html = fallback_to_html
        self.api_client: Optional[SeLogerAPIClient] = None
        self.properties: List[PropertyData] = []
        
    async def setup(self):
        """Initialise les ressources"""
        if self.use_api:
            try:
                self.api_client = SeLogerAPIClient()
                print("✅ Client API SeLoger initialisé")
            except Exception as e:
                print(f"⚠️  Erreur initialisation API: {e}")
                if not self.fallback_to_html:
                    raise
    
    async def search_properties(
        self,
        location: str = "Paris",
        property_type: str = "appartement",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_surface: Optional[int] = None,
        max_surface: Optional[int] = None,
        rooms: Optional[List[int]] = None,
        max_results: int = 100
    ) -> List[PropertyData]:
        """
        Recherche d'annonces
        
        Args:
            location: Localisation
            property_type: Type de bien
            min_price: Prix minimum
            max_price: Prix maximum
            min_surface: Surface minimum
            max_surface: Surface maximum
            rooms: Nombre de pièces
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste de PropertyData
        """
        self.properties = []
        
        # Essayer l'API d'abord
        if self.use_api and self.api_client:
            try:
                print("🔍 Recherche via API...")
                page = 1
                limit = 20
                
                while len(self.properties) < max_results:
                    result = await self.api_client.search_properties(
                        location=location,
                        property_type=property_type,
                        min_price=min_price,
                        max_price=max_price,
                        min_surface=min_surface,
                        max_surface=max_surface,
                        rooms=rooms,
                        page=page,
                        limit=limit
                    )
                    
                    if not result or not result.get('properties'):
                        break
                    
                    # Convertir les résultats en PropertyData
                    from api_client_base import BaseAPIClient
                    base_client = BaseAPIClient()
                    for prop_data in result['properties']:
                        prop = base_client.normalize_property_data(prop_data, 'seloger')
                        self.properties.append(prop)
                    
                    if len(result.get('properties', [])) < limit:
                        break
                    
                    page += 1
                
                print(f"✅ {len(self.properties)} annonces trouvées via API")
                return self.properties
                
            except Exception as e:
                print(f"⚠️  Erreur API: {e}")
                if not self.fallback_to_html:
                    raise
        
        # Fallback sur scraping HTML
        if self.fallback_to_html:
            print("🔍 Recherche via scraping HTML...")
            return await self._search_via_html(
                location=location,
                property_type=property_type,
                min_price=min_price,
                max_price=max_price,
                min_surface=min_surface,
                max_surface=max_surface,
                rooms=rooms,
                max_results=max_results
            )
        
        return []
    
    async def _search_via_html(
        self,
        location: str,
        property_type: str,
        min_price: Optional[int],
        max_price: Optional[int],
        min_surface: Optional[int],
        max_surface: Optional[int],
        rooms: Optional[List[int]],
        max_results: int
    ) -> List[PropertyData]:
        """Scraping HTML (fallback)"""
        print("⚠️  Scraping HTML non implémenté pour SeLoger")
        print("    Utilisez l'API ou implémentez le scraping HTML si nécessaire")
        return []
    
    async def get_property_details(self, property_id: str) -> Optional[PropertyData]:
        """
        Récupère les détails d'une annonce
        
        Args:
            property_id: ID de l'annonce
            
        Returns:
            PropertyData ou None
        """
        if self.use_api and self.api_client:
            try:
                result = await self.api_client.get_property_details(property_id)
                if result:
                    from api_client_base import BaseAPIClient
                    base_client = BaseAPIClient()
                    return base_client.normalize_property_data(result, 'seloger')
            except Exception as e:
                print(f"⚠️  Erreur récupération détails: {e}")
        
        return None
    
    async def cleanup(self):
        """Ferme les ressources"""
        if self.api_client:
            await self.api_client.close()


async def main():
    """Test du scraper"""
    print("🚀 TEST DU SCRAPER SELOGER")
    print("=" * 60)
    
    scraper = SeLogerScraper()
    
    try:
        await scraper.setup()
        
        # Recherche
        properties = await scraper.search_properties(
            location="Paris",
            rooms=[2, 3],
            max_results=10
        )
        
        print(f"\n📊 Résultats: {len(properties)} annonces")
        
        for i, prop in enumerate(properties[:5], 1):
            print(f"\n{i}. {prop.title}")
            print(f"   Prix: {prop.price}€")
            print(f"   Surface: {prop.surface}m²")
            print(f"   Pièces: {prop.rooms}")
            print(f"   URL: {prop.url}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

