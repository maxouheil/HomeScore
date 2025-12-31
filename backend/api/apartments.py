"""
API endpoint pour récupérer les appartements
"""
import json
import os
import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import sys

# Ajouter le répertoire parent au path pour importer generate_scorecard_html
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from generate_scorecard_html import load_scored_apartments
except Exception as e:
    print(f"⚠️ Erreur lors de l'import de generate_scorecard_html: {e}")
    import traceback
    traceback.print_exc()
    # Fallback: charger directement depuis les fichiers JSON
    def load_scored_apartments():
        """Fallback: charge directement depuis les fichiers JSON"""
        try:
            # Essayer d'abord avec le chemin relatif depuis le répertoire de travail
            scores_file = 'data/scores/all_apartments_scores.json'
            if os.path.exists(scores_file):
                with open(scores_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            # Sinon essayer avec le chemin absolu depuis le workspace
            import os as os_module
            workspace_root = os_module.getcwd()
            abs_scores_file = os_module.path.join(workspace_root, 'data', 'scores', 'all_apartments_scores.json')
            if os.path.exists(abs_scores_file):
                with open(abs_scores_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            raise FileNotFoundError(f"Fichier all_apartments_scores.json non trouvé dans {scores_file} ni {abs_scores_file}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des données: {str(e)}")

try:
    from criteria import format_cuisine, format_baignoire, format_style, format_exposition, format_prix
except Exception as e:
    print(f"⚠️ Erreur lors de l'import des critères: {e}")
    import traceback
    traceback.print_exc()
    # Fallback: fonctions vides
    def format_cuisine(apt): return {'indices': None}
    def format_baignoire(apt): return {'main_value': 'Non', 'indices': None, 'confidence': None}
    def format_style(apt): return {'indices': None}
    def format_exposition(apt): return {'main_value': 'Non spécifié', 'indices': None, 'confidence': None}
    def format_prix(apt): return {'main_value': None, 'indices': None, 'confidence': None}

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
        # Valider les scores selon les règles strictes (avec gestion d'erreur)
        try:
            apartment = validate_style_score(apartment)
        except Exception as e:
            print(f"⚠️ Erreur validate_style_score pour {apartment.get('id')}: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            apartment = validate_ensoleillement_score(apartment)
        except Exception as e:
            print(f"⚠️ Erreur validate_ensoleillement_score pour {apartment.get('id')}: {e}")
            import traceback
            traceback.print_exc()
        
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
            
            # Style - toujours créer formatted_data.style (même sans scores_detaille)
            # car format_style utilise la date de construction ou l'analyse photo
            try:
                style_formatted = format_style(apartment)
                if 'formatted_data' not in apartment:
                    apartment['formatted_data'] = {}
                apartment['formatted_data']['style'] = {
                    'main_value': style_formatted.get('main_value'),  # "Haussmannien", "Années 70", "Moderne", etc.
                    'indices': style_formatted.get('indices'),  # Peut être None si pas d'indices trouvés
                    'confidence': style_formatted.get('confidence')
                }
            except Exception as e:
                # En cas d'erreur, ne pas mettre de fallback générique
                # Le frontend gérera l'affichage si pas d'indices
                if 'formatted_data' not in apartment:
                    apartment['formatted_data'] = {}
                apartment['formatted_data']['style'] = {
                    'main_value': None,
                    'indices': None,
                    'confidence': None
                }
            
            # Exposition
            # Créer formatted_data.exposition si l'appartement a soit scores_detaille.ensoleillement, soit exposition (depuis scraping), soit etage_num depuis API, soit visavis_distance
            has_ensoleillement_score = 'ensoleillement' in apartment.get('scores_detaille', {})
            exposition_obj = apartment.get('exposition', {})
            has_exposition_data = bool(exposition_obj.get('exposition'))
            has_etage_num = 'etage_num' in exposition_obj.get('details', {})
            has_visavis = 'visavis_distance' in exposition_obj.get('details', {})
            
            if has_ensoleillement_score or has_exposition_data or has_etage_num or has_visavis:
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

def load_apartments_data(enrich: bool = True) -> List[Dict[str, Any]]:
    """Charge les appartements scorés et fusionne avec les données scrapées
    
    Args:
        enrich: Si True, enrichit les appartements avec les indices formatés (peut être lent)
    """
    global _cached_apartments, _cache_timestamp
    
    print("🔍 [DEBUG] load_apartments_data() appelée")
    
    # Vérifier si le cache est encore valide (basé sur les temps de modification des fichiers)
    try:
        scores_file = 'data/scores/all_apartments_scores.json'
        scraped_file = 'data/scraped_apartments.json'
        appartements_dir = 'data/appartements'
        
        print("🔍 [DEBUG] Vérification des mtimes...")
        scores_mtime = os.path.getmtime(scores_file) if os.path.exists(scores_file) else 0
        scraped_mtime = os.path.getmtime(scraped_file) if os.path.exists(scraped_file) else 0
        
        # Calculer le mtime max des fichiers individuels dans data/appartements/
        appartements_max_mtime = 0
        if os.path.exists(appartements_dir):
            try:
                for filename in os.listdir(appartements_dir):
                    if filename.endswith('.json') and filename not in ['test_001.json', 'test_no_photo.json', 'unknown.json']:
                        filepath = os.path.join(appartements_dir, filename)
                        if os.path.isfile(filepath):
                            file_mtime = os.path.getmtime(filepath)
                            appartements_max_mtime = max(appartements_max_mtime, file_mtime)
            except Exception as e:
                print(f"⚠️ Erreur lors du calcul du mtime de {appartements_dir}: {e}")
        
        max_mtime = max(scores_mtime, scraped_mtime, appartements_max_mtime)
        
        # Si le cache est encore valide, le retourner (même si enrich=False, on retourne le cache enrichi s'il existe)
        if _cached_apartments is not None and max_mtime <= _cache_timestamp:
            print(f"🔍 [DEBUG] Cache valide, retour de {len(_cached_apartments)} appartements")
            # Si enrich=False, on peut retourner le cache même s'il est enrichi (c'est mieux que rien)
            return _cached_apartments
        
        print("🔍 [DEBUG] Cache invalide, chargement des données...")
        
        # OPTIMISATION: Si pas d'enrichissement, charger directement depuis le fichier (beaucoup plus rapide)
        if not enrich:
            print(f"🔍 [DEBUG] Mode rapide (enrich=False), chargement direct depuis {scores_file}...")
            if os.path.exists(scores_file):
                with open(scores_file, 'r', encoding='utf-8') as f:
                    scored_apartments = json.load(f)
                    print(f"✅ Chargement rapide: {len(scored_apartments)} appartements")
                    _cached_apartments = scored_apartments
                    _cache_timestamp = max_mtime
                    return scored_apartments
            else:
                print(f"❌ Fichier {scores_file} n'existe pas")
                return []
        
        # Charger les appartements scorés (avec gestion d'erreur)
        # OPTIMISATION: Charger directement depuis le fichier pour éviter le blocage
        try:
            # Charger directement depuis le fichier JSON (plus rapide que load_scored_apartments qui fait une fusion complexe)
            if os.path.exists(scores_file):
                print(f"🔍 [DEBUG] Chargement direct depuis {scores_file}...")
                with open(scores_file, 'r', encoding='utf-8') as f:
                    scored_apartments = json.load(f)
                    print(f"✅ Chargement direct depuis {scores_file}: {len(scored_apartments)} appartements")
            else:
                # Fallback: utiliser load_scored_apartments si le fichier n'existe pas
                print("🔍 [DEBUG] Appel de load_scored_apartments()...")
                scored_apartments = load_scored_apartments()
                print(f"🔍 [DEBUG] load_scored_apartments() retourné {len(scored_apartments)} appartements")
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des appartements scorés: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: charger directement depuis le fichier
            try:
                if os.path.exists(scores_file):
                    print(f"🔍 [DEBUG] Fallback: chargement direct depuis {scores_file}")
                    with open(scores_file, 'r', encoding='utf-8') as f:
                        scored_apartments = json.load(f)
                        print(f"✅ Chargement direct depuis {scores_file}: {len(scored_apartments)} appartements")
                else:
                    print(f"❌ Fichier {scores_file} n'existe pas")
                    scored_apartments = []
            except Exception as e2:
                print(f"❌ Erreur lors du chargement direct: {e2}")
                # Retourner une liste vide ou utiliser le cache si disponible
                if _cached_apartments is not None:
                    return _cached_apartments
                scored_apartments = []
        
        # Créer un dictionnaire indexé par ID pour fusion rapide
        scored_by_id = {str(apt.get('id')): apt for apt in scored_apartments}
        
        # Charger les appartements scrapés depuis scraped_apartments.json
        scraped_apartments = []
        scraped_data_by_id = {}
        if os.path.exists(scraped_file):
            try:
                with open(scraped_file, 'r', encoding='utf-8') as f:
                    scraped_apartments = json.load(f)
                    # Créer un dict par ID pour faciliter la fusion
                    for apt in scraped_apartments:
                        apt_id = str(apt.get('id'))
                        if apt_id:
                            scraped_data_by_id[apt_id] = apt
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement de {scraped_file}: {e}")
        
        # Charger aussi depuis les fichiers individuels dans data/appartements/ (priorité sur scraped_apartments.json)
        individual_apartments = {}
        if os.path.exists(appartements_dir):
            try:
                for filename in os.listdir(appartements_dir):
                    if filename.endswith('.json') and filename not in ['test_001.json', 'test_no_photo.json', 'unknown.json']:
                        filepath = os.path.join(appartements_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                apt_data = json.load(f)
                                apt_id = str(apt_data.get('id'))
                                if apt_id:
                                    # Les fichiers individuels ont priorité sur scraped_apartments.json
                                    # MAIS préserver l'exposition depuis scraped_apartments.json si elle existe (pour avoir visavis_distance)
                                    if apt_id in scraped_data_by_id and 'exposition' in scraped_data_by_id[apt_id]:
                                        scraped_expo = scraped_data_by_id[apt_id]['exposition']
                                        if scraped_expo.get('details', {}).get('visavis_distance') is not None:
                                            # Préserver l'exposition avec visavis_distance depuis scraped_apartments.json
                                            if 'exposition' not in apt_data:
                                                apt_data['exposition'] = {}
                                            apt_data['exposition'] = scraped_expo
                                    individual_apartments[apt_id] = apt_data
                        except Exception as e:
                            # Ignorer les erreurs de lecture de fichiers individuels
                            print(f"⚠️ Erreur lecture {filepath}: {e}")
                            pass
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement de {appartements_dir}: {e}")
        
        # Fusionner : pour chaque appartement scrapé, utiliser les scores s'ils existent
        merged_apartments = []
        scraped_ids_processed = set()
        
        # D'abord, ajouter tous les appartements scorés
        for apt in scored_apartments:
            merged_apartments.append(apt)
            scraped_ids_processed.add(str(apt.get('id')))
        
        # Ensuite, ajouter les appartements depuis les fichiers individuels (priorité)
        for apt_id, apt_data in individual_apartments.items():
            if apt_id not in scraped_ids_processed:
                # Utiliser les données depuis les fichiers individuels (les plus récentes)
                merged_apartments.append(apt_data)
                scraped_ids_processed.add(apt_id)
        
        # Enfin, ajouter les appartements depuis scraped_apartments.json qui n'ont pas encore été ajoutés
        for apt in scraped_apartments:
            apt_id = str(apt.get('id'))
            if apt_id not in scraped_ids_processed:
                # Utiliser les données scrapées sans scores (ils seront scorés à la volée si nécessaire)
                merged_apartments.append(apt)
        
        print(f"📊 Fusion: {len(scored_apartments)} scorés + {len(individual_apartments)} fichiers individuels + {len(scraped_apartments) - len(scored_by_id)} depuis scraped_apartments.json = {len(merged_apartments)} total")
        
        # Enrichir chaque appartement avec les indices formatés (avec gestion d'erreur)
        # OPTIMISATION: Enrichir seulement si demandé (peut être lent avec beaucoup d'appartements)
        if enrich:
            print(f"🔍 [DEBUG] Enrichissement de {len(merged_apartments)} appartements...")
            enriched_apartments = []
            
            for i, apt in enumerate(merged_apartments):
                if i % 100 == 0:
                    print(f"🔍 [DEBUG] Enrichissement en cours: {i}/{len(merged_apartments)}")
                try:
                    # Enrichir seulement les données essentielles pour éviter le blocage
                    enriched_apt = enrich_apartment_with_indices(apt)
                    enriched_apartments.append(enriched_apt)
                except Exception as e:
                    # En cas d'erreur sur un appartement, l'ajouter quand même sans enrichissement
                    print(f"⚠️ Erreur enrichissement appartement {apt.get('id')}: {e}")
                    enriched_apartments.append(apt)  # Ajouter l'appartement sans enrichissement
            
            print(f"🔍 [DEBUG] Enrichissement terminé: {len(enriched_apartments)} appartements")
        else:
            # Pas d'enrichissement: retourner les données brutes (beaucoup plus rapide)
            print(f"🔍 [DEBUG] Pas d'enrichissement demandé, retour de {len(merged_apartments)} appartements bruts")
            enriched_apartments = merged_apartments
        _cached_apartments = enriched_apartments
        _cache_timestamp = max_mtime
        
        print(f"🔍 [DEBUG] Retour de {len(_cached_apartments)} appartements")
        return _cached_apartments
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erreur dans load_apartments_data: {e}")
        print(f"   Traceback: {error_trace}")
        # Retourner le cache si disponible, sinon liste vide
        if _cached_apartments is not None:
            print("   ⚠️ Utilisation du cache en cas d'erreur")
            return _cached_apartments
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des données: {str(e)}")

@router.get("/apartments")
async def get_apartments(enrich: bool = Query(False, description="Enrichir les appartements avec les indices formatés (peut être lent)")) -> List[Dict[str, Any]]:
    """
    Retourne la liste de tous les appartements avec leurs scores et détails
    """
    try:
        print(f"🔍 [DEBUG] GET /api/apartments appelé avec enrich={enrich}")
        apartments = load_apartments_data(enrich=enrich)
        print(f"🔍 [DEBUG] Retour de {len(apartments)} appartements")
        return apartments
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Erreur dans get_apartments: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/apartments/stats")
async def get_apartments_stats() -> Dict[str, Any]:
    """
    Retourne les statistiques sur les appartements :
    - Nombre d'appartements avec une note de calme
    - Nombre d'appartements avec une taille de pièce de vie
    """
    try:
        apartments = load_apartments_data()
        total_apartments = len(apartments)
        
        # Compter les appartements avec une note de calme
        apartments_with_calme = 0
        for apt in apartments:
            scores_detaille = apt.get('scores_detaille', {})
            calme_score = scores_detaille.get('calme', {})
            # Vérifier si le score calme existe et a une structure valide
            if calme_score and isinstance(calme_score, dict):
                if 'score' in calme_score and 'tier' in calme_score:
                    # Vérifier que les détails sont présents (nouvelle structure)
                    details = calme_score.get('details', {})
                    if details and ('type_rue' in details or 'bars_restos' in details or 'commerces_agites' in details):
                        apartments_with_calme += 1
        
        # Compter les appartements avec une taille de pièce de vie
        apartments_with_piece_vie = 0
        for apt in apartments:
            # Vérifier dans analyses.piece_de_vie
            analyses = apt.get('analyses', {})
            piece_de_vie = analyses.get('piece_de_vie', {})
            has_piece_vie = False
            
            if piece_de_vie and isinstance(piece_de_vie, dict):
                # Vérifier si on a une surface estimée ou un pourcentage
                if 'surface_estimee_m2' in piece_de_vie or 'pourcentage_surface_totale' in piece_de_vie:
                    # Vérifier que ce n'est pas juste une erreur
                    if 'error' not in piece_de_vie:
                        has_piece_vie = True
            
            # Vérifier aussi dans scores_detaille.large_piece_vie
            if not has_piece_vie:
                scores_detaille = apt.get('scores_detaille', {})
                large_piece_vie = scores_detaille.get('large_piece_vie', {})
                if large_piece_vie and isinstance(large_piece_vie, dict):
                    # Vérifier si on a des détails avec salon_size_estimate ou pourcentage_salon
                    details = large_piece_vie.get('details', {})
                    if details and ('salon_size_estimate' in details or 'pourcentage_salon' in details):
                        has_piece_vie = True
            
            if has_piece_vie:
                apartments_with_piece_vie += 1
        
        return {
            "total_apartments": total_apartments,
            "apartments_with_calme": apartments_with_calme,
            "apartments_with_piece_vie": apartments_with_piece_vie,
            "percentage_with_calme": round((apartments_with_calme / total_apartments * 100), 1) if total_apartments > 0 else 0,
            "percentage_with_piece_vie": round((apartments_with_piece_vie / total_apartments * 100), 1) if total_apartments > 0 else 0
        }
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


@router.post("/apartments/refresh")
async def refresh_apartments() -> Dict[str, Any]:
    """
    Rafraîchit tous les appartements depuis l'API Jinka
    Réutilise la logique de fetch_all_apartments_api.py
    Télécharge les photos et récupère toutes les données de l'API
    """
    try:
        # Token hardcodé pour l'instant
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
        
        # 8. Invalider le cache pour forcer le rechargement
        invalidate_cache()
        
        # 9. Calculer les nouveaux
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
        print(f"❌ Erreur dans refresh_apartments: {e}")
        print(f"   Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du rafraîchissement: {str(e)}")


@router.post("/apartments/refresh/stream")
async def refresh_apartments_stream():
    """
    Rafraîchit tous les appartements depuis l'API Jinka avec progression en temps réel via Server-Sent Events (SSE)
    """
    async def generate():
        try:
            # Token hardcodé pour l'instant
            alert_url = "https://www.jinka.fr/asrenter/alert/dashboard/cebed5288c18eafafadb04e048a4e776"
            alert_token = "cebed5288c18eafafadb04e048a4e776"
            
            # Essayer de récupérer le nom de l'alerte
            alert_name = "Alerte"
            try:
                from scrape_jinka_api import JinkaAPIScraper
                scraper_temp = JinkaAPIScraper()
                await scraper_temp.setup()
                if await scraper_temp.login():
                    alerts = await scraper_temp.api_client.get_alert_list()
                    if alerts:
                        for alert in alerts:
                            if alert.get('id') == alert_token or alert.get('token') == alert_token:
                                alert_name = alert.get('name') or alert.get('title') or alert.get('label') or 'Alerte'
                                break
                await scraper_temp.cleanup()
            except:
                pass
            
            # Envoyer le message initial de connexion
            yield f"data: {json.dumps({'type': 'connecting', 'message': f'Connexion à {alert_name}...'})}\n\n"
            
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
            yield f"data: {json.dumps({'type': 'connecting', 'message': f'Connexion à {alert_name}...'})}\n\n"
            scraper = JinkaAPIScraper()
            await scraper.setup()
            if not await scraper.login():
                yield f"data: {json.dumps({'type': 'error', 'message': 'Échec de la connexion à Jinka'})}\n\n"
                return
            
            # 2. Récupérer le total d'appartements depuis la première page pour avoir le total
            message = "Récupération du nombre total d'appartements..."
            yield f"data: {json.dumps({'type': 'fetching_total', 'message': message})}\n\n"
            dashboard_data = await scraper.api_client.get_alert_dashboard(
                alert_token=alert_token,
                filter_type="all",
                page=1
            )
            
            total_apartments = 0
            if dashboard_data and dashboard_data.get('pagination'):
                total_apartments = dashboard_data.get('pagination', {}).get('total', 0)
            
            # 3. Récupérer tous les appartements avec progression
            yield f"data: {json.dumps({'type': 'start', 'total': total_apartments, 'message': f'Récupération de {total_apartments} appartements...'})}\n\n"
            
            all_apartments = []
            page = 1
            has_more = True
            max_pages = 50
            current_count = 0
            
            while has_more and page <= max_pages:
                # Récupérer le dashboard de la page
                dashboard_data = await scraper.api_client.get_alert_dashboard(
                    alert_token=alert_token,
                    filter_type="all",
                    page=page
                )
                
                if not dashboard_data:
                    break
                
                # Extraire les appartements de cette page
                from scrape_jinka_api import adapt_dashboard_to_apartment_list
                page_apartments = adapt_dashboard_to_apartment_list(dashboard_data)
                
                if not page_apartments:
                    has_more = False
                    break
                
                # Scraper les détails de chaque appartement
                for apt_info in page_apartments:
                    apartment_id = apt_info['id']
                    apartment_data = await scraper.scrape_apartment(apt_info['url'])
                    
                    if apartment_data:
                        all_apartments.append(apartment_data)
                        current_count += 1
                        # Envoyer la progression
                        yield f"data: {json.dumps({'type': 'progress', 'current': current_count, 'total': total_apartments if total_apartments > 0 else current_count, 'message': f'{current_count}/{total_apartments if total_apartments > 0 else current_count} appartements récupérés'})}\n\n"
                
                # Vérifier la pagination
                pagination_info = dashboard_data.get('pagination', {})
                if pagination_info:
                    has_more_pages = pagination_info.get('has_more', None)
                    if has_more_pages is False:
                        has_more = False
                    # Mettre à jour le total si on le découvre
                    if pagination_info.get('total', 0) > total_apartments:
                        total_apartments = pagination_info.get('total', 0)
                
                if len(page_apartments) == 0:
                    has_more = False
                
                page += 1
            
            if not all_apartments:
                await scraper.cleanup()
                error_msg = "Aucun appartement récupéré depuis l'API"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return
            
            # 4. Charger les existants
            yield f"data: {json.dumps({'type': 'processing', 'message': 'Traitement des données...'})}\n\n"
            existing = load_existing_apartments()
            
            # 5. Nettoyer et valider
            cleaned = [clean_apartment_data(apt) for apt in all_apartments if validate_apartment(apt)]
            cleaned = remove_duplicates(cleaned)
            
            # 6. Fusionner
            merged = merge_apartment_data(existing, cleaned)
            
            # 7. Télécharger les photos pour tous les appartements
            yield f"data: {json.dumps({'type': 'downloading_photos', 'message': 'Téléchargement des photos...'})}\n\n"
            photo_manager = PhotoManager()
            photos_downloaded = 0
            for i, apt in enumerate(merged, 1):
                apt_id = apt.get('id', 'unknown')
                photos_before = len(apt.get('photos', []))
                
                if photos_before > 0:
                    apt_with_photos = photo_manager.download_apartment_photos(apt, max_photos=10)
                    merged[i-1] = apt_with_photos
                    
                    downloaded_count = sum(1 for p in apt_with_photos.get('photos', []) if p.get('local_path'))
                    photos_downloaded += downloaded_count
            
            # 8. Sauvegarder
            yield f"data: {json.dumps({'type': 'saving', 'message': 'Sauvegarde des données...'})}\n\n"
            output_file = Path('data/scraped_apartments.json')
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2, default=str)
            
            # 9. Invalider le cache
            invalidate_cache()
            
            # 10. Calculer les nouveaux
            new_count = len(merged) - len(existing)
            
            await scraper.cleanup()
            
            print(f"✅ Refresh terminé: {new_count} nouveaux appartements, {photos_downloaded} photos téléchargées")
            
            # Envoyer le message final
            yield f"data: {json.dumps({'type': 'complete', 'new_count': new_count, 'total_count': len(merged), 'photos_downloaded': photos_downloaded, 'message': f'{new_count} nouveaux appartements ajoutés, {photos_downloaded} photos téléchargées'})}\n\n"
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Erreur dans refresh_apartments_stream: {e}")
            print(f"   Traceback: {error_trace}")
            error_msg = f'Erreur lors du rafraîchissement: {str(e)}'
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


def detect_missing_enriched_data(apartment: Dict[str, Any]) -> List[str]:
    """
    Détecte quels critères n'ont pas de données enrichies (formatted_data)
    
    Returns:
        Liste des noms de critères manquants
    """
    missing_criteria = []
    formatted_data = apartment.get('formatted_data', {})
    
    # Liste des critères à vérifier
    criteria_to_check = ['prix', 'cuisine', 'baignoire', 'style', 'exposition']
    
    for criterion in criteria_to_check:
        if criterion not in formatted_data or not formatted_data[criterion]:
            missing_criteria.append(criterion)
    
    return missing_criteria


def enrich_apartment_data_only(apartment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrichit un appartement avec formatted_data uniquement, SANS calculer de score
    
    Cette fonction :
    1. Analyse les photos avec l'IA si nécessaire (style, cuisine, baignoire, luminosité)
    2. Utilise les fonctions de formatage pour remplir formatted_data
    
    Args:
        apartment: Dict avec données de l'appartement
        
    Returns:
        Dict avec formatted_data rempli pour chaque critère disponible
    """
    apartment_id = apartment.get('id', 'unknown')
    
    # Initialiser formatted_data si nécessaire
    if 'formatted_data' not in apartment:
        apartment['formatted_data'] = {}
    
    # ÉTAPE 1: Analyser les photos si nécessaire (style, cuisine, baignoire, luminosité)
    # Vérifier la présence de chaque critère individuellement pour éviter les ré-analyses inutiles
    style_analysis = apartment.get('style_analysis', {})
    baignoire_data = apartment.get('baignoire_data', {})
    
    has_style = bool(style_analysis.get('style'))
    has_cuisine = bool(style_analysis.get('cuisine'))
    has_baignoire = bool(baignoire_data.get('has_baignoire') is not None)  # Vérifier si la valeur existe (même False)
    has_luminosite = bool(style_analysis.get('luminosite'))
    
    # Identifier les critères manquants
    missing_criteria = []
    if not has_style:
        missing_criteria.append('style')
    if not has_cuisine:
        missing_criteria.append('cuisine')
    if not has_baignoire:
        missing_criteria.append('baignoire')
    if not has_luminosite:
        missing_criteria.append('luminosité')
    
    # Faire l'analyse si au moins un critère manque
    needs_analysis = len(missing_criteria) > 0
    
    if needs_analysis:
        missing_str = ', '.join(missing_criteria)
        print(f"   📸 Analyse des photos pour {apartment_id} avec Gemini Flash (manquants: {missing_str})...")
        try:
            # Utiliser directement UnifiedApartmentAnalyzer avec Gemini Flash (plus rapide et moins cher)
            from analyze_apartment_unified import UnifiedApartmentAnalyzer
            
            # OPTIMISATION: Utiliser seulement 2 photos au lieu de 3 (réduction de 33% des coûts)
            # Gemini Flash peut analyser plusieurs images en une seule requête
            unified_analyzer = UnifiedApartmentAnalyzer()
            unified_result = unified_analyzer.analyze_apartment_unified(apartment, max_photos=2)
            
            if unified_result:
                # Initialiser style_analysis si nécessaire (préserver les données existantes)
                if 'style_analysis' not in apartment:
                    apartment['style_analysis'] = {}
                
                # Adapter le résultat au format attendu par les fonctions de formatage
                # Style - seulement si manquant
                if unified_result.get('style') and not has_style:
                    style_data = unified_result['style']
                    elements_detectes = style_data.get('details', {}).get('elements_detectes', []) or style_data.get('indices', []) or []
                    apartment['style_analysis']['style'] = {
                        'type': style_data.get('type', 'autre'),
                        'confidence': style_data.get('confidence', 0),
                        'justification': style_data.get('justification', ''),
                        'details': elements_detectes if isinstance(elements_detectes, list) else []
                    }
                    # Mettre à jour les métadonnées seulement si c'est une nouvelle analyse
                    if 'photos_analyzed' not in apartment['style_analysis']:
                        apartment['style_analysis']['photos_analyzed'] = unified_result.get('photos_analyzed', 0)
                        apartment['style_analysis']['method'] = 'unified_gemini_flash'
                        apartment['style_analysis']['model'] = 'gemini-2.5-flash'
                
                # Cuisine - seulement si manquante
                if unified_result.get('cuisine') and not has_cuisine:
                    cuisine_data = unified_result['cuisine']
                    apartment['style_analysis']['cuisine'] = {
                        'ouverte': cuisine_data.get('ouverte', False),
                        'confidence': cuisine_data.get('confidence', 0),
                        'detected_photos': cuisine_data.get('detected_photos', []),
                        'justification': cuisine_data.get('justification', '')
                    }
                
                # Baignoire - seulement si manquante
                if unified_result.get('baignoire') and not has_baignoire:
                    baignoire_result = unified_result['baignoire']
                    apartment['baignoire_data'] = {
                        'has_baignoire': baignoire_result.get('presente', False),
                        'has_douche': not baignoire_result.get('presente', False),
                        'confidence': baignoire_result.get('confidence', 0),
                        'detected_photos': baignoire_result.get('detected_photos', []),
                        'justification': baignoire_result.get('justification', '')
                    }
                
                # Luminosité - seulement si manquante
                if unified_result.get('luminosite') and not has_luminosite:
                    luminosite_data = unified_result['luminosite']
                    apartment['style_analysis']['luminosite'] = {
                        'type': luminosite_data.get('type', 'moyen'),
                        'confidence': luminosite_data.get('confidence', 0),
                        'justification': luminosite_data.get('justification', '')
                    }
                
                print(f"      ✅ Photos analysées avec Gemini Flash (2 photos) pour {apartment_id}")
            else:
                print(f"      ⚠️ Aucun résultat d'analyse pour {apartment_id}")
        except Exception as e:
            print(f"   ⚠️ Erreur analyse photos pour {apartment_id}: {e}")
            import traceback
            traceback.print_exc()
    
    # ÉTAPE 2: Enrichir chaque critère avec les fonctions de formatage
    # (ces fonctions utilisent maintenant les analyses faites ci-dessus)
    
    # 0. Prix
    try:
        prix_formatted = format_prix(apartment)
        apartment['formatted_data']['prix'] = {
            'main_value': prix_formatted.get('main_value'),
            'indices': prix_formatted.get('indices'),
            'confidence': prix_formatted.get('confidence')
        }
    except Exception as e:
        print(f"   ⚠️ Erreur format_prix pour {apartment_id}: {e}")
    
    # 1. Cuisine
    try:
        cuisine_formatted = format_cuisine(apartment)
        apartment['formatted_data']['cuisine'] = {
            'indices': cuisine_formatted.get('indices')
        }
    except Exception as e:
        print(f"   ⚠️ Erreur format_cuisine pour {apartment_id}: {e}")
    
    # 2. Baignoire
    try:
        baignoire_formatted = format_baignoire(apartment)
        apartment['formatted_data']['baignoire'] = {
            'main_value': baignoire_formatted.get('main_value'),
            'indices': baignoire_formatted.get('indices'),
            'confidence': baignoire_formatted.get('confidence')
        }
    except Exception as e:
        print(f"   ⚠️ Erreur format_baignoire pour {apartment_id}: {e}")
    
    # 3. Style
    try:
        style_formatted = format_style(apartment)
        apartment['formatted_data']['style'] = {
            'main_value': style_formatted.get('main_value'),  # "Haussmannien", "Années 70", "Moderne", etc.
            'indices': style_formatted.get('indices'),
            'confidence': style_formatted.get('confidence')
        }
    except Exception as e:
        print(f"   ⚠️ Erreur format_style pour {apartment_id}: {e}")
    
    # 4. Exposition
    # Vérifier si l'appartement a les données nécessaires pour l'exposition
    has_ensoleillement_score = 'ensoleillement' in apartment.get('scores_detaille', {})
    exposition_obj = apartment.get('exposition', {})
    has_exposition_data = bool(exposition_obj.get('exposition'))
    has_etage_num = 'etage_num' in exposition_obj.get('details', {})
    has_visavis = 'visavis_distance' in exposition_obj.get('details', {})
    has_luminosite_analysis = bool(apartment.get('style_analysis', {}).get('luminosite'))
    
    if has_ensoleillement_score or has_exposition_data or has_etage_num or has_visavis or has_luminosite_analysis:
        try:
            exposition_formatted = format_exposition(apartment)
            apartment['formatted_data']['exposition'] = {
                'main_value': exposition_formatted.get('main_value'),
                'indices': exposition_formatted.get('indices'),
                'confidence': exposition_formatted.get('confidence')
            }
        except Exception as e:
            print(f"   ⚠️ Erreur format_exposition pour {apartment_id}: {e}")
    
    return apartment


def save_apartment_to_file(apartment: Dict[str, Any]) -> bool:
    """
    Sauvegarde un appartement dans son fichier JSON individuel
    
    Args:
        apartment: Dict avec données de l'appartement
        
    Returns:
        True si sauvegarde réussie, False sinon
    """
    apartment_id = apartment.get('id')
    if not apartment_id:
        print(f"   ⚠️ Pas d'ID pour l'appartement, skip")
        return False
    
    apartment_file = f"data/appartements/{apartment_id}.json"
    try:
        from pathlib import Path
        Path(apartment_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(apartment_file, 'w', encoding='utf-8') as f:
            json.dump(apartment, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        print(f"   ❌ Erreur sauvegarde {apartment_id}: {e}")
        return False


@router.post("/apartments/enrich/stream")
async def enrich_apartments_stream(limit: int = Query(default=5, ge=0, description="Nombre maximum d'appartements à enrichir (0 = tous)")):
    """
    Enrichit les appartements avec progression en temps réel via Server-Sent Events (SSE)
    """
    async def generate():
        try:
            print(f"🔧 ENRICHISSEMENT DES APPARTEMENTS (SSE)")
            print(f"   Limite: {limit if limit > 0 else 'tous'}")
            
            # Charger tous les appartements
            apartments = load_apartments_data()
            
            if not apartments:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Aucun appartement trouvé'})}\n\n"
                return
            
            # Trier par date (plus récent en premier) pour prendre les plus récents
            apartments_sorted = sorted(
                apartments,
                key=lambda apt: apt.get('date_creation_annonce') or apt.get('scraped_at') or '',
                reverse=True
            )
            
            # Identifier les appartements sans données enrichies
            apartments_to_enrich = []
            for apartment in apartments_sorted:
                missing = detect_missing_enriched_data(apartment)
                if missing:  # Si au moins un critère manque
                    apartments_to_enrich.append(apartment)
            
            # Limiter le nombre d'appartements à enrichir si limit > 0
            if limit > 0:
                apartments_to_enrich = apartments_to_enrich[:limit]
            
            total = len(apartments_to_enrich)
            print(f"   📊 {total} appartement(s) à enrichir sur {len(apartments)} total")
            
            # Envoyer le message initial avec le total
            yield f"data: {json.dumps({'type': 'start', 'total': total})}\n\n"
            
            # Enrichir chaque appartement
            enriched_count = 0
            for i, apartment in enumerate(apartments_to_enrich, 1):
                apartment_id = apartment.get('id', 'unknown')
                print(f"   [{i}/{total}] Enrichissement {apartment_id}...")
                
                # Envoyer la progression
                yield f"data: {json.dumps({'type': 'progress', 'current': i, 'total': total, 'apartment_id': apartment_id})}\n\n"
                
                try:
                    # Enrichir les données formatées uniquement (sans score)
                    enriched_apartment = enrich_apartment_data_only(apartment)
                    
                    # Sauvegarder l'appartement enrichi
                    if save_apartment_to_file(enriched_apartment):
                        enriched_count += 1
                        print(f"      ✅ {apartment_id} enrichi et sauvegardé")
                    else:
                        print(f"      ⚠️ {apartment_id} enrichi mais erreur sauvegarde")
                    
                    # Petit délai pour permettre au frontend de mettre à jour l'UI
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"      ❌ Erreur enrichissement {apartment_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Erreur enrichissement {apartment_id}: {str(e)}', 'current': i, 'total': total})}\n\n"
            
            # Invalider le cache pour forcer le rechargement
            invalidate_cache()
            
            print(f"✅ Enrichissement terminé: {enriched_count} appartement(s) enrichi(s)")
            
            # Envoyer le message final
            yield f"data: {json.dumps({'type': 'complete', 'enriched_count': enriched_count, 'total': total, 'message': f'{enriched_count} appartement(s) enrichi(s) avec succès'})}\n\n"
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Erreur dans enrich_apartments_stream: {e}")
            print(f"   Traceback: {error_trace}")
            error_msg = f'Erreur lors de l\'enrichissement: {str(e)}'
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/apartments/enrich")
async def enrich_apartments(limit: int = Query(default=5, ge=0, description="Nombre maximum d'appartements à enrichir (0 = tous)")) -> Dict[str, Any]:
    """
    Enrichit les appartements sans données enrichies (formatted_data)
    
    Pour chaque appartement sans données enrichies:
    - Remplit formatted_data pour chaque critère disponible
    - NE CALCULE PAS de score
    
    Args:
        limit: Nombre maximum d'appartements à enrichir (par défaut 5 pour test)
               Si 0, enrichit tous les appartements sans données enrichies
    
    Returns:
        Dict avec:
            - enriched_count: Nombre d'appartements enrichis
            - total_checked: Nombre total d'appartements vérifiés
            - message: Message de succès
    """
    try:
        print(f"🔧 ENRICHISSEMENT DES APPARTEMENTS")
        print(f"   Limite: {limit if limit > 0 else 'tous'}")
        
        # Charger tous les appartements
        apartments = load_apartments_data()
        
        if not apartments:
            raise HTTPException(status_code=500, detail="Aucun appartement trouvé")
        
        # Trier par date (plus récent en premier) pour prendre les plus récents
        apartments_sorted = sorted(
            apartments,
            key=lambda apt: apt.get('date_creation_annonce') or apt.get('scraped_at') or '',
            reverse=True
        )
        
        # Identifier les appartements sans données enrichies
        apartments_to_enrich = []
        for apartment in apartments_sorted:
            missing = detect_missing_enriched_data(apartment)
            if missing:  # Si au moins un critère manque
                apartments_to_enrich.append(apartment)
        
        # Limiter le nombre d'appartements à enrichir si limit > 0
        if limit > 0:
            apartments_to_enrich = apartments_to_enrich[:limit]
        
        print(f"   📊 {len(apartments_to_enrich)} appartement(s) à enrichir sur {len(apartments)} total")
        
        # Enrichir chaque appartement
        enriched_count = 0
        for i, apartment in enumerate(apartments_to_enrich, 1):
            apartment_id = apartment.get('id', 'unknown')
            print(f"   [{i}/{len(apartments_to_enrich)}] Enrichissement {apartment_id}...")
            
            try:
                # Enrichir les données formatées uniquement (sans score)
                enriched_apartment = enrich_apartment_data_only(apartment)
                
                # Sauvegarder l'appartement enrichi
                if save_apartment_to_file(enriched_apartment):
                    enriched_count += 1
                    print(f"      ✅ {apartment_id} enrichi et sauvegardé")
                else:
                    print(f"      ⚠️ {apartment_id} enrichi mais erreur sauvegarde")
            except Exception as e:
                print(f"      ❌ Erreur enrichissement {apartment_id}: {e}")
                import traceback
                traceback.print_exc()
        
        # Invalider le cache pour forcer le rechargement
        invalidate_cache()
        
        print(f"✅ Enrichissement terminé: {enriched_count} appartement(s) enrichi(s)")
        
        return {
            "enriched_count": enriched_count,
            "total_checked": len(apartments),
            "apartments_to_enrich": len(apartments_to_enrich),
            "message": f"{enriched_count} appartement(s) enrichi(s) avec succès"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erreur dans enrich_apartments: {e}")
        print(f"   Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enrichissement: {str(e)}")


# Invalider le cache au démarrage pour forcer le rechargement avec les nouvelles données
invalidate_cache()

