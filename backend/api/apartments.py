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

router = APIRouter(prefix="/api", tags=["apartments"])

# Cache pour éviter de recharger les données à chaque requête
_cached_apartments = None
_cache_timestamp = 0

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
        _cached_apartments = load_scored_apartments()
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

