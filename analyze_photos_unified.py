#!/usr/bin/env python3
"""
Analyse unifiée des photos - UNE SEULE FOIS pour style, cuisine, luminosité, baignoire
"""

import base64
import json
import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from cache_api import get_cache

load_dotenv()

class UnifiedPhotoAnalyzer:
    """Analyseur unifié qui extrait TOUTES les infos d'une photo en UNE SEULE analyse"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = "https://api.openai.com/v1"
        self.cache = get_cache()
    
    def analyze_photo_unified(self, photo_url: str, cache_key_prefix: str = "") -> Optional[Dict]:
        """
        Analyse UNE photo pour extraire TOUT en une seule fois:
        - Style (haussmannien, atypique, moderne)
        - Cuisine (ouverte/fermée)
        - Luminosité (très lumineux, lumineux, moyen, faible)
        - Baignoire (présente/absente)
        
        Args:
            photo_url: URL de la photo
            cache_key_prefix: Préfixe pour la clé de cache
            
        Returns:
            Dict avec toutes les analyses ou None si erreur
        """
        # Vérifier le cache
        cache_key = f"{cache_key_prefix}_unified_{photo_url}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            print(f"      💾 Cache hit: unified analysis")
            return cached_result
        
        try:
            # Télécharger l'image
            response = requests.get(photo_url, timeout=10)
            if response.status_code != 200:
                return None
            
            image_content = response.content
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            # Appel UNIQUE à OpenAI Vision avec prompt unifié
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4o-mini',  # Optimisé pour réduire les coûts
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': """Analyse cette photo d'appartement et extrais TOUTES les informations suivantes en UNE SEULE fois:

## TÂCHES À EFFECTUER :

### 1. STYLE ARCHITECTURAL
Détermine le style de l'appartement:
- "haussmannien" : moulures, parquet ancien, cheminée, hauts plafonds, architecture classique
- "atypique" : loft, conversion, original, unique, espace ouvert
- "moderne" : contemporain, récent, années 60-70, éléments modernes

### 2. CUISINE
Détermine si la cuisine est ouverte ou fermée:
- "ouverte" : cuisine visible depuis le salon, bar, séparation partielle ou ouverte
- "fermée" : cuisine séparée par un mur, porte, espace clos

### 3. LUMINOSITÉ
Évalue la luminosité globale:
- "tres_lumineux" : très clair, beaucoup de lumière naturelle
- "lumineux" : clair, bonne luminosité
- "moyen" : luminosité moyenne
- "faible" : sombre, peu de lumière

### 4. BAIGNOIRE
Détecte la présence d'une baignoire:
- "presente" : baignoire visible dans la photo
- "absente" : pas de baignoire (seulement douche ou pas de salle de bain visible)

## FORMAT DE RÉPONSE (JSON uniquement):
{
    "style": {
        "type": "haussmannien|atypique|moderne|autre",
        "confidence": 0.0-1.0,
        "indices": ["moulures", "parquet", ...]
    },
    "cuisine": {
        "ouverte": true|false,
        "confidence": 0.0-1.0,
        "indices": "description de ce qui est visible"
    },
    "luminosite": {
        "type": "tres_lumineux|lumineux|moyen|faible",
        "score": 0-10,
        "confidence": 0.0-1.0
    },
    "baignoire": {
        "presente": true|false,
        "confidence": 0.0-1.0,
        "is_bathroom": true|false
    }
}

