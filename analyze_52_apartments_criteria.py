#!/usr/bin/env python3
"""
Script optimisé pour analyser les 10 critères des 52 appartements
avec Gemini Flash Ultra optimisé pour vitesse et affichage instantané dans le frontend
"""

import json
import os
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Imports pour l'analyse
from gemini_analyzer import GeminiAnalyzer
from photo_manager import PhotoManager
from cache_api import get_cache
from scoring import load_scoring_config

load_dotenv()

# Les 10 critères à analyser
CRITERIA = [
    'haussmanien',
    'quartier',  # localisation
    'prix',
    'luminosite',
    'cuisine_ouverte',
    'ascenseur',
    'large_piece_vie',
    'hauteur_plafond',
    'renove',
    'calme'
]

class FastCriteriaAnalyzer:
    """Analyseur ultra-optimisé pour les 10 critères avec Gemini Flash"""
    
    def __init__(self):
        self.analyzer = GeminiAnalyzer('gemini-2.5-flash')
        self.photo_manager = PhotoManager()
        self.cache = get_cache()
        self.config = load_scoring_config()
    
    def load_apartment_data(self, apartment_id: str) -> Optional[Dict]:
        """Charge les données d'un appartement"""
        filepath = f"data/appartements/{apartment_id}.json"
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Charger aussi les scores si disponibles
            score_file = f"data/scores/apartment_{apartment_id}_score.json"
            if os.path.exists(score_file):
                with open(score_file, 'r', encoding='utf-8') as f:
                    score_data = json.load(f)
                    data.update(score_data)
            
            return data
        except Exception as e:
            print(f"❌ Erreur chargement {apartment_id}: {e}")
            return None
    
    def get_52_apartments(self) -> List[str]:
        """Récupère les IDs des 52 appartements"""
        apartments_dir = 'data/appartements'
        scores_dir = 'data/scores'
        
        if not os.path.exists(apartments_dir):
            return []
        
        # Trouver tous les appartements scrapés
        apartment_files = [f for f in os.listdir(apartments_dir) 
                          if f.endswith('.json') and not f.startswith('test_')]
        
        # Trier par date de modification (plus récents en premier)
        apartment_files_with_time = []
        for apartment_file in apartment_files:
            apartment_id = apartment_file.replace('.json', '')
            filepath = os.path.join(apartments_dir, apartment_file)
            mtime = os.path.getmtime(filepath)
            apartment_files_with_time.append((apartment_id, mtime))
        
        # Trier par date décroissante et prendre les 52 plus récents
        apartment_files_with_time.sort(key=lambda x: x[1], reverse=True)
        apartment_ids = [apt_id for apt_id, _ in apartment_files_with_time[:52]]
        
        return apartment_ids
    
    def analyze_criteria_unified(self, apartment: Dict) -> Dict:
        """
        Analyse les 10 critères en utilisant :
        - Fonctions de scoring existantes pour les critères basés sur texte
        - Gemini Flash pour les critères nécessitant des photos
        """
        apartment_id = apartment.get('id', 'unknown')
        description = apartment.get('description', '')
        caracteristiques = apartment.get('caracteristiques', '')
        photos = apartment.get('photos', [])
        
        # Vérifier le cache
        cache_key = f"criteria_analysis_{apartment_id}"
        cached = self.cache.get("criteria_analysis", cache_key)
        if cached:
            return cached
        
        # ÉTAPE 1: Analyser les critères basés sur texte avec les fonctions de scoring existantes
        result = self._analyze_text_based_criteria(apartment)
        
        # ÉTAPE 2: Analyser les critères nécessitant des photos avec Gemini Flash
        image_sources = []
        photos_dir = f"data/photos/{apartment_id}"
        
        # PRIORITÉ 1: Chercher les photos dans le dossier local
        if os.path.exists(photos_dir):
            photo_files = []
            try:
                for filename in os.listdir(photos_dir):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        photo_path = os.path.join(photos_dir, filename)
                        if os.path.exists(photo_path):
                            photo_files.append(photo_path)
                
                # Trier les fichiers par numéro de photo (photo_1, photo_2, etc.)
                def get_photo_number(path):
                    """Extrait le numéro de la photo depuis le nom de fichier"""
                    filename = os.path.basename(path)
                    # Chercher photo_N_xxx ou N_xxx
                    import re
                    match = re.search(r'photo[_\s]*(\d+)', filename, re.IGNORECASE)
                    if match:
                        return int(match.group(1))
                    # Sinon chercher juste un nombre au début
                    match = re.search(r'^(\d+)', filename)
                    if match:
                        return int(match.group(1))
                    return 9999  # Mettre à la fin si pas de numéro
                
                photo_files.sort(key=get_photo_number)
                
                # Prendre les 2 premières photos
                for photo_path in photo_files[:2]:
                    image_sources.append(photo_path)
                
                if image_sources:
                    print(f"   📸 {len(image_sources)} photo(s) locale(s) trouvée(s) dans {photos_dir}")
            except Exception as e:
                print(f"   ⚠️ Erreur lecture dossier photos: {e}")
        
        # PRIORITÉ 2: Si pas de photos locales, utiliser les URLs depuis les données
        if not image_sources and photos:
            for photo in photos[:2]:
                if isinstance(photo, dict):
                    local_path = photo.get('local_path', '')
                    if local_path and os.path.exists(local_path):
                        image_sources.append(local_path)
                    else:
                        url = photo.get('url', '')
                        if url and (url.startswith('http') or url.startswith('https')):
                            image_sources.append(url)
                elif isinstance(photo, str):
                    if os.path.exists(photo):
                        image_sources.append(photo)
                    elif photo.startswith('http') or photo.startswith('https'):
                        image_sources.append(photo)
        
        if image_sources:
            print(f"   📸 {len(image_sources)} photo(s) chargée(s) pour analyse")
            try:
                # Analyser avec Gemini Flash les critères nécessitant des photos
                photo_based_result = self._analyze_photo_based_criteria(apartment, image_sources)
                # Fusionner avec les résultats texte
                result.update(photo_based_result)
            except Exception as e:
                print(f"   ⚠️ Erreur analyse photos: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ⚠️ Pas de photos trouvées pour {apartment_id} (dossier: {photos_dir}) - analyse texte uniquement")
        
        # Mettre en cache
        if result:
            self.cache.set("criteria_analysis", cache_key, result)
        
        return result
    
    def _analyze_text_based_criteria(self, apartment: Dict) -> Dict:
        """Analyse les critères basés sur le texte avec les fonctions de scoring existantes"""
        from scoring import (
            score_localisation, score_prix, score_style, score_ensoleillement,
            score_ascenseur, score_renove, score_calme
        )
        
        result = {}
        
        try:
            # 1. QUARTIER (localisation)
            loc_score = score_localisation(apartment, self.config)
            result['quartier'] = {
                'tier1': loc_score.get('tier') == 'tier1',
                'zone': loc_score.get('justification', '')[:50],
                'confidence': 0.9 if loc_score.get('tier') else 0.5
            }
        except Exception as e:
            result['quartier'] = {'tier1': False, 'zone': '', 'confidence': 0.0}
        
        try:
            # 2. PRIX
            prix_score = score_prix(apartment, self.config)
            result['prix'] = {
                'tier1': prix_score.get('tier') == 'tier1',
                'prix_m2': self._extract_prix_m2(apartment),
                'confidence': 0.9 if prix_score.get('tier') else 0.5
            }
        except Exception as e:
            result['prix'] = {'tier1': False, 'prix_m2': None, 'confidence': 0.0}
        
        try:
            # 3. HAUSSMANIEN (style)
            style_score = score_style(apartment, self.config)
            is_haussmannien = style_score.get('tier') == 'tier1'
            result['haussmanien'] = {
                'detected': is_haussmannien,
                'confidence': 0.8 if style_score.get('tier') else 0.5,
                'indices': style_score.get('justification', '')[:100]
            }
        except Exception as e:
            result['haussmanien'] = {'detected': False, 'confidence': 0.0, 'indices': ''}
        
        try:
            # 4. LUMINOSITÉ (basée sur texte/étage)
            ensoleillement_score = score_ensoleillement(apartment, self.config)
            result['luminosite'] = {
                'tier1': ensoleillement_score.get('tier') == 'tier1',
                'type': 'lumineux' if ensoleillement_score.get('tier') == 'tier1' else 'moyen' if ensoleillement_score.get('tier') == 'tier2' else 'sombre',
                'confidence': 0.7 if ensoleillement_score.get('tier') else 0.5
            }
        except Exception as e:
            result['luminosite'] = {'tier1': False, 'type': 'sombre', 'confidence': 0.0}
        
        try:
            # 5. ASCENSEUR
            ascenseur_score = score_ascenseur(apartment, self.config)
            result['ascenseur'] = {
                'present': ascenseur_score.get('tier') == 'tier1',
                'confidence': 0.8 if ascenseur_score.get('tier') else 0.5
            }
        except Exception as e:
            result['ascenseur'] = {'present': False, 'confidence': 0.0}
        
        try:
            # 6. RÉNOVÉ
            renove_score = score_renove(apartment, self.config)
            result['renove'] = {
                'renove': renove_score.get('tier') == 'tier1',
                'confidence': 0.7 if renove_score.get('tier') else 0.5
            }
        except Exception as e:
            result['renove'] = {'renove': False, 'confidence': 0.0}
        
        try:
            # 7. CALME
            calme_score = score_calme(apartment, self.config)
            result['calme'] = {
                'calme': calme_score.get('tier') == 'tier1',
                'confidence': 0.7 if calme_score.get('tier') else 0.5
            }
        except Exception as e:
            result['calme'] = {'calme': False, 'confidence': 0.0}
        
        return result
    
    def _analyze_photo_based_criteria(self, apartment: Dict, image_sources: List) -> Dict:
        """Analyse les critères nécessitant des photos avec Gemini Flash"""
        apartment_id = apartment.get('id', 'unknown')
        description = apartment.get('description', '')
        caracteristiques = apartment.get('caracteristiques', '')
        
        # Créer le prompt pour les critères nécessitant des photos
        prompt = self._create_photo_criteria_prompt(description, caracteristiques, apartment)
        
        try:
            response_data = self.analyzer.analyze_multiple_images(
                image_sources,
                prompt,
                return_json=True
            )
            
            return self._parse_photo_criteria_response(response_data, apartment)
        except Exception as e:
            print(f"   ⚠️ Erreur analyse photos {apartment_id}: {e}")
            return {}
    
    def _extract_prix_m2(self, apartment: Dict) -> Optional[float]:
        """Extrait le prix/m² depuis les données de l'appartement"""
        prix_m2_str = apartment.get('prix_m2', '')
        if prix_m2_str and prix_m2_str != 'Prix/m² non trouvé':
            import re
            match = re.search(r'(\d+)', prix_m2_str.replace(' ', ''))
            if match:
                return float(match.group(1))
        
        # Calculer depuis prix et surface
        surface = apartment.get('surface', '')
        prix = apartment.get('prix', '')
        if surface and prix:
            import re
            surface_match = re.search(r'(\d+)', surface)
            prix_match = re.search(r'(\d+)', prix.replace(' ', ''))
            if surface_match and prix_match:
                surface_num = float(surface_match.group(1))
                prix_num = float(prix_match.group(1))
                if surface_num > 0:
                    return prix_num / surface_num
        
        return None
    
    def _create_photo_criteria_prompt(self, description: str, caracteristiques: str, apartment: Dict) -> str:
        """Crée le prompt pour analyser les critères nécessitant des photos"""
        surface = apartment.get('surface', '')
        
        return f"""Analyse ces photos d'appartement et détermine les critères suivants :

## DONNÉES DISPONIBLES
Description: {description[:300]}
Caractéristiques: {caracteristiques[:200]}
Surface: {surface}

## CRITÈRES À ANALYSER (nécessitent des photos)

1. **CUISINE OUVERTE** : Cuisine ouverte sur salon ? (visible depuis photos)
2. **LARGE PIÈCE DE VIE** : Salon > 35% surface totale ? (estimer depuis photos)
3. **HAUTEUR PLAFOND** : ≥ 2.80m ? (estimer depuis photos)
4. **HAUSSMANIEN** (confirmation) : Moulures, parquet, cheminée visibles ? (si pas déjà détecté depuis texte)

Réponds UNIQUEMENT en JSON :
{{
    "cuisine_ouverte": {{
        "ouverte": true|false,
        "confidence": 0.0-1.0
    }},
    "large_piece_vie": {{
        "grande": true|false,
        "pourcentage_estime": nombre,
        "confidence": 0.0-1.0
    }},
    "hauteur_plafond": {{
        "haute": true|false,
        "hauteur_estimee": nombre en mètres,
        "confidence": 0.0-1.0
    }},
    "haussmanien_photo": {{
        "detected": true|false,
        "indices": "moulures, parquet, cheminée...",
        "confidence": 0.0-1.0
    }}
}}"""
    
    def _parse_photo_criteria_response(self, response_data: Dict, apartment: Dict) -> Dict:
        """Parse la réponse JSON de l'analyse photo"""
        result = {}
        try:
            if isinstance(response_data, dict):
                data = response_data
                if 'raw_response' in data:
                    try:
                        data = json.loads(data['raw_response'])
                    except:
                        pass
            else:
                text = str(response_data).strip()
                if text.startswith('```json'):
                    text = text.replace('```json', '').replace('```', '').strip()
                elif text.startswith('```'):
                    text = text.replace('```', '').strip()
                data = json.loads(text)
            
            # Cuisine ouverte
            if 'cuisine_ouverte' in data:
                result['cuisine_ouverte'] = data['cuisine_ouverte']
            
            # Large pièce de vie
            if 'large_piece_vie' in data:
                result['large_piece_vie'] = data['large_piece_vie']
            
            # Hauteur plafond
            if 'hauteur_plafond' in data:
                result['hauteur_plafond'] = data['hauteur_plafond']
            
            # Haussmannien (confirmation photo)
            if 'haussmanien_photo' in data:
                photo_haussmannien = data['haussmanien_photo']
                # Si détecté depuis photos et pas déjà détecté depuis texte, mettre à jour
                if photo_haussmannien.get('detected') and photo_haussmannien.get('confidence', 0) > 0.7:
                    result['haussmanien'] = {
                        'detected': True,
                        'confidence': photo_haussmannien.get('confidence', 0.8),
                        'indices': photo_haussmannien.get('indices', '')
                    }
            
        except Exception as e:
            print(f"   ⚠️ Erreur parsing réponse photo: {e}")
        
        return result
    
    def _create_criteria_prompt_old(self, description: str, caracteristiques: str, apartment: Dict) -> str:
        """Crée le prompt optimisé pour analyser les 10 critères en une fois"""
        surface = apartment.get('surface', '')
        prix = apartment.get('prix', '')
        localisation = apartment.get('localisation', '')
        etage = apartment.get('etage', '')
        
        return f"""Analyse cet appartement et détermine TOUS les critères suivants en UNE SEULE analyse :

## DONNÉES DISPONIBLES
Description: {description[:300]}
Caractéristiques: {caracteristiques[:200]}
Surface: {surface}
Prix: {prix}
Localisation: {localisation}
Étage: {etage}

## 10 CRITÈRES À ANALYSER

1. **HAUSSMANIEN** : Style haussmannien détecté ? (moulures, parquet, cheminée, hauteur plafond)
2. **QUARTIER** : Zone Tier 1 ? (Belleville, Ménilmontant, Avron, Place de la Réunion, etc.)
3. **PRIX** : Prix/m² < 9.5k€ ? (calculer depuis prix et surface)
4. **LUMINOSITÉ** : Lumineux ? (Sud/Ouest, vue dégagée, pas de vis-à-vis)
5. **CUISINE OUVERTE** : Cuisine ouverte sur salon ? (visible depuis photos)
6. **ASCENSEUR** : Ascenseur présent ? (mentionné dans caractéristiques/description)
7. **LARGE PIÈCE DE VIE** : Salon > 35% surface totale ? (estimer depuis photos)
8. **HAUTEUR PLAFOND** : ≥ 2.80m ? (estimer depuis photos)
9. **RÉNOVÉ** : Mentionné comme rénové ? (dans description/caractéristiques)
10. **CALME** : Quartier calme ? (rue piétonne, peu de bars/restos)

Réponds UNIQUEMENT en JSON (pas de texte avant/après) :
{{
    "haussmanien": {{
        "detected": true|false,
        "confidence": 0.0-1.0,
        "indices": "moulures, parquet, cheminée..."
    }},
    "quartier": {{
        "tier1": true|false,
        "zone": "nom du quartier/métro",
        "confidence": 0.0-1.0
    }},
    "prix": {{
        "tier1": true|false,
        "prix_m2": nombre,
        "confidence": 0.0-1.0
    }},
    "luminosite": {{
        "tier1": true|false,
        "type": "lumineux|moyen|sombre",
        "confidence": 0.0-1.0
    }},
    "cuisine_ouverte": {{
        "ouverte": true|false,
        "confidence": 0.0-1.0
    }},
    "ascenseur": {{
        "present": true|false,
        "confidence": 0.0-1.0
    }},
    "large_piece_vie": {{
        "grande": true|false,
        "pourcentage_estime": nombre,
        "confidence": 0.0-1.0
    }},
    "hauteur_plafond": {{
        "haute": true|false,
        "hauteur_estimee": nombre en mètres,
        "confidence": 0.0-1.0
    }},
    "renove": {{
        "renove": true|false,
        "confidence": 0.0-1.0
    }},
    "calme": {{
        "calme": true|false,
        "confidence": 0.0-1.0
    }}
}}"""
    
    def _parse_criteria_response_old(self, response_data: Dict, apartment: Dict) -> Dict:
        """Parse la réponse JSON de l'analyse des critères"""
        try:
            # Si c'est déjà un dict
            if isinstance(response_data, dict):
                data = response_data
                if 'raw_response' in data:
                    try:
                        data = json.loads(data['raw_response'])
                    except:
                        pass
            else:
                # Si c'est une string, parser
                text = str(response_data).strip()
                if text.startswith('```json'):
                    text = text.replace('```json', '').replace('```', '').strip()
                elif text.startswith('```'):
                    text = text.replace('```', '').strip()
                data = json.loads(text)
            
            return data
            
        except Exception as e:
            print(f"   ⚠️ Erreur parsing réponse: {e}")
            return {}
    
    def save_analysis_results(self, apartment_id: str, results: Dict):
        """Sauvegarde les résultats d'analyse"""
        os.makedirs('data/criteria_analysis', exist_ok=True)
        filepath = f"data/criteria_analysis/{apartment_id}.json"
        
        results_with_metadata = {
            'apartment_id': apartment_id,
            'analyzed_at': datetime.now().isoformat(),
            'criteria': results
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results_with_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"   ❌ Erreur sauvegarde {apartment_id}: {e}")
    
    def analyze_all_52(self, progress_callback=None):
        """Analyse les 52 appartements avec rate limiting optimisé"""
        apartment_ids = self.get_52_apartments()
        
        if not apartment_ids:
            print("❌ Aucun appartement trouvé")
            return []
        
        print(f"📊 Analyse de {len(apartment_ids)} appartements")
        print(f"🎯 Critères à analyser: {', '.join(CRITERIA)}")
        print()
        
        results = []
        errors = []
        
        for i, apartment_id in enumerate(apartment_ids, 1):
            print(f"[{i}/{len(apartment_ids)}] Analyse {apartment_id}...", end=' ', flush=True)
            
            # Charger les données
            apartment = self.load_apartment_data(apartment_id)
            if not apartment:
                print("❌ Données non trouvées")
                errors.append(apartment_id)
                continue
            
            # Analyser les critères
            start_time = time.time()
            criteria_results = self.analyze_criteria_unified(apartment)
            elapsed = time.time() - start_time
            
            if criteria_results:
                # Sauvegarder les résultats
                self.save_analysis_results(apartment_id, criteria_results)
                results.append({
                    'apartment_id': apartment_id,
                    'criteria': criteria_results,
                    'analysis_time': elapsed
                })
                print(f"✅ ({elapsed:.1f}s)")
                
                # Callback pour mise à jour frontend
                if progress_callback:
                    progress_callback(i, len(apartment_ids), apartment_id, criteria_results)
            else:
                print("⚠️ Aucun résultat")
                errors.append(apartment_id)
            
            # Rate limiting optimisé : 2 secondes entre chaque appartement (30 RPM)
            if i < len(apartment_ids):
                time.sleep(2)
        
        print()
        print(f"✅ Analyse terminée: {len(results)}/{len(apartment_ids)} réussies")
        if errors:
            print(f"❌ Erreurs: {len(errors)}")
        
        return results


def main():
    """Fonction principale"""
    print("=" * 80)
    print("🚀 ANALYSE ULTRA-RAPIDE DES 10 CRITÈRES - 52 APPARTEMENTS")
    print("=" * 80)
    print()
    
    analyzer = FastCriteriaAnalyzer()
    analyzer.analyze_all_52()


if __name__ == "__main__":
    main()

