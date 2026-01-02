#!/usr/bin/env python3
"""
Client API pour Jinka - Accès direct à l'API sans authentification
"""

import requests
import time
import json
from typing import Dict, Optional, List
from config_jinka import (
    JINKA_API_BASE_URL,
    JINKA_ALERT_TOKEN,
    API_REQUEST_TIMEOUT,
    API_REQUEST_RETRIES,
    API_REQUEST_DELAY
)
from cookie_manager import CookieManager


class JinkaAPIClient:
    """Client pour interagir avec l'API Jinka"""
    
    def __init__(self):
        self.base_url = JINKA_API_BASE_URL
        self.alert_token = JINKA_ALERT_TOKEN
        self.session = requests.Session()
        self.cookie_manager = CookieManager()
        
        # Charger les cookies sauvegardés si disponibles
        saved_cookies = self.cookie_manager.load_cookies()
        if saved_cookies:
            cookie_dict = self.cookie_manager.cookies_to_requests_format(saved_cookies)
            self.session.cookies.update(cookie_dict)
            
            # Extraire le token JWT depuis les cookies pour le header Authorization
            self.api_token = cookie_dict.get('LA_API_TOKEN') or cookie_dict.get('la_api_token')
        else:
            self.api_token = None
        
        # Configurer les headers avec le token si disponible
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'https://www.jinka.fr',
            'Referer': 'https://www.jinka.fr/',
        }
        
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        
        self.session.headers.update(headers)
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Effectue une requête HTTP avec retry logic
        
        Args:
            endpoint: Endpoint de l'API (relatif à base_url)
            params: Paramètres de la requête
            
        Returns:
            Réponse JSON ou None en cas d'erreur
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(API_REQUEST_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=API_REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                # Délai entre les requêtes pour éviter le rate limiting
                if attempt < API_REQUEST_RETRIES - 1:
                    time.sleep(API_REQUEST_DELAY)
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Erreur lors de la requête (tentative {attempt + 1}/{API_REQUEST_RETRIES}): {e}")
                if attempt < API_REQUEST_RETRIES - 1:
                    time.sleep(API_REQUEST_DELAY * (attempt + 1))
                else:
                    print(f"❌ Échec après {API_REQUEST_RETRIES} tentatives")
                    return None
        
        return None
    
    def get_alert_info(self) -> Optional[Dict]:
        """
        Récupère les informations de l'alerte
        
        Returns:
            Dictionnaire avec les détails de l'alerte
        """
        endpoint = f"alert/{self.alert_token}"
        return self._make_request(endpoint)
    
    def get_alert_results(self, filter_type: str = "all", page: int = 1, rrkey: str = "") -> Optional[Dict]:
        """
        Récupère les résultats de l'alerte (appartements) via l'endpoint dashboard
        
        Args:
            filter_type: Type de filtre ("all", "seen", "unseen", etc.) - défaut: "all"
            page: Numéro de page (défaut: 1)
            rrkey: Clé de pagination pour la page suivante (optionnel)
        
        Returns:
            Dictionnaire avec les appartements dans la clé 'ads' ou None
        """
        # Utiliser l'endpoint dashboard documenté dans JINKA_API_REFERENCE.md
        endpoint = f"alert/{self.alert_token}/dashboard"
        params = {
            'filter': filter_type,
            'page': page,
        }
        if rrkey:
            params['rrkey'] = rrkey
        
        print(f"🔍 Appel de l'endpoint: {endpoint} (filter={filter_type}, page={page})")
        result = self._make_request(endpoint, params=params)
        
        if result:
            # L'endpoint dashboard retourne les appartements dans la clé 'ads'
            if isinstance(result, dict):
                if 'ads' in result and isinstance(result['ads'], list):
                    print(f"✅ {len(result['ads'])} appartement(s) trouvé(s) dans 'ads'")
                    return result
                else:
                    print(f"⚠️  Réponse reçue mais pas de clé 'ads' trouvée. Clés disponibles: {list(result.keys())[:10]}")
            elif isinstance(result, list) and len(result) > 0:
                print(f"✅ Liste de {len(result)} appartement(s) trouvée")
                return result
        
        print("⚠️  Aucun résultat d'appartements retourné")
        return None
    
    def get_apartment_details(self, apartment_id: str) -> Optional[Dict]:
        """
        Récupère les détails d'un appartement spécifique
        
        Args:
            apartment_id: ID de l'appartement
            
        Returns:
            Dictionnaire avec les détails de l'appartement
        """
        endpoints = [
            f"ad/{apartment_id}",
            f"apartment/{apartment_id}",
            f"property/{apartment_id}",
        ]
        
        for endpoint in endpoints:
            result = self._make_request(endpoint)
            if result:
                return result
        
        return None


def main():
    """Test du client API"""
    client = JinkaAPIClient()
    
    print("=" * 80)
    print("🔍 TEST DU CLIENT API JINKA")
    print("=" * 80)
    print()
    
    # Test 1: Récupérer les infos de l'alerte
    print("1️⃣  Récupération des informations de l'alerte...")
    alert_info = client.get_alert_info()
    if alert_info:
        print("✅ Informations de l'alerte récupérées")
        print(f"   ID: {alert_info.get('id')}")
        print(f"   Nom: {alert_info.get('name')}")
        print(f"   Prix min: {alert_info.get('rent_min')}")
        print(f"   Prix max: {alert_info.get('rent_max')}")
        print(f"   Surface min: {alert_info.get('area_min')}")
        print(f"   Surface max: {alert_info.get('area_max')}")
    else:
        print("❌ Impossible de récupérer les informations de l'alerte")
    
    print()
    
    # Test 2: Récupérer les résultats (appartements)
    print("2️⃣  Récupération des appartements...")
    results = client.get_alert_results()
    if results:
        print("✅ Résultats récupérés")
        print(f"   Structure: {list(results.keys())}")
        # Afficher un aperçu
        for key, value in results.items():
            if isinstance(value, list):
                print(f"   {key}: {len(value)} éléments")
            elif isinstance(value, dict):
                print(f"   {key}: dictionnaire avec {len(value)} clés")
    else:
        print("⚠️  Aucun résultat d'appartement trouvé via l'API")
        print("   Il faudra peut-être utiliser le scraping HTML")


if __name__ == "__main__":
    main()

