#!/usr/bin/env python3
"""
Classe de base pour les clients API immobiliers
Définit l'interface commune pour tous les clients API
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from datetime import datetime


class PropertyData:
    """Structure de données standardisée pour une propriété"""
    
    def __init__(self, source: str, property_id: str, **kwargs):
        self.source = source  # 'jinka', 'seloger', 'leboncoin'
        self.property_id = property_id
        self.title = kwargs.get('title', '')
        self.description = kwargs.get('description', '')
        self.price = kwargs.get('price', 0)
        self.surface = kwargs.get('surface', 0)
        self.rooms = kwargs.get('rooms', 0)
        self.location = kwargs.get('location', {})
        self.photos = kwargs.get('photos', [])
        self.url = kwargs.get('url', '')
        self.raw_data = kwargs.get('raw_data', {})
        self.scraped_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'source': self.source,
            'property_id': self.property_id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'surface': self.surface,
            'rooms': self.rooms,
            'location': self.location,
            'photos': self.photos,
            'url': self.url,
            'scraped_at': self.scraped_at.isoformat(),
            'raw_data': self.raw_data,
        }


class BaseAPIClient(ABC):
    """Classe de base abstraite pour tous les clients API immobiliers"""
    
    @abstractmethod
    async def search_properties(
        self,
        location: str,
        property_type: str = "appartement",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_surface: Optional[int] = None,
        max_surface: Optional[int] = None,
        rooms: Optional[List[int]] = None,
        page: int = 1,
        limit: int = 20
    ) -> List[PropertyData]:
        """
        Recherche d'annonces immobilières
        
        Returns:
            Liste de PropertyData standardisées
        """
        pass
    
    @abstractmethod
    async def get_property_details(self, property_id: str) -> Optional[PropertyData]:
        """
        Récupère les détails complets d'une annonce
        
        Args:
            property_id: ID de l'annonce
            
        Returns:
            PropertyData standardisée ou None
        """
        pass
    
    @abstractmethod
    async def get_property_photos(self, property_id: str) -> List[str]:
        """
        Récupère les URLs des photos d'une annonce
        
        Args:
            property_id: ID de l'annonce
            
        Returns:
            Liste d'URLs de photos
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Ferme les ressources (sessions, connexions, etc.)"""
        pass
    
    def normalize_property_data(self, raw_data: Dict[str, Any], source: str) -> PropertyData:
        """
        Normalise les données brutes d'une propriété selon la source
        
        Args:
            raw_data: Données brutes de l'API
            source: Source des données ('jinka', 'seloger', 'leboncoin')
            
        Returns:
            PropertyData standardisée
        """
        # Extraction générique basée sur les patterns communs
        property_id = str(raw_data.get('id') or raw_data.get('property_id') or raw_data.get('ad_id', ''))
        
        # Extraction du prix (peut être dans différents formats)
        price = 0
        if 'price' in raw_data:
            price = raw_data['price']
        elif 'rent' in raw_data:
            price = raw_data['rent']
        elif 'prix' in raw_data:
            price = raw_data['prix']
        
        # Extraction de la surface
        surface = raw_data.get('surface') or raw_data.get('area') or raw_data.get('surface_m2', 0)
        
        # Extraction du nombre de pièces
        rooms = raw_data.get('rooms') or raw_data.get('room') or raw_data.get('pieces', 0)
        
        # Extraction de la localisation
        location = {}
        if 'location' in raw_data:
            location = raw_data['location']
        elif 'address' in raw_data:
            location = {'address': raw_data['address']}
        elif 'city' in raw_data:
            location = {'city': raw_data['city']}
        
        # Extraction des photos
        photos = []
        if 'photos' in raw_data:
            photos = raw_data['photos']
        elif 'images' in raw_data:
            photos = raw_data['images']
        elif 'pictures' in raw_data:
            photos = raw_data['pictures']
        
        # Extraction de l'URL
        url = raw_data.get('url') or raw_data.get('link') or ''
        
        return PropertyData(
            source=source,
            property_id=property_id,
            title=raw_data.get('title') or raw_data.get('titre') or '',
            description=raw_data.get('description') or raw_data.get('desc') or '',
            price=price,
            surface=surface,
            rooms=rooms,
            location=location,
            photos=photos,
            url=url,
            raw_data=raw_data,
        )


class APIClientFactory:
    """Factory pour créer les clients API appropriés"""
    
    @staticmethod
    def create_client(source: str, **kwargs):
        """
        Crée un client API selon la source
        
        Args:
            source: 'jinka', 'seloger', ou 'leboncoin'
            **kwargs: Arguments supplémentaires pour le client
            
        Returns:
            Instance du client API approprié
        """
        if source.lower() == 'jinka':
            from jinka_api_client import JinkaAPIClient
            return JinkaAPIClient(**kwargs)
        elif source.lower() == 'seloger':
            from seloger_api_client import SeLogerAPIClient
            return SeLogerAPIClient(**kwargs)
        elif source.lower() == 'leboncoin':
            from leboncoin_api_client import LeBonCoinAPIClient
            return LeBonCoinAPIClient(**kwargs)
        else:
            raise ValueError(f"Source inconnue: {source}")


async def main():
    """Test de la factory"""
    print("🚀 TEST DE LA FACTORY DE CLIENTS API")
    print("=" * 60)
    
    # Test création des clients
    try:
        jinka_client = APIClientFactory.create_client('jinka')
        print("✅ Client Jinka créé")
        await jinka_client.close()
    except Exception as e:
        print(f"⚠️  Erreur création client Jinka: {e}")
    
    try:
        seloger_client = APIClientFactory.create_client('seloger')
        print("✅ Client SeLoger créé")
        await seloger_client.close()
    except Exception as e:
        print(f"⚠️  Erreur création client SeLoger: {e}")
    
    try:
        leboncoin_client = APIClientFactory.create_client('leboncoin')
        print("✅ Client LeBonCoin créé")
        await leboncoin_client.close()
    except Exception as e:
        print(f"⚠️  Erreur création client LeBonCoin: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



