#!/usr/bin/env python3
"""
Gestionnaire de cookies pour Jinka - Sauvegarde et réutilisation des cookies de session
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config_jinka import DATA_DIR


class CookieManager:
    """Gestionnaire de cookies pour Jinka"""
    
    def __init__(self):
        self.cookies_dir = DATA_DIR / "cookies"
        self.cookies_file = self.cookies_dir / "jinka_cookies.json"
        self.cookies_dir.mkdir(parents=True, exist_ok=True)
    
    def save_cookies(self, cookies: List[Dict], source: str = "selenium") -> bool:
        """
        Sauvegarde les cookies dans un fichier
        
        Args:
            cookies: Liste de cookies (format Selenium ou requests)
            source: Source des cookies ('selenium' ou 'requests')
            
        Returns:
            True si sauvegarde réussie
        """
        try:
            cookie_data = {
                'cookies': cookies,
                'source': source,
                'saved_at': datetime.now().isoformat(),
                'expires_at': None  # Sera calculé si possible
            }
            
            # Essayer de déterminer la date d'expiration
            if cookies:
                expires = []
                for cookie in cookies:
                    if 'expiry' in cookie:
                        expires.append(cookie['expiry'])
                    elif 'expires' in cookie:
                        expires.append(cookie['expires'])
                
                if expires:
                    max_expiry = max(expires)
                    cookie_data['expires_at'] = datetime.fromtimestamp(max_expiry).isoformat()
            
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 {len(cookies)} cookie(s) sauvegardé(s) dans {self.cookies_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des cookies: {e}")
            return False
    
    def load_cookies(self) -> Optional[List[Dict]]:
        """
        Charge les cookies sauvegardés
        
        Returns:
            Liste de cookies ou None si pas de cookies ou expirés
        """
        if not self.cookies_file.exists():
            return None
        
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            cookies = cookie_data.get('cookies', [])
            expires_at = cookie_data.get('expires_at')
            
            # Vérifier si les cookies sont expirés
            if expires_at:
                try:
                    expiry_date = datetime.fromisoformat(expires_at)
                    if datetime.now() > expiry_date:
                        print("⚠️  Les cookies sauvegardés sont expirés")
                        return None
                except Exception:
                    pass
            
            # Vérifier si les cookies sont trop anciens (plus de 30 jours)
            saved_at = cookie_data.get('saved_at')
            if saved_at:
                try:
                    saved_date = datetime.fromisoformat(saved_at)
                    if datetime.now() - saved_date > timedelta(days=30):
                        print("⚠️  Les cookies sauvegardés sont trop anciens (>30 jours)")
                        return None
                except Exception:
                    pass
            
            print(f"✅ {len(cookies)} cookie(s) chargé(s) depuis {self.cookies_file}")
            return cookies
            
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement des cookies: {e}")
            return None
    
    def cookies_to_requests_format(self, cookies: List[Dict]) -> Dict[str, str]:
        """
        Convertit les cookies Selenium au format requests
        
        Args:
            cookies: Liste de cookies (format Selenium)
            
        Returns:
            Dictionnaire {name: value} pour requests
        """
        cookie_dict = {}
        for cookie in cookies:
            name = cookie.get('name')
            value = cookie.get('value')
            if name and value:
                cookie_dict[name] = value
        return cookie_dict
    
    def add_cookies_to_driver(self, driver, cookies: List[Dict]) -> bool:
        """
        Ajoute les cookies au driver Selenium
        
        Args:
            driver: Instance WebDriver
            cookies: Liste de cookies
            
        Returns:
            True si succès
        """
        try:
            import time
            # Aller sur le domaine d'abord
            driver.get("https://www.jinka.fr")
            time.sleep(1)
            
            # Supprimer les cookies existants
            driver.delete_all_cookies()
            
            # Ajouter les cookies sauvegardés
            for cookie in cookies:
                try:
                    # S'assurer que le cookie a les champs requis
                    if 'name' in cookie and 'value' in cookie:
                        # Supprimer les champs qui peuvent causer des problèmes
                        # Préparer le cookie pour Selenium
                        cookie_to_add = {
                            'name': cookie['name'],
                            'value': cookie['value'],
                        }
                        
                        # Ajouter le domaine si présent (nécessaire pour Selenium)
                        domain = cookie.get('domain', '')
                        if domain:
                            # Selenium nécessite le domaine sans le point initial parfois
                            if domain.startswith('.'):
                                cookie_to_add['domain'] = domain[1:]  # Enlever le point initial
                            else:
                                cookie_to_add['domain'] = domain
                        else:
                            cookie_to_add['domain'] = 'jinka.fr'
                        
                        # Ajouter le path
                        cookie_to_add['path'] = cookie.get('path', '/')
                        
                        # Ajouter expiry seulement si présent et valide
                        if 'expiry' in cookie:
                            expiry = cookie['expiry']
                            if isinstance(expiry, (int, float)) and expiry > 0:
                                cookie_to_add['expiry'] = int(expiry)
                        
                        # Ajouter secure si présent
                        if cookie.get('secure'):
                            cookie_to_add['secure'] = True
                        
                        driver.add_cookie(cookie_to_add)
                except Exception as e:
                    # Ignorer les erreurs pour les cookies individuels
                    continue
            
            print(f"✅ {len(cookies)} cookie(s) ajouté(s) au navigateur")
            return True
            
        except Exception as e:
            print(f"⚠️  Erreur lors de l'ajout des cookies au navigateur: {e}")
            return False
    
    def clear_cookies(self) -> bool:
        """
        Supprime les cookies sauvegardés
        
        Returns:
            True si succès
        """
        try:
            if self.cookies_file.exists():
                self.cookies_file.unlink()
                print("🗑️  Cookies sauvegardés supprimés")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur lors de la suppression des cookies: {e}")
            return False
    
    def has_valid_cookies(self) -> bool:
        """
        Vérifie si des cookies valides sont disponibles
        
        Returns:
            True si des cookies valides existent
        """
        cookies = self.load_cookies()
        return cookies is not None and len(cookies) > 0


def main():
    """Test du gestionnaire de cookies"""
    manager = CookieManager()
    
    print("=" * 80)
    print("🔍 TEST DU GESTIONNAIRE DE COOKIES")
    print("=" * 80)
    print()
    
    # Test de chargement
    cookies = manager.load_cookies()
    if cookies:
        print(f"✅ Cookies trouvés: {len(cookies)}")
        print(f"   Exemples: {[c.get('name') for c in cookies[:5]]}")
    else:
        print("⚠️  Aucun cookie sauvegardé")
        print("   Pour sauvegarder des cookies, utilisez:")
        print("   python save_jinka_cookies.py")


if __name__ == "__main__":
    import time
    main()

