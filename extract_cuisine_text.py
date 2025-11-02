#!/usr/bin/env python3
"""
Module d'extraction de la cuisine ouverte depuis le texte avec IA
"""

from typing import Dict, List
from analyze_text_ai import TextAIAnalyzer
from analyze_photos import PhotoAnalyzer

class CuisineTextExtractor:
    """Extracteur de cuisine ouverte depuis le texte avec validation croisée photos"""
    
    def __init__(self):
        self.text_ai_analyzer = TextAIAnalyzer()
        self.photo_analyzer = PhotoAnalyzer()
        self.use_ai_analysis = True
    
    def extract_cuisine_from_text(self, description: str, caracteristiques: str = "") -> Dict:
        """Extrait si la cuisine est ouverte depuis le texte avec IA"""
        if self.use_ai_analysis and self.text_ai_analyzer.openai_api_key:
            ai_result = self.text_ai_analyzer.analyze_cuisine_ouverte(description, caracteristiques)
            
            if ai_result.get('available', False):
                cuisine_ouverte = ai_result.get('cuisine_ouverte')
                confidence = ai_result.get('confiance', 0)
                justification = ai_result.get('justification', '')
                indices = ai_result.get('indices', [])
                
                if cuisine_ouverte is True:
                    return {
                        'ouverte': True,
                        'confidence': 0.8,  # Mentionné seulement → 80%
                        'justification': f"Analyse IA: {justification}",
                        'method': 'ai_text_analysis',
                        'indices': indices
                    }
                elif cuisine_ouverte is False:
                    return {
                        'ouverte': False,
                        'confidence': 0.8,  # Mentionné seulement → 80%
                        'justification': f"Analyse IA: {justification}",
                        'method': 'ai_text_analysis',
                        'indices': indices
                    }
        
        # Fallback: recherche simple par mots-clés
        text = f"{description} {caracteristiques}".lower()
        
        # Mots-clés cuisine ouverte
        open_keywords = [
            'cuisine américaine',
            'cuisine ouverte',
            'cuisine intégrée',
            'séjour cuisine',
            'pièce à vivre'
        ]
        
        # Mots-clés cuisine fermée
        closed_keywords = [
            'cuisine fermée',
            'cuisine indépendante',
            'cuisine séparée'
        ]
        
        for keyword in open_keywords:
            if keyword in text:
                return {
                    'ouverte': True,
                    'confidence': 0.8,
                    'justification': f"Cuisine ouverte détectée (mot-clé: '{keyword}')",
                    'method': 'keyword_search',
                    'indices': [keyword]
                }
        
        for keyword in closed_keywords:
            if keyword in text:
                return {
                    'ouverte': False,
                    'confidence': 0.8,
                    'justification': f"Cuisine fermée détectée (mot-clé: '{keyword}')",
                    'method': 'keyword_search',
                    'indices': [keyword]
                }
        
        return {
            'ouverte': None,  # Ambigu
            'confidence': 0.0,
            'justification': 'Cuisine non spécifiée dans le texte',
            'method': 'none',
            'indices': []
        }
    
    def extract_cuisine_complete(self, description: str, caracteristiques: str = "", photos_urls: List[str] = None) -> Dict:
        """Extrait si la cuisine est ouverte avec validation croisée texte + photos"""
        # Phase 1: Analyse textuelle IA
        text_result = self.extract_cuisine_from_text(description, caracteristiques)
        
        # Phase 2: Analyse photos si disponibles
        photo_result = None
        if photos_urls:
            photo_result = self.photo_analyzer.analyze_photos_cuisine(photos_urls)
        
        # Phase 3: Validation croisée texte + photos
        if photo_result and photo_result.get('photos_analyzed', 0) > 0:
            validation = self.photo_analyzer.validate_text_with_photos(text_result, photo_result, 'cuisine')
            validation_status = validation.get('validation_status', 'text_only')
            
            # Construire résultat final enrichi
            final_result = text_result.copy()
            
            # Vérifier si le texte a un résultat valide (pas None) = mentionné
            text_has_result = text_result.get('ouverte') is not None
            
            # Vérifier si les photos ont détecté quelque chose
            photo_has_result = photo_result.get('ouverte') is not None
            
            # Calculer la confiance selon les règles simples :
            # - Si seulement mentionné dans le texte : 80%
            # - Si seulement détecté par photos : 60%
            # - Si les deux (mentionné + détecté) : 90%
            if text_has_result and photo_has_result:
                confiance_finale = 0.9  # Les deux : 90%
            elif text_has_result:
                confiance_finale = 0.8  # Seulement mentionné : 80%
            elif photo_has_result:
                confiance_finale = 0.6  # Seulement détecté : 60%
            else:
                confiance_finale = 0.0  # Aucun des deux
            
            # Si photos confirment ou contredisent, ajuster le résultat
            if validation_status == 'validated':
                # Cohérent → utiliser résultat texte si disponible, sinon utiliser photos
                if text_has_result:
                    # Texte a un résultat → utiliser texte avec confiance calculée
                    final_result['confidence'] = confiance_finale
                    if photo_has_result:
                        final_result['justification'] += f" | ✅ Validé par photos (confiance: {confiance_finale:.0%})"
                    else:
                        final_result['justification'] += f" | (confiance: {confiance_finale:.0%})"
                else:
                    # Texte n'a pas de résultat → utiliser résultat photos
                    final_result = {
                        'ouverte': photo_result.get('ouverte'),
                        'confidence': confiance_finale,
                        'justification': f"{photo_result.get('justification', '')} | ✅ Détecté par photos (confiance: {confiance_finale:.0%})",
                        'method': 'photo_analysis',
                        'indices': text_result.get('indices', [])
                    }
            elif validation_status == 'conflict':
                # Incohérent → préférer photos si plus confiantes OU si texte n'a pas de résultat
                # En cas de conflit, utiliser quand même la règle de confiance simple
                if not text_has_result or (photo_has_result and not text_has_result):
                    # Photos disponibles OU texte sans résultat → utiliser résultat photos
                    final_result = {
                        'ouverte': photo_result.get('ouverte'),
                        'confidence': confiance_finale,
                        'justification': f"{photo_result.get('justification', '')} | ⚠️ Conflit avec texte, photos prioritaires (confiance: {confiance_finale:.0%})",
                        'method': 'photo_analysis',
                        'indices': text_result.get('indices', [])
                    }
                else:
                    # Texte disponible → garder texte avec confiance calculée
                    final_result['confidence'] = confiance_finale
                    final_result['justification'] += f" | ⚠️ Conflit avec photos (confiance: {confiance_finale:.0%})"
            
            # Ajouter les infos de validation et les numéros d'images détectées
            final_result['photo_validation'] = validation.get('cross_validation')
            final_result['validation_status'] = validation_status
            final_result['detected_photos'] = photo_result.get('detected_photos', [])
            
            return final_result
        
        # Pas de photos → retourner résultat textuel uniquement avec confiance 80% si mentionné
        if text_result.get('ouverte') is not None:
            # Mentionné dans le texte seulement → confiance 80%
            text_result['confidence'] = 0.8
        return text_result