Réponds UNIQUEMENT au format JSON, sans texte avant ou après."""
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{image_base64}'
                                }
                            }
                        ]
                    }
                ]
            }
            
            api_response = requests.post(
                f'{self.openai_base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if api_response.status_code != 200:
                print(f"      ❌ Erreur API: {api_response.status_code}")
                return None
            
            response_data = api_response.json()
            response_text = response_data['choices'][0]['message']['content'].strip()
            
            # Parser le JSON
            try:
                # Nettoyer le texte (enlever markdown si présent)
                if response_text.startswith('```'):
                    lines = response_text.split('\n')
                    response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                
                analysis_result = json.loads(response_text)
                
                # Sauvegarder dans le cache
                self.cache.set(cache_key, analysis_result)
                print(f"      💾 Cache miss: unified analysis - sauvegardé")
                
                return analysis_result
                
            except json.JSONDecodeError as e:
                print(f"      ❌ Erreur parsing JSON: {e}")
                print(f"      Réponse: {response_text[:200]}...")
                return None
                
        except Exception as e:
            print(f"      ❌ Erreur analyse unifiée: {e}")
            return None
    
    def analyze_all_photos_unified(self, photos_urls: List[str], apartment_id: str = "") -> Dict:
        """
        Analyse toutes les photos UNE SEULE FOIS chacune et agrège les résultats
        
        Args:
            photos_urls: Liste des URLs des photos
            apartment_id: ID de l'appartement pour le cache
            
        Returns:
            Dict avec résultats agrégés pour style, cuisine, luminosité, baignoire
        """
        if not photos_urls:
            return {
                'style': {'type': 'autre', 'confidence': 0},
                'cuisine': {'ouverte': False, 'confidence': 0},
                'luminosite': {'type': 'faible', 'score': 0, 'confidence': 0},
                'baignoire': {'presente': False, 'confidence': 0},
                'photos_analyzed': 0
            }
        
        # Analyser les premières photos (max 5 pour optimiser)
        photos_to_analyze = photos_urls[:5]
        print(f"   📸 Analyse unifiée de {len(photos_to_analyze)} photos...")
        
        all_analyses = []
        for i, photo_url in enumerate(photos_to_analyze, 1):
            print(f"      📸 Photo {i}/{len(photos_to_analyze)}...")
            analysis = self.analyze_photo_unified(photo_url, cache_key_prefix=apartment_id)
            if analysis:
                all_analyses.append(analysis)
        
        if not all_analyses:
            return {
                'style': {'type': 'autre', 'confidence': 0},
                'cuisine': {'ouverte': False, 'confidence': 0},
                'luminosite': {'type': 'faible', 'score': 0, 'confidence': 0},
                'baignoire': {'presente': False, 'confidence': 0},
                'photos_analyzed': 0
            }
        
        # Agrégation des résultats
        return self._aggregate_unified_results(all_analyses)
    
    def _aggregate_unified_results(self, analyses: List[Dict]) -> Dict:
        """Agrège les résultats de plusieurs analyses"""
        from collections import Counter
        
        # Style: prendre le plus fréquent avec plus haute confiance
        styles = []
        style_confidences = {}
        for analysis in analyses:
            style_data = analysis.get('style', {})
            style_type = style_data.get('type', 'autre')
            confidence = style_data.get('confidence', 0)
            styles.append(style_type)
            if style_type not in style_confidences or confidence > style_confidences[style_type]:
                style_confidences[style_type] = confidence
        
        style_counter = Counter(styles)
        most_common_style = style_counter.most_common(1)[0][0] if style_counter else 'autre'
        
        # Cuisine: si au moins une photo montre cuisine ouverte → ouverte
        cuisines_ouvertes = []
        cuisine_confidences = []
        for analysis in analyses:
            cuisine_data = analysis.get('cuisine', {})
            if cuisine_data.get('ouverte') is not None:
                cuisines_ouvertes.append(cuisine_data.get('ouverte', False))
                cuisine_confidences.append(cuisine_data.get('confidence', 0))
        
        cuisine_ouverte = any(cuisines_ouvertes) if cuisines_ouvertes else False
        cuisine_confidence = max(cuisine_confidences) if cuisine_confidences else 0
        
        # Luminosité: moyenne des scores
        luminosites = []
        luminosite_scores = []
        for analysis in analyses:
            luminosite_data = analysis.get('luminosite', {})
            if luminosite_data.get('type'):
                luminosites.append(luminosite_data.get('type'))
                luminosite_scores.append(luminosite_data.get('score', 0))
        
        # Prendre la luminosité la plus fréquente
        luminosite_counter = Counter(luminosites)
        most_common_luminosite = luminosite_counter.most_common(1)[0][0] if luminosite_counter else 'faible'
        avg_luminosite_score = sum(luminosite_scores) / len(luminosite_scores) if luminosite_scores else 0
        
        # Baignoire: si au moins une photo montre baignoire → présente
        baignoires_presentes = []
        baignoire_confidences = []
        for analysis in analyses:
            baignoire_data = analysis.get('baignoire', {})
            if baignoire_data.get('presente') is not None and baignoire_data.get('is_bathroom', True):
                baignoires_presentes.append(baignoire_data.get('presente', False))
                baignoire_confidences.append(baignoire_data.get('confidence', 0))
        
        baignoire_presente = any(baignoires_presentes) if baignoires_presentes else False
        baignoire_confidence = max(baignoire_confidences) if baignoire_confidences else 0
        
        return {
            'style': {
                'type': most_common_style,
                'confidence': style_confidences.get(most_common_style, 0),
                'indices': []
            },
            'cuisine': {
                'ouverte': cuisine_ouverte,
                'confidence': cuisine_confidence,
                'detected_photos': [i for i, c in enumerate(cuisines_ouvertes) if c]
            },
            'luminosite': {
                'type': most_common_luminosite,
                'score': avg_luminosite_score,
                'confidence': 0.8 if len(analyses) > 1 else 0.6
            },
            'baignoire': {
                'presente': baignoire_presente,
                'confidence': baignoire_confidence,
                'detected_photos': [i for i, b in enumerate(baignoires_presentes) if b]
            },
            'photos_analyzed': len(analyses)
        }

