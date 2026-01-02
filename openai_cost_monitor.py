#!/usr/bin/env python3
"""
Système de monitoring et protection contre les coûts excessifs OpenAI
Arrête automatiquement les appels si le coût dépasse 5$ par exécution
"""

import os
import json
import time
import threading
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Limite de coût par exécution (en dollars)
COST_LIMIT_PER_RUN = 5.0

# Coûts par modèle (par 1M tokens input/output)
# Source: https://openai.com/pricing (janvier 2025)
MODEL_COSTS = {
    'gpt-4o-mini': {
        'input': 0.15 / 1_000_000,  # $0.15 per 1M input tokens
        'output': 0.60 / 1_000_000,  # $0.60 per 1M output tokens
        'vision_input': 0.15 / 1_000_000,  # Même prix pour vision
    },
    'gpt-4o': {
        'input': 2.50 / 1_000_000,  # $2.50 per 1M input tokens
        'output': 10.00 / 1_000_000,  # $10.00 per 1M output tokens
        'vision_input': 2.50 / 1_000_000,
    },
    'gpt-4-turbo': {
        'input': 10.00 / 1_000_000,
        'output': 30.00 / 1_000_000,
        'vision_input': 10.00 / 1_000_000,
    },
    # Modèles Gemini
    'gemini-1.5-flash': {
        'input': 0.075 / 1_000_000,  # $0.075 per 1M input tokens
        'output': 0.30 / 1_000_000,  # $0.30 per 1M output tokens
        'vision_input': 0.075 / 1_000_000,
    },
    'gemini-1.5-pro': {
        'input': 1.25 / 1_000_000,  # $1.25 per 1M input tokens
        'output': 5.00 / 1_000_000,  # $5.00 per 1M output tokens
        'vision_input': 1.25 / 1_000_000,
    },
}

# Coût estimé par image (approximation)
# GPT-4o-mini vision: ~$0.0001-0.0002 par image selon la résolution
ESTIMATED_COST_PER_IMAGE = 0.00015  # $0.00015 par image (conservateur)

# Coûts Gemini par image (basés sur pricing Google)
GEMINI_COST_PER_IMAGE = {
    'gemini-1.5-flash': 0.000075,  # $0.000075 par image
    'gemini-1.5-pro': 0.001315,    # $0.001315 par image
}


class CostLimitExceeded(Exception):
    """Exception levée quand la limite de coût est dépassée"""
    pass


