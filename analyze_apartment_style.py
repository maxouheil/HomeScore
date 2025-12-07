#!/usr/bin/env python3
"""
Analyse visuelle des photos d'appartement pour estimer:
- Style (haussmannien, 70s, moderne)
- Présence cuisine ouverte
- Luminosité
"""

import json
import os
import base64
import requests
from datetime import datetime
from analyze_text_ai import TextAIAnalyzer
from extract_cuisine_text import CuisineTextExtractor
from cache_api import get_cache

class ApartmentStyleAnalyzer:
    """Analyseur de style d'appartement basé sur les photos et le texte"""
    
    def __init__(self):
        # Forcer le rechargement du .env
        from dotenv import load_dotenv
        load_dotenv()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = "https://api.openai.com/v1"
        self.text_ai_analyzer = TextAIAnalyzer()
        self.cuisine_text_extractor = CuisineTextExtractor()
        self.use_text_analysis_style = False  # DÉSACTIVÉ pour le STYLE: Utiliser uniquement l'analyse des photos (plus fiable)
        self.use_text_analysis_cuisine = True  # ACTIVÉ pour la CUISINE: Analyse textuelle + photos
        self.cache = get_cache()
        
    def analyze_apartment_photos_from_data(self, apartment_data):
        """Analyse les photos directement depuis les données d'appartement
        STYLE: 100% analyse photos (analyse textuelle désactivée pour éviter erreurs)
        CUISINE: Analyse textuelle + photos (combinée)
        """
        description = apartment_data.get('description', '')
        caracteristiques = apartment_data.get('caracteristiques', '')
        photos = apartment_data.get('photos', [])
        
        # ANALYSE TEXTUELLE pour la CUISINE uniquement (pas pour le style)
        text_analysis = None
        if self.use_text_analysis_cuisine:
            # Analyser uniquement la cuisine depuis le texte
            cuisine_result = self.cuisine_text_extractor.extract_cuisine_from_text(description, caracteristiques)
            if cuisine_result:
                text_analysis = {
                    'cuisine': cuisine_result,
                    'style': None  # Style désactivé dans l'analyse textuelle
                }
        
        # STYLE: Analyser UNIQUEMENT depuis les photos (analyse textuelle désactivée)
        # L'analyse textuelle était trop permissive et causait des erreurs de classification
        photo_analysis = None
        if photos:
            # Prendre les 5 premières photos pour analyse détaillée (suffisant pour détecter le style)
            photos_to_analyze = photos[:5]
            
            # Extraire les URLs directement (pas besoin de télécharger)
            apartment_id = apartment_data.get('id', 'unknown')
            photo_urls = []
            for photo in photos_to_analyze:
                if isinstance(photo, dict):
                    url = photo.get('url')
                else:
                    url = photo
                if url:
                    photo_urls.append(url)
            
            if photo_urls:
                # Analyser les photos en parallèle avec les URLs directement
                from concurrent.futures import ThreadPoolExecutor, as_completed
                analyses = []
                
                def analyze_one_photo(photo_url):
                    return self.analyze_single_photo(photo_url, apartment_id=apartment_id, photo_url=photo_url)
                
                # Paralléliser les appels API (max 5 workers pour éviter rate limit)
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_url = {executor.submit(analyze_one_photo, url): url for url in photo_urls}
                    for future in as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            analysis = future.result()
                            if analysis:
                                analyses.append(analysis)
                        except Exception as e:
                            print(f"   ⚠️ Erreur analyse photo {url[:50]}...: {e}")
                
                if analyses:
                    photo_analysis = self.aggregate_analyses(analyses)
        
        # STYLE: Utiliser l'analyse visuelle uniquement (100% photos, pas de texte)
        # CUISINE: Combiner analyse photos + texte si disponible
        if photo_analysis:
            result = {
                'style': photo_analysis.get('style', {}),
                'cuisine': photo_analysis.get('cuisine', {}),
                'luminosite': photo_analysis.get('luminosite', {}),
                'hauteur_plafond': photo_analysis.get('hauteur_plafond', {}),
                'baignoire': photo_analysis.get('baignoire', {}),
                'visavis': photo_analysis.get('visavis', {}),
                'salon_size': photo_analysis.get('salon_size', {}),
                'photos_analyzed': photo_analysis.get('photos_analyzed', 0),
                'method': 'photo_analysis'
            }
            
            # Si on a une analyse textuelle pour la cuisine, on peut l'utiliser en complément
            # (mais le style vient toujours des photos uniquement)
            if text_analysis and text_analysis.get('cuisine'):
                # La cuisine peut être combinée texte + photos si nécessaire
                # Pour l'instant, on garde celle des photos par défaut
                pass
            
            return result
        
        # Pas de photos disponibles → retourner None (pas de fallback texte pour le style)
        return None
    
    def analyze_text(self, description: str, caracteristiques: str = ""):
        """Analyse le style et la cuisine depuis le texte avec IA"""
        if not self.text_ai_analyzer.openai_api_key:
            return None
        
        try:
            # Analyser le style
            style_result = self.text_ai_analyzer.analyze_style(description, caracteristiques)
            
            # Analyser la cuisine
            cuisine_result = self.cuisine_text_extractor.extract_cuisine_from_text(description, caracteristiques)
            
            if not style_result.get('available', False) and not cuisine_result.get('ouverte') is not None:
                return None
            
            result = {
                'style': None,
                'cuisine': None,
                'method': 'text_ai_analysis'
            }
            
            # Style
            if style_result.get('available', False):
                style_type = style_result.get('style', 'autre')
                # Utiliser confiance_globale si disponible, sinon confiance classique
                style_confidence = style_result.get('confiance_globale', style_result.get('confiance', 0))
                
                # Extraire les informations enrichies
                contexte_detection = style_result.get('contexte_detection', {})
                indices_architecturaux = style_result.get('indices_architecturaux', {})
                est_conversion = contexte_detection.get('est_conversion', False)
                type_conversion = contexte_detection.get('type_conversion', '')
                
                # Construire une justification courte en format tags (max 3 tags)
                tags = []
                
                # Extraire les indices architecturaux principaux
                elements_haussmannien = indices_architecturaux.get('elements_haussmannien', [])
                elements_atypique = indices_architecturaux.get('elements_atypique', [])
                elements_moderne = indices_architecturaux.get('elements_moderne', [])
                
                # Prioriser les éléments selon le style détecté
                if style_type == 'haussmannien' and elements_haussmannien:
                    # Prendre les 3-4 premiers éléments, limiter à 3 mots chacun
                    for elem in elements_haussmannien[:4]:
                        words = elem.split()[:3]  # Max 3 mots par tag
                        tags.append(' '.join(words))
                elif style_type in ['atypique', 'loft']:
                    if est_conversion and type_conversion:
                        tags.append('loft')
                    if elements_atypique:
                        for elem in elements_atypique[:3]:
                            words = elem.split()[:3]
                            tags.append(' '.join(words))
                elif elements_moderne:
                    for elem in elements_moderne[:3]:
                        words = elem.split()[:3]
                        tags.append(' '.join(words))
                
                # Si pas assez de tags, ajouter le style
                if len(tags) < 2:
                    if style_type == 'haussmannien':
                        tags.extend(['moulures', 'parquet', 'cheminée'])
                    elif style_type == 'atypique':
                        tags.extend(['loft', 'poutres'])
                    else:
                        tags.append('moderne')
                
                # Limiter à 4-5 tags max et joindre
                justification = ', '.join(tags[:5])
                
                # Calculer le score
                base_score = self.calculate_style_score(style_type)
                
                # Vérifier si mention explicite + caractéristiques détectées
                # Si style explicite mentionné ET indices architecturaux présents → confiance 100%
                style_explicite = style_result.get('style', '').lower() in ['haussmannien', 'atypique', 'loft']
                
                # Vérifier que les indices correspondent au style détecté
                has_indices = False
                if style_type == 'haussmannien':
                    has_indices = bool(indices_architecturaux.get('elements_haussmannien'))
                elif style_type in ['atypique', 'loft']:
                    has_indices = bool(indices_architecturaux.get('elements_atypique') or 
                                     contexte_detection.get('est_conversion'))
                else:
                    # Pour moderne, vérifier éléments modernes
                    has_indices = bool(indices_architecturaux.get('elements_moderne'))
                
                # Si mention explicite du style + caractéristiques correspondantes détectées → confiance 100%
                final_confidence = 1.0 if (style_explicite and has_indices) else style_confidence
                
                result['style'] = {
                    'type': style_type,
                    'confidence': final_confidence,
                    'score': base_score,
                    'justification': justification,
                    'indices': style_result.get('indices', []),
                    'details': {
                        'confiance_globale': style_confidence,
                        'confiance_finale': final_confidence,
                        'mention_explicite': style_explicite,
                        'caracteristiques_detectees': has_indices,
                        'contexte_detection': contexte_detection,
                        'indices_architecturaux': indices_architecturaux,
                        'est_conversion': est_conversion,
                        'type_conversion': type_conversion,
                        'note_scoring': style_result.get('note_scoring', '')
                    }
                }
            
            # Cuisine
            if cuisine_result.get('ouverte') is not None:
                cuisine_ouverte = cuisine_result.get('ouverte', False)
                cuisine_confidence = cuisine_result.get('confidence', 0)
                result['cuisine'] = {
                    'ouverte': cuisine_ouverte,
                    'confidence': cuisine_confidence,
                    'score': self.calculate_cuisine_score(cuisine_ouverte),
                    'justification': cuisine_result.get('justification', ''),
                    'indices': cuisine_result.get('indices', [])
                }
            
            return result if result['style'] or result['cuisine'] else None
            
        except Exception as e:
            print(f"   ⚠️ Erreur analyse texte IA: {e}")
            return None
    
    def combine_text_and_photo_analysis(self, text_analysis, photo_analysis):
        """Combine l'analyse texte et photo avec validation croisée"""
        if not photo_analysis and not text_analysis:
            return None
        
        # Si seulement texte → utiliser texte
        if not photo_analysis and text_analysis:
            return {
                'style': text_analysis.get('style', {}),
                'cuisine': text_analysis.get('cuisine', {}),
                'luminosite': {'type': 'inconnue', 'confidence': 0, 'score': 0},
                'photos_analyzed': 0,
                'method': 'text_only'
            }
        
        # Si seulement photos → utiliser photos
        if photo_analysis and not text_analysis:
            return photo_analysis
        
        # Si les deux → validation croisée avec PhotoAnalyzer
        from analyze_photos import PhotoAnalyzer
        photo_validator = PhotoAnalyzer()
        
        combined = {
            'style': photo_analysis.get('style', {}),
            'cuisine': photo_analysis.get('cuisine', {}),
            'luminosite': photo_analysis.get('luminosite', {}),
            'photos_analyzed': photo_analysis.get('photos_analyzed', 0),
            'method': 'combined'
        }
        
        # Valider style avec validation croisée
        if text_analysis.get('style') and photo_analysis.get('style'):
            text_style = text_analysis.get('style')
            photo_style = photo_analysis.get('style')
            style_validation = photo_validator.validate_text_with_photos(text_style, photo_style, 'style')
            
            if style_validation.get('validation_status') == 'validated':
                # Cohérent → utiliser texte si plus confiant, sinon photos
                if text_style.get('confidence', 0) > photo_style.get('confidence', 0):
                    combined['style'] = text_style
                    combined['style']['confidence'] = style_validation.get('confidence_adjusted', text_style.get('confidence', 0))
                    combined['style']['justification'] += f" | ✅ Validé par photos"
                else:
                    combined['style']['confidence'] = style_validation.get('confidence_adjusted', photo_style.get('confidence', 0))
            elif style_validation.get('validation_status') == 'conflict':
                # Incohérent → préférer celui avec plus de confiance
                if text_style.get('confidence', 0) > photo_style.get('confidence', 0):
                    combined['style'] = text_style
                    combined['style']['confidence'] = style_validation.get('confidence_adjusted', text_style.get('confidence', 0))
                    combined['style']['justification'] += f" | ⚠️ Conflit avec photos"
                else:
                    combined['style']['confidence'] = style_validation.get('confidence_adjusted', photo_style.get('confidence', 0))
                    combined['style']['justification'] += f" | ⚠️ Conflit avec texte"
            
            combined['style']['photo_validation'] = style_validation.get('cross_validation')
        
        # Valider cuisine avec validation croisée
        if text_analysis.get('cuisine') and photo_analysis.get('cuisine'):
            text_cuisine = text_analysis.get('cuisine')
            photo_cuisine = photo_analysis.get('cuisine')
            cuisine_validation = photo_validator.validate_text_with_photos(text_cuisine, photo_cuisine, 'cuisine')
            
            if cuisine_validation.get('validation_status') == 'validated':
                # Cohérent → utiliser texte si plus confiant, sinon photos
                if text_cuisine.get('confidence', 0) > photo_cuisine.get('confidence', 0):
                    combined['cuisine'] = text_cuisine
                    combined['cuisine']['confidence'] = cuisine_validation.get('confidence_adjusted', text_cuisine.get('confidence', 0))
                    combined['cuisine']['justification'] += f" | ✅ Validé par photos"
                else:
                    combined['cuisine']['confidence'] = cuisine_validation.get('confidence_adjusted', photo_cuisine.get('confidence', 0))
            elif cuisine_validation.get('validation_status') == 'conflict':
                # Incohérent → préférer celui avec plus de confiance
                if text_cuisine.get('confidence', 0) > photo_cuisine.get('confidence', 0):
                    combined['cuisine'] = text_cuisine
                    combined['cuisine']['confidence'] = cuisine_validation.get('confidence_adjusted', text_cuisine.get('confidence', 0))
                    combined['cuisine']['justification'] += f" | ⚠️ Conflit avec photos"
                else:
                    combined['cuisine']['confidence'] = cuisine_validation.get('confidence_adjusted', photo_cuisine.get('confidence', 0))
                    combined['cuisine']['justification'] += f" | ⚠️ Conflit avec texte"
            
            combined['cuisine']['photo_validation'] = cuisine_validation.get('cross_validation')
        
        return combined
    
    def analyze_apartment_photos(self, photos_dir="data/photos", apartment_id=None):
        """Analyse toutes les photos d'appartement"""
        print("🏠 ANALYSE VISUELLE DES PHOTOS D'APPARTEMENT")
        print("=" * 60)
        
        # Trouver toutes les photos d'appartement
        photo_files = []
        if os.path.exists(photos_dir):
            for file in os.listdir(photos_dir):
                if file.startswith("apartment_") and file.endswith(".jpg"):
                    photo_files.append(os.path.join(photos_dir, file))
        
        if not photo_files:
            print("❌ Aucune photo d'appartement trouvée")
            return None
        
        print(f"📸 {len(photo_files)} photos trouvées")
        
        # Extraire apartment_id depuis le nom du fichier si pas fourni
        if not apartment_id and photo_files:
            # Essayer d'extraire depuis le nom du fichier ou du répertoire
            first_file = photo_files[0]
            if 'apartment_' in first_file:
                # Chercher dans le chemin
                parts = first_file.split('/')
                for part in parts:
                    if part.startswith('apartment_'):
                        apartment_id = part.replace('apartment_', '').split('_')[0]
                        break
        
        # Analyser chaque photo
        analyses = []
        for i, photo_path in enumerate(photo_files, 1):
            print(f"\n📸 Analyse photo {i}: {os.path.basename(photo_path)}")
            analysis = self.analyze_single_photo(photo_path, apartment_id=apartment_id)
            if analysis:
                analyses.append(analysis)
        
        # Agréger les résultats
        if analyses:
            return self.aggregate_analyses(analyses)
        else:
            return None
    
    def analyze_single_photo(self, photo_path_or_url, apartment_id=None, photo_url=None):
        """Analyse une photo individuelle avec cache - accepte URL ou chemin de fichier"""
        # Déterminer l'URL réelle de la photo
        is_local_file = False
        if photo_url:
            actual_url = photo_url
        elif isinstance(photo_path_or_url, str) and photo_path_or_url.startswith('http'):
            actual_url = photo_path_or_url
        else:
            # Fichier local - encoder en base64 (pour compatibilité avec ancien code)
            is_local_file = True
            actual_url = photo_path_or_url
        
        # Générer une clé de cache basée sur l'URL de la photo ET l'ID de l'appartement
        cache_key = f"{apartment_id}:{actual_url}" if apartment_id else actual_url
        
        # Vérifier le cache d'abord
        cached_result = self.cache.get('style_photo', cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Préparer l'image pour l'API Vision
            if is_local_file:
                # Encoder le fichier local en base64
                with open(photo_path_or_url, 'rb') as image_file:
                    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                image_content = {
                    'type': 'image_url',
                    'image_url': {
                        'url': f'data:image/jpeg;base64,{image_base64}'
                    }
                }
            else:
                # Utiliser l'URL directement (beaucoup plus rapide!)
                image_content = {
                    'type': 'image_url',
                    'image_url': {
                        'url': actual_url
                    }
                }
            
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
                                'text': """Analyse cette photo d'appartement pour déterminer MULTIPLES CRITÈRES en une seule fois.

## TÂCHES À EFFECTUER :

### 1. STYLE ARCHITECTURAL (Classifier en Ancien / Neuf / Atypique)

**ANCIEN (Haussmannien)** :
- Caractéristiques OBLIGATOIRES : Moulures au plafond, cheminée, parquet pointe de Hongrie, balcon fer forgé, hauteur sous plafond importante (>2.80m), éléments architecturaux décoratifs
- Poutres apparentes au plafond = Peut être ancien (combles aménagés, charpente visible)
- ⚠️ Les poutres apparentes dans un contexte ancien (sans béton brut ni caractère industriel) = Ancien, pas Atypique

**NEUF (Moderne/Contemporain)** :
- Design épuré, sol moderne, terrasse métal, fenêtres modernes, plafond bas/réduit (<2.60m)
- Vue panoramique sur Paris depuis étage élevé = TRÈS caractéristique du Neuf

**ATYPIQUE (Loft/Unique)** :
- Espaces ouverts, volumes généreux, béton brut, caractère industriel, conversion d'entrepôt/atelier
- ⚠️ Pour être atypique, il faut aussi du béton brut, un caractère industriel, ou une conversion d'entrepôt

### 2. CUISINE OUVERTE
- Oui: cuisine visible depuis le salon, pas de séparation murale
- Non: cuisine fermée, séparée du salon

### 3. LUMINOSITÉ
- Excellente/Bonne/Moyenne/Faible selon la lumière naturelle visible

### 4. HAUTEUR SOUS PLAFOND (si visible)
- Estimer en mètres si possible (ex: 2.80m, 2.50m, 3.00m)
- Indices : proportions des portes/fenêtres, hauteur relative des murs

### 5. BAIGNOIRE (si photo de salle de bain)
- Détecter si une baignoire est visible (grand récipient pour se baigner, rectangulaire/ovale)
- OU si seulement une douche est visible (cabine de douche, douche italienne)
- Si ce n'est pas une photo de salle de bain, mettre null

### 6. VIS-À-VIS (si fenêtres de pièce principale visibles)
- Regarder par les fenêtres de la PIÈCE PRINCIPALE (salon/séjour) uniquement
- Estimer la distance en mètres jusqu'aux bâtiments/immeubles visibles en face
- Largeur de la rue pour aider à estimer (étroite <10m, moyenne 10-15m, large >15m)
- Si pas de vis-à-vis visible ou très lointain (>50m), utiliser une grande distance (ex: 100m)

### 7. TAILLE SALON (si photo montre le salon/séjour)
- Identifier si cette photo montre le salon/séjour (canapé, table basse, espace de vie)
- Si salon, estimer sa taille en m² en observant:
  * Profondeur de la pièce (distance mur avant → mur arrière)
  * Largeur visible de la pièce
  * Meubles comme référence (canapé standard ~2m, table basse ~1m)
- Catégories : grand (>25m²), moyen (15-25m²), petit (<15m²)

### FORMAT DE LA JUSTIFICATION (Style) :
Tags très courts séparés par virgules, max 15-20 mots.
Exemples : "moulures, parquet pointe de Hongrie, cheminée" ou "design épuré, matériaux modernes"

Réponds UNIQUEMENT au format JSON (pas de texte avant/après):
{
    "style": "haussmannien|atypique|moderne|autre",
    "style_confidence": 0.0-1.0,
    "style_justification": "tags très courts séparés par virgules, max 15-20 mots",
    "cuisine_ouverte": true|false,
    "cuisine_confidence": 0.0-1.0,
    "cuisine_details": "description courte de la cuisine",
    "luminosite": "excellente|bonne|moyenne|faible",
    "luminosite_confidence": 0.0-1.0,
    "luminosite_details": "description courte de la luminosité",
    "hauteur_plafond": nombre en mètres (ex: 2.80) ou null si non visible,
    "hauteur_plafond_confidence": 0.0-1.0,
    "has_baignoire": true|false|null (true=baignoire visible, false=douche seule, null=pas salle de bain),
    "has_douche": true|false|null (true=douche visible, null=pas salle de bain),
    "is_bathroom": true|false,
    "baignoire_confidence": 0.0-1.0,
    "visavis_distance": nombre entier en mètres (distance estimée) ou null si pas de fenêtres principales visibles,
    "fenetres_principales_visibles": true|false,
    "vue_par_fenetre": "degagee|moyenne|obstruee|null",
    "visavis_confidence": 0.0-1.0,
    "is_salon": true|false,
    "salon_size_estimate": nombre entier en m² (ou null si pas salon),
    "salon_category": "grand|moyen|petit|null",
    "salon_confidence": 0.0-1.0
}"""
                            },
                            image_content
                        ]
                    }
                ],
                'max_tokens': 500  # Augmenté pour inclure tous les nouveaux champs
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
            
            # Parser le JSON (gérer les blocs markdown)
            try:
                # Nettoyer le contenu (enlever les blocs markdown)
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                analysis = json.loads(content)
                print(f"   ✅ Analyse réussie")
                print(f"      Style: {analysis.get('style', 'N/A')} (confiance: {analysis.get('style_confidence', 0):.2f})")
                
                # Afficher la justification du style
                justification = analysis.get('style_justification', '')
                if justification:
                    print(f"      Justification: {justification}")
                
                print(f"      Cuisine: {'Ouverte' if analysis.get('cuisine_ouverte') else 'Fermée'} (confiance: {analysis.get('cuisine_confidence', 0):.2f})")
                print(f"      Luminosité: {analysis.get('luminosite', 'N/A')} (confiance: {analysis.get('luminosite_confidence', 0):.2f})")
                
                # Afficher les nouveaux champs si présents
                if analysis.get('hauteur_plafond') is not None:
                    print(f"      Hauteur plafond: {analysis.get('hauteur_plafond')}m (confiance: {analysis.get('hauteur_plafond_confidence', 0):.2f})")
                if analysis.get('is_bathroom'):
                    baignoire_status = 'Baignoire' if analysis.get('has_baignoire') else ('Douche' if analysis.get('has_douche') else 'Non détecté')
                    print(f"      Salle de bain: {baignoire_status} (confiance: {analysis.get('baignoire_confidence', 0):.2f})")
                if analysis.get('fenetres_principales_visibles'):
                    visavis = analysis.get('visavis_distance')
                    print(f"      Vis-à-vis: {visavis}m (confiance: {analysis.get('visavis_confidence', 0):.2f})" if visavis else "      Vis-à-vis: Non visible")
                if analysis.get('is_salon'):
                    salon_size = analysis.get('salon_size_estimate')
                    print(f"      Salon: {salon_size}m² ({analysis.get('salon_category', 'N/A')}) (confiance: {analysis.get('salon_confidence', 0):.2f})" if salon_size else "      Salon: Taille non estimable")
                
                # Mettre en cache avant de retourner
                self.cache.set('style_photo', cache_key, analysis)
                
                return analysis
                
            except json.JSONDecodeError as e:
                print(f"   ❌ Erreur parsing JSON: {e}")
                print(f"   Contenu brut: {content[:300]}...")
                # Essayer de récupérer les infos manuellement
                return self.extract_info_manually(content)
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout lors de l'analyse de la photo (limite 15s)")
            return None
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Erreur réseau: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Erreur analyse photo: {e}")
            return None
    
    def extract_info_manually(self, content):
        """Extrait les informations manuellement si le JSON ne parse pas"""
        try:
            # Extraire les informations avec des regex
            import re
            
            style_match = re.search(r'"style":\s*"([^"]+)"', content)
            style_raw = style_match.group(1) if style_match else 'inconnu'
            # Fusionner 70s et moderne en "moderne"
            if '70' in style_raw.lower() or 'seventies' in style_raw.lower() or '60' in style_raw.lower():
                style = 'moderne'
            else:
                style = style_raw
            
            cuisine_match = re.search(r'"cuisine_ouverte":\s*(true|false)', content)
            cuisine_ouverte = cuisine_match.group(1) == 'true' if cuisine_match else False
            
            luminosite_match = re.search(r'"luminosite":\s*"([^"]+)"', content)
            luminosite = luminosite_match.group(1) if luminosite_match else 'inconnue'
            
            # Extraire les nouveaux champs
            hauteur_match = re.search(r'"hauteur_plafond":\s*([0-9.]+|null)', content)
            hauteur_plafond = float(hauteur_match.group(1)) if hauteur_match and hauteur_match.group(1) != 'null' else None
            
            baignoire_match = re.search(r'"has_baignoire":\s*(true|false|null)', content)
            has_baignoire = baignoire_match.group(1) == 'true' if baignoire_match and baignoire_match.group(1) != 'null' else None
            
            douche_match = re.search(r'"has_douche":\s*(true|false|null)', content)
            has_douche = douche_match.group(1) == 'true' if douche_match and douche_match.group(1) != 'null' else None
            
            is_bathroom_match = re.search(r'"is_bathroom":\s*(true|false)', content)
            is_bathroom = is_bathroom_match.group(1) == 'true' if is_bathroom_match else False
            
            visavis_match = re.search(r'"visavis_distance":\s*([0-9]+|null)', content)
            visavis_distance = int(visavis_match.group(1)) if visavis_match and visavis_match.group(1) != 'null' else None
            
            fenetres_match = re.search(r'"fenetres_principales_visibles":\s*(true|false)', content)
            fenetres_principales_visibles = fenetres_match.group(1) == 'true' if fenetres_match else False
            
            is_salon_match = re.search(r'"is_salon":\s*(true|false)', content)
            is_salon = is_salon_match.group(1) == 'true' if is_salon_match else False
            
            salon_size_match = re.search(r'"salon_size_estimate":\s*([0-9]+|null)', content)
            salon_size_estimate = int(salon_size_match.group(1)) if salon_size_match and salon_size_match.group(1) != 'null' else None
            
            salon_category_match = re.search(r'"salon_category":\s*"([^"]+)"', content)
            salon_category = salon_category_match.group(1) if salon_category_match else None
            
            # Essayer d'extraire la justification aussi
            justification_match = re.search(r'"style_justification":\s*"([^"]+)"', content)
            style_justification = justification_match.group(1) if justification_match else f"Style {style} détecté"
            
            analysis = {
                'style': style,
                'style_confidence': 0.7,
                'style_justification': style_justification,
                'cuisine_ouverte': cuisine_ouverte,
                'cuisine_confidence': 0.7,
                'luminosite': luminosite,
                'luminosite_confidence': 0.7,
                'hauteur_plafond': hauteur_plafond,
                'hauteur_plafond_confidence': 0.5 if hauteur_plafond else 0.0,
                'has_baignoire': has_baignoire,
                'has_douche': has_douche,
                'is_bathroom': is_bathroom,
                'baignoire_confidence': 0.5 if has_baignoire is not None or has_douche is not None else 0.0,
                'visavis_distance': visavis_distance,
                'fenetres_principales_visibles': fenetres_principales_visibles,
                'vue_par_fenetre': 'moyenne' if visavis_distance else None,
                'visavis_confidence': 0.5 if visavis_distance else 0.0,
                'is_salon': is_salon,
                'salon_size_estimate': salon_size_estimate,
                'salon_category': salon_category,
                'salon_confidence': 0.5 if salon_size_estimate else 0.0
            }
            
            print(f"   ✅ Analyse manuelle réussie")
            print(f"      Style: {style}")
            print(f"      Cuisine: {'Ouverte' if cuisine_ouverte else 'Fermée'}")
            print(f"      Luminosité: {luminosite}")
            
            return analysis
            
        except Exception as e:
            print(f"   ❌ Erreur extraction manuelle: {e}")
            return None
    
    def aggregate_analyses(self, analyses):
        """Agrège les analyses de toutes les photos - Vote majoritaire pour le style avec justification"""
        print(f"\n📊 AGRÉGATION DES {len(analyses)} ANALYSES")
        print("-" * 40)
        
        # Compter les styles (fusionner 70s avec moderne)
        styles = []
        style_justifications = []  # Stocker les justifications pour chaque style
        
        for a in analyses:
            style = a.get('style', '')
            justification = a.get('style_justification', '')
            if style:  # Vérifier que style existe et n'est pas vide
                styles.append(style)
                if justification:
                    style_justifications.append((style, justification))
        
        style_counts = {}
        style_justifications_by_style = {}  # Regrouper les justifications par style
        
        for style in styles:
            # Fusionner 70s, 60s, contemporain, récent avec moderne
            style_normalized = style.lower()
            if '70' in style_normalized or 'seventies' in style_normalized or '60' in style_normalized:
                style_normalized = 'moderne'
            elif 'contemporain' in style_normalized or 'récent' in style_normalized or 'recent' in style_normalized:
                style_normalized = 'moderne'
            elif style_normalized not in ['moderne', 'contemporain', 'haussmannien', 'atypique', 'loft', 'autre']:
                # Si pas dans les styles connus, considérer comme moderne (neuf) par défaut
                style_normalized = 'moderne'
            style_counts[style_normalized] = style_counts.get(style_normalized, 0) + 1
        
        # Regrouper les justifications par style détecté
        for style, justification in style_justifications:
            style_normalized = style.lower()
            if '70' in style_normalized or 'seventies' in style_normalized or '60' in style_normalized:
                style_normalized = 'moderne'
            elif 'contemporain' in style_normalized or 'récent' in style_normalized or 'recent' in style_normalized:
                style_normalized = 'moderne'
            elif style_normalized not in ['moderne', 'contemporain', 'haussmannien', 'atypique', 'loft', 'autre']:
                # Si pas dans les styles connus, considérer comme moderne (neuf) par défaut
                style_normalized = 'moderne'
            
            if style_normalized not in style_justifications_by_style:
                style_justifications_by_style[style_normalized] = []
            style_justifications_by_style[style_normalized].append(justification)
        
        # Compter les cuisines ouvertes (ignorer None)
        cuisines_ouvertes = [a.get('cuisine_ouverte') for a in analyses if 'cuisine_ouverte' in a and a.get('cuisine_ouverte') is not None]
        cuisine_ouverte_ratio = sum(cuisines_ouvertes) / len(cuisines_ouvertes) if cuisines_ouvertes else 0
        
        # Compter les luminosités
        luminosites = [a.get('luminosite', 'inconnue') for a in analyses if a.get('luminosite')]
        luminosite_counts = {}
        for lum in luminosites:
            luminosite_counts[lum] = luminosite_counts.get(lum, 0) + 1
        
        # Calculer les scores moyens
        style_confidences = [a.get('style_confidence', 0) for a in analyses if a.get('style_confidence')]
        cuisine_confidences = [a.get('cuisine_confidence', 0) for a in analyses if a.get('cuisine_confidence')]
        luminosite_confidences = [a.get('luminosite_confidence', 0) for a in analyses if a.get('luminosite_confidence')]
        
        # Agréger hauteur plafond (moyenne des valeurs non-null)
        hauteurs_plafond = [a.get('hauteur_plafond') for a in analyses if a.get('hauteur_plafond') is not None]
        final_hauteur_plafond = sum(hauteurs_plafond) / len(hauteurs_plafond) if hauteurs_plafond else None
        hauteur_confidences = [a.get('hauteur_plafond_confidence', 0) for a in analyses if a.get('hauteur_plafond') is not None]
        
        # Agréger baignoire (vote majoritaire sur les photos de salle de bain)
        baignoires = [a.get('has_baignoire') for a in analyses if a.get('is_bathroom') and a.get('has_baignoire') is not None]
        douches = [a.get('has_douche') for a in analyses if a.get('is_bathroom') and a.get('has_douche') is not None]
        final_has_baignoire = None
        final_has_douche = None
        if baignoires:
            final_has_baignoire = sum(baignoires) / len(baignoires) > 0.5
        if douches and not final_has_baignoire:
            final_has_douche = sum(douches) / len(douches) > 0.5
        baignoire_confidences = [a.get('baignoire_confidence', 0) for a in analyses if a.get('is_bathroom')]
        
        # Agréger vis-à-vis (moyenne des distances, catégorie la plus fréquente)
        visavis_distances = [a.get('visavis_distance') for a in analyses if a.get('fenetres_principales_visibles') and a.get('visavis_distance') is not None]
        final_visavis_distance = int(sum(visavis_distances) / len(visavis_distances)) if visavis_distances else None
        # Catégoriser vis-à-vis
        final_visavis_category = None
        if final_visavis_distance:
            if final_visavis_distance > 20:
                final_visavis_category = 'good'
            elif final_visavis_distance >= 10:
                final_visavis_category = 'moyen'
            else:
                final_visavis_category = 'bad'
        vue_par_fenetre = [a.get('vue_par_fenetre') for a in analyses if a.get('vue_par_fenetre')]
        final_vue_par_fenetre = max(set(vue_par_fenetre), key=vue_par_fenetre.count) if vue_par_fenetre else None
        visavis_confidences = [a.get('visavis_confidence', 0) for a in analyses if a.get('fenetres_principales_visibles')]
        
        # Agréger taille salon (moyenne des estimations)
        salon_sizes = [a.get('salon_size_estimate') for a in analyses if a.get('is_salon') and a.get('salon_size_estimate') is not None]
        final_salon_size = int(sum(salon_sizes) / len(salon_sizes)) if salon_sizes else None
        salon_categories = [a.get('salon_category') for a in analyses if a.get('is_salon') and a.get('salon_category')]
        final_salon_category = max(set(salon_categories), key=salon_categories.count) if salon_categories else None
        salon_confidences = [a.get('salon_confidence', 0) for a in analyses if a.get('is_salon')]
        
        # Déterminer le style final par vote majoritaire
        final_style = max(style_counts, key=style_counts.get) if style_counts else 'inconnu'
        final_cuisine_ouverte = cuisine_ouverte_ratio > 0.5
        final_luminosite = max(luminosite_counts, key=luminosite_counts.get) if luminosite_counts else 'inconnue'
        
        # CORRECTION: Si "poutres apparentes" est dans les justifications, considérer comme "ancien" (haussmannien)
        # Les poutres apparentes sont caractéristiques des anciens immeubles (combles aménagés, charpente visible)
        all_justifications_combined = " ".join([j for just_list in style_justifications_by_style.values() for j in just_list]).lower()
        if 'poutres apparentes' in all_justifications_combined or 'poutre' in all_justifications_combined:
            # Vérifier si c'est vraiment atypique (loft industriel) ou ancien (charpente visible)
            # Si pas d'autres indices atypiques forts (béton brut, industriel), considérer comme ancien
            has_atypique_indicators = any(indicator in all_justifications_combined for indicator in ['béton brut', 'industriel', 'loft', 'entrepôt', 'atelier'])
            if not has_atypique_indicators and final_style not in ['haussmannien', 'atypique', 'loft']:
                print(f"   🔄 Correction: '{final_style}' → 'haussmannien' (poutres apparentes = ancien)")
                final_style = 'haussmannien'
                # Ajouter "haussmannien" aux styles si pas déjà présent
                if 'haussmannien' not in style_counts:
                    style_counts['haussmannien'] = 0
                style_counts['haussmannien'] += 1
        
        # Sélectionner et combiner les justifications pour le style final
        # Les justifications sont au format tags séparés par virgules, on les combine intelligemment
        final_justification = ""
        if final_style in style_justifications_by_style and style_justifications_by_style[final_style]:
            justifications = style_justifications_by_style[final_style]
            
            # Extraire tous les tags uniques de toutes les justifications
            all_tags = []
            for just in justifications:
                # Séparer par virgules et nettoyer
                tags = [tag.strip().lower() for tag in just.split(',') if tag.strip()]
                all_tags.extend(tags)
            
            # Dédupliquer intelligemment (éviter les doublons sémantiques)
            from collections import Counter
            tag_counts = Counter(all_tags)
            
            # Filtrer les doublons sémantiques et limiter la longueur des tags
            filtered_tags = []
            
            # Trier par fréquence décroissante
            sorted_tags = tag_counts.most_common()
            
            for tag, count in sorted_tags:
                # Limiter chaque tag à max 3 mots (raccourcir si trop long)
                tag_words = tag.split()
                if len(tag_words) > 3:
                    # Prendre les 3 premiers mots seulement
                    tag = ' '.join(tag_words[:3])
                    tag_words = tag_words[:3]
                
                # Vérifier si ce tag n'est pas un sous-ensemble d'un tag déjà ajouté
                is_duplicate = False
                for existing_tag in filtered_tags:
                    existing_words = set(existing_tag.split())
                    tag_words_set = set(tag_words)
                    # Si tous les mots du tag sont dans un tag existant, c'est un doublon
                    if tag_words_set.issubset(existing_words) and len(tag_words_set) < len(existing_words):
                        is_duplicate = True
                        break
                    # Si un tag existant est contenu dans celui-ci, remplacer
                    if existing_words.issubset(tag_words_set) and len(existing_words) < len(tag_words_set):
                        filtered_tags.remove(existing_tag)
                        break
                
                if not is_duplicate and len(filtered_tags) < 5:  # Limiter à 4-5 tags max
                    filtered_tags.append(tag)
            
            unique_tags = filtered_tags[:5]  # Maximum 4-5 tags
            
            # Combiner en une seule chaîne de tags
            if unique_tags:
                final_justification = ", ".join(unique_tags)
            else:
                final_justification = justifications[0] if justifications else ""
        
        # Si pas de justification, créer une justification par défaut basée sur le style
        if not final_justification:
            if final_style == 'haussmannien':
                final_justification = "moulures, parquet, cheminée, balcon fer forgé"
            elif final_style == 'atypique':
                final_justification = "loft, poutres apparentes, espace ouvert"
            elif final_style == 'moderne':
                final_justification = "design épuré, matériaux modernes"
            else:
                final_justification = f"style {final_style}"
        
        # Calculer les scores
        style_score = self.calculate_style_score(final_style)
        cuisine_score = self.calculate_cuisine_score(final_cuisine_ouverte)
        luminosite_score = self.calculate_luminosite_score(final_luminosite)
        
        result = {
            'style': {
                'type': final_style,
                'confidence': sum(style_confidences) / len(style_confidences) if style_confidences else 0,
                'score': style_score,
                'details': f"Style détecté: {final_style} (apparaît {style_counts.get(final_style, 0)}/{len(analyses)} photos)",
                'justification': final_justification  # Justification en 1 phrase pour affichage dans indices
            },
            'cuisine': {
                'ouverte': final_cuisine_ouverte,
                'confidence': sum(cuisine_confidences) / len(cuisine_confidences) if cuisine_confidences else 0,
                'score': cuisine_score,
                'details': f"Cuisine {'ouverte' if final_cuisine_ouverte else 'fermée'} ({cuisine_ouverte_ratio:.1%} des photos)"
            },
            'luminosite': {
                'type': final_luminosite,
                'confidence': sum(luminosite_confidences) / len(luminosite_confidences) if luminosite_confidences else 0,
                'score': luminosite_score,
                'details': f"Luminosité {final_luminosite} (apparaît {luminosite_counts.get(final_luminosite, 0)} fois)"
            },
            'hauteur_plafond': {
                'value': round(final_hauteur_plafond, 2) if final_hauteur_plafond else None,
                'confidence': sum(hauteur_confidences) / len(hauteur_confidences) if hauteur_confidences else 0,
                'details': f"Hauteur sous plafond estimée: {round(final_hauteur_plafond, 2)}m" if final_hauteur_plafond else "Hauteur non mesurable"
            },
            'baignoire': {
                'has_baignoire': final_has_baignoire,
                'has_douche': final_has_douche,
                'confidence': sum(baignoire_confidences) / len(baignoire_confidences) if baignoire_confidences else 0,
                'details': f"{'Baignoire' if final_has_baignoire else ('Douche' if final_has_douche else 'Non détecté')} détecté(e) sur {len([a for a in analyses if a.get('is_bathroom')])} photo(s) de salle de bain"
            },
            'visavis': {
                'distance': final_visavis_distance,
                'category': final_visavis_category,
                'vue_par_fenetre': final_vue_par_fenetre,
                'confidence': sum(visavis_confidences) / len(visavis_confidences) if visavis_confidences else 0,
                'details': f"Vis-à-vis estimé à {final_visavis_distance}m (catégorie: {final_visavis_category})" if final_visavis_distance else "Vis-à-vis non mesurable"
            },
            'salon_size': {
                'estimate': final_salon_size,
                'category': final_salon_category,
                'confidence': sum(salon_confidences) / len(salon_confidences) if salon_confidences else 0,
                'details': f"Salon estimé à {final_salon_size}m² (catégorie: {final_salon_category})" if final_salon_size else "Taille salon non estimable"
            },
            'photos_analyzed': len(analyses),
            'individual_analyses': analyses
        }
        
        return result
    
    def calculate_style_score(self, style):
        """Calcule le score de style - Ancien (20pts) / Atypique (10pts) / Neuf (0pts)"""
        style_normalized = style.lower()
        
        # Ancien = 20 pts
        if 'haussmann' in style_normalized:
            return 20
        
        # Atypique = 10 pts (loft, atypique, unique, original, entrepôt, usine, atelier)
        if ('loft' in style_normalized or 
            'atypique' in style_normalized or 
            'unique' in style_normalized or 
            'original' in style_normalized or
            'entrepot' in style_normalized or
            'usine' in style_normalized or
            'atelier' in style_normalized or
            'garage' in style_normalized):
            return 10
        
        # Tout le reste = Neuf = 0 pts
        return 0
    
    def calculate_cuisine_score(self, cuisine_ouverte):
        """Calcule le score de cuisine"""
        return 10 if cuisine_ouverte else 3
    
    def calculate_luminosite_score(self, luminosite):
        """Calcule le score de luminosité"""
        scores = {
            'excellente': 10,
            'bonne': 7,
            'moyenne': 5,
            'faible': 3,
            'inconnue': 0
        }
        return scores.get(luminosite.lower(), 0)

