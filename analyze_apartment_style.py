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
        self.use_text_analysis = True  # Activer l'analyse texte IA
        self.cache = get_cache()
        
    def analyze_apartment_photos_from_data(self, apartment_data):
        """Analyse les photos directement depuis les données d'appartement
        ET combine avec l'analyse texte IA si disponible
        """
        description = apartment_data.get('description', '')
        caracteristiques = apartment_data.get('caracteristiques', '')
        photos = apartment_data.get('photos', [])
        
        # Analyser le texte d'abord (IA intelligente)
        text_analysis = None
        if self.use_text_analysis:
            text_analysis = self.analyze_text(description, caracteristiques)
        
        # Analyser les photos
        photo_analysis = None
        if photos:
            # Prendre seulement les 3 premières photos pour économiser
            photos_to_analyze = photos[:3]
            
            # Télécharger temporairement les photos
            temp_photos = []
            for i, photo in enumerate(photos_to_analyze):
                try:
                    if isinstance(photo, dict):
                        url = photo.get('url')
                    else:
                        url = photo
                    
                    if url:
                        # Télécharger l'image
                        response = requests.get(url, timeout=5)
                        if response.status_code == 200:
                            temp_file = f"temp_photo_{i}.jpg"
                            with open(temp_file, 'wb') as f:
                                f.write(response.content)
                            temp_photos.append(temp_file)
                except:
                    continue
            
            if temp_photos:
                # Analyser les photos
                analyses = []
                for photo_path in temp_photos:
                    analysis = self.analyze_single_photo(photo_path)
                    if analysis:
                        analyses.append(analysis)
                    # Nettoyer le fichier temporaire
                    try:
                        os.remove(photo_path)
                    except:
                        pass
                
                if analyses:
                    photo_analysis = self.aggregate_analyses(analyses)
        
        # Combiner texte + photos (priorité aux photos mais texte comme validation)
        return self.combine_text_and_photo_analysis(text_analysis, photo_analysis)
    
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
                
                # Construire une justification enrichie
                justification_parts = [style_result.get('justification', '')]
                
                if est_conversion:
                    conversion_desc = f"Conversion d'ancien {type_conversion}" if type_conversion else "Conversion d'ancien espace"
                    justification_parts.append(f"🏭 {conversion_desc}")
                
                if contexte_detection.get('periode_mentionnee'):
                    justification_parts.append(f"📅 Période: {contexte_detection.get('periode_mentionnee')}")
                
                # Ajouter les indices architecturaux détectés
                elements_haussmannien = indices_architecturaux.get('elements_haussmannien', [])
                elements_atypique = indices_architecturaux.get('elements_atypique', [])
                elements_moderne = indices_architecturaux.get('elements_moderne', [])
                
                if elements_haussmannien:
                    justification_parts.append(f"🏛️ Éléments haussmanniens: {', '.join(elements_haussmannien[:3])}")
                if elements_atypique:
                    justification_parts.append(f"🏭 Éléments atypiques: {', '.join(elements_atypique[:3])}")
                if elements_moderne:
                    justification_parts.append(f"✨ Éléments modernes: {', '.join(elements_moderne[:3])}")
                
                justification = " | ".join(justification_parts)
                
                # Calculer le score
                base_score = self.calculate_style_score(style_type)
                
                # Si confiance globale très élevée (>0.85) et style atypique/haussmannien, on peut augmenter légèrement la confiance
                # Mais le score reste basé sur le style uniquement
                
                result['style'] = {
                    'type': style_type,
                    'confidence': style_confidence,
                    'score': base_score,
                    'justification': justification,
                    'indices': style_result.get('indices', []),
                    'details': {
                        'confiance_globale': style_confidence,
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
    
    def analyze_apartment_photos(self, photos_dir="data/photos"):
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
        
        # Analyser chaque photo
        analyses = []
        for i, photo_path in enumerate(photo_files, 1):
            print(f"\n📸 Analyse photo {i}: {os.path.basename(photo_path)}")
            analysis = self.analyze_single_photo(photo_path)
            if analysis:
                analyses.append(analysis)
        
        # Agréger les résultats
        if analyses:
            return self.aggregate_analyses(analyses)
        else:
            return None
    
    def analyze_single_photo(self, photo_path):
        """Analyse une photo individuelle avec cache"""
        # Générer une clé de cache basée sur le chemin du fichier
        # Pour les URLs, utiliser l'URL directement
        cache_key = photo_path if photo_path.startswith('http') else f"file:{photo_path}"
        
        # Vérifier le cache d'abord
        cached_result = self.cache.get('style_photo', cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Encoder l'image en base64
            with open(photo_path, 'rb') as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Appel à OpenAI Vision
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
                                'text': """Analyse cette photo d'appartement et estime:

1. STYLE ARCHITECTURAL (Ancien / Atypique / Neuf):
   - Ancien (20 pts): Haussmannien - moulures, parquet, hauteur sous plafond, cheminée, balcon en fer forgé
   - Atypique (10 pts): Loft, atypique, unique, original - espaces ouverts, volumes généreux, caractère unique
   - Neuf (0 pts): Tout le reste (moderne, contemporain, récent, années 20-70) - terrasse métal, vue, sol moderne, fenêtre moderne, hauteur plafond réduite, lignes épurées, matériaux modernes, design minimaliste
   - Autre: décris le style observé

2. CUISINE OUVERTE:
   - Oui: cuisine visible depuis le salon, pas de séparation murale
   - Non: cuisine fermée, séparée du salon

3. LUMINOSITÉ:
   - Excellente: très lumineux, nombreuses fenêtres, lumière naturelle abondante
   - Bonne: bien éclairé, quelques fenêtres, luminosité correcte
   - Moyenne: éclairage correct mais limité
   - Faible: peu lumineux, fenêtres petites ou peu nombreuses

Réponds au format JSON:
{
    "style": "haussmannien|moderne|autre",
    "note": "Pour le scoring: 'haussmannien' = ancien (20pts), tout le reste = neuf (0pts)",
    "style_confidence": 0.0-1.0,
    "style_details": "description détaillée des éléments observés",
    "cuisine_ouverte": true|false,
    "cuisine_confidence": 0.0-1.0,
    "cuisine_details": "description de la cuisine",
    "luminosite": "excellente|bonne|moyenne|faible",
    "luminosite_confidence": 0.0-1.0,
    "luminosite_details": "description de la luminosité",
    "elements_visuels": ["liste des éléments architecturaux observés"]
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
                'max_tokens': 800
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
                print(f"      Cuisine: {'Ouverte' if analysis.get('cuisine_ouverte') else 'Fermée'} (confiance: {analysis.get('cuisine_confidence', 0):.2f})")
                print(f"      Luminosité: {analysis.get('luminosite', 'N/A')} (confiance: {analysis.get('luminosite_confidence', 0):.2f})")
                
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
            
            analysis = {
                'style': style,
                'style_confidence': 0.7,
                'cuisine_ouverte': cuisine_ouverte,
                'cuisine_confidence': 0.7,
                'luminosite': luminosite,
                'luminosite_confidence': 0.7
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
        """Agrège les analyses de toutes les photos"""
        print(f"\n📊 AGRÉGATION DES {len(analyses)} ANALYSES")
        print("-" * 40)
        
        # Compter les styles (fusionner 70s avec moderne)
        styles = [a.get('style', 'inconnu') for a in analyses if a.get('style')]
        style_counts = {}
        for style in styles:
            # Fusionner 70s et 60s avec moderne
            style_normalized = style.lower()
            if '70' in style_normalized or 'seventies' in style_normalized or '60' in style_normalized:
                style_normalized = 'moderne'
            elif style_normalized not in ['moderne', 'contemporain']:
                style_normalized = style.lower()
            style_counts[style_normalized] = style_counts.get(style_normalized, 0) + 1
        
        # Compter les cuisines ouvertes
        cuisines_ouvertes = [a.get('cuisine_ouverte', False) for a in analyses if 'cuisine_ouverte' in a]
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
        
        # Déterminer les résultats finaux
        final_style = max(style_counts, key=style_counts.get) if style_counts else 'inconnu'
        final_cuisine_ouverte = cuisine_ouverte_ratio > 0.5
        final_luminosite = max(luminosite_counts, key=luminosite_counts.get) if luminosite_counts else 'inconnue'
        
        # Calculer les scores
        style_score = self.calculate_style_score(final_style)
        cuisine_score = self.calculate_cuisine_score(final_cuisine_ouverte)
        luminosite_score = self.calculate_luminosite_score(final_luminosite)
        
        result = {
            'style': {
                'type': final_style,
                'confidence': sum(style_confidences) / len(style_confidences) if style_confidences else 0,
                'score': style_score,
                'details': f"Style détecté: {final_style} (apparaît {style_counts.get(final_style, 0)} fois)"
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
