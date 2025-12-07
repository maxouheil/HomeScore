#!/usr/bin/env python3
"""
Client API Jinka - Réutilise l'authentification existante et appelle les endpoints API
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
from functools import lru_cache
from dotenv import load_dotenv
from scrape_jinka import JinkaScraper

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


class JinkaAPIClient:
    """Client pour interagir avec l'API Jinka"""
    
    BASE_URL = "https://api.jinka.fr/apiv2"
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
        self.scraper: Optional[JinkaScraper] = None
        self.enable_cache = enable_cache
        
        # Cache pour les données statiques
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        
        # Dernière requête pour éviter le rate limiting
        self._last_request_time: Optional[float] = None
        self._min_request_interval = 0.1  # 100ms entre les requêtes
    
    async def login(self) -> bool:
        """
        Se connecte à Jinka via email code et récupère le token API
        
        Réutilise la logique de login de JinkaScraper pour obtenir le token
        """
        print("🔐 Connexion à Jinka via API...")
        
        try:
            # Utiliser le scraper existant pour le login
            self.scraper = JinkaScraper()
            await self.scraper.setup()
            
            # Se connecter avec la méthode existante
            login_success = await self.scraper.login()
            
            if not login_success:
                print("❌ Échec de la connexion")
                return False
            
            # Récupérer les cookies depuis le navigateur
            browser_cookies = await self.scraper.context.cookies()
            self.cookies = browser_cookies
            
            # Extraire le token API depuis les cookies
            self.api_token = self._extract_api_token(browser_cookies)
            
            if not self.api_token:
                print("❌ Token API non trouvé dans les cookies")
                return False
            
            print(f"✅ Connexion réussie - Token API récupéré")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la connexion: {e}")
            return False
    
    def _extract_api_token(self, cookies: List[Dict[str, Any]]) -> Optional[str]:
        """Extrait le token API depuis les cookies"""
        for cookie in cookies:
            if cookie.get('name') == 'LA_API_TOKEN':
                return cookie.get('value')
        return None
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Génère les headers d'authentification"""
        if not self.api_token:
            raise ValueError("Token API non disponible. Appelez login() d'abord.")
        
        # Construire la string de cookies
        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in self.cookies])
        
        headers = {
            'Cookie': cookie_str,
            'Authorization': f'Bearer {self.api_token}',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Origin': 'https://www.jinka.fr',
            'Referer': 'https://www.jinka.fr/',
            'Accept': 'application/json',
        }
        
        return headers
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        use_cache: bool = False,
        cache_ttl_seconds: int = 3600,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Fait une requête HTTP vers l'API avec retry automatique
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Endpoint API (ex: '/alert')
            use_cache: Utiliser le cache pour cette requête
            cache_ttl_seconds: Durée de vie du cache en secondes
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
                result = await self._make_request_once(method, endpoint, **kwargs)
                
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
    
    async def _make_request_once(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Fait une seule requête HTTP (sans retry)"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
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
    
    async def get_config(self) -> Optional[Dict[str, Any]]:
        """Récupère la configuration de l'API (mis en cache)"""
        return await self._make_request('GET', '/config', use_cache=True, cache_ttl_seconds=3600)
    
    async def get_user_authenticated(self) -> Optional[Dict[str, Any]]:
        """Vérifie si l'utilisateur est authentifié"""
        return await self._make_request('GET', '/user/authenticated')
    
    async def get_alert_list(self) -> Optional[List[Dict[str, Any]]]:
        """Récupère la liste des alertes (mis en cache)"""
        return await self._make_request('GET', '/alert', use_cache=True, cache_ttl_seconds=300)
    
    async def get_alert_dashboard(
        self, 
        alert_token: str, 
        filter_type: str = "all", 
        page: int = 1,
        rrkey: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Récupère le dashboard d'une alerte
        
        Args:
            alert_token: Token de l'alerte (ex: "26c2ec3064303aa68ffa43f7c6518733")
            filter_type: Type de filtre ("all", "seen", "unseen", etc.)
            page: Numéro de page (défaut: 1)
            rrkey: Clé de rafraîchissement (optionnel)
        """
        endpoint = f"/alert/{alert_token}/dashboard"
        params = {
            'filter': filter_type,
            'page': page,
        }
        if rrkey:
            params['rrkey'] = rrkey
        
        return await self._make_request('GET', endpoint, params=params)
    
    async def get_apartment_details(
        self, 
        alert_token: str, 
        apartment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails complets d'un appartement
        
        Args:
            alert_token: Token de l'alerte
            apartment_id: ID de l'appartement (ex: "90931157")
        """
        endpoint = f"/alert/{alert_token}/ad/{apartment_id}"
        return await self._make_request('GET', endpoint)
    
    async def get_contact_info(self, apartment_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations de contact d'un appartement
        
        Args:
            apartment_id: ID de l'appartement
        """
        endpoint = f"/ad/{apartment_id}/contact_info"
        return await self._make_request('GET', endpoint)
    
    async def close(self):
        """Ferme les ressources (session HTTP et navigateur)"""
        if self.session:
            await self.session.close()
            self.session = None
        
        if self.scraper:
            await self.scraper.cleanup()
            self.scraper = None
    
    async def __aenter__(self):
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()


async def main():
    """Test du client API"""
    print("🚀 TEST DU CLIENT API JINKA")
    print("=" * 60)
    
    client = JinkaAPIClient()
    
    try:
        # Se connecter
        if not await client.login():
            print("❌ Échec de la connexion")
            return
        
        # Tester les endpoints
        print("\n📋 Test des endpoints...")
        
        # Config
        config = await client.get_config()
        if config:
            print("✅ Config récupérée")
        
        # User authenticated
        user = await client.get_user_authenticated()
        if user:
            print("✅ User authenticated récupéré")
        
        # Alert list
        alerts = await client.get_alert_list()
        if alerts:
            print(f"✅ Liste des alertes récupérée ({len(alerts)} alertes)")
        
        # Alert dashboard (avec token connu)
        alert_token = "26c2ec3064303aa68ffa43f7c6518733"
        dashboard = await client.get_alert_dashboard(alert_token)
        if dashboard:
            print("✅ Dashboard récupéré")
            if 'ads' in dashboard:
                print(f"   {len(dashboard['ads'])} appartements trouvés")
        
        # Apartment details
        apartment_id = "90931157"
        apartment = await client.get_apartment_details(alert_token, apartment_id)
        if apartment:
            print(f"✅ Détails appartement {apartment_id} récupérés")
            if 'ad' in apartment:
                ad = apartment['ad']
                print(f"   Prix: {ad.get('rent')}€")
                print(f"   Surface: {ad.get('area')}m²")
                print(f"   Pièces: {ad.get('room')}")
        
        # Contact info
        contact = await client.get_contact_info(apartment_id)
        if contact:
            print(f"✅ Contact info récupéré")
            print(f"   Téléphone: {contact.get('phone', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())



