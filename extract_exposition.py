#!/usr/bin/env python3
"""
Module d'extraction de l'exposition des appartements
Phase 1: Analyse textuelle
Phase 2: Analyse des photos (à venir)
"""

import re
import json
import os
import requests
from typing import Dict, List, Optional, Tuple
from analyze_photos import PhotoAnalyzer
from analyze_contextual_exposition import ContextualExpositionAnalyzer
from analyze_text_ai import TextAIAnalyzer
from dotenv import load_dotenv

load_dotenv()

class ExpositionExtractor:
    """Extracteur d'exposition pour les appartements"""
    
    def __init__(self):
        self.photo_analyzer = PhotoAnalyzer()
        self.contextual_analyzer = ContextualExpositionAnalyzer()
        self.text_ai_analyzer = TextAIAnalyzer()
        self.use_ai_validation = True  # Activer la validation IA pour éviter faux positifs
        
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
    
    def extract_exposition_textuelle(self, description: str, caracteristiques: str = "", etage: str = "") -> Dict:
        """Extrait l'exposition depuis le texte (Phase 1)"""
        try:
            # Combiner tous les textes
            text = f"{description} {caracteristiques} {etage}".lower()
            
            # Chercher l'exposition
            exposition_trouvee = None
            score_exposition = 0
            tier = 'tier3'
            justification = "Exposition non spécifiée"
            exposition_explicite = False
            
            # Chercher l'exposition en priorité (ordre d'importance)
            # D'abord chercher les expositions composées, puis les simples
            potential_expositions = []
            for expo, details in self.expositions.items():
                for keyword in details['keywords']:
                    # Utiliser des word boundaries pour éviter les faux positifs
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        potential_expositions.append({
                            'exposition': expo,
                            'keyword': keyword,
                            'score': details['score'],
                            'tier': details['tier'],
                            'description': details['description']
                        })
                        break
            
            # Variables pour stocker les infos IA (initialisées par défaut)
            ai_result = None
            confiance_globale = 0.0
            confiance_exposition = 0.0
            etage_analyse = {}
            vue_mentionnee = {}
            indices_trouves = []
            
            # Si exposition(s) trouvée(s), valider avec IA pour éviter faux positifs
            if potential_expositions and self.use_ai_validation and self.text_ai_analyzer.openai_api_key:
                ai_result = self.text_ai_analyzer.analyze_exposition(description, caracteristiques, etage)
                
                if ai_result.get('available', False):
                    exposition_ia = ai_result.get('exposition')
                    est_faux_positif = ai_result.get('est_faux_positif', False)
                    confiance_globale = ai_result.get('confiance_globale', 0.0)
                    confiance_exposition = ai_result.get('confiance_exposition', 0.0)
                    
                    # Extraire les informations supplémentaires
                    etage_analyse = ai_result.get('etage_analyse', {})
                    vue_mentionnee = ai_result.get('vue_mentionnee', {})
                    indices_trouves = ai_result.get('indices_trouves', [])
                    
                    if not est_faux_positif and exposition_ia:
                        # Trouver l'exposition validée dans la liste
                        for exp in potential_expositions:
                            if exp['exposition'] == exposition_ia:
                                exposition_trouvee = exp['exposition']
                                score_exposition = exp['score']
                                tier = exp['tier']
                                
                                # Construire une justification enrichie avec toutes les infos
                                justification_parts = [f"Analyse IA globale (confiance: {confiance_globale:.0%})"]
                                justification_parts.append(ai_result.get('justification', exp['description']))
                                
                                if etage_analyse.get('etage_trouve'):
                                    impact_etage = etage_analyse.get('impact_luminosite', 'neutre')
                                    if impact_etage == 'positif':
                                        justification_parts.append(f"Étage {etage_analyse.get('etage_trouve')} favorable (+)")
                                    elif impact_etage == 'negatif':
                                        justification_parts.append(f"Étage {etage_analyse.get('etage_trouve')} limitant (-)")
                                
                                if vue_mentionnee.get('vue_trouvee'):
                                    type_vue = vue_mentionnee.get('type_vue', '')
                                    impact_vue = vue_mentionnee.get('impact_luminosite', 'neutre')
                                    if impact_vue == 'positif':
                                        justification_parts.append(f"Vue {type_vue} favorable (+)")
                                    elif impact_vue == 'negatif':
                                        justification_parts.append(f"Vue {type_vue} limitante (-)")
                                
                                if indices_trouves:
                                    justification_parts.append(f"Indices: {', '.join(indices_trouves[:3])}")
                                
                                justification = " | ".join(justification_parts)
                                exposition_explicite = True
                                
                                # Ajuster le score si confiance globale élevée (>0.8) et score actuel moyen
                                if confiance_globale > 0.8 and score_exposition < 8:
                                    score_exposition = min(10, score_exposition + 1)
                                    if score_exposition >= 10:
                                        tier = 'tier1'
                                    elif score_exposition >= 7:
                                        tier = 'tier2'
                                
                                break
                    else:
                        # IA n'a pas confirmé → pas d'exposition explicite
                        # Mais on peut quand même utiliser les infos sur étage/vue pour ajuster
                        if confiance_globale > 0.5 and not est_faux_positif:
                            # Pas d'exposition explicite mais bonnes indications (étage élevé + vue)
                            # On garde une exposition None mais on note les indices positifs
                            justification = f"Pas d'exposition explicite mais indices positifs (confiance: {confiance_globale:.0%})"
                            if etage_analyse.get('impact_luminosite') == 'positif':
                                justification += f" | Étage {etage_analyse.get('etage_trouve')} favorable"
                            if vue_mentionnee.get('impact_luminosite') == 'positif':
                                justification += f" | Vue {vue_mentionnee.get('type_vue')} favorable"
                        else:
                            exposition_trouvee = None
                else:
                    # Erreur IA → utiliser la première trouvée avec warning
                    first_match = potential_expositions[0]
                    exposition_trouvee = first_match['exposition']
                    score_exposition = first_match['score']
                    tier = first_match['tier']
                    justification = f"{first_match['description']} (validation IA indisponible)"
                    exposition_explicite = True
            elif potential_expositions:
                # Pas de validation IA disponible → utiliser la première trouvée
                first_match = potential_expositions[0]
                exposition_trouvee = first_match['exposition']
                score_exposition = first_match['score']
                tier = first_match['tier']
                justification = first_match['description']
                exposition_explicite = True
            
            # Analyser la luminosité
            luminosite_score = self._analyze_luminosite(text)
            
            # Analyser la vue
            vue_score = self._analyze_vue(text)
            
            # Calculer le bonus étage >=4
            bonus_etage = self._calculate_etage_bonus(caracteristiques, etage)
            
            # Calculer le score total (max entre exposition, luminosité, vue)
            score_base = max(score_exposition, luminosite_score, vue_score)
            
            # Ajouter le bonus étage (max 10)
            score_total = min(10, score_base + bonus_etage)
            
            # Mettre à jour le tier si nécessaire après bonus
            if score_total >= 10:
                tier = 'tier1'
            elif score_total >= 7:
                tier = 'tier2'
            else:
                tier = 'tier3'
            
            return {
                'exposition': exposition_trouvee,
                'score': score_total,
                'tier': tier,
                'justification': justification,
                'luminosite': self._get_luminosite_level(text),
                'vue': self._get_vue_level(text),
                'exposition_explicite': exposition_explicite,
                'bonus_etage': bonus_etage,
                'details': {
                    'exposition_score': score_exposition,
                    'luminosite_score': luminosite_score,
                    'vue_score': vue_score,
                    'score_base': score_base,
                    'bonus_etage': bonus_etage,
                    'ai_analysis': {
                        'available': ai_result is not None and ai_result.get('available', False),
                        'confiance_globale': confiance_globale,
                        'confiance_exposition': confiance_exposition,
                        'etage_analyse': etage_analyse,
                        'vue_mentionnee': vue_mentionnee,
                        'indices_trouves': indices_trouves
                    } if ai_result else None
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
                'exposition_explicite': False,
                'bonus_etage': 0,
                'details': {}
            }
    
    def _calculate_etage_bonus(self, caracteristiques: str, etage: str = "") -> int:
        """Calcule le bonus étage >=4"""
        text = f"{caracteristiques} {etage}".lower()
        
        # Patterns pour détecter étage >= 4
        patterns = [
            r'\b(4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20)[èe]?me?\s*étage',
            r'\bétage\s*(4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20)',
            r'\b(4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20)[èe]?\s*étage',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    etage_num = int(match.group(1))
                    if etage_num >= 4:
                        return 1  # Bonus de +1 point pour étage >= 4
                except (ValueError, IndexError):
                    continue
        
        return 0  # Pas de bonus
    
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
    
    def extract_exposition_complete(self, description: str, caracteristiques: str = "", photos_urls: List[str] = None, etage: str = "") -> Dict:
        """Extrait l'exposition en combinant analyse textuelle et photos (Phase 1 + 2)
        
        Nouvelle logique:
        1. Si exposition explicite trouvée → retourner directement
        2. Sinon → analyser les photos
        3. Si photos analysées → utiliser résultat photos
        4. Sinon → retourner résultat textuel
        """
        # Phase 1: Analyse textuelle (avec bonus étage)
        text_result = self.extract_exposition_textuelle(description, caracteristiques, etage)
        
        # Phase 2: Analyse des photos si disponibles
        photo_result = None
        if photos_urls:
            photo_result = self.extract_exposition_photos(photos_urls)
        
        # Phase 3: Validation croisée texte + photos pour ajuster la confiance
        if photo_result and photo_result.get('photos_analyzed', 0) > 0:
            validation = self.photo_analyzer.validate_text_with_photos(text_result, photo_result, 'exposition')
            
            # Utiliser la confiance ajustée
            confiance_ajustee = validation.get('confidence_adjusted', text_result.get('details', {}).get('ai_analysis', {}).get('confiance_globale', 0.5))
            validation_status = validation.get('validation_status', 'text_only')
            
            # Construire résultat final enrichi
            final_result = text_result.copy()
            
            # Mettre à jour la justification avec info de validation
            if validation_status == 'validated':
                final_result['justification'] += f" | ✅ Validé par photos (confiance: {confiance_ajustee:.0%})"
            elif validation_status == 'conflict':
                final_result['justification'] += f" | ⚠️ Conflit texte/photos (confiance: {confiance_ajustee:.0%})"
            
            # Ajouter les infos de validation dans les détails
            if 'details' not in final_result:
                final_result['details'] = {}
            final_result['details']['photo_validation'] = validation.get('cross_validation')
            final_result['details']['ai_analysis'] = final_result['details'].get('ai_analysis', {})
            final_result['details']['ai_analysis']['confiance_globale'] = confiance_ajustee
            final_result['details']['ai_analysis']['validation_status'] = validation_status
            
            return final_result
        
        # Pas de photos → retourner résultat textuel uniquement
        return text_result
    
    def extract_exposition_contextual(self, apartment_data: Dict) -> Dict:
        """Extrait l'exposition en utilisant l'analyse contextuelle (Phase 3)"""
        return self.contextual_analyzer.analyze_contextual_exposition(apartment_data)
    
    def extract_exposition_ultimate(self, apartment_data: Dict) -> Dict:
        """Extrait l'exposition en combinant toutes les méthodes (Phase 1 + 2 + 3)
        
        Nouvelle logique selon CHANGELOG:
        1. Si exposition explicite trouvée → retourner directement
        2. Sinon → analyser les photos
        3. Si photos analysées → utiliser résultat photos
        4. Sinon → analyser contextuel (dernier recours)
        5. Sinon → retourner inconnu
        """
        description = apartment_data.get('description', '')
        caracteristiques = apartment_data.get('caracteristiques', '')
        etage = apartment_data.get('etage', '')
        photos = apartment_data.get('photos', [])
        
        # Phase 1: Analyse textuelle (avec bonus étage)
        text_result = self.extract_exposition_textuelle(description, caracteristiques, etage)
        
        # Si exposition explicite trouvée → retourner directement
        if text_result.get('exposition_explicite', False) and text_result.get('exposition'):
            return text_result
        
        # Phase 2: Analyse des photos (si pas d'exposition explicite)
        photo_result = None
        if photos:
            photo_result = self.extract_exposition_photos(photos)
        
        # Si photos analysées avec succès → utiliser résultat photos
        if photo_result and photo_result.get('photos_analyzed', 0) > 0:
            return photo_result
        
        # Phase 3: Analyse contextuelle (dernier recours)
        contextual_result = self.extract_exposition_contextual(apartment_data)
        
        # Si contextuel confiant → combiner avec textuel
        if contextual_result.get('confidence', 0) > 0.5:
            return self._combine_results(contextual_result, text_result)
        
        # Sinon → retourner résultat textuel (peut être None si aucune info)
        return text_result
    
    def _combine_all_results(self, text_result: Dict, photo_result: Optional[Dict], contextual_result: Dict) -> Dict:
        """Combine les résultats de toutes les méthodes d'analyse
        
        NOTE: Cette méthode n'est plus utilisée dans extract_exposition_ultimate()
        mais conservée pour compatibilité avec extract_exposition_complete()
        """
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
