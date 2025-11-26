#!/usr/bin/env python3
"""
Analyse unifiée d'appartement avec GPT-4o-mini Vision
Analyse style, cuisine, salle de bain, luminosité en UNE SEULE requête
"""

import json
import os
import base64
import requests
from typing import Dict, List, Optional
from pathlib import Path
from photo_manager import PhotoManager
from cache_api import get_cache
from dotenv import load_dotenv

load_dotenv()


class UnifiedApartmentAnalyzer:
    """Analyseur unifié qui analyse tout en une seule requête"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o-mini"  # GPT mini pour économiser
        self.photo_manager = PhotoManager()
        self.cache = get_cache()
    
    def _get_cache_input_data(self, apartment_id: str, photos: List[Dict]) -> str:
        """Génère les données d'entrée pour le cache basées sur l'ID et les URLs des photos"""
        photo_urls = [p.get('url', '') for p in photos[:3]]  # Optimisé: 3 photos au lieu de 5
        return f"{apartment_id}:{':'.join(photo_urls)}"
    
    def _load_photos_for_analysis(self, photos: List[Dict], max_photos: int = 3) -> List[bytes]:
        """
        Charge les photos depuis les chemins locaux ou URLs
        
        Args:
            photos: Liste des photos avec local_path ou url
            max_photos: Nombre maximum de photos à analyser
        
        Returns:
            Liste des contenus binaires des images
        """
        image_contents = []
        
        for photo in photos[:max_photos]:
            # Charger depuis le chemin local si disponible, sinon depuis l'URL
            local_path = photo.get('local_path')
            if local_path and os.path.exists(local_path):
                try:
                    with open(local_path, 'rb') as f:
                        image_contents.append(f.read())
                except Exception as e:
                    print(f"   ⚠️  Erreur chargement {local_path}: {e}")
                    continue
            else:
                # Télécharger depuis l'URL
                photo_url = photo.get('url', '')
                if photo_url:
                    try:
                        response = requests.get(photo_url, timeout=10)
                        if response.status_code == 200:
                            image_contents.append(response.content)
                    except Exception as e:
                        print(f"   ⚠️  Erreur téléchargement {photo_url[:50]}...: {e}")
                        continue
        
        return image_contents
    
    def analyze_apartment_unified(
        self, 
        apartment_data: Dict,
        max_photos: int = 3  # Optimisé: 3 photos par défaut (au lieu de 5)
    ) -> Optional[Dict]:
        """
        Analyse un appartement en UNE SEULE requête GPT-4o-mini Vision
        
        Analyse simultanément :
        - Style (haussmannien, moderne, atypique, etc.)
        - Cuisine (ouverte/fermée)
        - Salle de bain (baignoire/douche)
        - Luminosité
        
        Args:
            apartment_data: Données de l'appartement
            max_photos: Nombre maximum de photos à analyser (défaut: 3 pour optimiser les coûts)
        
        Returns:
            Résultat unifié de l'analyse
        """
        apartment_id = apartment_data.get('id', 'unknown')
        description = apartment_data.get('description', '')
        caracteristiques = apartment_data.get('caracteristiques', '')
        photos = apartment_data.get('photos', [])
        
        # OPTIMISATION 1: Vérifier si l'appartement a déjà des données d'analyse
        existing_analysis = apartment_data.get('_analysis_data') or apartment_data.get('style_analysis')
        if existing_analysis:
            print(f"   💾 Données d'analyse déjà présentes pour {apartment_id}, skip")
            # Convertir au format unifié si nécessaire
            if isinstance(existing_analysis, dict) and 'style' in existing_analysis:
                return existing_analysis
            # Sinon, retourner None pour forcer une nouvelle analyse si format incompatible
        
        if not photos:
            print(f"   ⚠️  Aucune photo pour l'appartement {apartment_id}")
            return None
        
        # OPTIMISATION 2: Vérifier le cache (amélioré)
        cache_input_data = self._get_cache_input_data(apartment_id, photos)
        cached = self.cache.get("unified_analysis", cache_input_data)
        if cached:
            print(f"   💾 Cache hit: analyse unifiée (évite re-analyse IA)")
            return cached
        
        print(f"   🤖 Analyse unifiée avec {self.model} ({len(photos[:max_photos])} photos)...")
        
        # Charger les photos depuis les chemins locaux
        image_contents = self._load_photos_for_analysis(photos, max_photos=max_photos)
        
        if not image_contents:
            print(f"   ⚠️  Impossible de charger les photos")
            return None
        
        # Préparer le prompt unifié
        prompt = self._create_unified_prompt(description, caracteristiques)
        
        # Préparer le contenu avec texte + toutes les images
        content = [{"type": "text", "text": prompt}]
        
        # Ajouter toutes les images en base64
        for i, image_content in enumerate(image_contents, 1):
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            })
        
        try:
            # UNE SEULE requête pour tout analyser
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': content
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 2000
            }
            
            response = requests.post(
                f'{self.openai_base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"   ❌ Erreur API: {response.status_code}")
                print(f"   {response.text[:200]}")
                return None
            
            result = response.json()
            response_text = result['choices'][0]['message']['content'].strip()
            
            # Parser la réponse JSON
            analysis_result = self._parse_unified_response(response_text, apartment_id)
            
            if analysis_result:
                # Mettre en cache
                self.cache.set("unified_analysis", cache_input_data, analysis_result)
                print(f"   ✅ Analyse unifiée terminée")
                return analysis_result
            else:
                print(f"   ⚠️  Erreur parsing de la réponse")
                return None
                
        except Exception as e:
            print(f"   ❌ Erreur analyse unifiée: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_unified_prompt(self, description: str, caracteristiques: str) -> str:
        """Crée le prompt unifié pour analyser tout en une fois"""
        return f"""Analyse ces photos d'appartement et le texte pour déterminer TOUS les éléments suivants en UNE SEULE analyse :

