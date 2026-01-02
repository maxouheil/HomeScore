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

# Import avec rechargement forcé pour éviter le cache Python
import importlib
import alert_scoring
importlib.reload(alert_scoring)
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
    # Nouveau format: 5 critères à 20pts chacun
    all: Optional[List[str]] = Field(default=None)
    # Ancien format (pour compatibilité)
    primary: List[str] = Field(default=[])
    secondary: List[str] = Field(default=[])


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
    try:
        ensure_alerts_dir()
        alerts = []
        
        if not os.path.exists(ALERTS_DIR):
            return alerts
        
        for filename in os.listdir(ALERTS_DIR):
            if filename.endswith('.json'):
                try:
                    alert_id = filename[:-5]  # Enlever .json
                    alert = load_alert(alert_id)
                    if alert:
                        alerts.append(alert)
                except Exception as e:
                    # Ignorer les alertes corrompues et continuer
                    print(f"⚠️ Erreur lors du chargement de l'alerte {filename}: {e}")
                    continue
        
        # Trier par date de création (plus récent en premier)
        alerts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return alerts
    except Exception as e:
        import traceback
        print(f"❌ Erreur dans list_all_alerts: {e}")
        traceback.print_exc()
        raise


@router.post("", status_code=201)
async def create_alert(alert_data: AlertCreate) -> Dict[str, Any]:
    """
    Crée une nouvelle alerte
    """
    # Validation: soit 5 critères dans 'all', soit 2+2 dans primary/secondary (ancien format)
    if alert_data.criteria.all is not None:
        if len(alert_data.criteria.all) != 5:
            raise HTTPException(
                status_code=400,
                detail="Une alerte doit avoir exactement 5 critères"
            )
    elif len(alert_data.criteria.primary) + len(alert_data.criteria.secondary) > 0:
        # Ancien format
        if len(alert_data.criteria.primary) != 2:
            raise HTTPException(
                status_code=400,
                detail="Une alerte doit avoir exactement 2 critères principaux (ancien format)"
            )
        if len(alert_data.criteria.secondary) != 2:
            raise HTTPException(
                status_code=400,
                detail="Une alerte doit avoir exactement 2 critères secondaires (ancien format)"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Une alerte doit avoir soit 5 critères dans 'all', soit 2 critères principaux et 2 secondaires"
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
    try:
        return list_all_alerts()
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erreur dans get_alerts: {e}")
        print(f"   Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des alertes: {str(e)}")


@router.get("/test-scoring")
async def test_scoring():
    """Endpoint de test pour vérifier que le scoring fonctionne sur 5"""
    try:
        import alert_scoring
        from scoring import load_scoring_config
        
        # Charger la vraie config de scoring
        config = load_scoring_config()
        if not config:
            return {
                'status': 'error',
                'error': 'Config de scoring non disponible'
            }
        
        test_apartment = {'id': 'test'}
        test_alert = {'criteria': {'all': ['quartier', 'prix', 'luminosite', 'cuisine_ouverte', 'haussmanien']}}
        result = alert_scoring.score_apartment_for_alert(test_apartment, test_alert, config)
        return {
            'score': result['score'],
            'max_score': result['max_score'],
            'tier': result['tier'],
            'criteria_scores': {k: v['score'] for k, v in result['criteria_scores'].items()},
            'status': 'ok'
        }
    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }


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
        # Validation: soit 5 critères dans 'all', soit 2+2 dans primary/secondary (ancien format)
        if alert_update.criteria.all is not None:
            if len(alert_update.criteria.all) != 5:
                raise HTTPException(
                    status_code=400,
                    detail="Une alerte doit avoir exactement 5 critères"
                )
        elif len(alert_update.criteria.primary) + len(alert_update.criteria.secondary) > 0:
            # Ancien format
            if len(alert_update.criteria.primary) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Une alerte doit avoir exactement 2 critères principaux (ancien format)"
                )
            if len(alert_update.criteria.secondary) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Une alerte doit avoir exactement 2 critères secondaires (ancien format)"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Une alerte doit avoir soit 5 critères dans 'all', soit 2 critères principaux et 2 secondaires"
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
        
        # Normaliser les appartements pour avoir les données criteria.display
        try:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            from normalizers.simple_normalizer import normalize_apartment
            
            normalized_apartments = []
            for apt in all_apartments:
                try:
                    normalized = normalize_apartment(apt)
                    normalized_apartments.append(normalized)
                except Exception as e:
                    # En cas d'erreur, utiliser l'appartement non normalisé
                    normalized_apartments.append(apt)
            all_apartments = normalized_apartments
        except Exception as e:
            # Si la normalisation échoue, continuer avec les données non normalisées
            print(f"⚠️ Erreur normalisation pour alertes: {e}")
            import traceback
            traceback.print_exc()
        
        # Filtrer selon les critères de l'alerte
        try:
            filters = alert.get('filters', {})
            print(f"🔍 Filtres de l'alerte: budget={filters.get('budget_min')}-{filters.get('budget_max')}, surface={filters.get('surface_min')}-{filters.get('surface_max')}, pièces={filters.get('pieces_min')}-{filters.get('pieces_max')}, localisation={filters.get('localisation', 'aucune')}")
            filtered_apartments = filter_apartments_by_alert(all_apartments, alert)
            print(f"📊 Filtrage: {len(all_apartments)} appartements au total, {len(filtered_apartments)} après filtrage")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du filtrage des appartements: {str(e)}")
        
        # Scorer chaque appartement selon les critères de l'alerte
        scored_apartments = []
        print(f"🔢 Scoring {len(filtered_apartments)} appartements...")
        for apartment in filtered_apartments:
            try:
                # FORCER le recalcul en supprimant les anciens scores s'ils existent
                apartment_clean = apartment.copy()
                # Supprimer les anciens scores pour forcer le recalcul
                apartment_clean.pop('alert_score', None)
                apartment_clean.pop('alert_tier', None)
                apartment_clean.pop('alert_criteria_scores', None)
                
                score_result = score_apartment_for_alert(apartment_clean, alert)
                
                # DEBUG: Log pour chaque appartement
                apt_id = apartment_clean.get('id', 'unknown')
                calculated_score = score_result['score']
                print(f"🔍 Scoring appartement {apt_id}: score={calculated_score}, max_score={score_result.get('max_score', 'N/A')}")
                
                # DEBUG: Vérifier que le score est bien sur 5
                if calculated_score > 5:
                    print(f"⚠️ ATTENTION: Score {calculated_score} > 5 pour appartement {apt_id}")
                    print(f"   Criteria scores: {score_result['criteria_scores']}")
                    print(f"   Max score attendu: 5")
                
                # Ajouter le score personnalisé à l'appartement (NOUVEAU SYSTÈME sur 5)
                apartment_with_score = apartment_clean.copy()
                # FORCER le score sur 5 maximum (sécurité)
                final_score = min(calculated_score, 5.0)
                apartment_with_score['alert_score'] = final_score  # Score sur 5 (max 5)
                print(f"   ✅ Score final assigné: {final_score}")
                apartment_with_score['alert_tier'] = score_result['tier']
                apartment_with_score['alert_criteria_scores'] = score_result['criteria_scores']  # Scores individuels (1pt, 0.5pt, 0pt)
                
                scored_apartments.append(apartment_with_score)
            except Exception as e:
                # En cas d'erreur, continuer avec les autres appartements
                print(f"⚠️ Erreur scoring appartement {apartment.get('id')} pour alerte {alert_id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Trier par score décroissant
        scored_apartments.sort(key=lambda x: x.get('alert_score', 0), reverse=True)
        
        print(f"✅ Retour de {len(scored_apartments)} appartements scorés")
        if len(scored_apartments) > 0:
            print(f"   Score min: {min(apt.get('alert_score', 0) for apt in scored_apartments)}")
            print(f"   Score max: {max(apt.get('alert_score', 0) for apt in scored_apartments)}")
        
        return scored_apartments
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.post("/{alert_id}/refresh")
async def refresh_alert_apartments(alert_id: str) -> Dict[str, Any]:
    """
    Rafraîchit les appartements d'une alerte depuis l'API Jinka
    Réutilise la logique de fetch_all_apartments_api.py
    Télécharge les photos et récupère toutes les données de l'API
    """
    try:
        alert = load_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alerte {alert_id} non trouvée")
        
        # Token hardcodé pour l'instant (peut être stocké dans l'alerte plus tard)
        alert_url = "https://www.jinka.fr/asrenter/alert/dashboard/cebed5288c18eafafadb04e048a4e776"
        
        # Importer les fonctions depuis fetch_all_apartments_api
        from fetch_all_apartments_api import (
            load_existing_apartments,
            merge_apartment_data,
            clean_apartment_data,
            remove_duplicates,
            validate_apartment
        )
        from scrape_jinka_api import JinkaAPIScraper
        from photo_manager import PhotoManager
        from pathlib import Path
        
        # 1. Initialiser le scraper
        scraper = JinkaAPIScraper()
        await scraper.setup()
        if not await scraper.login():
            raise HTTPException(status_code=500, detail="Échec de la connexion à Jinka")
        
        # 2. Récupérer tous les appartements (avec TOUTES les données via scrape_apartment)
        print(f"🔄 Récupération des appartements depuis l'API Jinka...")
        apartments = await scraper.scrape_alert_page(alert_url, filter_type="all", max_pages=50)
        
        if not apartments:
            await scraper.cleanup()
            raise HTTPException(status_code=500, detail="Aucun appartement récupéré depuis l'API")
        
        # 3. Charger les existants
        print(f"📂 Chargement des appartements existants...")
        existing = load_existing_apartments()
        
        # 4. Nettoyer et valider
        print(f"🧹 Nettoyage et validation des données...")
        cleaned = [clean_apartment_data(apt) for apt in apartments if validate_apartment(apt)]
        cleaned = remove_duplicates(cleaned)
        
        # 5. Fusionner (identifie automatiquement les nouveaux)
        print(f"🔀 Fusion avec les données existantes...")
        merged = merge_apartment_data(existing, cleaned)
        
        # 6. Télécharger les photos pour tous les appartements
        print(f"📸 Téléchargement des photos...")
        photo_manager = PhotoManager()
        photos_downloaded = 0
        for i, apt in enumerate(merged, 1):
            apt_id = apt.get('id', 'unknown')
            photos_before = len(apt.get('photos', []))
            
            if photos_before > 0:
                # Télécharger les photos
                apt_with_photos = photo_manager.download_apartment_photos(apt, max_photos=10)
                merged[i-1] = apt_with_photos
                
                downloaded_count = sum(1 for p in apt_with_photos.get('photos', []) if p.get('local_path'))
                photos_downloaded += downloaded_count
        
        # 7. Sauvegarder
        print(f"💾 Sauvegarde des données...")
        output_file = Path('data/scraped_apartments.json')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2, default=str)
        
        # 8. Calculer les nouveaux
        new_count = len(merged) - len(existing)
        
        await scraper.cleanup()
        
        print(f"✅ Refresh terminé: {new_count} nouveaux appartements, {photos_downloaded} photos téléchargées")
        
        return {
            "new_count": new_count,
            "total_count": len(merged),
            "photos_downloaded": photos_downloaded,
            "message": f"{new_count} nouveaux appartements ajoutés, {photos_downloaded} photos téléchargées"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erreur dans refresh_alert_apartments: {e}")
        print(f"   Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du rafraîchissement: {str(e)}")