class OpenAICostMonitor:
    """Monitor des coûts OpenAI avec protection automatique"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.current_cost = 0.0
        self.cost_limit = float(os.getenv('OPENAI_COST_LIMIT', COST_LIMIT_PER_RUN))
        self.session_start_time = datetime.now()
        self.call_count = 0
        self.blocked_calls = 0
        self.cost_history = []
        self._lock = threading.Lock()
        self._initialized = True
        
        # Charger l'historique depuis le fichier
        self._load_history()
    
    def _get_history_file(self) -> Path:
        """Retourne le chemin du fichier d'historique"""
        history_dir = Path('data/cost_history')
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir / 'cost_monitor.json'
    
    def _load_history(self):
        """Charge l'historique des coûts depuis le fichier"""
        history_file = self._get_history_file()
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.cost_history = data.get('history', [])
            except Exception as e:
                print(f"⚠️ Erreur chargement historique coûts: {e}")
                self.cost_history = []
    
    def _save_history(self):
        """Sauvegarde l'historique des coûts"""
        history_file = self._get_history_file()
        try:
            data = {
                'last_update': datetime.now().isoformat(),
                'history': self.cost_history[-100:],  # Garder seulement les 100 dernières entrées
            }
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde historique coûts: {e}")
    
    def estimate_cost(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        num_images: int = 0
    ) -> float:
        """
        Estime le coût d'un appel API
        
        Args:
            model: Modèle utilisé (ex: 'gpt-4o-mini', 'gemini-1.5-flash')
            input_tokens: Nombre de tokens d'entrée
            output_tokens: Nombre de tokens de sortie
            num_images: Nombre d'images (pour vision)
        
        Returns:
            Coût estimé en dollars
        """
        model = model.lower()
        
        # Pour Gemini, utiliser le coût par image directement
        if model.startswith('gemini'):
            if num_images > 0:
                cost_per_image = GEMINI_COST_PER_IMAGE.get(model, GEMINI_COST_PER_IMAGE['gemini-1.5-flash'])
                return num_images * cost_per_image
            # Si pas d'images, utiliser les coûts par token
            costs = MODEL_COSTS.get(model, MODEL_COSTS['gemini-1.5-flash'])
            token_cost = (input_tokens * costs['input']) + (output_tokens * costs['output'])
            return token_cost
        
        # Pour OpenAI, utiliser la méthode classique
        costs = MODEL_COSTS.get(model, MODEL_COSTS['gpt-4o-mini'])
        
        # Coût des tokens
        token_cost = (input_tokens * costs['input']) + (output_tokens * costs['output'])
        
        # Coût des images (si vision)
        image_cost = num_images * ESTIMATED_COST_PER_IMAGE
        
        return token_cost + image_cost
    
    def check_and_record(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        num_images: int = 0,
        actual_cost: Optional[float] = None
    ) -> float:
        """
        Vérifie la limite de coût et enregistre l'appel
        
        Args:
            model: Modèle utilisé
            input_tokens: Tokens d'entrée (si disponibles)
            output_tokens: Tokens de sortie (si disponibles)
            num_images: Nombre d'images analysées
            actual_cost: Coût réel si disponible (sinon estimé)
        
        Returns:
            Coût de cet appel
        
        Raises:
            CostLimitExceeded: Si la limite est dépassée
        """
        with self._lock:
            # Estimer le coût si non fourni
            if actual_cost is None:
                call_cost = self.estimate_cost(model, input_tokens, output_tokens, num_images)
            else:
                call_cost = actual_cost
            
            # Vérifier si on dépasse la limite AVANT l'appel
            if self.current_cost + call_cost > self.cost_limit:
                self.blocked_calls += 1
                error_msg = (
                    f"🚨 LIMITE DE COÛT DÉPASSÉE !\n"
                    f"   Coût actuel: ${self.current_cost:.4f}\n"
                    f"   Coût de cet appel: ${call_cost:.4f}\n"
                    f"   Total serait: ${self.current_cost + call_cost:.4f}\n"
                    f"   Limite: ${self.cost_limit:.2f}\n"
                    f"   Appel BLOQUÉ pour éviter les coûts excessifs."
                )
                print(error_msg)
                raise CostLimitExceeded(error_msg)
            
            # Enregistrer l'appel
            self.current_cost += call_cost
            self.call_count += 1
            
            # Enregistrer dans l'historique
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'model': model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'num_images': num_images,
                'cost': call_cost,
                'cumulative_cost': self.current_cost,
            }
            self.cost_history.append(history_entry)
            
            # Sauvegarder périodiquement (tous les 10 appels)
            if self.call_count % 10 == 0:
                self._save_history()
            
            return call_cost
    
    def get_status(self) -> Dict:
        """Retourne le statut actuel du monitor"""
        with self._lock:
            return {
                'current_cost': self.current_cost,
                'cost_limit': self.cost_limit,
                'remaining_budget': max(0, self.cost_limit - self.current_cost),
                'call_count': self.call_count,
                'blocked_calls': self.blocked_calls,
                'session_start': self.session_start_time.isoformat(),
                'session_duration_seconds': (datetime.now() - self.session_start_time).total_seconds(),
            }
    
    def reset(self):
        """Réinitialise le compteur pour une nouvelle session"""
        with self._lock:
            # Sauvegarder l'historique avant reset
            self._save_history()
            
            # Créer un résumé de la session
            if self.current_cost > 0:
                summary = {
                    'session_end': datetime.now().isoformat(),
                    'total_cost': self.current_cost,
                    'call_count': self.call_count,
                    'blocked_calls': self.blocked_calls,
                    'duration_seconds': (datetime.now() - self.session_start_time).total_seconds(),
                }
                print(f"\n📊 RÉSUMÉ DE SESSION:")
                print(f"   Coût total: ${self.current_cost:.4f}")
                print(f"   Appels effectués: {self.call_count}")
                print(f"   Appels bloqués: {self.blocked_calls}")
                print(f"   Durée: {(datetime.now() - self.session_start_time).total_seconds():.1f}s")
            
            # Reset
            self.current_cost = 0.0
            self.call_count = 0
            self.blocked_calls = 0
            self.session_start_time = datetime.now()
    
    def print_status(self):
        """Affiche le statut actuel"""
        status = self.get_status()
        print(f"\n💰 STATUT COÛTS OPENAI:")
        print(f"   Coût actuel: ${status['current_cost']:.4f} / ${status['cost_limit']:.2f}")
        print(f"   Budget restant: ${status['remaining_budget']:.4f}")
        print(f"   Appels effectués: {status['call_count']}")
        print(f"   Appels bloqués: {status['blocked_calls']}")


