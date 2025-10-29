#!/usr/bin/env python3
"""
Module d'extraction de l'exposition des appartements
Phase 1: Analyse textuelle
Phase 2: Analyse des photos (à venir)
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from analyze_photos import PhotoAnalyzer
from analyze_contextual_exposition import ContextualExpositionAnalyzer

class ExpositionExtractor:
    """Extracteur d'exposition pour les appartements"""
    
    def __init__(self):
        self.photo_analyzer = PhotoAnalyzer()
        self.contextual_analyzer = ContextualExpositionAnalyzer()
        
        # Mots-clés d'exposition avec leurs scores (ordre de spécificité)
        self.expositions = {
            'sud_ouest': {
                'keywords': ['sud-ouest', 'sud ouest', 'so', 'ouest-sud'],
                'score': 10,
                'tier': 'tier1',
                'description': 'Excellente exposition Sud-Ouest'
            },
            'nord_est': {
                'keywords': ['nord-est', 'nord est', 'ne', 'nord-est'],
                'score': 3,
                'tier': 'tier3',
                'description': 'Exposition Nord-Est limitée'
            },
            'sud': {
                'keywords': ['exposition sud', 'plein sud', 'orientation sud', 'sud'],
                'score': 10,
                'tier': 'tier1',
                'description': 'Excellente exposition Sud'
            },
            'nord': {
                'keywords': ['exposition nord', 'nord'],
                'score': 3,
                'tier': 'tier3',
                'description': 'Exposition Nord limitée'
            },
            'ouest': {
                'keywords': ['exposition ouest', 'ouest', 'couchant'],
                'score': 7,
                'tier': 'tier2',
                'description': 'Bonne exposition Ouest'
            },
            'est': {
                'keywords': ['exposition est', 'est', 'levant'],
                'score': 7,
                'tier': 'tier2',
                'description': 'Bonne exposition Est'
            }
        }
        
        # Mots-clés de luminosité
        self.luminosite_keywords = {
            'excellent': ['très lumineux', 'très clair', 'plein de lumière', 'très ensoleillé', 'lumineux toute la journée'],
            'bon': ['lumineux', 'clair', 'bien éclairé', 'ensoleillé', 'bien exposé'],
            'moyen': ['assez lumineux', 'correctement éclairé', 'luminosité correcte'],
            'faible': ['peu lumineux', 'sombre', 'peu éclairé', 'manque de lumière']
        }
        
        # Mots-clés de vue
        self.vue_keywords = {
            'excellent': ['vue dégagée', 'vue panoramique', 'vue sur parc', 'vue sur cour', 'pas de vis-à-vis', 'vue libre'],
            'bon': ['vue correcte', 'vue agréable', 'vue sur rue calme', 'vue dégagée partiellement'],
            'moyen': ['vue limitée', 'vue sur cour', 'vue partiellement obstruée'],
            'faible': ['vis-à-vis', 'vue obstruée', 'pas de vue', 'vue sur mur']
        }
    
    def extract_exposition_textuelle(self, description: str, caracteristiques: str = "") -> Dict:
        """Extrait l'exposition depuis le texte (Phase 1)"""
        try:
            # Combiner tous les textes
            text = f"{description} {caracteristiques}".lower()
            
            # Chercher l'exposition
            exposition_trouvee = None
            score_exposition = 0
            tier = 'tier3'
            justification = "Exposition non spécifiée"
            
            # Chercher l'exposition en priorité (ordre d'importance)
            # D'abord chercher les expositions composées, puis les simples
            for expo, details in self.expositions.items():
                for keyword in details['keywords']:
                    # Utiliser des word boundaries pour éviter les faux positifs
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        exposition_trouvee = expo
                        score_exposition = details['score']
                        tier = details['tier']
                        justification = details['description']
                        break
                if exposition_trouvee:
                    break
            
            # Analyser la luminosité
            luminosite_score = self._analyze_luminosite(text)
            
            # Analyser la vue
            vue_score = self._analyze_vue(text)
            
            # Calculer le score total
            score_total = max(score_exposition, luminosite_score, vue_score)
            
            return {
                'exposition': exposition_trouvee,
                'score': score_total,
                'tier': tier,
                'justification': justification,
                'luminosite': self._get_luminosite_level(text),
                'vue': self._get_vue_level(text),
                'details': {
                    'exposition_score': score_exposition,
                    'luminosite_score': luminosite_score,
                    'vue_score': vue_score
                }
            }
            
        except Exception as e:
            return {
                'exposition': None,
                'score': 3,
                'tier': 'tier3',
                'justification': f"Erreur extraction: {e}",
                'luminosite': 'inconnue',
                'vue': 'inconnue',
                'details': {}
            }
    
    def _analyze_luminosite(self, text: str) -> int:
        """Analyse la luminosité mentionnée"""
        for level, keywords in self.luminosite_keywords.items():
            if any(keyword in text for keyword in keywords):
                if level == 'excellent':
                    return 10
                elif level == 'bon':
                    return 7
                elif level == 'moyen':
                    return 5
                else:  # faible
                    return 3
        return 5  # Score par défaut
    
    def _analyze_vue(self, text: str) -> int:
        """Analyse la qualité de la vue"""
        for level, keywords in self.vue_keywords.items():
            if any(keyword in text for keyword in keywords):
                if level == 'excellent':
                    return 10
                elif level == 'bon':
                    return 7
                elif level == 'moyen':
                    return 5
                else:  # faible
                    return 3
        return 5  # Score par défaut
    
    def _get_luminosite_level(self, text: str) -> str:
        """Retourne le niveau de luminosité"""
        for level, keywords in self.luminosite_keywords.items():
            if any(keyword in text for keyword in keywords):
                return level
        return 'inconnue'
    
    def _get_vue_level(self, text: str) -> str:
        """Retourne le niveau de vue"""
        for level, keywords in self.vue_keywords.items():
            if any(keyword in text for keyword in keywords):
                return level
        return 'inconnue'
    
    def extract_exposition_photos(self, photos_urls: List[str]) -> Dict:
        """Extrait l'exposition depuis les photos (Phase 2)"""
        return self.photo_analyzer.analyze_photos_exposition(photos_urls)
    
    def get_exposition_score(self, exposition_data: Dict) -> int:
        """Retourne le score d'exposition final"""
        return exposition_data.get('score', 3)
    
    def get_exposition_tier(self, exposition_data: Dict) -> str:
        """Retourne le tier d'exposition"""
        return exposition_data.get('tier', 'tier3')
    
    def get_exposition_justification(self, exposition_data: Dict) -> str:
        """Retourne la justification de l'exposition"""
        return exposition_data.get('justification', 'Exposition non déterminée')
    
    def extract_exposition_complete(self, description: str, caracteristiques: str = "", photos_urls: List[str] = None) -> Dict:
        """Extrait l'exposition en combinant analyse textuelle et photos (Phase 1 + 2)"""
        # Phase 1: Analyse textuelle
        text_result = self.extract_exposition_textuelle(description, caracteristiques)
        
        # Phase 2: Analyse des photos (si disponibles)
        photo_result = None
        if photos_urls:
            photo_result = self.extract_exposition_photos(photos_urls)
        
        # Combiner les résultats
        if photo_result and photo_result.get('photos_analyzed', 0) > 0:
            # Priorité à l'analyse des photos si disponible
            return self._combine_results(photo_result, text_result)
        else:
            # Utiliser uniquement l'analyse textuelle
            return text_result
    
    def extract_exposition_contextual(self, apartment_data: Dict) -> Dict:
        """Extrait l'exposition en utilisant l'analyse contextuelle (Phase 3)"""
        return self.contextual_analyzer.analyze_contextual_exposition(apartment_data)
    
    def extract_exposition_ultimate(self, apartment_data: Dict) -> Dict:
        """Extrait l'exposition en combinant toutes les méthodes (Phase 1 + 2 + 3)"""
        description = apartment_data.get('description', '')
        caracteristiques = apartment_data.get('caracteristiques', '')
        photos = apartment_data.get('photos', [])
        
        # Phase 1: Analyse textuelle
        text_result = self.extract_exposition_textuelle(description, caracteristiques)
        
        # Phase 2: Analyse des photos
        photo_result = None
        if photos:
            photo_result = self.extract_exposition_photos(photos)
        
        # Phase 3: Analyse contextuelle
        contextual_result = self.extract_exposition_contextual(apartment_data)
        
        # Combiner tous les résultats
        return self._combine_all_results(text_result, photo_result, contextual_result)
    
    def _combine_all_results(self, text_result: Dict, photo_result: Optional[Dict], contextual_result: Dict) -> Dict:
        """Combine les résultats de toutes les méthodes d'analyse"""
        # Priorité: Photos > Contextuel > Textuel
        if photo_result and photo_result.get('photos_analyzed', 0) > 0:
            # Photos disponibles - priorité aux photos
            if contextual_result.get('confidence', 0) > 0.7:
                # Contextuel très confiant - combiner photos + contextuel
                return self._combine_results(photo_result, contextual_result)
            else:
                # Utiliser uniquement les photos
                return photo_result
        elif contextual_result.get('confidence', 0) > 0.5:
            # Contextuel confiant - combiner contextuel + textuel
            return self._combine_results(contextual_result, text_result)
        else:
            # Utiliser uniquement l'analyse textuelle
            return text_result
    
    def _combine_results(self, photo_result: Dict, text_result: Dict) -> Dict:
        """Combine les résultats de l'analyse textuelle et des photos"""
        # Priorité aux photos pour l'exposition
        exposition = photo_result.get('exposition') or text_result.get('exposition')
        
        # Score combiné (moyenne pondérée)
        photo_score = photo_result.get('score', 0)
        text_score = text_result.get('score', 0)
        
        # Poids: 70% photos, 30% texte
        combined_score = int(photo_score * 0.7 + text_score * 0.3)
        
        # Déterminer le tier
        if combined_score >= 10:
            tier = 'tier1'
        elif combined_score >= 7:
            tier = 'tier2'
        else:
            tier = 'tier3'
        
        return {
            'exposition': exposition,
            'score': combined_score,
            'tier': tier,
            'justification': f"Analyse combinée: {photo_result.get('justification', '')} + {text_result.get('justification', '')}",
            'luminosite': photo_result.get('luminosite', text_result.get('luminosite', 'inconnue')),
            'vue': photo_result.get('vue', text_result.get('vue', 'inconnue')),
            'photos_analyzed': photo_result.get('photos_analyzed', 0),
            'details': {
                'photo_score': photo_score,
                'text_score': text_score,
                'combined_score': combined_score,
                'photo_details': photo_result.get('details', {}),
                'text_details': text_result.get('details', {})
            }
        }

