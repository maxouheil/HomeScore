#!/usr/bin/env python3
"""
Client API Jinka - Réutilise l'authentification existante et appelle les endpoints API
"""

import asyncio
import json
import os
import aiohttp
from pathlib import Path
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from scrape_jinka import JinkaScraper

load_dotenv()


class JinkaAPIClient:
    """Client pour interagir avec l'API Jinka"""
    
    BASE_URL = "https://api.jinka.fr/apiv2"
    
    def __init__(self):
        """Initialise le client API"""
        self.api_token: Optional[str] = None
        self.cookies: List[Dict[str, Any]] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.scraper: Optional[JinkaScraper] = None
    
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
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Fait une requête HTTP vers l'API"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = self._get_auth_headers()
        
        # Fusionner les headers personnalisés si fournis
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
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
                    print(f"❌ Erreur 401: Non autorisé. Token peut-être expiré.")
                    return None
                elif response.status == 429:
                    print(f"⚠️  Erreur 429: Rate limiting. Attendre avant de réessayer.")
                    return None
                else:
                    text = await response.text()
                    print(f"❌ Erreur {response.status}: {text[:200]}")
                    return None
                    
        except Exception as e:
            print(f"❌ Erreur lors de la requête: {e}")
            return None
    
    async def get_config(self) -> Optional[Dict[str, Any]]:
        """Récupère la configuration de l'API"""
        return await self._make_request('GET', '/config')
    
    async def get_user_authenticated(self) -> Optional[Dict[str, Any]]:
        """Vérifie si l'utilisateur est authentifié"""
        return await self._make_request('GET', '/user/authenticated')
    
    async def get_alert_list(self) -> Optional[List[Dict[str, Any]]]:
        """Récupère la liste des alertes"""
        return await self._make_request('GET', '/alert')
    
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