## TEXTE DISPONIBLE
Description: {description[:500]}
Caractéristiques: {caracteristiques[:200]}

## TÂCHES À EFFECTUER

### 1. STYLE ARCHITECTURAL
Détermine le style de l'appartement :
- haussmannien (moulures, parquet, cheminée, hauteur sous plafond)
- moderne (lignes épurées, design contemporain)
- atypique/loft (conversion, poutres apparentes)
- 70s (carrelage, couleurs caractéristiques)
- autre

### 2. CUISINE
Détermine si la cuisine est :
- ouverte (visible depuis le salon, pas de séparation)
- fermée (séparée par un mur ou porte)
- semi-ouverte (bar, comptoir)

### 3. SALLE DE BAIN
Détermine la présence de :
- baignoire (oui/non)
- douche (oui/non)
- les deux

### 4. LUMINOSITÉ
Évalue la luminosité globale :
- très_lumineux (beaucoup de lumière naturelle)
- lumineux (bonne luminosité)
- moyen (luminosité modérée)
- faible (peu de lumière)

## FORMAT DE RÉPONSE (JSON UNIQUEMENT)

Réponds UNIQUEMENT au format JSON suivant (pas de texte avant/après) :

{{
    "style": {{
        "type": "haussmannien|moderne|atypique|70s|autre",
        "confidence": 0.0-1.0,
        "score": 0-20,
        "justification": "description courte avec éléments détectés",
        "elements_detectes": ["moulures", "parquet", ...]
    }},
    "cuisine": {{
        "ouverte": true|false,
        "confidence": 0.0-1.0,
        "score": 0-10,
        "justification": "description de ce qui est visible"
    }},
    "salle_de_bain": {{
        "baignoire": true|false,
        "douche": true|false,
        "confidence": 0.0-1.0,
        "score": 0-10,
        "justification": "description"
    }},
    "luminosite": {{
        "type": "tres_lumineux|lumineux|moyen|faible",
        "confidence": 0.0-1.0,
        "score": 0-10,
        "justification": "description"
    }},
    "photos_analyzed": 0
}}"""
    
    def _parse_unified_response(self, response_text: str, apartment_id: str) -> Optional[Dict]:
        """Parse la réponse JSON de l'analyse unifiée"""
        try:
            # Nettoyer la réponse (enlever markdown si présent)
            text = response_text.strip()
            if text.startswith('```json'):
                text = text.replace('```json', '').replace('```', '').strip()
            elif text.startswith('```'):
                text = text.replace('```', '').strip()
            
            # Parser le JSON
            data = json.loads(text)
            
            # Adapter au format attendu par le système
            result = {
                'style': {
                    'type': data.get('style', {}).get('type', 'autre'),
                    'confidence': data.get('style', {}).get('confidence', 0.5),
                    'score': data.get('style', {}).get('score', 0),
                    'justification': data.get('style', {}).get('justification', ''),
                    'details': {
                        'elements_detectes': data.get('style', {}).get('elements_detectes', [])
                    }
                },
                'cuisine': {
                    'ouverte': data.get('cuisine', {}).get('ouverte', False),
                    'confidence': data.get('cuisine', {}).get('confidence', 0.5),
                    'score': data.get('cuisine', {}).get('score', 0),
                    'justification': data.get('cuisine', {}).get('justification', '')
                },
                'baignoire': {
                    'presente': data.get('salle_de_bain', {}).get('baignoire', False),
                    'confidence': data.get('salle_de_bain', {}).get('confidence', 0.5),
                    'score': data.get('salle_de_bain', {}).get('score', 0),
                    'justification': data.get('salle_de_bain', {}).get('justification', '')
                },
                'luminosite': {
                    'type': data.get('luminosite', {}).get('type', 'moyen'),
                    'confidence': data.get('luminosite', {}).get('confidence', 0.5),
                    'score': data.get('luminosite', {}).get('score', 0),
                    'justification': data.get('luminosite', {}).get('justification', '')
                },
                'photos_analyzed': data.get('photos_analyzed', 0),
                'method': 'unified_analysis',
                'model': self.model
            }
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Erreur parsing JSON: {e}")
            print(f"   Réponse reçue: {response_text[:500]}")
            return None
        except Exception as e:
            print(f"   ⚠️  Erreur parsing: {e}")
            return None


