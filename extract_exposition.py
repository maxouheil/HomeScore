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
import unicodedata
from typing import Dict, List, Optional, Tuple
from collections import Counter
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
    
    def _upgrade_tier_if_good_visavis(self, tier: str, visavis_category: Optional[str]) -> str:
        """Upgrade le tier d'un niveau si vis-à-vis est 'good'
        
        Args:
            tier: Tier actuel ('tier1', 'tier2', 'tier3')
            visavis_category: Catégorie du vis-à-vis ('good', 'moyen', 'bad', ou None)
        
        Returns:
            Nouveau tier (upgradé si visavis_category == 'good')
        """
        if visavis_category == 'good':
            if tier == 'tier3':
                return 'tier2'
            elif tier == 'tier2':
                return 'tier1'
            # tier1 reste tier1
        return tier
    
    def _add_brightness_to_result(self, result: Dict, photos: List, style_analysis: Dict = None) -> Dict:
        """Ajoute brightness_value et visavis aux détails d'un résultat, même si exposition déjà trouvée"""
        if not photos or not result:
            return result
        
        try:
            # Extraire les URLs des photos (peut être une liste de strings ou une liste de dicts)
            photo_urls = []
            for photo in photos:
                if isinstance(photo, str):
                    photo_urls.append(photo)
                elif isinstance(photo, dict):
                    photo_url = photo.get('url')
                    if photo_url:
                        photo_urls.append(photo_url)
            
            if not photo_urls:
                return result
            
            # Analyser la luminosité des photos
            photo_result = self.extract_exposition_photos(photo_urls)
            if photo_result and photo_result.get('photos_analyzed', 0) > 0:
                photo_details = photo_result.get('details', {})
                brightness_value = photo_details.get('brightness_value')
                if brightness_value is not None:
                    if 'details' not in result:
                        result['details'] = {}
                    result['details']['brightness_value'] = brightness_value
                    result['details']['image_brightness'] = brightness_value
            
            # Analyser le vis-à-vis depuis les photos (utiliser style_analysis si disponible)
            visavis_result = self.photo_analyzer.analyze_photos_visavis(photo_urls, style_analysis=style_analysis)
            if visavis_result and visavis_result.get('photos_analyzed', 0) > 0:
                visavis_distance = visavis_result.get('visavis_distance')
                visavis_category = visavis_result.get('visavis_category')
                if visavis_distance is not None:
                    if 'details' not in result:
                        result['details'] = {}
                    result['details']['visavis_distance'] = visavis_distance
                    result['details']['visavis_category'] = visavis_category
                    result['details']['visavis_confidence'] = visavis_result.get('confidence', 0.0)
                    result['details']['visavis_justification'] = visavis_result.get('justification', '')
                    
                    # Upgrade le tier si vis-à-vis est 'good'
                    if visavis_category == 'good' and 'tier' in result:
                        old_tier = result['tier']
                        new_tier = self._upgrade_tier_if_good_visavis(old_tier, visavis_category)
                        if new_tier != old_tier:
                            result['tier'] = new_tier
                            # Mettre à jour la justification pour indiquer l'upgrade
                            if 'justification' in result:
                                result['justification'] += f" | ⬆️ Tier upgradé ({old_tier}→{new_tier}) grâce au vis-à-vis good"
        except Exception:
            # En cas d'erreur, continuer sans brightness_value ni visavis
            pass
        
        return result
    
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
                    
                    # NOUVELLE LOGIQUE : Si mention explicite étage ET/OU exposition → confiance 70%
                    etage_trouve = etage_analyse.get('etage_trouve')
                    exposition_explicite_detectee = bool(exposition_ia and not est_faux_positif)
                    
                    if (etage_trouve or exposition_explicite_detectee):
                        # Monter à 70% de confiance si étage ET/OU exposition mentionnés
                        confiance_globale = max(confiance_globale, 0.7)
                    
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
        if not photos_urls:
            return {
                'exposition': None,
                'score': 0,
                'tier': 'tier3',
                'justification': 'Aucune photo disponible',
                'photos_analyzed': 0,
                'details': {}
            }
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
        
        NOUVELLE LOGIQUE:
        1. PRIORITÉ 1: Analyse textuelle - Si mention explicite étage ET/OU exposition → confiance 70%
        2. PRIORITÉ 2: Si confiance < 70% → analyser les photos (top 5) pour mesurer la luminosité moyenne
        3. Agrégation basée sur la luminosité moyenne des photos (brightness)
        """
        # Phase 1: Analyse textuelle (avec bonus étage)
        text_result = self.extract_exposition_textuelle(description, caracteristiques, etage)
        
        # Vérifier si confiance >= 70% (mention explicite détectée)
        confiance_textuelle = 0.0
        if text_result and isinstance(text_result, dict):
            ai_analysis = text_result.get('details', {}).get('ai_analysis')
            if ai_analysis:
                confiance_textuelle = ai_analysis.get('confiance_globale', 0.0)
        
        # Même si confiance >= 70%, analyser les photos pour obtenir brightness_value
        # Si confiance >= 70% → retourner directement (mais avec brightness_value si disponible)
        if text_result and isinstance(text_result, dict) and confiance_textuelle >= 0.7:
            # Toujours analyser les photos pour obtenir brightness_value
            text_result = self._add_brightness_to_result(text_result, photos_urls)
            return text_result
        
        # Phase 2: Si confiance < 70% → analyser les photos
        photo_result = None
        if photos_urls:
            # Analyser les 5 premières photos pour détection précise
            photos_to_analyze = photos_urls[:5]
            photo_result = self.extract_exposition_photos(photos_to_analyze)
        
        # Phase 3: Si photos analysées → combiner avec résultat textuel
        if photo_result and photo_result.get('photos_analyzed', 0) > 0:
            if text_result and isinstance(text_result, dict):
                validation = self.photo_analyzer.validate_text_with_photos(text_result, photo_result, 'exposition')
                
                # Utiliser la confiance ajustée
                ai_analysis = text_result.get('details', {}).get('ai_analysis')
                confiance_textuelle_base = ai_analysis.get('confiance_globale', 0.5) if ai_analysis else 0.5
                confiance_ajustee = validation.get('confidence_adjusted', confiance_textuelle_base)
                validation_status = validation.get('validation_status', 'text_only')
                
                # Construire résultat final enrichi
                final_result = text_result.copy()
            else:
                # Pas de résultat textuel → utiliser uniquement les photos
                final_result = photo_result.copy()
                confiance_ajustee = photo_result.get('confidence', 0.5)
                validation_status = 'photo_only'
            
            # Mettre à jour la justification avec info de validation
            if validation_status == 'validated':
                final_result['justification'] += f" | ✅ Validé par photos (confiance: {confiance_ajustee:.0%})"
            elif validation_status == 'conflict':
                final_result['justification'] += f" | ⚠️ Conflit texte/photos (confiance: {confiance_ajustee:.0%})"
            
            # Ajouter les infos de validation dans les détails
            if 'details' not in final_result:
                final_result['details'] = {}
            final_result['details']['photo_validation'] = validation.get('cross_validation')
            
            # Initialiser ai_analysis si nécessaire
            if 'ai_analysis' not in final_result['details'] or final_result['details']['ai_analysis'] is None:
                final_result['details']['ai_analysis'] = {}
            final_result['details']['ai_analysis']['confiance_globale'] = confiance_ajustee
            final_result['details']['ai_analysis']['validation_status'] = validation_status
            
            # brightness_value est déjà dans photo_result.details, le copier si nécessaire
            if 'brightness_value' not in final_result.get('details', {}):
                photo_brightness = photo_result.get('details', {}).get('brightness_value')
                if photo_brightness is not None:
                    if 'details' not in final_result:
                        final_result['details'] = {}
                    final_result['details']['brightness_value'] = photo_brightness
                    final_result['details']['image_brightness'] = photo_brightness
            
            return final_result
        
        # Pas de photos → retourner résultat textuel uniquement (brightness_value déjà ajouté si disponible)
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
        
        NOUVEAU: Analyse du vis-à-vis depuis les photos pour tous les cas
        """
        description = apartment_data.get('description', '')
        caracteristiques = apartment_data.get('caracteristiques', '')
        etage = apartment_data.get('etage', '')
        photos = apartment_data.get('photos', [])
        
        # Phase 1: Analyse textuelle (avec bonus étage)
        text_result = self.extract_exposition_textuelle(description, caracteristiques, etage)
        
        # Récupérer style_analysis si disponible
        style_analysis = apartment_data.get('style_analysis')
        
        # Si exposition explicite trouvée → analyser quand même les photos pour brightness_value et visavis
        if text_result.get('exposition_explicite', False) and text_result.get('exposition'):
            # Toujours analyser les photos pour obtenir brightness_value et visavis
            text_result = self._add_brightness_to_result(text_result, photos, style_analysis=style_analysis)
            return text_result
        
        # Phase 2: Analyse des photos (si pas d'exposition explicite)
        photo_result = None
        if photos:
            # Extraire les URLs des photos
            photo_urls = []
            for photo in photos:
                if isinstance(photo, str):
                    photo_urls.append(photo)
                elif isinstance(photo, dict):
                    photo_url = photo.get('url')
                    if photo_url:
                        photo_urls.append(photo_url)
            
            if photo_urls:
                photo_result = self.extract_exposition_photos(photo_urls)
                
                # Ajouter l'analyse du vis-à-vis au résultat photo (utiliser style_analysis si disponible)
                if photo_result:
                    style_analysis = apartment_data.get('style_analysis')
                    visavis_result = self.photo_analyzer.analyze_photos_visavis(photo_urls, style_analysis=style_analysis)
                    if visavis_result and visavis_result.get('photos_analyzed', 0) > 0:
                        visavis_distance = visavis_result.get('visavis_distance')
                        visavis_category = visavis_result.get('visavis_category')
                        if visavis_distance is not None:
                            if 'details' not in photo_result:
                                photo_result['details'] = {}
                            photo_result['details']['visavis_distance'] = visavis_distance
                            photo_result['details']['visavis_category'] = visavis_category
                            photo_result['details']['visavis_confidence'] = visavis_result.get('confidence', 0.0)
                            photo_result['details']['visavis_justification'] = visavis_result.get('justification', '')
                            
                            # Upgrade le tier si vis-à-vis est 'good'
                            if visavis_category == 'good' and 'tier' in photo_result:
                                old_tier = photo_result['tier']
                                new_tier = self._upgrade_tier_if_good_visavis(old_tier, visavis_category)
                                if new_tier != old_tier:
                                    photo_result['tier'] = new_tier
                                    # Mettre à jour la justification pour indiquer l'upgrade
                                    if 'justification' in photo_result:
                                        photo_result['justification'] += f" | ⬆️ Tier upgradé ({old_tier}→{new_tier}) grâce au vis-à-vis good"
        
        # Si photos analysées avec succès → utiliser résultat photos
        if photo_result and photo_result.get('photos_analyzed', 0) > 0:
            return photo_result
        
        # Phase 3: Analyse contextuelle (dernier recours)
        contextual_result = self.extract_exposition_contextual(apartment_data)
        
        # Si contextuel confiant → combiner avec textuel
        if contextual_result.get('confidence', 0) > 0.5:
            combined = self._combine_results(contextual_result, text_result)
            # Toujours ajouter brightness_value et visavis si photos disponibles
            style_analysis = apartment_data.get('style_analysis')
            combined = self._add_brightness_to_result(combined, photos, style_analysis=style_analysis)
            return combined
        
        # Sinon → retourner résultat textuel (peut être None si aucune info)
        # Toujours ajouter brightness_value et visavis si photos disponibles
        if text_result:
            style_analysis = apartment_data.get('style_analysis')
            text_result = self._add_brightness_to_result(text_result, photos, style_analysis=style_analysis)
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
        
        # Vérifier le visavis_category dans les détails et upgrade le tier si nécessaire
        visavis_category = None
        photo_details = photo_result.get('details', {})
        text_details = text_result.get('details', {})
        
        # Chercher visavis_category dans photo_details ou text_details
        if 'visavis_category' in photo_details:
            visavis_category = photo_details['visavis_category']
        elif 'visavis_category' in text_details:
            visavis_category = text_details['visavis_category']
        
        # Upgrade le tier si vis-à-vis est 'good'
        old_tier = tier
        if visavis_category == 'good':
            tier = self._upgrade_tier_if_good_visavis(tier, visavis_category)
        
        # Construire la justification
        justification = f"Analyse combinée: {photo_result.get('justification', '')} + {text_result.get('justification', '')}"
        if visavis_category == 'good' and tier != old_tier:
            justification += f" | ⬆️ Tier upgradé ({old_tier}→{tier}) grâce au vis-à-vis good"
        
        return {
            'exposition': exposition,
            'score': combined_score,
            'tier': tier,
            'justification': justification,
            'luminosite': photo_result.get('luminosite', text_result.get('luminosite', 'inconnue')),
            'vue': photo_result.get('vue', text_result.get('vue', 'inconnue')),
            'photos_analyzed': photo_result.get('photos_analyzed', 0),
            'details': {
                'photo_score': photo_score,
                'text_score': text_score,
                'combined_score': combined_score,
                'photo_details': photo_details,
                'text_details': text_details
            }
        }
    
    def _normalize_orientation(self, text: str) -> str:
        """Normalise l'orientation: minuscules, sans accents, sans espaces/traits"""
        # Enlever accents
        text = unicodedata.normalize('NFD', text.lower())
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        # Enlever espaces et traits
        text = text.replace(' ', '').replace('-', '').replace('_', '')
        return text
    
    def _classify_orientation(self, orientation_text: str) -> Optional[str]:
        """Classe l'orientation: Lumineux, Moyen, ou Sombre"""
        if not orientation_text:
            return None
        
        normalized = self._normalize_orientation(orientation_text)
        
        # Lumineux: sud, sudouest, sudest
        if 'sudouest' in normalized or normalized == 'sudouest':
            return 'Lumineux'
        if 'sudest' in normalized or normalized == 'sudest':
            return 'Lumineux'
        if normalized == 'sud':
            return 'Lumineux'
        
        # Sombre: nord, nordouest, nordest (vérifier AVANT est/ouest)
        if 'nordouest' in normalized or normalized == 'nordouest':
            return 'Sombre'
        if 'nordest' in normalized or normalized == 'nordest':
            return 'Sombre'
        if normalized == 'nord':
            return 'Sombre'
        
        # Moyen: est, ouest (seulement si pas de sud/nord)
        if normalized == 'est':
            return 'Moyen'
        if normalized == 'ouest':
            return 'Moyen'
        
        return None
    
    def _extract_etage_number(self, caracteristiques: str, etage: str = "") -> Optional[int]:
        """Extrait le numéro d'étage depuis le texte"""
        text = f"{caracteristiques} {etage}".lower()
        
        # Patterns pour détecter étage
        patterns = [
            r'\b(\d+)[èe]?me?\s*étage',
            r'\bétage\s*(\d+)',
            r'\b(\d+)[èe]?\s*étage',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        # Vérifier RDC
        if re.search(r'\b(rdc|rez[\s-]de[\s-]chaussée|rez[\s-]de[\s-]chaussee)\b', text, re.IGNORECASE):
            return 0
        
        return None
    
    def _classify_etage(self, etage_num: Optional[int]) -> Optional[str]:
        """Classe l'étage: Lumineux, Moyen, ou Sombre
        
        Barème:
        - Si >4 étages (>=5): Lumineux (sauf si autres signaux contraires)
        - Si <3 étages (<=2): Sombre (sauf si autres signaux contraires)
        - 3-4 étages: Moyen (par défaut)
        """
        if etage_num is None:
            return None
        
        if etage_num > 4:  # >=5 étages
            return 'Lumineux'
        elif etage_num < 3:  # <=2 étages (inclut RDC = 0)
            return 'Sombre'
        else:  # 3-4 étages
            return 'Moyen'
    
    def _classify_image_brightness(self, brightness_value: float) -> Optional[str]:
        """Classe l'exposition image: Lumineux, Moyen, ou Sombre"""
        if brightness_value is None:
            return None
        
        if brightness_value >= 0.70:
            return 'Lumineux'
        elif brightness_value >= 0.40:
            return 'Moyen'
        else:
            return 'Sombre'
    
    def _get_image_intensity(self, brightness_value: float) -> str:
        """Détermine l'intensité du signal image: Fort, Faible, ou Normal"""
        if brightness_value is None:
            return 'Normal'
        
        if brightness_value >= 0.85 or brightness_value <= 0.25:
            return 'Fort'
        elif 0.45 <= brightness_value <= 0.55:
            return 'Faible'
        else:
            return 'Normal'
    
    def extract_exposition_voting(self, description: str, caracteristiques: str = "", 
                                   etage: str = "", photos_urls: List[str] = None) -> Dict:
        """Extrait l'exposition avec système de vote selon règles explicites
        
        Règles:
        1. Classification par signal (orientation, étage, image)
        2. Vote majoritaire pour décision finale
        3. Calcul de confiance selon règles précises
        """
        try:
            # 1. CLASSIFICATION PAR SIGNAL
            
            # Signal orientation
            text = f"{description} {caracteristiques} {etage}".lower()
            orientation_class = None
            orientation_found = None
            
            # Chercher orientation dans le texte
            for expo, details in self.expositions.items():
                for keyword in details['keywords']:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        orientation_found = expo
                        orientation_class = self._classify_orientation(expo)
                        break
                if orientation_class:
                    break
            
            # Signal étage
            etage_num = self._extract_etage_number(caracteristiques, etage)
            etage_class = self._classify_etage(etage_num)
            
            # Signal image
            image_class = None
            image_brightness = None
            image_intensity = 'Normal'
            
            if photos_urls:
                photo_result = self.extract_exposition_photos(photos_urls[:5])
                if photo_result and photo_result.get('photos_analyzed', 0) > 0:
                    details = photo_result.get('details', {})
                    image_brightness = details.get('brightness_value')
                    if image_brightness is not None:
                        image_class = self._classify_image_brightness(image_brightness)
                        image_intensity = self._get_image_intensity(image_brightness)
            
            # 2. DÉCISION FINALE (vote majoritaire)
            signals = []
            if orientation_class:
                signals.append(('orientation', orientation_class))
            if etage_class:
                signals.append(('etage', etage_class))
            if image_class:
                signals.append(('image', image_class))
            
            if not signals:
                # Aucun signal → Moyen, 50%
                return {
                    'exposition': None,
                    'score': 10,  # Moyen = 10 points
                    'tier': 'tier2',
                    'justification': 'Aucun signal disponible',
                    'luminosite': 'moyen',
                    'vue': 'inconnue',
                    'confidence': 50,
                    'details': {
                        'method': 'voting',
                        'signals': [],
                        'final_class': 'Moyen',
                        'vote_result': {}
                    }
                }
            
            # Compter les votes
            votes = Counter([cls for _, cls in signals])
            final_class = votes.most_common(1)[0][0] if votes else 'Moyen'
            
            # En cas d'égalité parfaite, tranche avec l'image
            if len(votes) > 1 and len(set(votes.values())) == 1:  # Égalité parfaite
                if image_class:
                    final_class = image_class
                    if image_intensity == 'Faible':
                        final_class = 'Moyen'
                else:
                    final_class = 'Moyen'
            
            # Points selon classe finale
            points_map = {'Lumineux': 20, 'Moyen': 10, 'Sombre': 0}
            score = points_map.get(final_class, 10)
            
            # 3. CALCUL DE CONFIANCE
            
            # Base: 60% si un seul signal
            if len(signals) == 1:
                confidence = 60
            else:
                # Base: 60% pour plusieurs signaux
                confidence = 60
                # +20% pour chaque signal d'accord avec la classe finale
                # -15% pour chaque signal en désaccord
                for signal_name, signal_class in signals:
                    if signal_class == final_class:
                        confidence += 20
                    else:
                        confidence -= 15
            
            # +10% si image forte et d'accord avec classe finale
            if image_intensity == 'Fort' and image_class == final_class:
                confidence += 10
            
            # -10% si image faible (quelle que soit la classe)
            if image_intensity == 'Faible':
                confidence -= 10
            
            # Bornes: min 50%, max 95%
            confidence = max(50, min(95, confidence))
            
            # Construire justification
            justification_parts = []
            if orientation_class:
                justification_parts.append(f"Orientation: {orientation_class}")
            if etage_class:
                justification_parts.append(f"Étage: {etage_class}")
            if image_class:
                justification_parts.append(f"Image: {image_class} (brightness: {image_brightness:.2f}, intensity: {image_intensity})")
            justification_parts.append(f"Vote: {final_class} ({confidence}% confiance)")
            
            justification = " | ".join(justification_parts)
            
            # Déterminer tier
            if final_class == 'Lumineux':
                tier = 'tier1'
            elif final_class == 'Moyen':
                tier = 'tier2'
            else:
                tier = 'tier3'
            
            return {
                'exposition': orientation_found,
                'score': score,
                'tier': tier,
                'justification': justification,
                'luminosite': final_class.lower(),
                'vue': 'inconnue',
                'confidence': confidence,
                'details': {
                    'method': 'voting',
                    'signals': [
                        {'name': name, 'class': cls} for name, cls in signals
                    ],
                    'final_class': final_class,
                    'vote_result': dict(votes),
                    'image_brightness': image_brightness,
                    'image_intensity': image_intensity,
                    'etage_num': etage_num
                }
            }
            
        except Exception as e:
            return {
                'exposition': None,
                'score': 10,
                'tier': 'tier2',
                'justification': f"Erreur extraction voting: {e}",
                'luminosite': 'moyen',
                'vue': 'inconnue',
                'confidence': 50,
                'details': {'error': str(e)}
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
