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
from analyze_photos import PhotoAnalyzer
from analyze_text_ai import TextAIAnalyzer
from cache_api import get_cache
import requests

class BaignoireExtractor:
    """Extracteur de baignoire pour les appartements"""
    
    def __init__(self):
        self.photo_analyzer = PhotoAnalyzer()
        self.text_ai_analyzer = TextAIAnalyzer()
        self.use_ai_analysis = True  # Activer l'analyse IA pour éviter faux positifs
        self.cache = get_cache()  # Cache partagé (photo_analyzer a déjà son propre cache)
        
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
            if self.use_ai_analysis and self.text_ai_analyzer.openai_api_key:
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
    
    def extract_baignoire_photos(self, photos_urls: List[str]) -> Dict:
        """Extrait la présence de baignoire depuis les photos avec analyse d'images"""
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
    
    def extract_baignoire_complete(self, description: str, caracteristiques: str = "", photos_urls: List[str] = None) -> Dict:
        """Extrait la présence de baignoire avec validation croisée texte + photos"""
        # Phase 1: Analyse textuelle IA
        text_result = self.extract_baignoire_textuelle(description, caracteristiques)
        
        # Phase 2: Analyse photos si disponibles
        photo_result = None
        if photos_urls:
            # Utiliser la nouvelle méthode unifiée du PhotoAnalyzer
            photo_result = self.photo_analyzer.analyze_photos_baignoire(photos_urls)
        
        # Phase 3: Validation croisée texte + photos
        if photo_result and photo_result.get('photos_analyzed', 0) > 0:
            validation = self.photo_analyzer.validate_text_with_photos(text_result, photo_result, 'baignoire')
            
            # Utiliser la confiance ajustée
            confiance_ajustee = validation.get('confidence_adjusted', text_result.get('confidence', 0) / 100)
            validation_status = validation.get('validation_status', 'text_only')
            
            # Construire résultat final enrichi
            final_result = text_result.copy()
            
            # Si photos confirment ou contredisent, ajuster le résultat
            if validation_status == 'validated':
                # Cohérent → utiliser résultat texte mais avec confiance augmentée
                final_result['confidence'] = int(confiance_ajustee * 100)
                final_result['justification'] += f" | ✅ Validé par photos (confiance: {confiance_ajustee:.0%})"
            elif validation_status == 'conflict':
                # Incohérent → préférer photos si plus confiantes
                photo_confidence = photo_result.get('confidence', 0)
                text_confidence = text_result.get('confidence', 0) / 100
                
                if photo_confidence > text_confidence:
                    # Photos plus confiantes → utiliser résultat photos
                    final_result = {
                        'has_baignoire': photo_result.get('has_baignoire', False),
                        'has_douche': photo_result.get('has_douche', False),
                        'detected_from_text': False,
                        'found_in_description': False,
                        'found_in_caracteristiques': False,
                        'score': photo_result.get('score', 0),
                        'tier': photo_result.get('tier', 'tier3'),
                        'justification': f"{photo_result.get('justification', '')} | ⚠️ Conflit avec texte, photos prioritaires",
                        'confidence': int(confiance_ajustee * 100),
                        'photos_analyzed': photo_result.get('photos_analyzed', 0)
                    }
                else:
                    # Texte plus confiant → garder texte mais réduire confiance
                    final_result['confidence'] = int(confiance_ajustee * 100)
                    final_result['justification'] += f" | ⚠️ Conflit avec photos (confiance: {confiance_ajustee:.0%})"
            
            # Ajouter les infos de validation dans les détails
            if 'details' not in final_result:
                final_result['details'] = {}
            final_result['details']['photo_validation'] = validation.get('cross_validation')
            final_result['details']['validation_status'] = validation_status
            
            return final_result
        
        # Pas de photos → retourner résultat textuel uniquement
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
        
        # Extraire les URLs des photos
        photos_urls = []
        if photos:
            if isinstance(photos[0], dict):
                photos_urls = [p.get('url', '') for p in photos if p.get('url')]
            else:
                photos_urls = [p for p in photos if p]
        
        # Wrapper pour exécuter avec timeout
        def _extract_with_timeout():
            return self.extract_baignoire_complete(description, caracteristiques, photos_urls)
        
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

