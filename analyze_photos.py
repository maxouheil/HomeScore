#!/usr/bin/env python3
"""
Module d'analyse des photos pour l'exposition
Phase 2: Analyse des photos avec OpenAI Vision
"""

import base64
import json
import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class PhotoAnalyzer:
    """Analyseur de photos pour l'exposition"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = "https://api.openai.com/v1"
        
    def analyze_photos_exposition(self, photos_urls: List[str]) -> Dict:
        """Analyse les photos pour déterminer l'exposition"""
        if not photos_urls:
            return {
                'exposition': None,
                'score': 0,
                'tier': 'tier3',
                'justification': 'Aucune photo disponible',
                'photos_analyzed': 0,
                'details': {}
            }
        
        try:
            # Analyser les premières photos (max 3 pour économiser les tokens)
            photos_to_analyze = photos_urls[:3]
            analysis_results = []
            
            for i, photo_url in enumerate(photos_to_analyze):
                print(f"   📸 Analyse photo {i+1}/{len(photos_to_analyze)}: {photo_url[:50]}...")
                result = self._analyze_single_photo(photo_url)
                if result:
                    analysis_results.append(result)
            
            # Agréger les résultats
            return self._aggregate_photo_results(analysis_results)
            
        except Exception as e:
            return {
                'exposition': None,
                'score': 0,
                'tier': 'tier3',
                'justification': f'Erreur analyse photos: {e}',
                'photos_analyzed': 0,
                'details': {}
            }
    
    def _analyze_single_photo(self, photo_url: str) -> Optional[Dict]:
        """Analyse une photo individuelle"""
        try:
            # Télécharger l'image
            response = requests.get(photo_url, timeout=5)
            if response.status_code != 200:
                print(f"   ❌ Erreur téléchargement: {response.status_code}")
                return None
            
            # Encoder en base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            
            # Appel à OpenAI Vision
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4o',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': """Analyse cette photo d'appartement et détermine l'exposition (orientation des fenêtres).

Critères d'analyse:
1. Orientation des fenêtres (Sud, Sud-Ouest, Ouest, Est, Nord, Nord-Est)
2. Luminosité naturelle (très lumineux, lumineux, moyen, faible)
3. Qualité de la vue (dégagée, correcte, limitée, obstruée)
4. Présence d'ombres ou de lumière directe
5. Orientation des pièces par rapport au soleil

Réponds au format JSON:
{
    "exposition": "sud|sud_ouest|ouest|est|nord|nord_est|null",
    "luminosite": "excellent|bon|moyen|faible",
    "vue": "excellent|bon|moyen|faible",
    "confidence": 0.0-1.0,
    "details": "description détaillée de ce que tu vois",
    "indices": ["liste des indices visuels trouvés"]
}"""
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{image_base64}'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 500
            }
            
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"   ❌ Erreur API OpenAI: {response.status_code}")
                return None
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parser le JSON
            try:
                analysis = json.loads(content)
                print(f"   ✅ Photo analysée: {analysis.get('exposition', 'N/A')}")
                return analysis
            except json.JSONDecodeError:
                print(f"   ❌ Erreur parsing JSON: {content[:100]}...")
                return None
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout lors de l'analyse de la photo (limite 15s)")
            return None
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Erreur réseau: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Erreur analyse photo: {e}")
            return None
    
    def _aggregate_photo_results(self, results: List[Dict]) -> Dict:
        """Agrège les résultats de plusieurs photos"""
        if not results:
            return {
                'exposition': None,
                'score': 0,
                'tier': 'tier3',
                'justification': 'Aucune photo analysée avec succès',
                'photos_analyzed': 0,
                'details': {}
            }
        
        # Compter les expositions
        expositions = [r.get('exposition') for r in results if r.get('exposition')]
        luminosites = [r.get('luminosite') for r in results if r.get('luminosite')]
        vues = [r.get('vue') for r in results if r.get('vue')]
        
        # Déterminer l'exposition la plus fréquente
        if expositions:
            exposition_counts = {}
            for expo in expositions:
                exposition_counts[expo] = exposition_counts.get(expo, 0) + 1
            most_common_exposition = max(exposition_counts, key=exposition_counts.get)
        else:
            most_common_exposition = None
        
        # Calculer les scores moyens
        luminosite_scores = {
            'excellent': 10, 'bon': 7, 'moyen': 5, 'faible': 3
        }
        vue_scores = {
            'excellent': 10, 'bon': 7, 'moyen': 5, 'faible': 3
        }
        
        avg_luminosite = sum(luminosite_scores.get(l, 5) for l in luminosites) / len(luminosites) if luminosites else 5
        avg_vue = sum(vue_scores.get(v, 5) for v in vues) / len(vues) if vues else 5
        
        # Score d'exposition
        exposition_scores = {
            'sud': 10, 'sud_ouest': 10, 'ouest': 7, 'est': 7, 'nord': 3, 'nord_est': 3
        }
        exposition_score = exposition_scores.get(most_common_exposition, 0)
        
        # Score total
        total_score = max(exposition_score, avg_luminosite, avg_vue)
        
        # Déterminer le tier
        if total_score >= 10:
            tier = 'tier1'
        elif total_score >= 7:
            tier = 'tier2'
        else:
            tier = 'tier3'
        
        return {
            'exposition': most_common_exposition,
            'score': int(total_score),
            'tier': tier,
            'justification': f'Analyse de {len(results)} photos: {most_common_exposition or "indéterminée"}',
            'photos_analyzed': len(results),
            'details': {
                'exposition_score': exposition_score,
                'luminosite_score': avg_luminosite,
                'vue_score': avg_vue,
                'confidence': sum(r.get('confidence', 0.5) for r in results) / len(results)
            }
        }

def test_photo_analysis():
    """Test de l'analyse de photos"""
    analyzer = PhotoAnalyzer()
    
    # Test avec des URLs d'exemple
    test_photos = [
        "https://example.com/photo1.jpg",
        "https://example.com/photo2.jpg"
    ]
    
    print("📸 TEST D'ANALYSE DE PHOTOS")
    print("=" * 50)
    
    result = analyzer.analyze_photos_exposition(test_photos)
    
    print(f"Exposition: {result['exposition']}")
    print(f"Score: {result['score']}/10")
    print(f"Tier: {result['tier']}")
    print(f"Justification: {result['justification']}")
    print(f"Photos analysées: {result['photos_analyzed']}")

if __name__ == "__main__":
    test_photo_analysis()
