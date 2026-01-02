#!/usr/bin/env python3
"""
Wrapper unifié pour l'analyse visuelle avec support OpenAI et Gemini
Permet de basculer facilement entre les deux providers
"""

import os
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum

load_dotenv()


class Provider(Enum):
    """Fournisseurs d'API disponibles"""
    OPENAI = "openai"
    GEMINI = "gemini"


class VisionAnalyzer:
    """
    Analyseur d'images unifié supportant OpenAI et Gemini
    """
    
    def __init__(self, provider: Union[str, Provider] = Provider.GEMINI, **kwargs):
        """
        Initialise l'analyseur
        
        Args:
            provider: 'openai', 'gemini', ou Provider enum
            **kwargs: Arguments spécifiques au provider
                - Pour Gemini: model='gemini-1.5-flash' ou 'gemini-1.5-pro'
                - Pour OpenAI: model='gpt-4o-mini' ou 'gpt-4o'
        """
        if isinstance(provider, str):
            provider = Provider(provider.lower())
        
        self.provider = provider
        self._analyzer = None
        
        if provider == Provider.GEMINI:
            from gemini_analyzer import GeminiAnalyzer
            model = kwargs.get('model', 'gemini-1.5-flash')
            self._analyzer = GeminiAnalyzer(model=model)
            self.cost_per_image = self._analyzer.cost_per_image
            
        elif provider == Provider.OPENAI:
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY non trouvée dans .env")
                
                self._client = OpenAI(api_key=api_key)
                model = kwargs.get('model', 'gpt-4o-mini')
                self._model = model
                
                # Coûts OpenAI (approximatifs)
                costs = {
                    'gpt-4o-mini': 0.0003,
                    'gpt-4o': 0.005525,
                }
                self.cost_per_image = costs.get(model, 0.0003)
                
            except ImportError:
                raise ImportError(
                    "openai package non installé. "
                    "Installez avec: pip install openai"
                )
        else:
            raise ValueError(f"Provider non supporté: {provider}")
    
    def analyze_image(
        self,
        image_source: Union[str, Path],
        prompt: str,
        return_json: bool = False
    ) -> Union[str, Dict]:
        """
        Analyse une image
        
        Args:
            image_source: URL ou chemin vers l'image
            prompt: Question ou instruction
            return_json: Si True, retourne un JSON
        
        Returns:
            Réponse textuelle ou dictionnaire
        """
        if self.provider == Provider.GEMINI:
            return self._analyzer.analyze_image(
                image_source, prompt, return_json=return_json
            )
        
        elif self.provider == Provider.OPENAI:
            # Charger l'image pour OpenAI
            import base64
            import requests
            
            if isinstance(image_source, (str, Path)):
                path = Path(image_source)
                
                # Si URL
                if str(path).startswith(('http://', 'https://')):
                    image_url = str(path)
                    response = self._client.chat.completions.create(
                        model=self._model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": image_url}
                                    }
                                ]
                            }
                        ],
                        max_tokens=1000
                    )
                    text = response.choices[0].message.content
                    
                # Si fichier local
                else:
                    with open(path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    response = self._client.chat.completions.create(
                        model=self._model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=1000
                    )
                    text = response.choices[0].message.content
            else:
                raise ValueError("Type d'image non supporté pour OpenAI")
            
            # Parser JSON si demandé
            if return_json:
                import json
                text = text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                elif text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw_response": text}
            
            return text
    
    def analyze_multiple_images(
        self,
        image_sources: List[Union[str, Path]],
        prompt: str,
        return_json: bool = False
    ) -> Union[str, Dict]:
        """
        Analyse plusieurs images
        
        Args:
            image_sources: Liste d'images
            prompt: Question ou instruction
            return_json: Si True, retourne un JSON
        
        Returns:
            Réponse textuelle ou dictionnaire
        """
        if self.provider == Provider.GEMINI:
            return self._analyzer.analyze_multiple_images(
                image_sources, prompt, return_json=return_json
            )
        
        elif self.provider == Provider.OPENAI:
            # Pour OpenAI, analyser chaque image séparément
            results = []
            for img in image_sources:
                result = self.analyze_image(img, prompt, return_json=return_json)
                results.append(result)
            
            # Combiner les résultats
            if return_json:
                return {"results": results}
            else:
                return "\n\n".join(str(r) for r in results)
    
    def estimate_cost(self, num_images: int) -> float:
        """Estime le coût pour un nombre d'images"""
        return num_images * self.cost_per_image
    
    def get_provider_info(self) -> Dict:
        """Retourne les informations sur le provider"""
        info = {
            "provider": self.provider.value,
            "cost_per_image": self.cost_per_image,
        }
        
        if self.provider == Provider.GEMINI:
            info["model"] = self._analyzer.model_name
        elif self.provider == Provider.OPENAI:
            info["model"] = self._model
        
        return info


# Fonction de comparaison des coûts
def compare_providers(num_images: int = 1000) -> Dict:
    """
    Compare les coûts entre OpenAI et Gemini
    
    Args:
        num_images: Nombre d'images à comparer
    
    Returns:
        Dictionnaire avec la comparaison
    """
    gemini_flash = VisionAnalyzer(Provider.GEMINI, model='gemini-1.5-flash')
    gemini_pro = VisionAnalyzer(Provider.GEMINI, model='gemini-1.5-pro')
    
    try:
        openai_mini = VisionAnalyzer(Provider.OPENAI, model='gpt-4o-mini')
        openai_available = True
    except:
        openai_available = False
    
    comparison = {
        "num_images": num_images,
        "providers": {
            "gemini_flash": {
                "cost": gemini_flash.estimate_cost(num_images),
                "model": "gemini-1.5-flash",
                "savings_vs_openai": None
            },
            "gemini_pro": {
                "cost": gemini_pro.estimate_cost(num_images),
                "model": "gemini-1.5-pro",
                "savings_vs_openai": None
            }
        }
    }
    
    if openai_available:
        openai_cost = openai_mini.estimate_cost(num_images)
        comparison["providers"]["openai_mini"] = {
            "cost": openai_cost,
            "model": "gpt-4o-mini"
        }
        
        # Calculer les économies
        comparison["providers"]["gemini_flash"]["savings_vs_openai"] = (
            openai_cost - comparison["providers"]["gemini_flash"]["cost"]
        )
        comparison["providers"]["gemini_pro"]["savings_vs_openai"] = (
            openai_cost - comparison["providers"]["gemini_pro"]["cost"]
        )
    
    return comparison


if __name__ == "__main__":
    print("🔍 Test du Vision Analyzer")
    print("=" * 60)
    
    # Comparaison des coûts
    print("\n💰 Comparaison des coûts (pour 1000 images):")
    comp = compare_providers(1000)
    
    for provider_name, info in comp["providers"].items():
        print(f"\n{provider_name}:")
        print(f"  Modèle: {info['model']}")
        print(f"  Coût: ${info['cost']:.4f}")
        if 'savings_vs_openai' in info and info['savings_vs_openai']:
            savings_pct = (info['savings_vs_openai'] / comp['providers']['openai_mini']['cost']) * 100
            print(f"  Économies vs OpenAI: ${info['savings_vs_openai']:.4f} ({savings_pct:.1f}%)")