def test_exposition_extraction():
    """Test de l'extraction d'exposition"""
    extractor = ExpositionExtractor()
    
    # Test avec différentes descriptions
    test_cases = [
        {
            'description': 'Appartement très lumineux avec exposition Sud, vue dégagée sur le parc',
            'caracteristiques': 'Balcon, terrasse'
        },
        {
            'description': 'Duplex avec orientation Ouest, bien éclairé',
            'caracteristiques': 'Ascenseur'
        },
        {
            'description': 'Appartement au 4e étage, exposition Nord',
            'caracteristiques': 'Vis-à-vis'
        },
        {
            'description': 'Magnifique appartement haussmannien',
            'caracteristiques': 'Parking'
        }
    ]
    
    print("🧭 TEST D'EXTRACTION D'EXPOSITION")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Test case:")
        print(f"   Description: {case['description']}")
        print(f"   Caractéristiques: {case['caracteristiques']}")
        
        result = extractor.extract_exposition_textuelle(
            case['description'], 
            case['caracteristiques']
        )
        
        print(f"   Résultat:")
        print(f"      Exposition: {result['exposition']}")
        print(f"      Score: {result['score']}/10")
        print(f"      Tier: {result['tier']}")
        print(f"      Justification: {result['justification']}")
        print(f"      Luminosité: {result['luminosite']}")
        print(f"      Vue: {result['vue']}")

if __name__ == "__main__":
    test_exposition_extraction()
