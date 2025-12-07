#!/usr/bin/env python3
"""
Module d'extraction de la présence de baignoire
Logique:
1. Main: analyse texte (description + caractéristiques)
2. Fallback: analyse images avec OpenAI Vision pour trouver douche ou baignoire
3. Si douche: BAD / Si baignoire: GOOD
"""

import re
import json
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import requests

# Imports conditionnels pour éviter les crashes
try:
    from analyze_photos import PhotoAnalyzer
except Exception as e:
    print(f"⚠️ Erreur lors de l'import de PhotoAnalyzer: {e}")
    PhotoAnalyzer = None

try:
    from analyze_text_ai import TextAIAnalyzer
except Exception as e:
    print(f"⚠️ Erreur lors de l'import de TextAIAnalyzer: {e}")
    TextAIAnalyzer = None

try:
    from cache_api import get_cache
except Exception as e:
    print(f"⚠️ Erreur lors de l'import de cache_api: {e}")
    def get_cache():
        return {}

class BaignoireExtractor:
    """Extracteur de baignoire pour les appartements"""
    
    def __init__(self):
        self.photo_analyzer = PhotoAnalyzer() if PhotoAnalyzer else None
        self.text_ai_analyzer = TextAIAnalyzer() if TextAIAnalyzer else None
        self.use_ai_analysis = True  # Activer l'analyse IA pour éviter faux positifs
        try:
            self.cache = get_cache()  # Cache partagé (photo_analyzer a déjà son propre cache)
        except:
            self.cache = {}
        
        # Mots-clés baignoire
        self.baignoire_keywords = [
            'baignoire', 'baignoir', 'salle de bain', 'salle de bains',
            'sdb', 'bain', 'bath', 'bathtub'
        ]
        
        # Mots-clés douche
        self.douche_keywords = [
            'douche', 'cabine de douche', 'douche italienne', 'douche à l\'italienne',
            'shower', 'salle d\'eau', 'salle d\'eau'
        ]
    
    def extract_baignoire_textuelle(self, description: str, caracteristiques: str = "") -> Dict:
        """Extrait la présence de baignoire depuis le texte avec analyse IA intelligente"""
        try:
            # Essayer d'abord l'analyse IA si disponible
            if self.use_ai_analysis and self.text_ai_analyzer and hasattr(self.text_ai_analyzer, 'openai_api_key') and self.text_ai_analyzer.openai_api_key:
                ai_result = self.text_ai_analyzer.analyze_baignoire(description, caracteristiques)
                
                if ai_result.get('available', False):
                    baignoire_presente = ai_result.get('baignoire_presente')
                    douche_seule = ai_result.get('douche_seule', False)
                    ai_confidence = ai_result.get('confiance', 0)
                    ai_justification = ai_result.get('justification', '')
                    
                    if baignoire_presente is True:
                        return {
                            'has_baignoire': True,
                            'has_douche': False,
                            'justification': f"Analyse IA: {ai_justification}",
                            'tier': 'tier1',
                            'score': 10,
                            'confidence': int(ai_confidence * 100),
                            'found_in_description': True,
                            'found_in_caracteristiques': False,
                            'method': 'ai_analysis'
                        }
                    elif douche_seule or baignoire_presente is False:
                        return {
                            'has_baignoire': False,
                            'has_douche': True,
                            'justification': f"Analyse IA: {ai_justification}",
                            'tier': 'tier3',
                            'score': 0,
                            'confidence': int(ai_confidence * 100),
                            'found_in_description': True,
                            'found_in_caracteristiques': False,
                            'method': 'ai_analysis'
                        }
                    # Si null (ambigu), continuer avec recherche mots-clés
            
            # Fallback: Recherche par mots-clés (méthode originale)
            description_lower = description.lower()
            caracteristiques_lower = caracteristiques.lower()
            
            baignoire_trouvee = False
            douche_trouvee = False
            justification = "Information non spécifiée dans le texte"
            tier = 'tier3'  # Par défaut BAD
            score = 0
            confidence = 0
            found_in_description = False
            found_in_caracteristiques = False
            
            # Chercher baignoire dans la DESCRIPTION d'abord (plus fiable)
            for keyword in self.baignoire_keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, description_lower, re.IGNORECASE):
                    baignoire_trouvee = True
                    found_in_description = True
                    justification = f"Baignoire détectée dans la description (mot-clé: '{keyword}')"
                    tier = 'tier1'
                    score = 10  # GOOD
                    confidence = 90  # Haute confiance si dans description
                    break
            
            # Si pas dans description, chercher dans caractéristiques (moins fiable)
            if not baignoire_trouvee:
                for keyword in self.baignoire_keywords:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, caracteristiques_lower, re.IGNORECASE):
                        baignoire_trouvee = True
                        found_in_caracteristiques = True
                        justification = f"Baignoire mentionnée dans les caractéristiques (moins fiable - nécessite vérification photos)"
                        tier = 'tier1'
                        score = 10  # GOOD
                        confidence = 50  # Confiance moyenne si seulement dans caractéristiques
                        break
            
            # Si pas de baignoire, chercher douche dans DESCRIPTION d'abord
            if not baignoire_trouvee:
                for keyword in self.douche_keywords:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, description_lower, re.IGNORECASE):
                        douche_trouvee = True
                        found_in_description = True
                        justification = f"Douche détectée dans la description (mot-clé: '{keyword}')"
                        tier = 'tier3'
                        score = 0  # BAD
                        confidence = 90
                        break
            
            # Si pas dans description, chercher douche dans caractéristiques
            if not baignoire_trouvee and not douche_trouvee:
                for keyword in self.douche_keywords:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, caracteristiques_lower, re.IGNORECASE):
                        douche_trouvee = True
                        found_in_caracteristiques = True
                        justification = f"Douche mentionnée dans les caractéristiques (moins fiable - nécessite vérification photos)"
                        tier = 'tier3'
                        score = 0  # BAD
                        confidence = 50
                        break
            
            return {
                'has_baignoire': baignoire_trouvee,
                'has_douche': douche_trouvee,
                'detected_from_text': baignoire_trouvee or douche_trouvee,
                'found_in_description': found_in_description,
                'found_in_caracteristiques': found_in_caracteristiques,
                'score': score,
                'tier': tier,
                'justification': justification,
                'confidence': confidence,
                'needs_photo_verification': found_in_caracteristiques and not found_in_description  # Si seulement dans caractéristiques, vérifier avec photos
            }
            
        except Exception as e:
            return {
                'has_baignoire': False,
                'has_douche': False,
                'detected_from_text': False,
                'found_in_description': False,
                'found_in_caracteristiques': False,
                'score': 0,
                'tier': 'tier3',
                'justification': f"Erreur extraction: {e}",
                'confidence': 0,
                'needs_photo_verification': True
            }
    
    def extract_baignoire_photos(self, photos_urls: List[str], style_analysis: Dict = None) -> Dict:
        """Extrait la présence de baignoire depuis les photos avec analyse d'images
        
        Si style_analysis est fourni et contient des données baignoire, les utilise directement
        pour éviter de refaire des appels API coûteux.
        """
        # PRIORITÉ 1: Vérifier si style_analysis contient déjà les données baignoire
        if style_analysis:
            baignoire_data = style_analysis.get('baignoire', {})
            if baignoire_data and baignoire_data.get('has_baignoire') is not None:
                print(f"   ✅ Utilisation des données baignoire depuis style_analysis (cache)")
                has_baignoire = baignoire_data.get('has_baignoire', False)
                has_douche = baignoire_data.get('has_douche', False)
                confidence = baignoire_data.get('confidence', 0)
                
                # Convertir en format attendu
                tier = 'tier1' if has_baignoire else ('tier3' if has_douche else 'tier2')
                score = 10 if has_baignoire else (0 if has_douche else 5)
                
                return {
                    'has_baignoire': has_baignoire,
                    'has_douche': has_douche,
                    'score': score,
                    'tier': tier,
                    'justification': baignoire_data.get('details', 'Baignoire détectée depuis style_analysis'),
                    'photos_analyzed': style_analysis.get('photos_analyzed', 0),
                    'confidence': int(confidence * 100),
                    'method': 'style_analysis_cache'
                }
        
        if not photos_urls:
            return {
                'has_baignoire': False,
                'has_douche': False,
                'score': 0,
                'tier': 'tier3',
                'justification': 'Aucune photo disponible',
                'photos_analyzed': 0,
                'confidence': 0
            }
        
        try:
            # PRIORITÉ 2: Analyser les photos (fallback si pas de style_analysis)
            # Analyser les premières photos (max 3 pour éviter les timeouts, limite stricte)
            photos_to_analyze = photos_urls[:3]
            analysis_results = []
            
            for i, photo_url in enumerate(photos_to_analyze):
                print(f"   📸 Analyse photo {i+1}/{len(photos_to_analyze)} pour baignoire: {photo_url[:50]}...")
                try:
                    result = self._analyze_single_photo_baignoire(photo_url)
                    if result:
                        analysis_results.append(result)
                except Exception as e:
                    print(f"   ⚠️ Erreur sur photo {i+1}, passage à la suivante: {e}")
                    continue
            
            # Agréger les résultats
            return self._aggregate_photo_results_baignoire(analysis_results)
            
        except Exception as e:
            return {
                'has_baignoire': False,
                'has_douche': False,
                'score': 0,
                'tier': 'tier3',
                'justification': f'Erreur analyse photos: {e}',
                'photos_analyzed': 0,
                'confidence': 0
            }
    
    def _analyze_single_photo_baignoire(self, photo_url: str) -> Optional[Dict]:
        """Analyse une photo individuelle pour détecter baignoire ou douche"""
        try:
            # Télécharger l'image
            import requests
            import base64
            
            response = requests.get(photo_url, timeout=5)
            if response.status_code != 200:
                print(f"   ❌ Erreur téléchargement: {response.status_code}")
                return None
            
            # Encoder en base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            
            # Appel à OpenAI Vision
            if not self.photo_analyzer:
                return None
                
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            headers = {
                'Authorization': f'Bearer {self.photo_analyzer.openai_api_key}',
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
                                'text': """Analyse cette photo d'appartement pour détecter la présence d'une baignoire ou d'une douche dans la salle de bain.

CRITÈRES D'ANALYSE:
1. BAIGNOIRE:
   - Détecte si une baignoire est visible dans l'image
   - Une baignoire est un grand récipient pour se baigner, généralement rectangulaire/ovale, plus grand qu'une douche
   - Peut être encastrée ou indépendante

2. DOUCHE:
   - Détecte si seulement une douche est visible (cabine de douche, douche italienne)
   - Une douche est un espace plus petit avec un pommeau de douche ou une cabine
   - Pas de baignoire = juste une douche

3. AUCUN:
   - Si ce n'est pas une photo de salle de bain
   - Si on ne voit ni baignoire ni douche clairement

Réponds au format JSON STRICT:
{
    "has_baignoire": true|false,
    "has_douche": true|false,
    "is_bathroom": true|false,
    "confidence": 0.0-1.0,
    "details": "description détaillée de ce que tu observes (baignoire, douche, ou autre)"
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
                f"{self.photo_analyzer.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"   ❌ Erreur API OpenAI: {response.status_code}")
                return None
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Nettoyer le contenu JSON
            json_text = content.strip()
            if json_text.startswith('```json'):
                json_text = json_text.replace('```json', '').replace('```', '').strip()
            elif json_text.startswith('```'):
                json_text = json_text.replace('```', '').strip()
            
            # Parser le JSON
            try:
                analysis = json.loads(json_text)
                print(f"   ✅ Photo analysée: baignoire={analysis.get('has_baignoire', False)}, douche={analysis.get('has_douche', False)}")
                return analysis
            except json.JSONDecodeError as e:
                print(f"   ❌ Erreur parsing JSON: {e}")
                print(f"   📝 Contenu reçu: {json_text[:200]}...")
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
    
    def _aggregate_photo_results_baignoire(self, results: List[Dict]) -> Dict:
        """Agrège les résultats de plusieurs photos pour déterminer baignoire vs douche"""
        if not results:
            return {
                'has_baignoire': False,
                'has_douche': False,
                'score': 0,
                'tier': 'tier3',
                'justification': 'Aucune photo analysée avec succès',
                'photos_analyzed': 0,
                'confidence': 0
            }
        
        # Compter les détections
        baignoire_count = sum(1 for r in results if r.get('has_baignoire', False) and r.get('is_bathroom', True))
        douche_count = sum(1 for r in results if r.get('has_douche', False) and not r.get('has_baignoire', False) and r.get('is_bathroom', True))
        bathroom_count = sum(1 for r in results if r.get('is_bathroom', False))
        
        # Calculer la confiance moyenne
        avg_confidence = sum(r.get('confidence', 0.5) for r in results) / len(results) if results else 0.5
        confidence_rounded = round(avg_confidence * 100 / 10) * 10  # Arrondir à 10%
        
        # Déterminer le résultat
        # Si au moins une photo montre une baignoire -> GOOD
        # Si seulement douche (pas de baignoire) -> BAD
        # Si pas de salle de bain visible -> BAD par défaut
        
        has_baignoire = baignoire_count > 0
        has_douche_only = douche_count > 0 and baignoire_count == 0
        
        if has_baignoire:
            tier = 'tier1'
            score = 10  # GOOD
            justification = f"Baignoire détectée dans {baignoire_count} photo(s)"
        elif has_douche_only:
            tier = 'tier3'
            score = 0  # BAD
            justification = f"Douche détectée dans {douche_count} photo(s) (pas de baignoire)"
        elif bathroom_count > 0:
            # Salle de bain visible mais pas clair ce qui est dedans
            tier = 'tier3'
            score = 0  # BAD par défaut (on suppose douche si pas de baignoire claire)
            justification = f"Salle de bain visible mais baignoire non détectée ({bathroom_count} photo(s))"
        else:
            # Pas de salle de bain visible
            tier = 'tier3'
            score = 0  # BAD par défaut
            justification = "Aucune salle de bain visible dans les photos analysées"
        
        return {
            'has_baignoire': has_baignoire,
            'has_douche': has_douche_only,
            'score': score,
            'tier': tier,
            'justification': justification,
            'photos_analyzed': len(results),
            'confidence': confidence_rounded,
            'details': {
                'baignoire_count': baignoire_count,
                'douche_count': douche_count,
                'bathroom_count': bathroom_count,
                'photo_results': results
            }
        }
    
    def extract_baignoire_complete(self, description: str, caracteristiques: str = "", photos_urls: List[str] = None, style_analysis: Dict = None) -> Dict:
        """Extrait la présence de baignoire avec validation croisée texte + photos
        
        Args:
            description: Description de l'appartement
            caracteristiques: Caractéristiques de l'appartement
            photos_urls: Liste des URLs des photos
            style_analysis: Analyse de style existante (optionnel, pour éviter les appels API)
        """
        # Phase 1: Analyse textuelle IA
        text_result = self.extract_baignoire_textuelle(description, caracteristiques)
        
        # Phase 2: Analyse photos si disponibles
        photo_result = None
        if photos_urls:
            # Utiliser extract_baignoire_photos qui vérifie d'abord style_analysis
            try:
                photo_result = self.extract_baignoire_photos(photos_urls, style_analysis=style_analysis)
            except Exception as e:
                print(f"⚠️ Erreur analyse photos baignoire: {e}")
                photo_result = None
        
        # Phase 3: Validation croisée texte + photos
        validation = None
        if photo_result and photo_result.get('photos_analyzed', 0) > 0 and self.photo_analyzer:
            try:
                validation = self.photo_analyzer.validate_text_with_photos(text_result, photo_result, 'baignoire')
            except Exception as e:
                print(f"⚠️ Erreur validation croisée: {e}")
                validation = {'validation_status': 'text_only', 'confidence_adjusted': text_result.get('confidence', 0) / 100}
        
        if validation:
            # Utiliser la confiance ajustée
            confiance_ajustee = validation.get('confidence_adjusted', text_result.get('confidence', 0) / 100)
            validation_status = validation.get('validation_status', 'text_only')
            
            # Construire résultat final enrichi
            final_result = text_result.copy()
            
            # Vérifier si le texte a un résultat valide (pas None) = mentionné
            text_has_result = text_result.get('has_baignoire') is not None or text_result.get('has_douche') is not None
            
            # Vérifier si les photos ont détecté quelque chose
            photo_has_result = photo_result.get('has_baignoire') is not None or photo_result.get('has_douche') is not None
            
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
                    final_result['confidence'] = int(confiance_finale * 100)
                    if photo_has_result:
                        final_result['justification'] += f" | ✅ Validé par photos (confiance: {confiance_finale:.0%})"
                    else:
                        final_result['justification'] += f" | (confiance: {confiance_finale:.0%})"
                else:
                    # Texte n'a pas de résultat → utiliser résultat photos
                    final_result = {
                        'has_baignoire': photo_result.get('has_baignoire', False),
                        'has_douche': photo_result.get('has_douche', False),
                        'detected_from_text': False,
                        'found_in_description': False,
                        'found_in_caracteristiques': False,
                        'score': photo_result.get('score', 0),
                        'tier': photo_result.get('tier', 'tier3'),
                        'justification': f"{photo_result.get('justification', '')} | ✅ Détecté par photos (confiance: {confiance_finale:.0%})",
                        'confidence': int(confiance_finale * 100),
                        'photos_analyzed': photo_result.get('photos_analyzed', 0)
                    }
            elif validation_status == 'conflict':
                # Incohérent → préférer photos si plus confiantes OU si texte n'a pas de résultat
                # En cas de conflit, utiliser quand même la règle de confiance simple
                if not text_has_result or (photo_has_result and not text_has_result):
                    # Photos disponibles OU texte sans résultat → utiliser résultat photos
                    final_result = {
                        'has_baignoire': photo_result.get('has_baignoire', False),
                        'has_douche': photo_result.get('has_douche', False),
                        'detected_from_text': False,
                        'found_in_description': False,
                        'found_in_caracteristiques': False,
                        'score': photo_result.get('score', 0),
                        'tier': photo_result.get('tier', 'tier3'),
                        'justification': f"{photo_result.get('justification', '')} | ⚠️ Conflit avec texte, photos prioritaires (confiance: {confiance_finale:.0%})",
                        'confidence': int(confiance_finale * 100),
                        'photos_analyzed': photo_result.get('photos_analyzed', 0)
                    }
                else:
                    # Texte disponible → garder texte avec confiance calculée
                    final_result['confidence'] = int(confiance_finale * 100)
                    final_result['justification'] += f" | ⚠️ Conflit avec photos (confiance: {confiance_finale:.0%})"
            
            # Ajouter les infos de validation et les numéros d'images détectées
            # Structurer comme pour la cuisine avec photo_validation.photo_result
            if 'details' not in final_result:
                final_result['details'] = {}
            
            # Créer photo_result pour compatibilité avec le formatage cuisine
            photo_result_formatted = {
                'has_baignoire': photo_result.get('has_baignoire'),
                'has_douche': photo_result.get('has_douche'),
                'detected_photos': photo_result.get('detected_photos', [])
            }
            
            final_result['details']['photo_validation'] = {
                'cross_validation': validation.get('cross_validation') if validation else None,
                'photo_result': photo_result_formatted
            }
            final_result['details']['validation_status'] = validation_status
            final_result['detected_photos'] = photo_result.get('detected_photos', [])
            
            return final_result
        
        # Pas de photos → retourner résultat textuel uniquement avec confiance 80% si mentionné
        if text_result.get('has_baignoire') is not None or text_result.get('has_douche') is not None:
            # Mentionné dans le texte seulement → confiance 80%
            text_result['confidence'] = 80
        return text_result
    
    def extract_baignoire_ultimate(self, apartment_data: Dict) -> Dict:
        """
        Extrait la présence de baignoire avec logique complète :
        1. Analyse texte (description + caractéristiques)
        2. Si pas trouvé → fallback sur analyse images
        3. Si douche: BAD / Si baignoire: GOOD
        
        Avec timeout global de 30 secondes pour éviter les blocages
        """
        description = apartment_data.get('description', '')
        caracteristiques = apartment_data.get('caracteristiques', '')
        photos = apartment_data.get('photos', [])
        style_analysis = apartment_data.get('style_analysis')  # Utiliser style_analysis si disponible
        
        # Extraire les URLs des photos
        photos_urls = []
        if photos:
            if isinstance(photos[0], dict):
                photos_urls = [p.get('url', '') for p in photos if p.get('url')]
            else:
                photos_urls = [p for p in photos if p]
        
        # Wrapper pour exécuter avec timeout
        def _extract_with_timeout():
            return self.extract_baignoire_complete(description, caracteristiques, photos_urls, style_analysis=style_analysis)
        
        # Exécuter avec timeout global de 30 secondes
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_extract_with_timeout)
                result = future.result(timeout=30)
                return result
        except FutureTimeoutError:
            print(f"   ⏱️ Timeout global (30s) pour l'extraction de baignoire")
            # Retourner résultat basé uniquement sur texte (rapide)
            text_result = self.extract_baignoire_textuelle(description, caracteristiques)
            return {
                'has_baignoire': text_result.get('has_baignoire', False),
                'has_douche': text_result.get('has_douche', False),
                'score': text_result.get('score', 0),
                'tier': text_result.get('tier', 'tier3'),
                'justification': f"{text_result.get('justification', '')} (analyse photos timeout)",
                'photos_analyzed': 0,
                'confidence': text_result.get('confidence', 0)
            }
        except Exception as e:
            print(f"   ❌ Erreur extraction baignoire: {e}")
            # Fallback sur texte uniquement
            text_result = self.extract_baignoire_textuelle(description, caracteristiques)
            return text_result


def test_baignoire_extraction():
    """Test de l'extraction de baignoire"""
    extractor = BaignoireExtractor()
    
    # Test avec différentes descriptions
    test_cases = [
        {
            'description': 'Appartement avec salle de bain équipée d\'une baignoire',
            'caracteristiques': 'Balcon, ascenseur'
        },
        {
            'description': 'Appartement moderne avec salle d\'eau avec douche italienne',
            'caracteristiques': 'Cuisine ouverte'
        },
        {
            'description': 'Magnifique appartement haussmannien',
            'caracteristiques': 'Baignoire, parquet'
        },
        {
            'description': 'Appartement récent avec douche',
            'caracteristiques': 'Parking'
        }
    ]
    
    print("🛁 TEST D'EXTRACTION DE BAIGNOIRE")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Test case:")
        print(f"   Description: {case['description']}")
        print(f"   Caractéristiques: {case['caracteristiques']}")
        
        result = extractor.extract_baignoire_textuelle(
            case['description'], 
            case['caracteristiques']
        )
        
        print(f"   Résultat:")
        print(f"      Baignoire: {result['has_baignoire']}")
        print(f"      Douche: {result['has_douche']}")
        print(f"      Score: {result['score']}/10")
        print(f"      Tier: {result['tier']}")
        print(f"      Justification: {result['justification']}")

if __name__ == "__main__":
    test_baignoire_extraction()

