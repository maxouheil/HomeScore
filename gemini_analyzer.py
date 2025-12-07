#!/usr/bin/env python3
"""
Module d'analyse visuelle avec Google Gemini API
Remplace OpenAI pour réduire les coûts de 96% avec Gemini 1.5 Flash
"""

import os
import json
import time
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import PIL.Image
import requests
from io import BytesIO

# Charger les variables d'environnement
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Coûts par modèle (en USD par image)
COSTS = {
    'gemini-2.5-flash': 0.000075,  # $0.000075 par image (gratuit jusqu'à 15 RPM)
    'gemini-2.5-pro': 0.001315,    # $0.001315 par image
    'gemini-pro-latest': 0.0,      # Modèle texte uniquement
    'gemini-flash-latest': 0.000075,  # Alias pour flash
}

# Rate limiting pour respecter les quotas gratuits
RATE_LIMIT_RPM = 15  # Requêtes par minute pour Flash (gratuit)
_last_request_times = []


class GeminiAnalyzer:
    """Analyseur d'images utilisant Google Gemini API"""
    
    def __init__(self, model: str = 'gemini-2.5-flash'):
        """
        Initialise l'analyseur Gemini
        
        Args:
            model: Modèle à utiliser ('gemini-2.5-flash' ou 'gemini-2.5-pro')
        """
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY non trouvée. "
                "Créez un fichier .env avec GEMINI_API_KEY=votre_cle"
            )
        
        self.model_name = model
        self.model = genai.GenerativeModel(model)
        self.cost_per_image = COSTS.get(model, 0.000075)
        
    def _rate_limit(self):
        """Applique le rate limiting pour respecter les quotas gratuits"""
        global _last_request_times
        current_time = time.time()
        
        # Nettoyer les requêtes de plus d'une minute
        _last_request_times = [t for t in _last_request_times if current_time - t < 60]
        
        # Si on dépasse la limite, attendre
        if len(_last_request_times) >= RATE_LIMIT_RPM:
            sleep_time = 60 - (current_time - _last_request_times[0])
            if sleep_time > 0:
                print(f"⏳ Rate limit atteint, attente de {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                _last_request_times = []
        
        _last_request_times.append(time.time())
    
    def _load_image(self, image_source: Union[str, Path, bytes, PIL.Image.Image]) -> PIL.Image.Image:
        """
        Charge une image depuis différentes sources
        
        Args:
            image_source: URL, chemin fichier, bytes, ou PIL.Image
        
        Returns:
            Image PIL
        """
        if isinstance(image_source, PIL.Image.Image):
            return image_source
        
        if isinstance(image_source, (str, Path)):
            path = Path(image_source)
            
            # Si c'est une URL
            if str(path).startswith(('http://', 'https://')):
                response = requests.get(str(path))
                response.raise_for_status()
                return PIL.Image.open(BytesIO(response.content))
            
            # Si c'est un chemin local
            if path.exists():
                return PIL.Image.open(path)
            
            raise FileNotFoundError(f"Image non trouvée: {image_source}")
        
        if isinstance(image_source, bytes):
            return PIL.Image.open(BytesIO(image_source))
        
        raise ValueError(f"Type d'image non supporté: {type(image_source)}")
    
    def analyze_image(
        self,
        image_source: Union[str, Path, bytes, PIL.Image.Image],
        prompt: str,
        return_json: bool = False,
        max_retries: int = 3
    ) -> Union[str, Dict]:
        """
        Analyse une image avec Gemini
        
        Args:
            image_source: URL, chemin fichier, bytes, ou PIL.Image
            prompt: Question ou instruction pour l'analyse
            return_json: Si True, essaie de parser la réponse en JSON
            max_retries: Nombre de tentatives en cas d'erreur
        
        Returns:
            Réponse textuelle ou dictionnaire JSON
        """
        self._rate_limit()
        
        # Charger l'image
        img = self._load_image(image_source)
        
        # Préparer le prompt pour JSON si demandé
        if return_json:
            prompt = f"{prompt}\n\nRéponds UNIQUEMENT avec un JSON valide, sans texte supplémentaire, sans markdown."
        
        # Tentatives avec retry
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content([prompt, img])
                
                if not response.text:
                    raise ValueError("Réponse vide de Gemini")
                
                text = response.text.strip()
                
                # Parser JSON si demandé
                if return_json:
                    # Nettoyer le texte (enlever markdown si présent)
                    if text.startswith("```json"):
                        text = text[7:]
                    elif text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                    
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        # Si le parsing JSON échoue, retourner le texte brut
                        print(f"⚠️ Impossible de parser en JSON, retour du texte brut")
                        return {"raw_response": text}
                
                return text
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Backoff exponentiel
                    print(f"⚠️ Erreur (tentative {attempt + 1}/{max_retries}): {e}")
                    print(f"   Nouvelle tentative dans {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
    
    def analyze_multiple_images(
        self,
        image_sources: List[Union[str, Path, bytes, PIL.Image.Image]],
        prompt: str,
        return_json: bool = False
    ) -> Union[str, Dict]:
        """
        Analyse plusieurs images avec Gemini
        
        Args:
            image_sources: Liste d'images à analyser
            prompt: Question ou instruction pour l'analyse
            return_json: Si True, essaie de parser la réponse en JSON
        
        Returns:
            Réponse textuelle ou dictionnaire JSON
        """
        self._rate_limit()
        
        # Charger toutes les images
        images = [self._load_image(img) for img in image_sources]
        
        # Préparer le prompt
        if return_json:
            prompt = f"{prompt}\n\nRéponds UNIQUEMENT avec un JSON valide, sans texte supplémentaire."
        
        # Créer le contenu avec toutes les images
        content = [prompt] + images
        
        try:
            response = self.model.generate_content(content)
            
            if not response.text:
                raise ValueError("Réponse vide de Gemini")
            
            text = response.text.strip()
            
            # Parser JSON si demandé
            if return_json:
                if text.startswith("```json"):
                    text = text[7:]
                elif text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw_response": text}
            
            return text
            
        except Exception as e:
            raise Exception(f"Erreur lors de l'analyse de plusieurs images: {e}")
    
    def estimate_cost(self, num_images: int) -> float:
        """
        Estime le coût pour un nombre d'images
        
        Args:
            num_images: Nombre d'images
        
        Returns:
            Coût estimé en USD
        """
        return num_images * self.cost_per_image


# Fonctions utilitaires pour les cas d'usage spécifiques

def analyze_apartment_style(image_paths: List[str]) -> Dict:
    """
    Analyse le style d'un appartement à partir de photos avec classification détaillée
    
    Args:
        image_paths: Liste des chemins vers les photos
    
    Returns:
        Dictionnaire avec les informations de style incluant classification et indice
    """
    analyzer = GeminiAnalyzer('gemini-2.5-flash')
    
    prompt = """Analyse ces photos d'appartement et réponds en JSON avec:
    - classification_style (une seule valeur parmi: "haussmannien", "decennies_jusque_80", "moderne")
    - indice_style (nombre entre 0 et 100, où 0 = très haussmannien, 50 = décennies jusqu'à 80, 100 = très moderne)
    - hauteur_plafond_estimee (en mètres, estimation)
    - type_pieces_visibles (liste des types de pièces visibles)
    - ambiance (chaleureux, minimaliste, luxueux, etc.)
    - materiau_dominant (bois, pierre, béton, etc.)
    - elements_style (liste des éléments caractéristiques observés: moulures, parquet, etc.)
    
    Classification:
    - "haussmannien": immeubles parisiens typiques 1850-1870, hauts plafonds, moulures, parquet, cheminées
    - "decennies_jusque_80": années 50-80, style fonctionnel, moins d'ornements, matériaux modernes
    - "moderne": années 90+, design contemporain, matériaux modernes, ouvertures, espaces ouverts
    """
    
    return analyzer.analyze_multiple_images(image_paths, prompt, return_json=True)


def detect_bathtub(image_path: str) -> Dict:
    """
    Détecte la présence d'une baignoire dans une photo
    
    Args:
        image_path: Chemin vers la photo
    
    Returns:
        Dictionnaire avec la détection
    """
    analyzer = GeminiAnalyzer('gemini-2.5-flash')
    
    prompt = """Analyse cette photo de salle de bain et réponds en JSON:
    - presence_baignoire (oui/non)
    - type_baignoire (droite, coin, balnéo, etc. ou null si absente)
    - presence_douche (oui/non)
    - confiance (0-100, niveau de confiance de la détection)
    """
    
    return analyzer.analyze_image(image_path, prompt, return_json=True)


def detect_open_kitchen(image_path: str) -> Dict:
    """
    Détecte si la cuisine est ouverte ou fermée
    
    Args:
        image_path: Chemin vers la photo
    
    Returns:
        Dictionnaire avec la détection
    """
    analyzer = GeminiAnalyzer('gemini-2.5-flash')
    
    prompt = """Analyse cette photo de cuisine et réponds en JSON:
    - cuisine_ouverte (oui/non)
    - type_cuisine (ouverte, fermée, semi-ouverte)
    - presence_ile (oui/non)
    - confiance (0-100)
    """
    
    return analyzer.analyze_image(image_path, prompt, return_json=True)


def estimate_ceiling_height(image_path: str) -> Dict:
    """
    Estime la hauteur sous plafond
    
    Args:
        image_path: Chemin vers la photo
    
    Returns:
        Dictionnaire avec l'estimation
    """
    analyzer = GeminiAnalyzer('gemini-2.5-pro')  # Utilise Pro pour meilleure précision
    
    prompt = """Analyse cette photo et estime la hauteur sous plafond en mètres.
    Réponds en JSON:
    - hauteur_estimee (en mètres, nombre décimal)
    - confiance (0-100)
    - elements_reference (liste des éléments utilisés pour l'estimation: portes, fenêtres, etc.)
    """
    
    return analyzer.analyze_image(image_path, prompt, return_json=True)


def analyze_living_room_size(image_path: str, surface_totale_m2: float = None) -> Dict:
    """
    Analyse la taille de la pièce de vie et calcule le pourcentage sur la surface totale
    
    Args:
        image_path: Chemin vers la photo
        surface_totale_m2: Surface totale de l'appartement en m² (optionnel)
    
    Returns:
        Dictionnaire avec l'analyse incluant le pourcentage
    """
    analyzer = GeminiAnalyzer('gemini-2.5-flash')
    
    prompt_surface = f"Surface totale de l'appartement: {surface_totale_m2} m². " if surface_totale_m2 else ""
    
    prompt = f"""{prompt_surface}Analyse cette photo de pièce de vie et réponds en JSON:
    - taille_estimee (petite, moyenne, grande, tres_grande)
    - surface_estimee_m2 (estimation en m², nombre décimal)
    - confiance (0-100)
    - elements_visibles (liste des éléments visibles: canapé, table, etc.)
    - pourcentage_surface_totale (pourcentage de la surface totale si surface_totale_m2 fournie, sinon null)
    """
    
    result = analyzer.analyze_image(image_path, prompt, return_json=True)
    
    # Calculer le pourcentage si la surface totale est fournie
    if surface_totale_m2 and 'surface_estimee_m2' in result:
        surface_estimee = result.get('surface_estimee_m2', 0)
        if isinstance(surface_estimee, (int, float)) and surface_totale_m2 > 0:
            result['pourcentage_surface_totale'] = round((surface_estimee / surface_totale_m2) * 100, 1)
    
    return result


def estimate_distance_vis_a_vis(image_path: str) -> Dict:
    """
    Estime la distance vis-à-vis depuis une fenêtre
    
    Args:
        image_path: Chemin vers la photo
    
    Returns:
        Dictionnaire avec l'estimation
    """
    analyzer = GeminiAnalyzer('gemini-2.5-flash')
    
    prompt = """Analyse cette photo prise depuis une fenêtre et estime la distance vis-à-vis.
    Réponds en JSON:
    - distance_estimee_m (en mètres, nombre)
    - confiance (0-100)
    - type_vis_a_vis (immeuble, mur, espace_vert, etc.)
    - luminosite_impactee (oui/non, si le vis-à-vis impacte la luminosité)
    """
    
    return analyzer.analyze_image(image_path, prompt, return_json=True)


if __name__ == "__main__":
    # Test simple
    print("🧪 Test du module Gemini Analyzer")
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY non configurée")
        print("   Créez un fichier .env avec GEMINI_API_KEY=votre_cle")
    else:
        print("✅ Clé API trouvée")
        analyzer = GeminiAnalyzer('gemini-2.5-flash')
        print(f"✅ Modèle {analyzer.model_name} initialisé")
        print(f"💰 Coût par image: ${analyzer.cost_per_image:.6f}")
        print(f"💰 Coût pour 100 images: ${analyzer.estimate_cost(100):.4f}")

