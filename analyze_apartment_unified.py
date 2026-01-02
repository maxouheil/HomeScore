#!/usr/bin/env python3
"""
Analyse unifiée d'appartement avec Gemini Flash
Analyse style, cuisine, salle de bain, luminosité en UNE SEULE requête
"""

import json
import os
from typing import Dict, List, Optional, Union
from pathlib import Path
from photo_manager import PhotoManager
from cache_api import get_cache
from dotenv import load_dotenv
from gemini_analyzer import GeminiAnalyzer

load_dotenv()


class UnifiedApartmentAnalyzer:
    """Analyseur unifié qui analyse tout en une seule requête avec Gemini Flash"""
    
    def __init__(self):
        self.analyzer = GeminiAnalyzer('gemini-2.5-flash')
        self.model = "gemini-2.5-flash"
        self.photo_manager = PhotoManager()
        self.cache = get_cache()
    
    def _get_cache_input_data(self, apartment_id: str, photos: List[Dict], max_photos: int = 7) -> str:
        """Génère les données d'entrée pour le cache basées sur l'ID et les URLs des photos"""
        photo_urls = [p.get('url', '') for p in photos[:max_photos]]
        return f"{apartment_id}:{':'.join(photo_urls)}"
    
    def _load_photos_for_analysis(self, photos: List[Dict], max_photos: int = 7) -> List:
        """
        Charge les photos depuis les chemins locaux ou URLs pour Gemini
        
        Args:
            photos: Liste des photos avec local_path ou url
            max_photos: Nombre maximum de photos à analyser
        
        Returns:
            Liste des sources d'images (chemins ou URLs) pour GeminiAnalyzer
        """
        image_sources = []
        
        for photo in photos[:max_photos]:
            # Priorité au chemin local si disponible
            local_path = photo.get('local_path')
            if local_path and os.path.exists(local_path):
                image_sources.append(local_path)
            else:
                # Sinon utiliser l'URL (GeminiAnalyzer peut charger depuis URL)
                photo_url = photo.get('url', '')
                if photo_url:
                    image_sources.append(photo_url)
        
        return image_sources
    
    def analyze_apartment_unified(
        self, 
        apartment_data: Dict,
        max_photos: int = 7,  # Analyser jusqu'à 7 photos pour une meilleure couverture des critères
        force_reanalysis: bool = False  # Force la réanalyse même si déjà analysé
    ) -> Optional[Dict]:
        """
        Analyse un appartement en UNE SEULE requête Gemini Flash
        
        Analyse simultanément :
        - Style (haussmannien, moderne, atypique, etc.)
        - Cuisine (ouverte/fermée)
        - Salle de bain (baignoire/douche)
        - Luminosité
        - Hauteur plafond
        - Taille pièce de vie
        - Vis-à-vis
        
        Args:
            apartment_data: Données de l'appartement
            max_photos: Nombre maximum de photos à analyser (défaut: 7 pour une meilleure analyse)
        
        Returns:
            Résultat unifié de l'analyse
        """
        apartment_id = apartment_data.get('id', 'unknown')
        description = apartment_data.get('description', '')
        caracteristiques = apartment_data.get('caracteristiques', '')
        photos = apartment_data.get('photos', [])
        
        if not photos:
            print(f"   ⚠️  Aucune photo pour l'appartement {apartment_id}")
            return None
        
        # Préparer les données de cache (toujours nécessaire pour la mise en cache après)
        cache_input_data = self._get_cache_input_data(apartment_id, photos, max_photos=max_photos)
        
        # OPTIMISATION: Vérifier le cache seulement si pas de réanalyse forcée
        if not force_reanalysis:
            cached = self.cache.get("unified_analysis", cache_input_data)
            if cached:
                print(f"   💾 Cache hit: analyse unifiée (évite re-analyse IA)")
                return cached
        else:
            print(f"   🔄 Réanalyse forcée pour {apartment_id} (ignore le cache)")
        
        # Debug: afficher le nombre de photos disponibles et max_photos
        total_photos = len(photos)
        photos_to_analyze = min(total_photos, max_photos)
        print(f"   🤖 Analyse unifiée avec {self.model} ({photos_to_analyze}/{total_photos} photos, max_photos={max_photos})...")
        
        # Charger les photos pour Gemini
        image_sources = self._load_photos_for_analysis(photos, max_photos=max_photos)
        
        # Debug: afficher combien de photos ont été chargées
        print(f"   📸 Photos chargées pour analyse: {len(image_sources)}")
        
        if not image_sources:
            print(f"   ⚠️  Impossible de charger les photos")
            return None
        
        # Préparer le prompt unifié
        prompt = self._create_unified_prompt(description, caracteristiques)
        
        try:
            # UNE SEULE requête Gemini pour tout analyser (multi-images)
            response_data = self.analyzer.analyze_multiple_images(
                image_sources,
                prompt,
                return_json=True
            )
            
            # Debug: afficher la réponse brute pour la cuisine
            if isinstance(response_data, dict) and 'raw_response' not in response_data:
                cuisine_raw = response_data.get('cuisine', {})
                if cuisine_raw:
                    print(f"      🔍 [DEBUG] Réponse cuisine brute: {cuisine_raw}")
            
            # Adapter la réponse au format attendu
            analysis_result = self._parse_unified_response(response_data, apartment_id, len(image_sources))
            
            # Debug: afficher ce qui a été détecté
            if analysis_result:
                detected = []
                if analysis_result.get('style'): detected.append('style')
                cuisine_data = analysis_result.get('cuisine', {})
                if cuisine_data and cuisine_data.get('ouverte') is not None:
                    detected.append('cuisine')
                    cuisine_status = 'ouverte' if cuisine_data.get('ouverte') else 'fermée'
                    if not cuisine_data.get('visible', True):
                        cuisine_status += ' (non visible)'
                    print(f"      🍳 Cuisine: {cuisine_status}")
                elif cuisine_data and cuisine_data.get('visible') is False:
                    print(f"      🍳 Cuisine: non visible dans les photos")
                if analysis_result.get('douche'): detected.append('douche')
                if analysis_result.get('baignoire'): detected.append('baignoire')
                if analysis_result.get('luminosite'): detected.append('luminosite')
                if analysis_result.get('hauteur_plafond'): detected.append('hauteur_plafond')
                if analysis_result.get('piece_vie'): detected.append('piece_vie')
                if analysis_result.get('annee_construction'): detected.append('annee_construction')
                if analysis_result.get('visavis'): detected.append('visavis')
                print(f"      🔍 Critères détectés: {', '.join(detected) if detected else 'aucun'}")
            
            if analysis_result:
                # Mettre en cache seulement si pas de réanalyse forcée (pour éviter d'écraser avec les mêmes données)
                # Si réanalyse forcée, on met quand même à jour le cache avec les nouvelles données
                self.cache.set("unified_analysis", cache_input_data, analysis_result)
                if force_reanalysis:
                    print(f"   ✅ Analyse unifiée terminée (réanalyse forcée, cache mis à jour)")
                else:
                    print(f"   ✅ Analyse unifiée terminée")
                return analysis_result
            else:
                print(f"   ⚠️  Erreur parsing de la réponse")
                return None
                
        except Exception as e:
            print(f"   ❌ Erreur analyse unifiée: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_unified_prompt(self, description: str, caracteristiques: str) -> str:
        """Crée le prompt unifié optimisé pour analyser tout en une fois avec analyse détaillée"""
        return f"""Analyse ces photos d'appartement (jusqu'à 7 images) et réponds en JSON. Examine TOUTES les photos attentivement pour chaque critère.

TEXTE: {description[:200]} {caracteristiques[:100]}

## CRITÈRES À ANALYSER EN DÉTAIL:

1. **STYLE ARCHITECTURAL**: 
   IMPORTANT: Indique UNIQUEMENT les éléments que tu VOIS et DÉTECTES dans les photos. Ne mentionne JAMAIS ce qui est absent ou manquant. Utilise des phrases positives décrivant ce qui est présent.
   
   - "haussmannien": Détecte si tu vois: moulures au plafond, parquet pointe de Hongrie ou parquet ancien, cheminée visible, hauteur plafond élevée (>2.80m), balcon avec fer forgé, rosaces décoratives, éléments décoratifs classiques, portes hautes, fenêtres avec moulures
   - "70s": Détecte si tu vois: lignes épurées des années 70, parquet 70s (lattes larges, teinte caractéristique), mobilier style HLM, grande terrasse ou balcon, carrelage coloré, design caractéristique des années 1970, matériaux typiques de l'époque
   - "moderne": Détecte si tu vois: poteaux apparents, structure atypique, style minimaliste, matériaux modernes (béton, métal, verre), fenêtres contemporaines, plafond bas/réduit (<2.60m), terrasse métal, design épuré sans ornements
   - "atypique": Détecte si tu vois: loft, conversion d'usine/bureau, béton brut, caractère industriel, volumes généreux, espace ouvert, structure originale
   - "autre": style non classable avec les critères ci-dessus
   
   Dans "elements_detectes", liste UNIQUEMENT les éléments architecturaux que tu observes réellement dans les photos (ex: ["moulures", "parquet", "cheminée"] ou ["lignes épurées", "parquet 70s"] ou ["poteaux", "style minimaliste"]). Ne liste pas ce qui est absent.

2. **ANNEE_CONSTRUCTION**: 
   - Estimer depuis l'architecture, les détails, les matériaux
   - Fournir année ou décennie (ex: 1970, 1980s)

3. **CUISINE (CRITIQUE)**: 
   - Examine TOUTES les photos pour détecter la cuisine
   - Cherche: réfrigérateur, four, plaques de cuisson, évier, meubles de cuisine, îlot central, bar, hotte
   - Si cuisine visible (même partiellement depuis salon/séjour):
     * "ouverte": sans mur/porte, directement connectée au salon, bar ou îlot visible, espace fluide
     * "fermée": séparée par un mur complet, porte, espace clos
   - Si cuisine ABSOLUMENT PAS visible dans aucune photo: "visible": false, "ouverte": null

4. **DOUCHE**: 
   - Présente si cabine de douche, douche italienne, ou pommeau de douche visible dans salle de bain
   - Absente si seulement baignoire ou pas de salle de bain visible

5. **BAIGNOIRE**: 
   - Présente si baignoire visible (grand récipient rectangulaire/ovale pour se baigner)
   - Absente si seulement douche ou pas de salle de bain visible

6. **LUMINOSITÉ**: 
   - "tres_lumineux": très clair, beaucoup de lumière naturelle, grandes fenêtres, orientation favorable
   - "lumineux": clair, bonne luminosité naturelle
   - "moyen": luminosité moyenne
   - "faible": sombre, peu de lumière naturelle

7. **HAUTEUR_PLAFOND (CRITIQUE)**: 
   - Estimer en mètres (typique: 2.5-3.5m)
   - Utiliser références: hauteur des portes (standard ~2.10m), fenêtres, proportions des murs
   - Comparer avec éléments connus pour estimation précise
   - Si non visible, mettre null

8. **PIECE_VIE (CRITIQUE - TAILLE SALON/SÉJOUR)**: 
   - Identifier si photos montrent le salon/séjour (canapé, table basse, espace de vie)
   - Si salon visible, estimer sa taille en m² en observant:
     * Profondeur de la pièce (distance mur avant → mur arrière)
     * Largeur visible de la pièce
     * Meubles comme référence (canapé standard ~2m, table basse ~1m, chaise ~0.5m)
   - Fournir estimation en m² (ex: 20, 25, 30, 35, 40)
   - Catégorie: "grande" si >25m², "moyenne" si 15-25m², "petite" si <15m²
   - Si pas de salon visible, mettre null

9. **VISAVIS**: 
   - Analyser UNIQUEMENT les fenêtres de la pièce principale (salon/séjour)
   - Distance en mètres jusqu'au bâtiment/immeuble le plus proche visible
   - Estimer largeur de rue si visible (étroite <10m, moyenne 10-15m, large >15m)
   - Distance: 0-100m, null si pas de fenêtre visible ou vue dégagée sans vis-à-vis >50m
   - Catégorie: "good" si >20m, "moyen" si 10-20m, "bad" si <10m

Réponds UNIQUEMENT en JSON (pas de texte avant/après):
{{
    "style": {{"type": "haussmannien|moderne|atypique|70s|autre", "elements_detectes": ["mot1", "mot2"], "confidence": 0.0-1.0, "justification": "Décris UNIQUEMENT les éléments que tu vois (ex: 'Moulures au plafond, parquet pointe de Hongrie, cheminée visible' ou 'Lignes épurées, parquet 70s, grande terrasse' ou 'Poteaux apparents, style minimaliste'). Ne mentionne JAMAIS ce qui est absent."}},
    "annee_construction": {{"annee": 1970, "decennie": "1970s", "confidence": 0.0-1.0}},
    "cuisine": {{"ouverte": true|false|null, "visible": true|false, "confidence": 0.0-1.0, "justification": "description courte"}},
    "douche": {{"presente": true|false, "confidence": 0.0-1.0}},
    "baignoire": {{"presente": true|false, "confidence": 0.0-1.0}},
    "luminosite": {{"type": "tres_lumineux|lumineux|moyen|faible", "confidence": 0.0-1.0}},
    "hauteur_plafond": {{"hauteur_estimee": 2.8, "confidence": 0.0-1.0, "justification": "méthode d'estimation"}},
    "piece_vie": {{"taille_m2": 25, "taille": "grande|moyenne|petite", "confidence": 0.0-1.0, "justification": "méthode d'estimation"}},
    "visavis": {{"distance": 25, "category": "good|moyen|bad", "confidence": 0.0-1.0}}
}}"""
    
    def _process_cuisine_data(self, cuisine_data: Dict) -> Dict:
        """Traite les données de la cuisine et gère le cas où elle n'est pas visible"""
        # Si cuisine_data est vide ou None, la cuisine n'a pas été détectée
        if not cuisine_data:
            return {
                'ouverte': None,  # None = non détectée
                'visible': False,
                'confidence': 0,
                'score': 0,
                'justification': 'Cuisine non détectée dans les photos'
            }
        
        cuisine_visible = cuisine_data.get('visible')
        cuisine_ouverte = cuisine_data.get('ouverte')
        
        # Si visible est explicitement False, la cuisine n'est pas visible
        if cuisine_visible is False:
            return {
                'ouverte': None,  # None = non détectée (différent de False = fermée)
                'visible': False,
                'confidence': 0,
                'score': 0,
                'justification': cuisine_data.get('justification', 'Cuisine non visible dans les photos')
            }
        
        # Si cuisine_ouverte est None mais visible n'est pas False, 
        # on assume que la cuisine est visible mais on ne peut pas déterminer si elle est ouverte/fermée
        # Dans ce cas, on retourne None pour indiquer qu'on ne peut pas déterminer
        if cuisine_ouverte is None:
            # Si visible n'est pas spécifié, on assume True par défaut
            if cuisine_visible is None:
                return {
                    'ouverte': None,  # Non déterminable
                    'visible': True,  # On assume visible mais non analysable
                    'confidence': 0,
                    'score': 0,
                    'justification': cuisine_data.get('justification', 'Cuisine visible mais statut ouverte/fermée non déterminable')
                }
        
        # Si on arrive ici, on a une valeur pour ouverte (True ou False)
        return {
            'ouverte': cuisine_ouverte if cuisine_ouverte is not None else False,
            'visible': cuisine_visible if cuisine_visible is not None else True,
            'confidence': cuisine_data.get('confidence', 0.5),
            'score': cuisine_data.get('score', 0),
            'justification': cuisine_data.get('justification', '')
        }
    
    def _process_visavis_data(self, visavis_data: Dict) -> Dict:
        """Traite les données du vis-à-vis et calcule la catégorie si nécessaire"""
        distance = visavis_data.get('distance')
        
        # Calculer la catégorie si pas fournie mais distance disponible
        category = visavis_data.get('category')
        if distance is not None and not category:
            if distance > 20:
                category = 'good'
            elif distance >= 10:
                category = 'moyen'
            else:
                category = 'bad'
        
        return {
            'distance': distance,
            'category': category,
            'confidence': visavis_data.get('confidence', 0.5),
            'justification': visavis_data.get('justification', '')
        }
    
    def _parse_unified_response(self, response_data: Union[str, Dict], apartment_id: str, photos_analyzed: int = 0) -> Optional[Dict]:
        """Parse la réponse JSON de l'analyse unifiée"""
        try:
            # Si c'est déjà un dict (cas Gemini avec return_json=True)
            if isinstance(response_data, dict):
                data = response_data
                # Si Gemini a retourné raw_response, essayer de parser
                if 'raw_response' in data:
                    try:
                        data = json.loads(data['raw_response'])
                    except:
                        pass
            else:
                # Si c'est une string, parser le JSON
                text = str(response_data).strip()
                if text.startswith('```json'):
                    text = text.replace('```json', '').replace('```', '').strip()
                elif text.startswith('```'):
                    text = text.replace('```', '').strip()
                data = json.loads(text)
            
            # Adapter au format attendu par le système
            result = {
                'style': {
                    'type': data.get('style', {}).get('type', 'autre'),
                    'confidence': data.get('style', {}).get('confidence', 0.5),
                    'score': data.get('style', {}).get('score', 0),
                    'justification': data.get('style', {}).get('justification', ''),
                    'details': {
                        'elements_detectes': data.get('style', {}).get('elements_detectes', [])
                    }
                },
                'annee_construction': {
                    'annee': data.get('annee_construction', {}).get('annee'),
                    'decennie': data.get('annee_construction', {}).get('decennie'),
                    'confidence': data.get('annee_construction', {}).get('confidence', 0.5),
                    'justification': data.get('annee_construction', {}).get('justification', '')
                },
                'cuisine': self._process_cuisine_data(data.get('cuisine', {})),
                'douche': {
                    'presente': data.get('douche', {}).get('presente', False),
                    'confidence': data.get('douche', {}).get('confidence', 0.5),
                    'justification': data.get('douche', {}).get('justification', '')
                },
                'baignoire': {
                    # Support ancien format (salle_de_bain) et nouveau format (baignoire)
                    'presente': data.get('baignoire', {}).get('presente', False) or 
                               data.get('salle_de_bain', {}).get('baignoire', False),
                    'confidence': data.get('baignoire', {}).get('confidence', 0.5) or 
                                 data.get('salle_de_bain', {}).get('confidence', 0.5),
                    'score': data.get('baignoire', {}).get('score', 0) or 
                            data.get('salle_de_bain', {}).get('score', 0),
                    'justification': data.get('baignoire', {}).get('justification', '') or 
                                   data.get('salle_de_bain', {}).get('justification', '')
                },
                'luminosite': {
                    'type': data.get('luminosite', {}).get('type', 'moyen'),
                    'confidence': data.get('luminosite', {}).get('confidence', 0.5),
                    'score': data.get('luminosite', {}).get('score', 0),
                    'justification': data.get('luminosite', {}).get('justification', '')
                },
                'hauteur_plafond': {
                    'hauteur_estimee': data.get('hauteur_plafond', {}).get('hauteur_estimee'),
                    'confidence': data.get('hauteur_plafond', {}).get('confidence', 0.5),
                    'justification': data.get('hauteur_plafond', {}).get('justification', '')
                },
                'piece_vie': {
                    'taille_m2': data.get('piece_vie', {}).get('taille_m2'),
                    'taille': data.get('piece_vie', {}).get('taille', 'moyenne'),
                    'confidence': data.get('piece_vie', {}).get('confidence', 0.5),
                    'justification': data.get('piece_vie', {}).get('justification', '')
                },
                'visavis': self._process_visavis_data(data.get('visavis', {})),
                'photos_analyzed': data.get('photos_analyzed', photos_analyzed),
                'method': 'unified_analysis',
                'model': self.model
            }
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Erreur parsing JSON: {e}")
            print(f"   Réponse reçue: {str(response_data)[:500]}")
            return None
        except Exception as e:
            print(f"   ⚠️  Erreur parsing: {e}")
            import traceback
            traceback.print_exc()
            return None


def analyze_apartment_unified(apartment_data: Dict) -> Optional[Dict]:
    """
    Fonction utilitaire pour analyser un appartement de manière unifiée
    
    Args:
        apartment_data: Données de l'appartement
    
    Returns:
        Résultat de l'analyse unifiée
    """
    analyzer = UnifiedApartmentAnalyzer()
    return analyzer.analyze_apartment_unified(apartment_data)


if __name__ == "__main__":
    """Test de l'analyseur unifié"""
    from data_loader import load_apartments
    
    print("🧪 TEST ANALYSEUR UNIFIÉ")
    print("=" * 60)
    
    apartments = load_apartments(prefer_api=True)
    if apartments:
        test_apt = apartments[0]
        print(f"\n📋 Test avec appartement: {test_apt.get('id')}")
        print(f"   Titre: {test_apt.get('titre')}")
        print(f"   Photos: {len(test_apt.get('photos', []))}")
        
        analyzer = UnifiedApartmentAnalyzer()
        result = analyzer.analyze_apartment_unified(test_apt, max_photos=7)  # Analyse jusqu'à 7 photos
        
        if result:
            print(f"\n✅ RÉSULTATS DE L'ANALYSE UNIFIÉE:")
            print(f"   Style: {result['style']['type']} (confiance: {result['style']['confidence']:.2f})")
            print(f"   Cuisine: {'Ouverte' if result['cuisine']['ouverte'] else 'Fermée'} (confiance: {result['cuisine']['confidence']:.2f})")
            print(f"   Baignoire: {'Oui' if result['baignoire']['presente'] else 'Non'} (confiance: {result['baignoire']['confidence']:.2f})")
            print(f"   Luminosité: {result['luminosite']['type']} (confiance: {result['luminosite']['confidence']:.2f})")
            print(f"   Photos analysées: {result['photos_analyzed']}")
            print(f"   Modèle: {result['model']}")
        else:
            print("❌ Échec de l'analyse")
    else:
        print("❌ Aucun appartement trouvé")

