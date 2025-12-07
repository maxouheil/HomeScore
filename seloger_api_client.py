#!/usr/bin/env python3
"""
Client API SeLoger - Reverse engineered API client
Avec retry automatique, rate limiting et cache
"""

import asyncio
import json
import os
import time
import aiohttp
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Exceptions personnalisées
class APIError(Exception):
    """Erreur générique de l'API"""
    pass

class AuthenticationError(APIError):
    """Erreur d'authentification"""
    pass

class RateLimitError(APIError):
    """Erreur de rate limiting"""
    pass

class NetworkError(APIError):
    """Erreur réseau"""
    pass


class SeLogerAPIClient:
    """Client pour interagir avec l'API SeLoger"""
    
    BASE_URL = "https://www.seloger.com"  # À adapter selon les endpoints découverts
    API_BASE_URL = "https://api.seloger.com"  # À adapter selon les endpoints découverts
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 1  # secondes
    RATE_LIMIT_DELAY = 60  # secondes en cas de 429
    
    def __init__(self, enable_cache: bool = True):
        """
        Initialise le client API
        
        Args:
            enable_cache: Active le cache des données statiques
        """
        self.api_token: Optional[str] = None
        self.cookies: List[Dict[str, Any]] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.enable_cache = enable_cache
        
        # Cache pour les données statiques
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        
        # Dernière requête pour éviter le rate limiting
        self._last_request_time: Optional[float] = None
        self._min_request_interval = 0.2  # 200ms entre les requêtes (plus conservateur)
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Génère les headers d'authentification"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9',
            'Origin': 'https://www.seloger.com',
            'Referer': 'https://www.seloger.com/',
        }
        
        # Ajouter les cookies si disponibles
        if self.cookies:
            cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in self.cookies])
            headers['Cookie'] = cookie_str
        
        # Ajouter le token si disponible
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        
        return headers
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        use_cache: bool = False,
        cache_ttl_seconds: int = 3600,
        base_url: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Fait une requête HTTP vers l'API avec retry automatique
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Endpoint API (ex: '/api/search')
            use_cache: Utiliser le cache pour cette requête
            cache_ttl_seconds: Durée de vie du cache en secondes
            base_url: URL de base (par défaut API_BASE_URL)
            **kwargs: Arguments supplémentaires pour aiohttp.request
        """
        # Vérifier le cache si activé
        cache_key = f"{method}:{endpoint}:{str(kwargs.get('params', {}))}"
        if use_cache and self.enable_cache and cache_key in self._cache:
            cache_expiry = self._cache_ttl.get(cache_key)
            if cache_expiry and datetime.now() < cache_expiry:
                return self._cache[cache_key]
        
        # Respecter l'intervalle minimum entre requêtes
        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - elapsed)
        
        # Retry avec backoff exponentiel
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self._make_request_once(method, endpoint, base_url=base_url, **kwargs)
                
                # Si succès, mettre en cache si demandé
                if result and use_cache and self.enable_cache:
                    self._cache[cache_key] = result
                    self._cache_ttl[cache_key] = datetime.now() + timedelta(seconds=cache_ttl_seconds)
                
                return result
                
            except RateLimitError:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RATE_LIMIT_DELAY * (2 ** attempt)
                    print(f"⏳ Rate limit atteint, attente de {wait_time}s avant retry...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Rate limit après {self.MAX_RETRIES} tentatives")
                    return None
                    
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAY_BASE * (2 ** attempt)
                    print(f"⚠️  Erreur (tentative {attempt + 1}/{self.MAX_RETRIES}): {e}")
                    print(f"   Retry dans {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Échec après {self.MAX_RETRIES} tentatives: {e}")
                    return None
        
        return None
    
    async def _make_request_once(
        self, 
        method: str, 
        endpoint: str, 
        base_url: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fait une seule requête HTTP (sans retry)"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        base = base_url or self.API_BASE_URL
        url = f"{base}/{endpoint.lstrip('/')}"
        headers = self._get_auth_headers()
        
        # Fusionner les headers personnalisés si fournis
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        self._last_request_time = time.time()
        
        try:
            async with self.session.request(method, url, headers=headers, **kwargs) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        text = await response.text()
                        print(f"⚠️  Réponse non-JSON: {content_type}")
                        return {'text': text}
                elif response.status == 401:
                    raise AuthenticationError("Token expiré ou invalide")
                elif response.status == 429:
                    raise RateLimitError("Rate limit atteint")
                else:
                    text = await response.text()
                    raise APIError(f"Erreur {response.status}: {text[:200]}")
                    
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise NetworkError(f"Erreur réseau: {e}")
    
    def clear_cache(self):
        """Vide le cache"""
        self._cache.clear()
        self._cache_ttl.clear()
        print("🗑️  Cache vidé")
    
    async def search_properties(
        self,
        location: str = "Paris",
        property_type: str = "appartement",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_surface: Optional[int] = None,
        max_surface: Optional[int] = None,
        rooms: Optional[List[int]] = None,
        page: int = 1,
        limit: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Recherche d'annonces immobilières
        
        Args:
            location: Localisation (ex: "Paris")
            property_type: Type de bien (ex: "appartement", "maison")
            min_price: Prix minimum
            max_price: Prix maximum
            min_surface: Surface minimum (m²)
            max_surface: Surface maximum (m²)
            rooms: Nombre de pièces (ex: [2, 3, 4])
            page: Numéro de page
            limit: Nombre de résultats par page
        """
        # À adapter selon les endpoints découverts lors de l'exploration
        endpoint = "/api/search"  # À adapter
        params = {
            'location': location,
            'type': property_type,
            'page': page,
            'limit': limit,
        }
        
        if min_price:
            params['min_price'] = min_price
        if max_price:
            params['max_price'] = max_price
        if min_surface:
            params['min_surface'] = min_surface
        if max_surface:
            params['max_surface'] = max_surface
        if rooms:
            params['rooms'] = ','.join(map(str, rooms))
        
        return await self._make_request('GET', endpoint, params=params)
    
    async def get_property_details(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails complets d'une annonce
        
        Args:
            property_id: ID de l'annonce
        """
        # À adapter selon les endpoints découverts lors de l'exploration
        endpoint = f"/api/properties/{property_id}"  # À adapter
        return await self._make_request('GET', endpoint)
    
    async def get_property_photos(self, property_id: str) -> Optional[List[str]]:
        """
        Récupère les photos d'une annonce
        
        Args:
            property_id: ID de l'annonce
        """
        # À adapter selon les endpoints découverts lors de l'exploration
        endpoint = f"/api/properties/{property_id}/photos"  # À adapter
        result = await self._make_request('GET', endpoint)
        if result and 'photos' in result:
            return result['photos']
        return []
    
    async def close(self):
        """Ferme les ressources"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def __aenter__(self):
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()


async def main():
    """Test du client API"""
    print("🚀 TEST DU CLIENT API SELOGER")
    print("=" * 60)
    print("⚠️  Ce client nécessite l'exploration préalable des endpoints")
    print("    Exécutez explore_seloger_api.py d'abord")
    print("=" * 60)
    
    client = SeLogerAPIClient()
    
    try:
        # Tester la recherche (nécessite les endpoints découverts)
        print("\n📋 Test de recherche...")
        results = await client.search_properties(location="Paris", rooms=[2, 3])
        
        if results:
            print("✅ Recherche réussie")
            print(f"   Résultats: {len(results.get('properties', []))}")
        else:
            print("⚠️  Aucun résultat ou endpoints non configurés")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())



