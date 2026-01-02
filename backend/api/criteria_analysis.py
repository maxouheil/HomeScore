"""
API endpoints pour l'analyse des 10 critères des appartements
"""
import json
import os
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from analyze_52_apartments_criteria import FastCriteriaAnalyzer

router = APIRouter(prefix="/api/criteria", tags=["criteria"])

# État de l'analyse en cours
_analysis_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_apartment': None,
    'results': [],
    'errors': []
}

class AnalysisProgress(BaseModel):
    running: bool
    progress: int
    total: int
    current_apartment: Optional[str]
    completed: int
    errors: int

def load_analysis_results(apartment_id: str) -> Optional[Dict]:
    """Charge les résultats d'analyse pour un appartement"""
    filepath = f"data/criteria_analysis/{apartment_id}.json"
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def progress_callback(current: int, total: int, apartment_id: str, results: Dict):
    """Callback pour mettre à jour le statut de l'analyse"""
    _analysis_status['progress'] = current
    _analysis_status['total'] = total
    _analysis_status['current_apartment'] = apartment_id
    _analysis_status['results'].append({
        'apartment_id': apartment_id,
        'criteria': results
    })

@router.post("/analyze-all")
async def start_analysis(background_tasks: BackgroundTasks):
    """Démarre l'analyse des 10 critères pour les 52 appartements"""
    global _analysis_status
    
    if _analysis_status['running']:
        raise HTTPException(status_code=400, detail="Analyse déjà en cours")
    
    # Réinitialiser le statut
    _analysis_status = {
        'running': True,
        'progress': 0,
        'total': 0,
        'current_apartment': None,
        'results': [],
        'errors': []
    }
    
    # Lancer l'analyse en arrière-plan
    def run_analysis():
        try:
            analyzer = FastCriteriaAnalyzer()
            analyzer.analyze_all_52(progress_callback=progress_callback)
        except Exception as e:
            print(f"❌ Erreur analyse: {e}")
        finally:
            _analysis_status['running'] = False
    
    background_tasks.add_task(run_analysis)
    
    return {
        'status': 'started',
        'message': 'Analyse démarrée en arrière-plan'
    }

@router.get("/status")
async def get_analysis_status() -> AnalysisProgress:
    """Récupère le statut de l'analyse en cours"""
    return AnalysisProgress(
        running=_analysis_status['running'],
        progress=_analysis_status['progress'],
        total=_analysis_status['total'],
        current_apartment=_analysis_status['current_apartment'],
        completed=len(_analysis_status['results']),
        errors=len(_analysis_status['errors'])
    )

@router.get("/results/{apartment_id}")
async def get_apartment_results(apartment_id: str) -> Dict:
    """Récupère les résultats d'analyse pour un appartement spécifique"""
    results = load_analysis_results(apartment_id)
    if not results:
        raise HTTPException(status_code=404, detail="Résultats non trouvés")
    return results

@router.get("/results")
async def get_all_results() -> List[Dict]:
    """Récupère tous les résultats d'analyse disponibles"""
    results_dir = 'data/criteria_analysis'
    if not os.path.exists(results_dir):
        return []
    
    results = []
    for filename in os.listdir(results_dir):
        if filename.endswith('.json'):
            apartment_id = filename.replace('.json', '')
            result = load_analysis_results(apartment_id)
            if result:
                results.append(result)
    
    return results

@router.get("/latest")
async def get_latest_results() -> Dict:
    """Récupère les derniers résultats de l'analyse en cours"""
    return {
        'status': _analysis_status,
        'latest_results': _analysis_status['results'][-10:] if _analysis_status['results'] else []
    }


