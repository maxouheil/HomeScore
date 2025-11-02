"""
API endpoint pour récupérer les appartements
"""
import json
import os
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
import sys

# Ajouter le répertoire parent au path pour importer generate_scorecard_html
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from generate_scorecard_html import load_scored_apartments
from criteria import format_cuisine, format_baignoire, format_style, format_exposition

# Importer la fonction de scoring pour valider les scores style
try:
    from scoring import score_style
    import json as json_module
    _scoring_config = None
    def load_scoring_config():
        """Charge la configuration de scoring"""
        global _scoring_config
        if _scoring_config is None:
            try:
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'scoring_config.json')
                with open(config_path, 'r', encoding='utf-8') as f:
                    _scoring_config = json_module.load(f)
            except Exception as e:
                print(f"⚠️ Erreur chargement scoring_config: {e}")
                _scoring_config = {}
        return _scoring_config
except ImportError:
    print("⚠️ Module scoring non disponible, validation style désactivée")
    score_style = None
    load_scoring_config = None

router = APIRouter(prefix="/api", tags=["apartments"])

# Cache pour éviter de recharger les données à chaque requête
_cached_apartments = None
_cache_timestamp = 0

def validate_style_score(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """Valide et corrige le score style selon les règles strictes"""
    if not score_style or 'scores_detaille' not in apartment:
        return apartment
    
    try:
        config = load_scoring_config()
        if not config or 'axes' not in config or 'style' not in config['axes']:
            return apartment
        
        # Utiliser score_style pour calculer le score selon les règles
        style_result = score_style(apartment, config)
        
        # Override le score style dans scores_detaille avec les valeurs calculées
        if 'style' not in apartment['scores_detaille']:
            apartment['scores_detaille']['style'] = {}
        
        apartment['scores_detaille']['style']['score'] = style_result['score']
        apartment['scores_detaille']['style']['tier'] = style_result['tier']
        apartment['scores_detaille']['style']['justification'] = style_result['justification']
        if style_result.get('confidence'):
            apartment['scores_detaille']['style']['confidence'] = style_result['confidence']
        
    except Exception as e:
        # En cas d'erreur, ne pas bloquer le chargement
        print(f"⚠️ Erreur validation style pour {apartment.get('id')}: {e}")
    
    return apartment

def validate_ensoleillement_score(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """Valide et recalcule le score ensoleillement selon les nouvelles règles de vote"""
    if 'scores_detaille' not in apartment:
        return apartment
    
    try:
        from scoring import score_ensoleillement
        config = load_scoring_config()
        if not config or 'axes' not in config or 'ensoleillement' not in config['axes']:
            return apartment
        
        # Recalculer le score avec les nouvelles règles
        ensoleillement_result = score_ensoleillement(apartment, config)
        
        # Mettre à jour le score dans scores_detaille
        if 'ensoleillement' not in apartment['scores_detaille']:
            apartment['scores_detaille']['ensoleillement'] = {}
        
        apartment['scores_detaille']['ensoleillement']['score'] = ensoleillement_result['score']
        apartment['scores_detaille']['ensoleillement']['tier'] = ensoleillement_result['tier']
        apartment['scores_detaille']['ensoleillement']['justification'] = ensoleillement_result['justification']
        if ensoleillement_result.get('confidence'):
            apartment['scores_detaille']['ensoleillement']['confidence'] = ensoleillement_result['confidence']
        
    except Exception as e:
        # En cas d'erreur, ne pas bloquer le chargement
        print(f"⚠️ Erreur validation ensoleillement pour {apartment.get('id')}: {e}")
        import traceback
        traceback.print_exc()
    
    return apartment

def enrich_apartment_with_indices(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """Enrichit un appartement avec les indices formatés depuis le module criteria"""
    try:
        # Valider les scores selon les règles strictes
        apartment = validate_style_score(apartment)
        apartment = validate_ensoleillement_score(apartment)
        
        # Enrichir avec les indices pour cuisine, baignoire et style
        if 'scores_detaille' in apartment:
            # Cuisine
            if 'cuisine' in apartment.get('scores_detaille', {}):
                try:
                    cuisine_formatted = format_cuisine(apartment)
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    apartment['formatted_data']['cuisine'] = {
                        'indices': cuisine_formatted.get('indices')
                    }
                except Exception as e:
                    # En cas d'erreur, utiliser la phrase par défaut
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    apartment['formatted_data']['cuisine'] = {
                        'indices': "Style expo cuisine et baignoire"
                    }
            
            # Baignoire
            if 'baignoire' in apartment.get('scores_detaille', {}):
                try:
                    baignoire_formatted = format_baignoire(apartment)
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    apartment['formatted_data']['baignoire'] = {
                        'main_value': baignoire_formatted.get('main_value'),
                        'indices': baignoire_formatted.get('indices'),
                        'confidence': baignoire_formatted.get('confidence')
                    }
                except Exception as e:
                    # En cas d'erreur, utiliser la phrase par défaut
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    apartment['formatted_data']['baignoire'] = {
                        'main_value': 'Non',
                        'indices': "Style expo cuisine et baignoire",
                        'confidence': None
                    }
            
            # Style
            if 'style' in apartment.get('scores_detaille', {}):
                try:
                    style_formatted = format_style(apartment)
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    apartment['formatted_data']['style'] = {
                        'indices': style_formatted.get('indices')  # Peut être None si pas d'indices trouvés
                    }
                except Exception as e:
                    # En cas d'erreur, ne pas mettre de fallback générique
                    # Le frontend gérera l'affichage si pas d'indices
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    apartment['formatted_data']['style'] = {
                        'indices': None
                    }
            
            # Exposition
            # Créer formatted_data.exposition si l'appartement a soit scores_detaille.ensoleillement, soit exposition (depuis scraping)
            has_ensoleillement_score = 'ensoleillement' in apartment.get('scores_detaille', {})
            has_exposition_data = bool(apartment.get('exposition', {}).get('exposition'))
            
            if has_ensoleillement_score or has_exposition_data:
                try:
                    exposition_formatted = format_exposition(apartment)
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    apartment['formatted_data']['exposition'] = {
                        'main_value': exposition_formatted.get('main_value'),
                        'indices': exposition_formatted.get('indices'),
                        'confidence': exposition_formatted.get('confidence')
                    }
                except Exception as e:
                    # Logger l'erreur pour debug
                    import traceback
                    print(f"❌ Erreur format_exposition pour {apartment.get('id')}: {e}")
                    print(traceback.format_exc())
                    # En cas d'erreur, ne pas ajouter de données formatées
                    pass
    except Exception as e:
        # Ne pas faire échouer la requête si l'enrichissement échoue
        pass
    
    return apartment

def load_apartments_data() -> List[Dict[str, Any]]:
    """Charge les appartements scorés et fusionne avec les données scrapées"""
    global _cached_apartments, _cache_timestamp
    
    # Vérifier si le cache est encore valide (basé sur les temps de modification des fichiers)
    try:
        scores_file = 'data/scores/all_apartments_scores.json'
        scraped_file = 'data/scraped_apartments.json'
        
        scores_mtime = os.path.getmtime(scores_file) if os.path.exists(scores_file) else 0
        scraped_mtime = os.path.getmtime(scraped_file) if os.path.exists(scraped_file) else 0
        max_mtime = max(scores_mtime, scraped_mtime)
        
        # Si le cache est encore valide, le retourner
        if _cached_apartments is not None and max_mtime <= _cache_timestamp:
            return _cached_apartments
        
        # Sinon, recharger les données
        apartments = load_scored_apartments()
        
        # Enrichir chaque appartement avec les indices formatés
        enriched_apartments = [enrich_apartment_with_indices(apt) for apt in apartments]
        
        _cached_apartments = enriched_apartments
        _cache_timestamp = max_mtime
        
        return _cached_apartments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des données: {str(e)}")

@router.get("/apartments")
async def get_apartments() -> List[Dict[str, Any]]:
    """
    Retourne la liste de tous les appartements avec leurs scores et détails
    """
    try:
        apartments = load_apartments_data()
        return apartments
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/apartments/{apartment_id}")
async def get_apartment(apartment_id: str) -> Dict[str, Any]:
    """
    Retourne les détails d'un appartement spécifique
    """
    try:
        apartments = load_apartments_data()
        for apt in apartments:
            if str(apt.get('id')) == str(apartment_id):
                return apt
        raise HTTPException(status_code=404, detail=f"Appartement {apartment_id} non trouvé")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

def invalidate_cache():
    """Invalide le cache pour forcer un rechargement"""
    global _cached_apartments, _cache_timestamp
    _cached_apartments = None
    _cache_timestamp = 0

@router.post("/apartments/invalidate-cache")
async def invalidate_apartments_cache():
    """Invalide le cache des appartements pour forcer un rechargement"""
    invalidate_cache()
    return {"message": "Cache invalidé avec succès"}

# Invalider le cache au démarrage pour forcer le rechargement avec les nouvelles données
invalidate_cache()