def main():
    """Fonction principale"""
    analyzer = ApartmentStyleAnalyzer()
    
    # Vérifier la clé API
    if not analyzer.openai_api_key or analyzer.openai_api_key == 'votre_clé_openai':
        print("❌ Clé API OpenAI non configurée")
        print("   Configurez OPENAI_API_KEY dans le fichier .env")
        return
    
    # Analyser les photos
    result = analyzer.analyze_apartment_photos()
    
    if result:
        print(f"\n🎯 RÉSULTATS FINAUX:")
        print("=" * 60)
        
        # Style
        style = result['style']
        print(f"🏛️ STYLE: {style['type'].upper()}")
        print(f"   Score: {style['score']}/20")
        print(f"   Confiance: {style['confidence']:.2f}")
        print(f"   Détails: {style['details']}")
        print()
        
        # Cuisine
        cuisine = result['cuisine']
        print(f"🍳 CUISINE: {'OUVERTE' if cuisine['ouverte'] else 'FERMÉE'}")
        print(f"   Score: {cuisine['score']}/10")
        print(f"   Confiance: {cuisine['confidence']:.2f}")
        print(f"   Détails: {cuisine['details']}")
        print()
        
        # Luminosité
        luminosite = result['luminosite']
        print(f"💡 LUMINOSITÉ: {luminosite['type'].upper()}")
        print(f"   Score: {luminosite['score']}/10")
        print(f"   Confiance: {luminosite['confidence']:.2f}")
        print(f"   Détails: {luminosite['details']}")
        print()
        
        # Score total
        total_score = style['score'] + cuisine['score'] + luminosite['score']
        print(f"📊 SCORE TOTAL: {total_score}/40")
        print(f"   Photos analysées: {result['photos_analyzed']}")
        
        # Sauvegarder les résultats
        with open('data/apartment_style_analysis.json', 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvegardés dans data/apartment_style_analysis.json")
        
    else:
        print("❌ Aucune analyse possible")

if __name__ == "__main__":
    main()