def analyze_apartment_unified(apartment_data: Dict) -> Optional[Dict]:
    """
    Fonction utilitaire pour analyser un appartement de manière unifiée
    
    Args:
        apartment_data: Données de l'appartement
    
    Returns:
        Résultat de l'analyse unifiée
    """
    analyzer = UnifiedApartmentAnalyzer()
    return analyzer.analyze_apartment_unified(apartment_data)


if __name__ == "__main__":
    """Test de l'analyseur unifié"""
    from data_loader import load_apartments
    
    print("🧪 TEST ANALYSEUR UNIFIÉ")
    print("=" * 60)
    
    apartments = load_apartments(prefer_api=True)
    if apartments:
        test_apt = apartments[0]
        print(f"\n📋 Test avec appartement: {test_apt.get('id')}")
        print(f"   Titre: {test_apt.get('titre')}")
        print(f"   Photos: {len(test_apt.get('photos', []))}")
        
        analyzer = UnifiedApartmentAnalyzer()
        result = analyzer.analyze_apartment_unified(test_apt, max_photos=3)  # Optimisé: 3 photos
        
        if result:
            print(f"\n✅ RÉSULTATS DE L'ANALYSE UNIFIÉE:")
            print(f"   Style: {result['style']['type']} (confiance: {result['style']['confidence']:.2f})")
            print(f"   Cuisine: {'Ouverte' if result['cuisine']['ouverte'] else 'Fermée'} (confiance: {result['cuisine']['confidence']:.2f})")
            print(f"   Baignoire: {'Oui' if result['baignoire']['presente'] else 'Non'} (confiance: {result['baignoire']['confidence']:.2f})")
            print(f"   Luminosité: {result['luminosite']['type']} (confiance: {result['luminosite']['confidence']:.2f})")
            print(f"   Photos analysées: {result['photos_analyzed']}")
            print(f"   Modèle: {result['model']}")
        else:
            print("❌ Échec de l'analyse")
    else:
        print("❌ Aucun appartement trouvé")

