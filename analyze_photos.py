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
from cache_api import get_cache

load_dotenv()

class PhotoAnalyzer:
    """Analyseur de photos pour l'exposition"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = "https://api.openai.com/v1"
        self.cache = get_cache()
        
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
        """Analyse une photo individuelle avec cache"""
        # Vérifier le cache d'abord
        cached_result = self.cache.get('exposition_photo', photo_url)
        if cached_result:
            return cached_result
        
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
                'model': 'gpt-4o-mini',  # Optimisé pour réduire les coûts
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': """Analyse cette photo d'appartement et détermine l'exposition et les caractéristiques de luminosité.

Critères d'analyse détaillés:
1. Orientation des fenêtres (Sud, Sud-Ouest, Ouest, Est, Nord, Nord-Est) - basé sur position du soleil, ombres
2. Luminosité relative par rapport à la moyenne parisienne (très_lumineux, lumineux, moyen, faible)
3. Nombre de fenêtres visibles dans la pièce principale (nb_fenetres: nombre entier)
4. Taille des fenêtres (grandes, moyennes, petites)
5. Vis-à-vis (aucun, leger, important, obstrué)
6. Vue dégagée (true/false)
7. Balcon/Terrasse visible (true/false)
8. Taille du balcon si visible (grand, moyen, petit, aucun)

