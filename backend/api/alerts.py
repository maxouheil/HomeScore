"""
API endpoints pour la gestion des alertes
"""
import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import sys

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from alert_scoring import score_apartment_for_alert, filter_apartments_by_alert
from backend.api.apartments import load_apartments_data

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

ALERTS_DIR = "data/alerts"


# Modèles Pydantic pour validation
class AlertFilters(BaseModel):
    localisation: Optional[str] = None
    budget_min: int = Field(default=0, ge=0)
    budget_max: int = Field(default=10000000, ge=0)
    surface_min: int = Field(default=0, ge=0)
    surface_max: int = Field(default=1000, ge=0)
    pieces_min: int = Field(default=0, ge=0)
    pieces_max: int = Field(default=20, ge=0)


class AlertCriteria(BaseModel):
    primary: List[str] = Field(default=[], max_items=2, min_items=2)
    secondary: List[str] = Field(default=[], max_items=2, min_items=2)


class AlertCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    filters: AlertFilters
    criteria: AlertCriteria


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    filters: Optional[AlertFilters] = None
    criteria: Optional[AlertCriteria] = None


def ensure_alerts_dir():
    """Crée le dossier data/alerts s'il n'existe pas"""
    os.makedirs(ALERTS_DIR, exist_ok=True)


def get_alert_path(alert_id: str) -> str:
    """Retourne le chemin du fichier d'alerte"""
    return os.path.join(ALERTS_DIR, f"{alert_id}.json")


def load_alert(alert_id: str) -> Optional[Dict[str, Any]]:
    """Charge une alerte depuis le fichier"""
    alert_path = get_alert_path(alert_id)
    if not os.path.exists(alert_path):
        return None
    
    try:
        with open(alert_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement de l'alerte: {str(e)}")


def save_alert(alert: Dict[str, Any]) -> None:
    """Sauvegarde une alerte dans un fichier"""
    ensure_alerts_dir()
    alert_id = alert['id']
    alert_path = get_alert_path(alert_id)
    
    try:
        with open(alert_path, 'w', encoding='utf-8') as f:
            json.dump(alert, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde de l'alerte: {str(e)}")


def list_all_alerts() -> List[Dict[str, Any]]:
    """Liste toutes les alertes"""
    ensure_alerts_dir()
    alerts = []
    
    if not os.path.exists(ALERTS_DIR):
        return alerts
    
    for filename in os.listdir(ALERTS_DIR):
        if filename.endswith('.json'):
            alert_id = filename[:-5]  # Enlever .json
            alert = load_alert(alert_id)
            if alert:
                alerts.append(alert)
    
    # Trier par date de création (plus récent en premier)
    alerts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return alerts


@router.post("", status_code=201)
async def create_alert(alert_data: AlertCreate) -> Dict[str, Any]:
    """
    Crée une nouvelle alerte
    """
    # Validation: exactement 2 critères principaux et 2 secondaires
    if len(alert_data.criteria.primary) != 2:
        raise HTTPException(
            status_code=400,
            detail="Une alerte doit avoir exactement 2 critères principaux"
        )
    
    if len(alert_data.criteria.secondary) != 2:
        raise HTTPException(
            status_code=400,
            detail="Une alerte doit avoir exactement 2 critères secondaires"
        )
    
    # Créer l'alerte
    alert_id = str(uuid.uuid4())
    alert = {
        'id': alert_id,
        'name': alert_data.name,
        'created_at': datetime.now().isoformat(),
        'filters': alert_data.filters.dict(),
        'criteria': alert_data.criteria.dict()
    }
    
    save_alert(alert)
    return alert


@router.get("")
async def get_alerts() -> List[Dict[str, Any]]:
    """
    Liste toutes les alertes
    """
    return list_all_alerts()


@router.get("/{alert_id}")
async def get_alert(alert_id: str) -> Dict[str, Any]:
    """
    Récupère les détails d'une alerte
    """
    alert = load_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alerte {alert_id} non trouvée")
    return alert


@router.put("/{alert_id}")
async def update_alert(alert_id: str, alert_update: AlertUpdate) -> Dict[str, Any]:
    """
    Met à jour une alerte
    """
    alert = load_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alerte {alert_id} non trouvée")
    
    # Mettre à jour les champs fournis
    if alert_update.name is not None:
        alert['name'] = alert_update.name
    
    if alert_update.filters is not None:
        alert['filters'] = alert_update.filters.dict()
    
    if alert_update.criteria is not None:
        # Validation: exactement 2 critères principaux et 2 secondaires
        if len(alert_update.criteria.primary) != 2:
            raise HTTPException(
                status_code=400,
                detail="Une alerte doit avoir exactement 2 critères principaux"
            )
        if len(alert_update.criteria.secondary) != 2:
            raise HTTPException(
                status_code=400,
                detail="Une alerte doit avoir exactement 2 critères secondaires"
            )
        alert['criteria'] = alert_update.criteria.dict()
    
    alert['updated_at'] = datetime.now().isoformat()
    save_alert(alert)
    return alert


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str) -> Dict[str, str]:
    """
    Supprime une alerte
    """
    alert = load_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alerte {alert_id} non trouvée")
    
    alert_path = get_alert_path(alert_id)
    try:
        os.remove(alert_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")
    
    return {"message": f"Alerte {alert_id} supprimée avec succès"}


@router.get("/{alert_id}/apartments")
async def get_alert_apartments(alert_id: str) -> List[Dict[str, Any]]:
    """
    Récupère les appartements filtrés et scorés selon une alerte
    """
    try:
        alert = load_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alerte {alert_id} non trouvée")
        
        # Charger tous les appartements
        try:
            all_apartments = load_apartments_data()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des appartements: {str(e)}")
        
        # Filtrer selon les critères de l'alerte
        try:
            filtered_apartments = filter_apartments_by_alert(all_apartments, alert)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du filtrage des appartements: {str(e)}")
        
        # Scorer chaque appartement selon les critères de l'alerte
        scored_apartments = []
        for apartment in filtered_apartments:
            try:
                score_result = score_apartment_for_alert(apartment, alert)
                
                # Ajouter le score personnalisé à l'appartement
                apartment_with_score = apartment.copy()
                apartment_with_score['alert_score'] = score_result['score']
                apartment_with_score['alert_tier'] = score_result['tier']
                apartment_with_score['alert_criteria_scores'] = score_result['criteria_scores']
                
                scored_apartments.append(apartment_with_score)
            except Exception as e:
                # En cas d'erreur, continuer avec les autres appartements
                print(f"⚠️ Erreur scoring appartement {apartment.get('id')} pour alerte {alert_id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Trier par score décroissant
        scored_apartments.sort(key=lambda x: x.get('alert_score', 0), reverse=True)
        
        return scored_apartments
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")



