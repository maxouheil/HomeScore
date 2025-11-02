#!/usr/bin/env python3
"""
Module de cache pour les résultats d'API OpenAI
Cache les résultats par hash de l'input (texte ou URL photo) + type d'analyse
"""

import json
import os
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class APICache:
    """Cache pour les résultats d'API OpenAI"""
    
    def __init__(self, cache_file='data/api_cache.json', ttl_days=30):
        """
        Args:
            cache_file: Chemin vers le fichier de cache
            ttl_days: Durée de vie du cache en jours (30 par défaut)
        """
        self.cache_file = cache_file
        self.ttl_days = ttl_days
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Charge le cache depuis le fichier"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # Nettoyer les entrées expirées
                    return self._clean_expired(cache)
            except Exception as e:
                print(f"⚠️ Erreur chargement cache: {e}")
                return {}
        return {}
    
    def _clean_expired(self, cache: Dict) -> Dict:
        """Nettoie les entrées expirées du cache"""
        cleaned = {}
        cutoff_date = datetime.now() - timedelta(days=self.ttl_days)
        
        for key, value in cache.items():
            cached_at_str = value.get('cached_at')
            if cached_at_str:
                try:
                    cached_at = datetime.fromisoformat(cached_at_str)
                    if cached_at > cutoff_date:
                        cleaned[key] = value
                except:
                    # Si erreur parsing date, garder l'entrée
                    cleaned[key] = value
            else:
                # Pas de date, garder l'entrée
                cleaned[key] = value
        
        return cleaned
    
    def _save_cache(self):
        """Sauvegarde le cache dans le fichier"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde cache: {e}")
    
    def _generate_key(self, analysis_type: str, input_data: str) -> str:
        """
        Génère une clé de cache unique
        
        Args:
            analysis_type: Type d'analyse (ex: 'exposition', 'baignoire', 'style', 'cuisine')
            input_data: Données d'entrée (texte ou URL photo)
        
        Returns:
            Clé de cache (hash)
        """
        key_string = f"{analysis_type}:{input_data}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(self, analysis_type: str, input_data: str) -> Optional[Dict]:
        """
        Récupère un résultat depuis le cache
        
        Args:
            analysis_type: Type d'analyse
            input_data: Données d'entrée (texte ou URL photo)
        
        Returns:
            Résultat en cache ou None
        """
        key = self._generate_key(analysis_type, input_data)
        cached_result = self.cache.get(key)
        
        if cached_result:
            # Vérifier si expiré
            cached_at_str = cached_result.get('cached_at')
            if cached_at_str:
                try:
                    cached_at = datetime.fromisoformat(cached_at_str)
                    if cached_at < datetime.now() - timedelta(days=self.ttl_days):
                        # Expiré, supprimer
                        del self.cache[key]
                        self._save_cache()
                        return None
                except:
                    pass
            
            print(f"   💾 Cache hit: {analysis_type} (key: {key[:8]}...)")
            return cached_result.get('result')
        
        return None
    
    def set(self, analysis_type: str, input_data: str, result: Dict):
        """
        Stocke un résultat dans le cache
        
        Args:
            analysis_type: Type d'analyse
            input_data: Données d'entrée (texte ou URL photo)
            result: Résultat à mettre en cache
        """
        key = self._generate_key(analysis_type, input_data)
        self.cache[key] = {
            'result': result,
            'cached_at': datetime.now().isoformat(),
            'analysis_type': analysis_type,
            'input_hash': hashlib.md5(input_data.encode('utf-8')).hexdigest()[:8]
        }
        self._save_cache()
        print(f"   💾 Cache miss: {analysis_type} (key: {key[:8]}...) - sauvegardé")
    
    def clear(self):
        """Vide le cache"""
        self.cache = {}
        self._save_cache()
        print("🗑️ Cache vidé")
    
    def stats(self) -> Dict:
        """Retourne les statistiques du cache"""
        total = len(self.cache)
        by_type = {}
        
        for key, value in self.cache.items():
            analysis_type = value.get('analysis_type', 'unknown')
            by_type[analysis_type] = by_type.get(analysis_type, 0) + 1
        
        return {
            'total_entries': total,
            'by_type': by_type,
            'cache_file': self.cache_file
        }

# Instance globale du cache
_global_cache = None

def get_cache() -> APICache:
    """Retourne l'instance globale du cache"""
    global _global_cache
    if _global_cache is None:
        _global_cache = APICache()
    return _global_cache