Réponds UNIQUEMENT au format JSON (pas de texte avant/après):
{
    "exposition": "sud|sud_ouest|ouest|est|nord|nord_est|null",
    "luminosite_relative": "tres_lumineux|lumineux|moyen|faible",
    "nb_fenetres": nombre_entier,
    "taille_fenetres": "grandes|moyennes|petites",
    "vis_a_vis": "aucun|leger|important|obstrué",
    "vue_degagee": true|false,
    "balcon_visible": true|false,
    "taille_balcon": "grand|moyen|petit|aucun",
    "score_luminosite": 0-10,
    "score_fenetres": 0-10,
    "score_vue": 0-10,
    "confidence": 0.0-1.0,
    "details": "description détaillée de ce que tu vois"
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
                
                # Mettre en cache avant de retourner
                self.cache.set('exposition_photo', photo_url, analysis)
                
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
        """Agrège les résultats de plusieurs photos avec score relatif pondéré
        
        Calcul selon CHANGELOG:
        Score total = (
            exposition_score * 0.3 +      # 30% exposition pure
            luminosite_score * 0.3 +       # 30% luminosité relative
            fenetres_score * 0.2 +         # 20% nombre/taille fenêtres
            vue_score * 0.2                # 20% vis-à-vis/dégagement
        ) + balcon_bonus                    # Bonus balcon
        """
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
        
        # Déterminer l'exposition la plus fréquente
        if expositions:
            exposition_counts = {}
            for expo in expositions:
                exposition_counts[expo] = exposition_counts.get(expo, 0) + 1
            most_common_exposition = max(exposition_counts, key=exposition_counts.get)
        else:
            most_common_exposition = None
        
        # Score d'exposition (30%)
        exposition_scores = {
            'sud': 10, 'sud_ouest': 10, 'ouest': 7, 'est': 7, 'nord': 3, 'nord_est': 3
        }
        exposition_score = exposition_scores.get(most_common_exposition, 0)
        
        # Score luminosité relative (30%) - utiliser score_luminosite si disponible, sinon convertir luminosite_relative
        luminosite_scores_list = []
        for r in results:
            if 'score_luminosite' in r and r['score_luminosite'] is not None:
                luminosite_scores_list.append(r['score_luminosite'])
            elif 'luminosite_relative' in r:
                luminosite_map = {'tres_lumineux': 10, 'lumineux': 7, 'moyen': 5, 'faible': 3}
                luminosite_scores_list.append(luminosite_map.get(r['luminosite_relative'], 5))
            elif 'luminosite' in r:
                # Fallback ancien format
                luminosite_map = {'excellent': 10, 'bon': 7, 'moyen': 5, 'faible': 3}
                luminosite_scores_list.append(luminosite_map.get(r['luminosite'], 5))
        
        avg_luminosite_score = sum(luminosite_scores_list) / len(luminosite_scores_list) if luminosite_scores_list else 5
        
        # Score fenêtres (20%) - basé sur nombre et taille
        fenetres_scores_list = []
        for r in results:
            if 'score_fenetres' in r and r['score_fenetres'] is not None:
                fenetres_scores_list.append(r['score_fenetres'])
            elif 'nb_fenetres' in r and r['nb_fenetres'] is not None:
                nb_fenetres = r['nb_fenetres']
                taille = r.get('taille_fenetres', 'moyennes')
                # Score de base : 2 points par fenêtre
                score_base = min(10, nb_fenetres * 2)
                # Bonus taille
                taille_bonus = {'grandes': 2, 'moyennes': 1, 'petites': 0}.get(taille, 1)
                fenetres_scores_list.append(min(10, score_base + taille_bonus))
        
        avg_fenetres_score = sum(fenetres_scores_list) / len(fenetres_scores_list) if fenetres_scores_list else 5
        
        # Score vue (20%) - basé sur vis-à-vis et vue dégagée
        vue_scores_list = []
        for r in results:
            if 'score_vue' in r and r['score_vue'] is not None:
                vue_scores_list.append(r['score_vue'])
            else:
                # Calculer depuis vis_a_vis et vue_degagee
                vis_a_vis = r.get('vis_a_vis', 'inconnu')
                vue_degagee = r.get('vue_degagee', False)
                if vue_degagee and vis_a_vis == 'aucun':
                    vue_scores_list.append(10)
                elif vue_degagee and vis_a_vis == 'leger':
                    vue_scores_list.append(8)
                elif not vue_degagee and vis_a_vis == 'important':
                    vue_scores_list.append(5)
                elif vis_a_vis == 'obstrué':
                    vue_scores_list.append(3)
                else:
                    # Fallback ancien format
                    vue_map = {'excellent': 10, 'bon': 7, 'moyen': 5, 'faible': 3}
                    vue_scores_list.append(vue_map.get(r.get('vue', 'moyen'), 5))
        
        avg_vue_score = sum(vue_scores_list) / len(vue_scores_list) if vue_scores_list else 5
        
        # Bonus balcon
        balcon_bonus = 0
        balcons = [r.get('balcon_visible', False) for r in results]
        if any(balcons):
            tailles_balcon = [r.get('taille_balcon', 'aucun') for r in results if r.get('balcon_visible', False)]
            if tailles_balcon:
                taille_balcon_moyenne = max(set(tailles_balcon), key=tailles_balcon.count)
                balcon_bonus_map = {'grand': 2, 'moyen': 1, 'petit': 0.5, 'aucun': 0}
                balcon_bonus = balcon_bonus_map.get(taille_balcon_moyenne, 0)
        
        # Calcul du score relatif pondéré
        score_pondere = (
            exposition_score * 0.3 +
            avg_luminosite_score * 0.3 +
            avg_fenetres_score * 0.2 +
            avg_vue_score * 0.2
        ) + balcon_bonus
        
        # Limiter à 10 max
        total_score = min(10, score_pondere)
        
        # Déterminer le tier
        if total_score >= 10:
            tier = 'tier1'
        elif total_score >= 7:
            tier = 'tier2'
        else:
            tier = 'tier3'
        
        # Calculer nb_fenetres moyen pour la justification
        nb_fenetres_list = [r.get('nb_fenetres', 0) for r in results if r.get('nb_fenetres') is not None]
        nb_fenetres_moyen = sum(nb_fenetres_list) / len(nb_fenetres_list) if nb_fenetres_list else 0
        
        # Construire la justification
        justification_parts = []
        if most_common_exposition:
            justification_parts.append(f"Exposition {most_common_exposition} détectée")
        if avg_luminosite_score >= 7:
            justification_parts.append("Luminosité élevée")
        if nb_fenetres_moyen > 0:
            justification_parts.append(f"{nb_fenetres_moyen:.1f} fenêtres en moyenne")
        if avg_vue_score >= 7:
            justification_parts.append("Vue dégagée")
        if balcon_bonus > 0:
            justification_parts.append("Balcon détecté")
        
        justification = f"Analyse de {len(results)} photos: {', '.join(justification_parts) if justification_parts else 'Informations limitées'}"
        
        return {
            'exposition': most_common_exposition,
            'score': int(total_score),
            'tier': tier,
            'justification': justification,
            'photos_analyzed': len(results),
            'luminosite': self._get_luminosite_level_from_score(avg_luminosite_score),
            'vue': self._get_vue_level_from_score(avg_vue_score),
            'details': {
                'exposition_score': exposition_score,
                'luminosite_score': avg_luminosite_score,
                'fenetres_score': avg_fenetres_score,
                'vue_score': avg_vue_score,
                'balcon_bonus': balcon_bonus,
                'nb_fenetres_moyen': nb_fenetres_moyen,
                'confidence': sum(r.get('confidence', 0.5) for r in results) / len(results)
            }
        }
    
    def _get_luminosite_level_from_score(self, score: float) -> str:
        """Convertit un score de luminosité en niveau"""
        if score >= 9:
            return 'excellent'
        elif score >= 7:
            return 'bon'
        elif score >= 5:
            return 'moyen'
        else:
            return 'faible'
    
    def _get_vue_level_from_score(self, score: float) -> str:
        """Convertit un score de vue en niveau"""
        if score >= 9:
            return 'excellent'
        elif score >= 7:
            return 'bon'
        elif score >= 5:
            return 'moyen'
        else:
            return 'faible'
    
    def analyze_photos_baignoire(self, photos_urls: List[str]) -> Dict:
        """Analyse les photos pour détecter la présence de baignoire"""
        if not photos_urls:
            return {
                'has_baignoire': None,
                'has_douche': None,
                'confidence': 0.0,
                'justification': 'Aucune photo disponible',
                'photos_analyzed': 0
            }
        
        try:
            # Analyser les premières photos (max 3 pour économiser)
            photos_to_analyze = photos_urls[:3]
            analysis_results = []
            
            for i, photo_url in enumerate(photos_to_analyze):
                print(f"   📸 Analyse photo baignoire {i+1}/{len(photos_to_analyze)}: {photo_url[:50]}...")
                result = self._analyze_single_photo_baignoire(photo_url)
                if result:
                    analysis_results.append(result)
            
            # Agréger les résultats
            return self._aggregate_baignoire_results(analysis_results)
            
        except Exception as e:
            return {
                'has_baignoire': None,
                'has_douche': None,
                'confidence': 0.0,
                'justification': f'Erreur analyse photos: {e}',
                'photos_analyzed': 0
            }
    
    def _analyze_single_photo_baignoire(self, photo_url: str) -> Optional[Dict]:
        """Analyse une photo pour détecter baignoire/douche avec cache"""
        # Vérifier le cache d'abord
        cached_result = self.cache.get('baignoire_photo', photo_url)
        if cached_result:
            return cached_result
        
        try:
            response = requests.get(photo_url, timeout=5)
            if response.status_code != 200:
                return None
            
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': """Analyse cette photo et détermine si une BAIGNOIRE ou une DOUCHE est visible.

Critères:
- Baignoire: baignoire visible (rectangulaire, ovale, ronde)
- Douche: cabine de douche, douche italienne, douche à l'italienne, pommeau de douche visible
- Ambigu: salle de bain visible mais pas de baignoire ni douche clairement identifiable

Réponds UNIQUEMENT au format JSON (pas de texte avant/après):
{
    "baignoire_visible": true|false,
    "douche_visible": true|false,
    "type_douche": "cabine|italienne|pommeau|null",
    "confidence": 0.0-1.0,
    "details": "description de ce que tu vois"
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
                'max_tokens': 300
            }
            
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code != 200:
                return None
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parser le JSON
            try:
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                analysis = json.loads(content)
                
                # Mettre en cache avant de retourner
                self.cache.set('baignoire_photo', photo_url, analysis)
                
                return analysis
            except json.JSONDecodeError:
                return None
                
        except Exception as e:
            return None
    
    def _aggregate_baignoire_results(self, results: List[Dict]) -> Dict:
        """Agrège les résultats de plusieurs photos pour baignoire"""
        if not results:
            return {
                'has_baignoire': None,
                'has_douche': None,
                'confidence': 0.0,
                'justification': 'Aucune photo analysée avec succès',
                'photos_analyzed': 0
            }
        
        # Compter les détections
        baignoires = [r.get('baignoire_visible', False) for r in results]
        douches = [r.get('douche_visible', False) for r in results]
        
        has_baignoire = any(baignoires)
        has_douche = any(douches) and not has_baignoire  # Si baignoire trouvée, on ignore douche
        
        # Confiance moyenne
        confidences = [r.get('confidence', 0.5) for r in results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        # Justification
        if has_baignoire:
            justification = f"Baignoire détectée sur {sum(baignoires)}/{len(results)} photos analysées"
        elif has_douche:
            justification = f"Douche détectée sur {sum(douches)}/{len(results)} photos analysées"
        else:
            justification = f"Aucune baignoire ni douche clairement visible sur {len(results)} photos"
        
        return {
            'has_baignoire': has_baignoire,
            'has_douche': has_douche,
            'confidence': avg_confidence,
            'justification': justification,
            'photos_analyzed': len(results)
        }
    
    def analyze_photos_cuisine(self, photos_urls: List[str]) -> Dict:
        """Analyse les photos pour détecter si la cuisine est ouverte"""
        if not photos_urls:
            return {
                'ouverte': None,
                'confidence': 0.0,
                'justification': 'Aucune photo disponible',
                'photos_analyzed': 0
            }
        
        try:
            # Analyser les premières photos (max 3)
            photos_to_analyze = photos_urls[:3]
            analysis_results = []
            
            for i, photo_url in enumerate(photos_to_analyze):
                print(f"   📸 Analyse photo cuisine {i+1}/{len(photos_to_analyze)}: {photo_url[:50]}...")
                result = self._analyze_single_photo_cuisine(photo_url)
                if result:
                    analysis_results.append(result)
            
            # Agréger les résultats
            return self._aggregate_cuisine_results(analysis_results)
            
        except Exception as e:
            return {
                'ouverte': None,
                'confidence': 0.0,
                'justification': f'Erreur analyse photos: {e}',
                'photos_analyzed': 0
            }
    
    def _analyze_single_photo_cuisine(self, photo_url: str) -> Optional[Dict]:
        """Analyse une photo pour détecter cuisine ouverte/fermée avec cache"""
        # Vérifier le cache d'abord
        cached_result = self.cache.get('cuisine_photo', photo_url)
        if cached_result:
            return cached_result
        
        try:
            response = requests.get(photo_url, timeout=5)
            if response.status_code != 200:
                return None
            
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': """Analyse cette photo et détermine si la CUISINE EST OUVERTE sur le salon/séjour.

Critères:
- Cuisine ouverte: cuisine visible depuis le salon/séjour, pas de séparation murale, cuisine intégrée au séjour
- Cuisine fermée: cuisine séparée par un mur, porte visible, espace clos
- Ambigu: cuisine non visible ou impossible à déterminer

Réponds UNIQUEMENT au format JSON (pas de texte avant/après):
{
    "cuisine_ouverte": true|false|null,
    "cuisine_visible": true|false,
    "separation_murale": true|false,
    "confidence": 0.0-1.0,
    "details": "description de ce que tu vois"
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
                'max_tokens': 300
            }
            
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code != 200:
                return None
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parser le JSON
            try:
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                analysis = json.loads(content)
                
                # Mettre en cache avant de retourner
                self.cache.set('cuisine_photo', photo_url, analysis)
                
                return analysis
            except json.JSONDecodeError:
                return None
                
        except Exception as e:
            return None
    
    def _aggregate_cuisine_results(self, results: List[Dict]) -> Dict:
        """Agrège les résultats de plusieurs photos pour cuisine"""
        if not results:
            return {
                'ouverte': None,
                'confidence': 0.0,
                'justification': 'Aucune photo analysée avec succès',
                'photos_analyzed': 0
            }
        
        # Compter les détections
        cuisines_ouvertes = [r.get('cuisine_ouverte', False) for r in results if r.get('cuisine_ouverte') is not None]
        cuisines_fermees = [r.get('cuisine_ouverte', True) == False for r in results if r.get('cuisine_ouverte') is not None]
        
        if not cuisines_ouvertes and not cuisines_fermees:
            return {
                'ouverte': None,
                'confidence': 0.0,
                'justification': 'Cuisine non visible sur les photos analysées',
                'photos_analyzed': len(results)
            }
        
        # Déterminer si ouverte (majorité)
        count_ouverte = sum(cuisines_ouvertes)
        count_fermee = sum(cuisines_fermees)
        
        if count_ouverte > count_fermee:
            ouverte = True
        elif count_fermee > count_ouverte:
            ouverte = False
        else:
            ouverte = None  # Ambigu
        
        # Confiance moyenne
        confidences = [r.get('confidence', 0.5) for r in results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        # Justification
        if ouverte is True:
            justification = f"Cuisine ouverte détectée sur {count_ouverte}/{len(results)} photos"
        elif ouverte is False:
            justification = f"Cuisine fermée détectée sur {count_fermee}/{len(results)} photos"
        else:
            justification = f"Résultat ambigu: {count_ouverte} ouvertes vs {count_fermee} fermées"
        
        return {
            'ouverte': ouverte,
            'confidence': avg_confidence,
            'justification': justification,
            'photos_analyzed': len(results)
        }
    
    def validate_text_with_photos(self, text_result: Dict, photo_result: Dict, criterion: str) -> Dict:
        """Valide un résultat textuel avec un résultat photo pour ajuster la confiance
        
        Args:
            text_result: Résultat de l'analyse textuelle
            photo_result: Résultat de l'analyse photo
            criterion: Type de critère ('exposition', 'baignoire', 'cuisine', 'style')
        
        Returns:
            Dict avec confiance ajustée et validation croisée
        """
        if not photo_result or photo_result.get('photos_analyzed', 0) == 0:
            # Pas de photos → utiliser texte uniquement
            return {
                'final_result': text_result,
                'confidence_adjusted': text_result.get('confidence', text_result.get('confiance_globale', 0.5)),
                'validation_status': 'text_only',
                'cross_validation': None
            }
        
        text_confidence = text_result.get('confidence', text_result.get('confiance_globale', 0.5))
        photo_confidence = photo_result.get('confidence', 0.5)
        
        # Vérifier la cohérence selon le critère
        is_consistent = self._check_consistency(text_result, photo_result, criterion)
        
        if is_consistent:
            # Cohérent → augmenter la confiance
            # Moyenne pondérée: 60% texte + 40% photo (texte plus fiable généralement)
            adjusted_confidence = min(1.0, (text_confidence * 0.6 + photo_confidence * 0.4) + 0.1)
            validation_status = 'validated'
        else:
            # Incohérent → réduire la confiance
            adjusted_confidence = max(0.3, (text_confidence + photo_confidence) / 2 - 0.2)
            validation_status = 'conflict'
        
        return {
            'final_result': text_result,
            'confidence_adjusted': adjusted_confidence,
            'validation_status': validation_status,
            'cross_validation': {
                'text_confidence': text_confidence,
                'photo_confidence': photo_confidence,
                'is_consistent': is_consistent,
                'photo_result': photo_result
            }
        }
    
    def _check_consistency(self, text_result: Dict, photo_result: Dict, criterion: str) -> bool:
        """Vérifie la cohérence entre texte et photo"""
        if criterion == 'exposition':
            text_expo = text_result.get('exposition')
            photo_expo = photo_result.get('exposition')
            # Cohérent si même exposition ou si l'un est None (pas de contradiction)
            return text_expo == photo_expo or text_expo is None or photo_expo is None
        
        elif criterion == 'baignoire':
            text_has = text_result.get('has_baignoire')
            photo_has = photo_result.get('has_baignoire')
            return text_has == photo_has or text_has is None or photo_has is None
        
        elif criterion == 'cuisine':
            text_ouverte = text_result.get('ouverte')
            photo_ouverte = photo_result.get('ouverte')
            return text_ouverte == photo_ouverte or text_ouverte is None or photo_ouverte is None
        
        elif criterion == 'style':
            text_style = text_result.get('type', text_result.get('style', ''))
            photo_style = photo_result.get('type', photo_result.get('style', ''))
            # Normaliser pour comparaison
            text_style_norm = text_style.lower() if text_style else ''
            photo_style_norm = photo_style.lower() if photo_style else ''
            return text_style_norm == photo_style_norm or not text_style_norm or not photo_style_norm
        
        return True  # Par défaut, considérer cohérent

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