# Instance globale
_monitor_instance = None

def get_cost_monitor() -> OpenAICostMonitor:
    """Retourne l'instance globale du monitor"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = OpenAICostMonitor()
    return _monitor_instance


def safe_openai_call(
    api_call_func,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    num_images: int = 0,
    *args,
    **kwargs
):
    """
    Wrapper sécurisé pour les appels OpenAI qui vérifie les limites de coût
    
    Args:
        api_call_func: Fonction qui fait l'appel API (doit retourner un dict avec 'usage' ou 'tokens')
        model: Modèle utilisé
        input_tokens: Estimation des tokens d'entrée (si connu avant l'appel)
        output_tokens: Estimation des tokens de sortie (si connu avant l'appel)
        num_images: Nombre d'images (pour vision)
        *args, **kwargs: Arguments passés à api_call_func
    
    Returns:
        Résultat de l'appel API
    
    Raises:
        CostLimitExceeded: Si la limite est dépassée
    """
    monitor = get_cost_monitor()
    
    # Vérifier et enregistrer AVANT l'appel
    estimated_cost = monitor.estimate_cost(model, input_tokens, output_tokens, num_images)
    monitor.check_and_record(model, input_tokens, output_tokens, num_images)
    
    # Faire l'appel
    try:
        result = api_call_func(*args, **kwargs)
        
        # Si l'appel retourne des informations d'usage, mettre à jour avec le coût réel
        if isinstance(result, dict):
            usage = result.get('usage') or result.get('_usage')
            if usage:
                actual_input = usage.get('prompt_tokens', input_tokens)
                actual_output = usage.get('completion_tokens', output_tokens)
                actual_cost = monitor.estimate_cost(model, actual_input, actual_output, num_images)
                
                # Ajuster le coût si différent de l'estimation
                if actual_cost != estimated_cost:
                    with monitor._lock:
                        monitor.current_cost -= estimated_cost
                        monitor.current_cost += actual_cost
        
        return result
        
    except CostLimitExceeded:
        # Re-raise pour que l'appelant puisse gérer
        raise
    except Exception as e:
        # En cas d'erreur, on ne peut pas récupérer les tokens réels
        # Le coût estimé reste enregistré
        raise


if __name__ == "__main__":
    """Test du système de monitoring"""
    monitor = get_cost_monitor()
    
    print("🧪 TEST SYSTÈME DE MONITORING DES COÛTS")
    print("=" * 60)
    
    # Test 1: Estimation de coût
    print("\n1. Estimation de coût:")
    cost1 = monitor.estimate_cost('gpt-4o-mini', input_tokens=1000, output_tokens=500)
    print(f"   GPT-4o-mini (1000 input, 500 output): ${cost1:.6f}")
    
    cost2 = monitor.estimate_cost('gpt-4o-mini', num_images=3)
    print(f"   GPT-4o-mini Vision (3 images): ${cost2:.6f}")
    
    # Test 2: Enregistrement d'appels
    print("\n2. Enregistrement d'appels:")
    try:
        monitor.check_and_record('gpt-4o-mini', input_tokens=1000, output_tokens=500)
        monitor.print_status()
        
        monitor.check_and_record('gpt-4o-mini', num_images=3)
        monitor.print_status()
        
    except CostLimitExceeded as e:
        print(f"   ✅ Protection activée: {e}")
    
    # Test 3: Test de limite
    print("\n3. Test de limite:")
    monitor.reset()
    monitor.cost_limit = 0.01  # Limite très basse pour test
    
    try:
        # Ces appels devraient passer
        monitor.check_and_record('gpt-4o-mini', input_tokens=1000, output_tokens=500)
        print("   ✅ Premier appel accepté")
        
        # Celui-ci devrait être bloqué
        monitor.check_and_record('gpt-4o-mini', num_images=100)  # Coût élevé
        print("   ❌ Ne devrait pas arriver ici")
        
    except CostLimitExceeded as e:
        print(f"   ✅ Protection activée correctement!")
        print(f"   {str(e)[:200]}...")
    
    monitor.print_status()
    print("\n✅ Tests terminés")

