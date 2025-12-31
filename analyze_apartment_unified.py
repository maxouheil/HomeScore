#!/usr/bin/env python3
"""
Analyse unifiée d'appartement avec Gemini Flash
Analyse style, cuisine, salle de bain, luminosité en UNE SEULE requête
"""

import json
import os
from typing import Dict, List, Optional, Union
from pathlib import Path
from photo_manager import PhotoManager
from cache_api import get_cache
from dotenv import load_dotenv
from gemini_analyzer import GeminiAnalyzer

load_dotenv()


class UnifiedApartmentAnalyzer:
    """Analyseur unifié qui analyse tout en une seule requête avec Gemini Flash"""
    
    def __init__(self):
        self.analyzer = GeminiAnalyzer('gemini-2.5-flash')
        self.model = "gemini-2.5-flash"
        self.photo_manager = PhotoManager()
        self.cache = get_cache()
    
    def _get_cache_input_data(self, apartment_id: str, photos: List[Dict]) -> str:
        """Génère les données d'entrée pour le cache basées sur l'ID et les URLs des photos"""
        photo_urls = [p.get('url', '') for p in photos[:2]]  # OPTIMISÉ: 2 photos pour réduire les coûts
        return f"{apartment_id}:{':'.join(photo_urls)}"
    
    def _load_photos_for_analysis(self, photos: List[Dict], max_photos: int = 3) -> List:
        """
        Charge les photos depuis les chemins locaux ou URLs pour Gemini
        
        Args:
            photos: Liste des photos avec local_path ou url
            max_photos: Nombre maximum de photos à analyser
        
        Returns:
            Liste des sources d'images (chemins ou URLs) pour GeminiAnalyzer
        """
        image_sources = []
        
        for photo in photos[:max_photos]:
            # Priorité au chemin local si disponible
            local_path = photo.get('local_path')
            if local_path and os.path.exists(local_path):
                image_sources.append(local_path)
            else:
                # Sinon utiliser l'URL (GeminiAnalyzer peut charger depuis URL)
                photo_url = photo.get('url', '')
                if photo_url:
                    image_sources.append(photo_url)
        
        return image_sources
    
    def analyze_apartment_unified(
        self, 
        apartment_data: Dict,
        max_photos: int = 2  # OPTIMISÉ: 2 photos par défaut (réduction de 33% des coûts vs 3 photos)
    ) -> Optional[Dict]:
        """
        Analyse un appartement en UNE SEULE requête Gemini Flash
        
        Analyse simultanément :
        - Style (haussmannien, moderne, atypique, etc.)
        - Cuisine (ouverte/fermée)
        - Salle de bain (baignoire/douche)
        - Luminosité
        
        Args:
            apartment_data: Données de l'appartement
            max_photos: Nombre maximum de photos à analyser (défaut: 2 pour optimiser les coûts)
        
        Returns:
            Résultat unifié de l'analyse
        """
        apartment_id = apartment_data.get('id', 'unknown')
        description = apartment_data.get('description', '')
        caracteristiques = apartment_data.get('caracteristiques', '')
        photos = apartment_data.get('photos', [])
        
        # OPTIMISATION 1: Vérifier si l'appartement a déjà TOUTES les données d'analyse
        # Si certaines données manquent, on force l'analyse pour compléter
        existing_analysis = apartment_data.get('_analysis_data') or apartment_data.get('style_analysis')
        style_analysis = apartment_data.get('style_analysis', {})
        baignoire_data = apartment_data.get('baignoire_data', {})
        
        has_style = bool(style_analysis.get('style'))
        has_cuisine = bool(style_analysis.get('cuisine'))
        has_baignoire = (baignoire_data.get('has_baignoire') is not None)
        has_luminosite = bool(style_analysis.get('luminosite'))
        
        has_all_data = has_style and has_cuisine and has_baignoire and has_luminosite
        
        if has_all_data:
            print(f"   💾 Toutes les données d'analyse déjà présentes pour {apartment_id}, skip")
            # Convertir au format unifié si nécessaire
            if isinstance(existing_analysis, dict) and 'style' in existing_analysis:
                return existing_analysis
            # Sinon, retourner None pour forcer une nouvelle analyse si format incompatible
        else:
            missing = []
            if not has_style:
                missing.append('style')
            if not has_cuisine:
                missing.append('cuisine')
            if not has_baignoire:
                missing.append('baignoire')
            if not has_luminosite:
                missing.append('luminosité')
            missing_str = ', '.join(missing)
            print(f"   📸 Données manquantes pour {apartment_id} ({missing_str}), analyse nécessaire")
        
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
        
        # Charger les photos pour Gemini
        image_sources = self._load_photos_for_analysis(photos, max_photos=max_photos)
        
        if not image_sources:
            print(f"   ⚠️  Impossible de charger les photos")
            return None
        
        # Préparer le prompt unifié
        prompt = self._create_unified_prompt(description, caracteristiques)
        
        try:
            # UNE SEULE requête Gemini pour tout analyser (multi-images)
            response_data = self.analyzer.analyze_multiple_images(
                image_sources,
                prompt,
                return_json=True
            )
            
            # Adapter la réponse au format attendu
            analysis_result = self._parse_unified_response(response_data, apartment_id, len(image_sources))
            
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
        """Crée le prompt unifié optimisé pour analyser tout en une fois (version courte pour vitesse)"""
        # OPTIMISATION: Prompt plus court pour réduire les tokens et accélérer
        return f"""Analyse ces photos et texte pour déterminer en UNE SEULE analyse:

TEXTE: {description[:300]} {caracteristiques[:150]}

TÂCHES:
1. STYLE: haussmannien|moderne|atypique|70s|autre (avec éléments détectés: moulures, parquet, etc.)
2. CUISINE: ouverte|fermée|semi-ouverte (visible depuis salon?)
3. BAIGNOIRE: présente|absente (dans salle de bain?)
4. LUMINOSITÉ: tres_lumineux|lumineux|moyen|faible (selon lumière naturelle)

Réponds UNIQUEMENT en JSON (pas de texte avant/après):
{{
    "style": {{"type": "...", "confidence": 0.0-1.0, "justification": "éléments détectés", "elements_detectes": []}},
    "cuisine": {{"ouverte": true|false, "confidence": 0.0-1.0, "justification": "..."}},
    "baignoire": {{"presente": true|false, "confidence": 0.0-1.0, "justification": "..."}},
    "luminosite": {{"type": "...", "confidence": 0.0-1.0, "justification": "..."}},
    "photos_analyzed": 0
}}"""
    
    def _parse_unified_response(self, response_data: Union[str, Dict], apartment_id: str, photos_analyzed: int = 0) -> Optional[Dict]:
        """Parse la réponse JSON de l'analyse unifiée"""
        try:
            # Si c'est déjà un dict (cas Gemini avec return_json=True)
            if isinstance(response_data, dict):
                data = response_data
                # Si Gemini a retourné raw_response, essayer de parser
                if 'raw_response' in data:
                    try:
                        data = json.loads(data['raw_response'])
                    except:
                        pass
            else:
                # Si c'est une string, parser le JSON
                text = str(response_data).strip()
                if text.startswith('```json'):
                    text = text.replace('```json', '').replace('```', '').strip()
                elif text.startswith('```'):
                    text = text.replace('```', '').strip()
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
                    # Support ancien format (salle_de_bain) et nouveau format (baignoire)
                    'presente': data.get('baignoire', {}).get('presente', False) or 
                               data.get('salle_de_bain', {}).get('baignoire', False),
                    'confidence': data.get('baignoire', {}).get('confidence', 0.5) or 
                                 data.get('salle_de_bain', {}).get('confidence', 0.5),
                    'score': data.get('baignoire', {}).get('score', 0) or 
                            data.get('salle_de_bain', {}).get('score', 0),
                    'justification': data.get('baignoire', {}).get('justification', '') or 
                                   data.get('salle_de_bain', {}).get('justification', '')
                },
                'luminosite': {
                    'type': data.get('luminosite', {}).get('type', 'moyen'),
                    'confidence': data.get('luminosite', {}).get('confidence', 0.5),
                    'score': data.get('luminosite', {}).get('score', 0),
                    'justification': data.get('luminosite', {}).get('justification', '')
                },
                'photos_analyzed': data.get('photos_analyzed', photos_analyzed),
                'method': 'unified_analysis',
                'model': self.model
            }
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Erreur parsing JSON: {e}")
            print(f"   Réponse reçue: {str(response_data)[:500]}")
            return None
        except Exception as e:
            print(f"   ⚠️  Erreur parsing: {e}")
            import traceback
            traceback.print_exc()
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

