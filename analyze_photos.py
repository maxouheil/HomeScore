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
from io import BytesIO
from PIL import Image
import numpy as np
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
            # Si le cache n'a pas brightness_value, le calculer maintenant
            if cached_result.get('brightness_value') is None:
                try:
                    response = requests.get(photo_url, timeout=5)
                    if response.status_code == 200:
                        brightness = self._calculate_photo_brightness(response.content)
                        cached_result['brightness_value'] = brightness
                except:
                    pass
            return cached_result
        
        try:
            # Télécharger l'image
            response = requests.get(photo_url, timeout=5)
            if response.status_code != 200:
                print(f"   ❌ Erreur téléchargement: {response.status_code}")
                return None
            
            # Sauvegarder le contenu pour calcul brightness
            image_content = response.content
            
            # Encoder en base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
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
                                'text': """Analyse cette photo d'appartement pour déterminer la luminosité relative.

## TÂCHE PRINCIPALE : Évaluer la luminosité globale de la photo

### INDICES À DÉTECTER :

- Luminosité relative (très_lumineux, lumineux, moyen, faible)
- Balcon/Terrasse visible (optionnel)

Réponds UNIQUEMENT au format JSON (pas de texte avant/après):
{
    "luminosite_relative": "tres_lumineux|lumineux|moyen|faible",
    "score_luminosite": 0-10,
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
                'max_tokens': 800  # Augmenté pour les indices précis détaillés
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
                # Nettoyer le contenu (enlever les blocs markdown)
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                analysis = json.loads(content)
                
                # Calculer la luminosité moyenne de la photo
                brightness = self._calculate_photo_brightness(image_content)
                analysis['brightness_value'] = brightness
                
                print(f"   ✅ Photo analysée: luminosité {analysis.get('luminosite_relative', 'N/A')} (brightness: {brightness:.2f})")
                
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
    
    def _calculate_photo_brightness(self, image_data: bytes) -> float:
        """Calcule la luminosité moyenne d'une photo (0.0 = sombre, 1.0 = très lumineux)"""
        try:
            # Vérifier que ce sont bien des bytes
            if not isinstance(image_data, bytes):
                return 0.5
            
            # Ouvrir l'image depuis les bytes
            image_bytes_io = BytesIO(image_data)
            image = Image.open(image_bytes_io)
            
            # Convertir en RGB si nécessaire
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Redimensionner si trop grande (pour performance)
            max_size = 1000
            if image.size[0] > max_size or image.size[1] > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convertir en numpy array
            img_array = np.array(image)
            
            # Vérifier les dimensions
            if len(img_array.shape) != 3 or img_array.shape[2] != 3:
                return 0.5
            
            # Calculer la luminance moyenne (formule standard: 0.299*R + 0.587*G + 0.114*B)
            # Normaliser entre 0 et 1
            luminance = (0.299 * img_array[:, :, 0] + 
                        0.587 * img_array[:, :, 1] + 
                        0.114 * img_array[:, :, 2]) / 255.0
            
            # Moyenne de la luminance
            brightness = float(np.mean(luminance))
            
            return brightness
        except Exception as e:
            print(f"   ⚠️ Erreur calcul brightness: {e}")
            import traceback
            traceback.print_exc()
            return 0.5  # Valeur par défaut si erreur
    
    def _aggregate_photo_results(self, results: List[Dict]) -> Dict:
        """Agrège les résultats de plusieurs photos avec luminosité moyenne
        
        NOUVELLE LOGIQUE:
        - Calcule la luminosité moyenne des photos (brightness)
        - Utilise la luminosité IA si disponible, sinon utilise brightness_value
        - Score basé sur luminosité moyenne
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
        
        # Calculer la luminosité moyenne des photos
        brightness_values = [r.get('brightness_value') for r in results if r.get('brightness_value') is not None]
        avg_brightness = sum(brightness_values) / len(brightness_values) if brightness_values else 0.5
        
        # Convertir brightness (0.0-1.0) en score (0-10)
        # Échelle: <0.3 = sombre (3), 0.3-0.5 = moyen (5), 0.5-0.7 = lumineux (7), >0.7 = très lumineux (10)
        if avg_brightness < 0.3:
            brightness_score = 3
            brightness_level = 'faible'
        elif avg_brightness < 0.5:
            brightness_score = 5
            brightness_level = 'moyen'
        elif avg_brightness < 0.7:
            brightness_score = 7
            brightness_level = 'bon'
        else:
            brightness_score = 10
            brightness_level = 'excellent'
        
        # Utiliser aussi les scores IA de luminosité si disponibles (pour combiner)
        luminosite_scores_list = []
        for r in results:
            if 'score_luminosite' in r and r['score_luminosite'] is not None:
                luminosite_scores_list.append(r['score_luminosite'])
            elif 'luminosite_relative' in r:
                luminosite_map = {'tres_lumineux': 10, 'lumineux': 7, 'moyen': 5, 'faible': 3}
                luminosite_scores_list.append(luminosite_map.get(r['luminosite_relative'], 5))
        
        # Combiner brightness_score et scores IA (moyenne pondérée: 70% brightness, 30% IA)
        if luminosite_scores_list:
            avg_ia_luminosite = sum(luminosite_scores_list) / len(luminosite_scores_list)
            combined_luminosite_score = brightness_score * 0.7 + avg_ia_luminosite * 0.3
        else:
            combined_luminosite_score = brightness_score
        
        # Score total basé uniquement sur la luminosité moyenne
        total_score = min(10, combined_luminosite_score)
        
        # Déterminer le tier
        if total_score >= 9:
            tier = 'tier1'
        elif total_score >= 7:
            tier = 'tier2'
        else:
            tier = 'tier3'
        
        # Construire la justification
        justification_parts = []
        justification_parts.append(f"Luminosité moyenne: {avg_brightness:.2f} ({brightness_level})")
        if brightness_values:
            justification_parts.append(f"{len(brightness_values)} photos analysées")
        
        justification = f"Analyse de {len(results)} photos: {', '.join(justification_parts)}"
        
        return {
            'exposition': None,  # Plus de détection d'exposition depuis photos
            'score': int(total_score),
            'tier': tier,
            'justification': justification,
            'photos_analyzed': len(results),
            'luminosite': brightness_level,
            'vue': 'inconnue',  # Plus de détection de vue
            'details': {
                'brightness_value': avg_brightness,
                'brightness_score': brightness_score,
                'luminosite_score': combined_luminosite_score,
                'confidence': sum(r.get('confidence', 0.5) for r in results) / len(results) if results else 0.5
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
                'photos_analyzed': 0,
                'detected_photos': []
            }
        
        try:
            # Analyser les top 10 photos (comme pour la cuisine)
            photos_to_analyze = photos_urls[:10]
            analysis_results = []
            
            for i, photo_url in enumerate(photos_to_analyze):
                print(f"   📸 Analyse photo baignoire {i+1}/{len(photos_to_analyze)}: {photo_url[:50]}...")
                result = self._analyze_single_photo_baignoire(photo_url)
                if result:
                    # Ajouter le numéro de la photo (1-indexed)
                    result['photo_number'] = i + 1
                    analysis_results.append(result)
            
            # Agréger les résultats
            return self._aggregate_baignoire_results(analysis_results)
            
        except Exception as e:
            return {
                'has_baignoire': None,
                'has_douche': None,
                'confidence': 0.0,
                'justification': f'Erreur analyse photos: {e}',
                'photos_analyzed': 0,
                'detected_photos': []
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
                'photos_analyzed': 0,
                'detected_photos': []
            }
        
        # Compter les détections avec numéros d'images
        baignoires_photos = []
        douches_photos = []
        
        for r in results:
            photo_number = r.get('photo_number', 0)
            baignoire_visible = r.get('baignoire_visible', False)
            douche_visible = r.get('douche_visible', False)
            
            if baignoire_visible:
                baignoires_photos.append(photo_number)
            elif douche_visible:
                douches_photos.append(photo_number)
        
        has_baignoire = len(baignoires_photos) > 0
        has_douche = len(douches_photos) > 0 and not has_baignoire  # Si baignoire trouvée, on ignore douche
        
        # Confiance moyenne
        confidences = [r.get('confidence', 0.5) for r in results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        # Déterminer les photos détectées
        if has_baignoire:
            detected_photos = sorted(baignoires_photos)
            justification = f"Baignoire détectée sur {len(baignoires_photos)}/{len(results)} photos analysées"
        elif has_douche:
            detected_photos = sorted(douches_photos)
            justification = f"Douche détectée sur {len(douches_photos)}/{len(results)} photos analysées"
        else:
            detected_photos = []
            justification = f"Aucune baignoire ni douche clairement visible sur {len(results)} photos"
        
        return {
            'has_baignoire': has_baignoire,
            'has_douche': has_douche,
            'confidence': avg_confidence,
            'justification': justification,
            'photos_analyzed': len(results),
            'detected_photos': detected_photos
        }
    
    def analyze_photos_cuisine(self, photos_urls: List[str]) -> Dict:
        """Analyse les photos pour détecter si la cuisine est ouverte"""
        if not photos_urls:
            return {
                'ouverte': None,
                'confidence': 0.0,
                'justification': 'Aucune photo disponible',
                'photos_analyzed': 0,
                'detected_photos': []
            }
        
        try:
            # Analyser les 5 premières photos
            photos_to_analyze = photos_urls[:5]
            analysis_results = []
            
            for i, photo_url in enumerate(photos_to_analyze):
                print(f"   📸 Analyse photo cuisine {i+1}/{len(photos_to_analyze)}: {photo_url[:50]}...")
                result = self._analyze_single_photo_cuisine(photo_url)
                if result:
                    # Ajouter le numéro de la photo (1-indexed)
                    result['photo_number'] = i + 1
                    analysis_results.append(result)
            
            # Agréger les résultats
            return self._aggregate_cuisine_results(analysis_results)
            
        except Exception as e:
            return {
                'ouverte': None,
                'confidence': 0.0,
                'justification': f'Erreur analyse photos: {e}',
                'photos_analyzed': 0,
                'detected_photos': []
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
                'photos_analyzed': 0,
                'detected_photos': []
            }
        
        # Compter les détections avec numéros d'images
        cuisines_ouvertes = []
        cuisines_fermees = []
        
        for r in results:
            cuisine_ouverte = r.get('cuisine_ouverte')
            photo_number = r.get('photo_number', 0)
            
            if cuisine_ouverte is True:
                cuisines_ouvertes.append(photo_number)
            elif cuisine_ouverte is False:
                cuisines_fermees.append(photo_number)
        
        if not cuisines_ouvertes and not cuisines_fermees:
            return {
                'ouverte': None,
                'confidence': 0.0,
                'justification': 'Cuisine non visible sur les photos analysées',
                'photos_analyzed': len(results),
                'detected_photos': []
            }
        
        # Déterminer si ouverte (majorité)
        count_ouverte = len(cuisines_ouvertes)
        count_fermee = len(cuisines_fermees)
        
        if count_ouverte > count_fermee:
            ouverte = True
            detected_photos = sorted(cuisines_ouvertes)
        elif count_fermee > count_ouverte:
            ouverte = False
            detected_photos = sorted(cuisines_fermees)
        else:
            ouverte = None  # Ambigu
            detected_photos = sorted(cuisines_ouvertes + cuisines_fermees)
        
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
            'photos_analyzed': len(results),
            'detected_photos': detected_photos
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
            # Plus de détection d'exposition depuis photos, on compare la luminosité
            text_luminosite = text_result.get('luminosite', 'inconnue')
            photo_luminosite = photo_result.get('luminosite', 'inconnue')
            
            # Mapping des niveaux de luminosité pour comparaison
            luminosite_map = {
                'excellent': 10,
                'bon': 7,
                'moyen': 5,
                'faible': 3,
                'inconnue': 5  # Par défaut
            }
            
            text_score = luminosite_map.get(text_luminosite, 5)
            photo_score = luminosite_map.get(photo_luminosite, 5)
            
            # Cohérent si différence de score <= 2 points
            return abs(text_score - photo_score) <= 2
        
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
