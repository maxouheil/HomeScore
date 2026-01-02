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
    from criteria import format_cuisine, format_baignoire, format_style, format_exposition, format_prix, format_hauteur, format_piece_vie
except Exception as e:
    print(f"⚠️ Erreur lors de l'import des critères: {e}")
    import traceback
    traceback.print_exc()
    # Fallback: fonctions vides
    def format_cuisine(apt): return {'indices': None}
    def format_baignoire(apt): return {'main_value': 'Non', 'indices': None, 'confidence': None}
    def format_style(apt): return {'indices': None}
    def format_hauteur(apt): return {'main_value': 'Non spécifié', 'indices': None, 'confidence': None}
    def format_exposition(apt): return {'main_value': 'Non spécifié', 'indices': None, 'confidence': None}
    def format_prix(apt): return {'main_value': None, 'indices': None, 'confidence': None}
    def format_piece_vie(apt): return {'main_value': 'Non spécifié', 'indices': None, 'confidence': None}

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
# Deux caches séparés: un pour les données enrichies, un pour les données brutes
_cached_apartments_enriched = None
_cached_apartments_raw = None
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
                    # Récupérer les photos détectées depuis style_analysis ou photo_validation
                    detected_photos = []
                    style_cuisine = apartment.get('style_analysis', {}).get('cuisine', {})
                    if style_cuisine.get('detected_photos'):
                        detected_photos = style_cuisine['detected_photos']
                    else:
                        # Fallback: chercher dans photo_validation
                        cuisine_score = apartment.get('scores_detaille', {}).get('cuisine', {})
                        photo_validation = cuisine_score.get('details', {}).get('photo_validation', {})
                        photo_result = photo_validation.get('photo_result', {})
                        if photo_result.get('detected_photos'):
                            detected_photos = photo_result['detected_photos']
                    apartment['formatted_data']['cuisine'] = {
                        'main_value': cuisine_formatted.get('main_value'),
                        'indices': cuisine_formatted.get('indices'),
                        'confidence': cuisine_formatted.get('confidence'),
                        'detected_photos': detected_photos if detected_photos else None
                    }
                    # #region agent log
                    import time
                    with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                        import json as json_module
                        logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:189","message":"Storing cuisine data in formatted_data","data":{"apartment_id":apartment.get('id'),"main_value":cuisine_formatted.get('main_value'),"detected_photos":detected_photos,"detected_photos_type":type(detected_photos).__name__,"detected_photos_len":len(detected_photos) if detected_photos else 0,"indices":cuisine_formatted.get('indices')[:100] if cuisine_formatted.get('indices') else None,"formatted_data_cuisine":apartment['formatted_data']['cuisine']},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
                    # #endregion
                except Exception as e:
                    # En cas d'erreur, utiliser la phrase par défaut
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    apartment['formatted_data']['cuisine'] = {
                        'main_value': None,
                        'indices': "Style expo cuisine et baignoire",
                        'confidence': None,
                        'detected_photos': None
                    }
            
            # Baignoire
            if 'baignoire' in apartment.get('scores_detaille', {}):
                try:
                    baignoire_formatted = format_baignoire(apartment)
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    # Récupérer les photos détectées depuis style_analysis ou photo_validation
                    detected_photos = []
                    style_baignoire = apartment.get('style_analysis', {}).get('baignoire', {})
                    if style_baignoire.get('detected_photos'):
                        detected_photos = style_baignoire['detected_photos']
                    else:
                        # Fallback: chercher dans photo_validation
                        baignoire_score = apartment.get('scores_detaille', {}).get('baignoire', {})
                        photo_validation = baignoire_score.get('details', {}).get('photo_validation', {})
                        photo_result = photo_validation.get('photo_result', {})
                        if photo_result.get('detected_photos'):
                            detected_photos = photo_result['detected_photos']
                    apartment['formatted_data']['baignoire'] = {
                        'main_value': baignoire_formatted.get('main_value'),
                        'indices': baignoire_formatted.get('indices'),
                        'confidence': baignoire_formatted.get('confidence'),
                        'detected_photos': detected_photos if detected_photos else None
                    }
                except Exception as e:
                    # En cas d'erreur, utiliser la phrase par défaut
                    if 'formatted_data' not in apartment:
                        apartment['formatted_data'] = {}
                    apartment['formatted_data']['baignoire'] = {
                        'main_value': 'Non',
                        'indices': "Style expo cuisine et baignoire",
                        'confidence': None,
                        'detected_photos': None
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
            
            # Hauteur plafond - toujours créer formatted_data.hauteur_plafond (même si non analysé)
            try:
                hauteur_formatted = format_hauteur(apartment)
                if 'formatted_data' not in apartment:
                    apartment['formatted_data'] = {}
                apartment['formatted_data']['hauteur_plafond'] = {
                    'main_value': hauteur_formatted.get('main_value'),
                    'indices': hauteur_formatted.get('indices'),
                    'confidence': hauteur_formatted.get('confidence')
                }
            except Exception as e:
                # Logger l'erreur pour debug
                import traceback
                print(f"❌ Erreur format_hauteur pour {apartment.get('id')}: {e}")
                print(traceback.format_exc())
                # En cas d'erreur, créer quand même avec "Non spécifié"
                if 'formatted_data' not in apartment:
                    apartment['formatted_data'] = {}
                apartment['formatted_data']['hauteur_plafond'] = {
                    'main_value': 'Non spécifié',
                    'indices': 'Hauteur Indice:\nNon spécifié',
                    'confidence': None
                }
            
            # Pièce de vie - toujours créer formatted_data.piece_vie (même si non analysé)
            try:
                piece_vie_formatted = format_piece_vie(apartment)
                if 'formatted_data' not in apartment:
                    apartment['formatted_data'] = {}
                apartment['formatted_data']['piece_vie'] = {
                    'main_value': piece_vie_formatted.get('main_value'),
                    'indices': piece_vie_formatted.get('indices'),
                    'confidence': piece_vie_formatted.get('confidence')
                }
            except Exception as e:
                # Logger l'erreur pour debug
                import traceback
                print(f"❌ Erreur format_piece_vie pour {apartment.get('id')}: {e}")
                print(traceback.format_exc())
                # En cas d'erreur, créer quand même avec "Non spécifié"
                if 'formatted_data' not in apartment:
                    apartment['formatted_data'] = {}
                apartment['formatted_data']['piece_vie'] = {
                    'main_value': 'Non spécifié',
                    'indices': 'Pièce de vie Indice:\nNon spécifié',
                    'confidence': None
                }
    except Exception as e:
        # Ne pas faire échouer la requête si l'enrichissement échoue
        pass
    
    return apartment

def load_apartments_data(enrich: bool = True) -> List[Dict[str, Any]]:
    """Charge les appartements depuis le fichier unique data/all_apartments.json
    
    Args:
        enrich: Si True, enrichit les appartements avec les indices formatés (peut être lent)
    """
    global _cached_apartments_enriched, _cached_apartments_raw, _cache_timestamp
    
    print("🔍 [DEBUG] load_apartments_data() appelée")
    
    # Fichier unique centralisé
    apartments_file = 'data/all_apartments.json'
    
    # Vérifier si le cache est encore valide (basé sur le temps de modification du fichier)
    try:
        import time
        print("🔍 [DEBUG] Vérification du mtime...")
        file_mtime = os.path.getmtime(apartments_file) if os.path.exists(apartments_file) else 0
        
        # Vérifier le cache approprié selon le mode d'enrichissement
        cached_apartments = _cached_apartments_enriched if enrich else _cached_apartments_raw
        
        # Si le cache est encore valide, le retourner
        if cached_apartments is not None and file_mtime <= _cache_timestamp:
            print(f"🔍 [DEBUG] Cache valide ({'enrichi' if enrich else 'brut'}), retour de {len(cached_apartments)} appartements")
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:299","message":"Cache hit - returning cached data","data":{"cache_count":len(cached_apartments),"file_mtime":file_mtime,"cache_timestamp":_cache_timestamp,"enrich":enrich},"sessionId":"debug-session","runId":"run1","hypothesisId":"D"}) + "\n")
            # #endregion
            return cached_apartments
        
        print(f"🔍 [DEBUG] Cache invalide ({'enrichi' if enrich else 'brut'}), chargement des données...")
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            cache_is_none = (_cached_apartments_enriched is None if enrich else _cached_apartments_raw is None)
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:303","message":"Cache miss - loading from file","data":{"file_mtime":file_mtime,"cache_timestamp":_cache_timestamp,"cache_is_none":cache_is_none,"enrich":enrich},"sessionId":"debug-session","runId":"run1","hypothesisId":"D"}) + "\n")
        # #endregion
        
        # Charger depuis le fichier unique
        if not os.path.exists(apartments_file):
            print(f"❌ Fichier {apartments_file} n'existe pas")
            # Fallback: essayer les anciens fichiers pour compatibilité
            print("⚠️  Tentative de fallback vers les anciens fichiers...")
            scores_file = 'data/scores/all_apartments_scores.json'
            if os.path.exists(scores_file):
                with open(scores_file, 'r', encoding='utf-8') as f:
                    apartments = json.load(f)
                    print(f"✅ Chargement depuis fallback: {len(apartments)} appartements")
                    if enrich:
                        _cached_apartments_enriched = apartments
                    else:
                        _cached_apartments_raw = apartments
                    _cache_timestamp = os.path.getmtime(scores_file)
                    return apartments
            return []
        
        # Charger depuis le fichier unique
        print(f"🔍 [DEBUG] Chargement depuis {apartments_file}...")
        with open(apartments_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        
        print(f"✅ Chargement depuis {apartments_file}: {len(apartments)} appartements")
        
        # Enrichir chaque appartement avec les indices formatés (avec gestion d'erreur)
        # OPTIMISATION: Enrichir seulement si demandé (peut être lent avec beaucoup d'appartements)
        if enrich:
            print(f"🔍 [DEBUG] Enrichissement de {len(apartments)} appartements...")
            enriched_apartments = []
            
            for i, apt in enumerate(apartments):
                if i % 100 == 0:
                    print(f"🔍 [DEBUG] Enrichissement en cours: {i}/{len(apartments)}")
                try:
                    # Enrichir seulement les données essentielles pour éviter le blocage
                    enriched_apt = enrich_apartment_with_indices(apt)
                    enriched_apartments.append(enriched_apt)
                except Exception as e:
                    # En cas d'erreur sur un appartement, l'ajouter quand même sans enrichissement
                    print(f"⚠️ Erreur enrichissement appartement {apt.get('id')}: {e}")
                    enriched_apartments.append(apt)  # Ajouter l'appartement sans enrichissement
            
            print(f"🔍 [DEBUG] Enrichissement terminé: {len(enriched_apartments)} appartements")
            apartments = enriched_apartments
            # Mettre en cache les données enrichies
            _cached_apartments_enriched = apartments
        else:
            # Pas d'enrichissement: retourner les données brutes (beaucoup plus rapide)
            print(f"🔍 [DEBUG] Pas d'enrichissement demandé, retour de {len(apartments)} appartements bruts")
            # Mettre en cache les données brutes
            _cached_apartments_raw = apartments
        
        _cache_timestamp = file_mtime
        
        # #region agent log
        import time
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            first_apt_id = apartments[0].get('id') if apartments else None
            first_has_style = bool(apartments[0].get('style_analysis', {}).get('style', {}).get('type')) if apartments else False
            # Vérifier un appartement enrichi spécifiquement
            enriched_apt = next((apt for apt in apartments if str(apt.get('id')) in ['95589222', '94739175', '91986959', '95510819']), None)
            enriched_id = enriched_apt.get('id') if enriched_apt else None
            enriched_has_style = bool(enriched_apt.get('style_analysis', {}).get('style', {}).get('type')) if enriched_apt else False
            enriched_has_formatted = bool(enriched_apt.get('formatted_data')) if enriched_apt else False
            enriched_has_hauteur = bool(enriched_apt.get('formatted_data', {}).get('hauteur_plafond') or enriched_apt.get('formatted_data', {}).get('hauteur')) if enriched_apt else False
            enriched_has_cuisine = bool(enriched_apt.get('formatted_data', {}).get('cuisine')) if enriched_apt else False
            enriched_has_piece_vie = bool(enriched_apt.get('formatted_data', {}).get('piece_vie')) if enriched_apt else False
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:362","message":"Data loaded and cached","data":{"count":len(apartments),"file_mtime":file_mtime,"cache_timestamp":_cache_timestamp,"first_id":first_apt_id,"first_has_style":first_has_style,"enrich":enrich,"enriched_id":enriched_id,"enriched_has_style":enriched_has_style,"enriched_has_formatted":enriched_has_formatted,"enriched_has_hauteur":enriched_has_hauteur,"enriched_has_cuisine":enriched_has_cuisine,"enriched_has_piece_vie":enriched_has_piece_vie},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        # #endregion
        if apartments is None or len(apartments) == 0:
            raise HTTPException(status_code=500, detail="Erreur: aucun appartement chargé")
        print(f"🔍 [DEBUG] Retour de {len(apartments)} appartements ({'enrichis' if enrich else 'bruts'})")
        return apartments
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erreur dans load_apartments_data: {e}")
        print(f"   Traceback: {error_trace}")
        # Retourner le cache si disponible, sinon liste vide
        cached_apartments = _cached_apartments_enriched if enrich else _cached_apartments_raw
        if cached_apartments is not None:
            print(f"   ⚠️ Utilisation du cache ({'enrichi' if enrich else 'brut'}) en cas d'erreur")
            return cached_apartments
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des données: {str(e)}")

@router.get("/apartments")
async def get_apartments(enrich: bool = Query(False, description="Enrichir les appartements avec les indices formatés (peut être lent)")) -> List[Dict[str, Any]]:
    """
    Retourne la liste de tous les appartements avec leurs scores et détails
    """
    try:
        import time
        print(f"🔍 [DEBUG] GET /api/apartments appelé avec enrich={enrich}")
        
        # Charger tous les appartements d'abord
        all_apartments = load_apartments_data(enrich=False)  # Charger sans enrich pour être rapide
        
        # Normaliser TOUS les appartements (pas seulement 5)
        print(f"🔍 [DEBUG] Normalisation de {len(all_apartments)} appartements...")
        try:
            # Import du normaliseur depuis le répertoire backend
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            normalizers_path = os.path.join(backend_dir, 'normalizers')
            if normalizers_path not in sys.path:
                sys.path.insert(0, backend_dir)
            
            from normalizers.simple_normalizer import normalize_apartment
            
            normalized_apartments = []
            for i, apt in enumerate(all_apartments):
                try:
                    apt_id = apt.get('id', 'N/A')
                    if (i + 1) % 100 == 0:
                        print(f"🔍 [DEBUG] Normalisation en cours: {i + 1}/{len(all_apartments)}")
                    
                    normalized = normalize_apartment(apt)
                    normalized_apartments.append(normalized)
                except Exception as e:
                    print(f"⚠️ Erreur normalisation {apt.get('id', 'N/A')}: {e}")
                    import traceback
                    traceback.print_exc()
                    # En cas d'erreur, retourner l'appartement non normalisé
                    normalized_apartments.append(apt)
            
            print(f"✅ {len(normalized_apartments)} appartements normalisés retournés")
            # Log du premier appartement pour vérifier
            if normalized_apartments:
                first = normalized_apartments[0]
                print(f"🔍 [DEBUG] Premier appartement normalisé: {first.get('id')}, criteria={bool(first.get('criteria'))}")
            return normalized_apartments
        except Exception as e:
            print(f"⚠️ Erreur import normaliseur: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: retourner les appartements non normalisés
            print(f"⚠️ Fallback: retour de {len(all_apartments)} appartements non normalisés")
            return all_apartments
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
    import time
    global _cached_apartments_enriched, _cached_apartments_raw, _cache_timestamp
    # #region agent log
    with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
        import json as json_module
        logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:467","message":"invalidate_cache called","data":{"cache_enriched_was_none":_cached_apartments_enriched is None,"cache_raw_was_none":_cached_apartments_raw is None,"old_timestamp":_cache_timestamp},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
    # #endregion
    _cached_apartments_enriched = None
    _cached_apartments_raw = None
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
        output_file = Path('data/all_apartments.json')
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
    
    # ÉTAPE 1: Analyser les photos (toujours analyser pour forcer la mise à jour)
    # On force toujours l'analyse pour s'assurer que toutes les données sont à jour
    needs_analysis = True
    
    if needs_analysis:
        print(f"   📸 Analyse des photos pour {apartment_id} avec Gemini Flash (analyse complète)...")
        try:
            # Utiliser directement UnifiedApartmentAnalyzer avec Gemini Flash (plus rapide et moins cher)
            from analyze_apartment_unified import UnifiedApartmentAnalyzer
            
            # Analyse jusqu'à 7 photos pour une meilleure couverture des critères (taille pièce de vie, hauteur plafond, cuisine, baignoire, style)
            # Gemini Flash peut analyser plusieurs images en une seule requête
            # Force la réanalyse pour toujours avoir les données à jour
            unified_analyzer = UnifiedApartmentAnalyzer()
            unified_result = unified_analyzer.analyze_apartment_unified(apartment, max_photos=7, force_reanalysis=True)
            
            if unified_result:
                # Initialiser style_analysis si nécessaire (préserver les données existantes)
                if 'style_analysis' not in apartment:
                    apartment['style_analysis'] = {}
                
                # Initialiser analyses si nécessaire
                if 'analyses' not in apartment:
                    apartment['analyses'] = {}
                
                # Adapter le résultat au format attendu par les fonctions de formatage
                # Style - toujours mettre à jour si disponible
                if unified_result.get('style'):
                    style_data = unified_result['style']
                    elements_detectes = style_data.get('details', {}).get('elements_detectes', []) or style_data.get('indices', []) or []
                    apartment['style_analysis']['style'] = {
                        'type': style_data.get('type', 'autre'),
                        'confidence': style_data.get('confidence', 0),
                        'justification': style_data.get('justification', ''),
                        'details': {'elements_detectes': elements_detectes if isinstance(elements_detectes, list) else []}
                    }
                    # Mettre à jour les métadonnées
                    apartment['style_analysis']['photos_analyzed'] = unified_result.get('photos_analyzed', 0)
                    apartment['style_analysis']['method'] = 'unified_gemini_flash'
                    apartment['style_analysis']['model'] = 'gemini-2.5-flash'
                
                # Année de construction depuis l'image - toujours mettre à jour si disponible
                if unified_result.get('annee_construction'):
                    annee_data = unified_result['annee_construction']
                    annee = annee_data.get('annee')
                    if annee:
                        # Stocker dans _api_data.features.year si pas déjà présent depuis l'API
                        if '_api_data' not in apartment:
                            apartment['_api_data'] = {}
                        if 'features' not in apartment['_api_data']:
                            apartment['_api_data']['features'] = {}
                        # Ne pas écraser si déjà présent depuis l'API (priorité API > image)
                        if not apartment['_api_data']['features'].get('year'):
                            apartment['_api_data']['features']['year'] = annee
                
                # Cuisine - toujours mettre à jour si disponible
                if unified_result.get('cuisine'):
                    cuisine_data = unified_result['cuisine']
                    cuisine_ouverte = cuisine_data.get('ouverte')
                    cuisine_visible = cuisine_data.get('visible', True)  # Par défaut True si non spécifié
                    
                    # Si la cuisine n'est pas visible (explicitement False), ne pas mettre à jour
                    if cuisine_visible is False:
                        print(f"      ⚠️  Cuisine non visible dans les photos pour {apartment.get('id', 'unknown')}")
                    # Si cuisine_ouverte est None mais visible n'est pas False, 
                    # on met quand même à jour pour indiquer qu'elle est visible mais non déterminable
                    elif cuisine_ouverte is None:
                        apartment['style_analysis']['cuisine'] = {
                            'ouverte': None,  # Non déterminable
                            'confidence': 0,
                            'detected_photos': cuisine_data.get('detected_photos', []),
                            'justification': cuisine_data.get('justification', 'Cuisine visible mais statut ouverte/fermée non déterminable')
                        }
                        print(f"      ⚠️  Cuisine visible mais statut ouverte/fermée non déterminable pour {apartment.get('id', 'unknown')}")
                    else:
                        # Cuisine détectée avec statut clair (ouverte ou fermée)
                        apartment['style_analysis']['cuisine'] = {
                            'ouverte': cuisine_ouverte,
                            'confidence': cuisine_data.get('confidence', 0),
                            'detected_photos': cuisine_data.get('detected_photos', []),
                            'justification': cuisine_data.get('justification', '')
                        }
                        cuisine_status = 'Ouverte' if cuisine_ouverte else 'Fermée'
                        print(f"      ✅ Cuisine détectée: {cuisine_status} (confiance: {cuisine_data.get('confidence', 0):.0%})")
                
                # Douche - toujours mettre à jour si disponible
                if unified_result.get('douche'):
                    douche_data = unified_result['douche']
                    if 'baignoire_data' not in apartment:
                        apartment['baignoire_data'] = {}
                    apartment['baignoire_data']['has_douche'] = douche_data.get('presente', False)
                    if not apartment['baignoire_data'].get('has_baignoire'):
                        # Si pas de baignoire détectée, on peut supposer qu'il y a une douche
                        apartment['baignoire_data']['has_baignoire'] = not douche_data.get('presente', True)
                
                # Baignoire - toujours mettre à jour si disponible
                if unified_result.get('baignoire'):
                    baignoire_result = unified_result['baignoire']
                    if 'baignoire_data' not in apartment:
                        apartment['baignoire_data'] = {}
                    apartment['baignoire_data']['has_baignoire'] = baignoire_result.get('presente', False)
                    apartment['baignoire_data']['has_douche'] = not baignoire_result.get('presente', False)
                    apartment['baignoire_data']['confidence'] = baignoire_result.get('confidence', 0)
                    apartment['baignoire_data']['detected_photos'] = baignoire_result.get('detected_photos', [])
                    apartment['baignoire_data']['justification'] = baignoire_result.get('justification', '')
                
                # Luminosité - toujours mettre à jour si disponible
                if unified_result.get('luminosite'):
                    luminosite_data = unified_result['luminosite']
                    apartment['style_analysis']['luminosite'] = {
                        'type': luminosite_data.get('type', 'moyen'),
                        'confidence': luminosite_data.get('confidence', 0),
                        'justification': luminosite_data.get('justification', '')
                    }
                    print(f"      ✅ Luminosité détectée: {luminosite_data.get('type', 'N/A')}")
                
                # Hauteur plafond - toujours mettre à jour si disponible
                if unified_result.get('hauteur_plafond'):
                    hauteur_data = unified_result['hauteur_plafond']
                    hauteur_estimee = hauteur_data.get('hauteur_estimee')
                    if hauteur_estimee:
                        apartment['analyses']['hauteur_plafond'] = {
                            'hauteur_estimee': hauteur_estimee,
                            'confiance': hauteur_data.get('confidence', 0.7),
                            'justification': hauteur_data.get('justification', '')
                        }
                        print(f"      ✅ Hauteur plafond détectée: {hauteur_estimee}m")
                
                # Pièce de vie - toujours mettre à jour si disponible
                if unified_result.get('piece_vie'):
                    piece_vie_data = unified_result['piece_vie']
                    taille_m2 = piece_vie_data.get('taille_m2')
                    taille = piece_vie_data.get('taille', 'moyenne')
                    apartment['piece_vie'] = {
                        'taille': taille,
                        'taille_m2': taille_m2,  # Estimation en m² depuis l'analyse d'image
                        'confidence': piece_vie_data.get('confidence', 0),
                        'justification': piece_vie_data.get('justification', '')
                    }
                    if taille_m2:
                        print(f"      ✅ Pièce de vie détectée: {taille} ({taille_m2}m²)")
                    else:
                        print(f"      ✅ Pièce de vie détectée: {taille}")
                
                # Vis-à-vis - toujours mettre à jour si disponible
                if unified_result.get('visavis'):
                    visavis_data = unified_result['visavis']
                    visavis_distance = visavis_data.get('distance')
                    visavis_category = visavis_data.get('category')
                    
                    if visavis_distance is not None:
                        # Initialiser exposition si nécessaire
                        if 'exposition' not in apartment:
                            apartment['exposition'] = {}
                        if 'details' not in apartment['exposition']:
                            apartment['exposition']['details'] = {}
                        
                        # Sauvegarder les données du vis-à-vis
                        apartment['exposition']['details']['visavis_distance'] = visavis_distance
                        if visavis_category:
                            apartment['exposition']['details']['visavis_category'] = visavis_category
                        apartment['exposition']['details']['visavis_confidence'] = visavis_data.get('confidence', 0.5)
                        apartment['exposition']['details']['visavis_justification'] = visavis_data.get('justification', '')
                        
                        print(f"      ✅ Vis-à-vis détecté: {visavis_distance}m ({visavis_category or 'N/A'})")
                
                # Afficher le nombre réel de photos analysées
                photos_analyzed_count = unified_result.get('photos_analyzed', 0)
                print(f"      ✅ Photos analysées avec Gemini Flash ({photos_analyzed_count} photos) pour {apartment_id}")
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
            'main_value': cuisine_formatted.get('main_value'),
            'indices': cuisine_formatted.get('indices'),
            'confidence': cuisine_formatted.get('confidence')
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
    
    # 5. Hauteur plafond
    # Toujours créer formatted_data.hauteur_plafond (même si non analysé, pour afficher "Non analysé")
    try:
        hauteur_formatted = format_hauteur(apartment)
        apartment['formatted_data']['hauteur_plafond'] = {
            'main_value': hauteur_formatted.get('main_value'),
            'indices': hauteur_formatted.get('indices'),
            'confidence': hauteur_formatted.get('confidence')
        }
    except Exception as e:
        print(f"   ⚠️ Erreur format_hauteur pour {apartment_id}: {e}")
        # En cas d'erreur, créer quand même avec "Non analysé"
        apartment['formatted_data']['hauteur_plafond'] = {
            'main_value': 'Non spécifié',
            'indices': 'Hauteur Indice:\nNon spécifié',
            'confidence': None
        }
    
    # 6. Pièce de vie
    # Toujours créer formatted_data.piece_vie (même si non analysé)
    try:
        piece_vie_formatted = format_piece_vie(apartment)
        apartment['formatted_data']['piece_vie'] = {
            'main_value': piece_vie_formatted.get('main_value'),
            'indices': piece_vie_formatted.get('indices'),
            'confidence': piece_vie_formatted.get('confidence')
        }
    except Exception as e:
        print(f"   ⚠️ Erreur format_piece_vie pour {apartment_id}: {e}")
        # En cas d'erreur, créer quand même avec "Non analysé"
        apartment['formatted_data']['piece_vie'] = {
            'main_value': 'Non spécifié',
            'indices': 'Pièce de vie Indice:\nNon spécifié',
            'confidence': None
        }
    
    return apartment


def save_apartment_to_file(apartment: Dict[str, Any]) -> bool:
    """
    Sauvegarde un appartement dans le fichier unique data/all_apartments.json
    
    Args:
        apartment: Dict avec données de l'appartement
        
    Returns:
        True si sauvegarde réussie, False sinon
    """
    import time
    apartment_id = apartment.get('id')
    if not apartment_id:
        print(f"   ⚠️ Pas d'ID pour l'appartement, skip")
        return False
    
    apartments_file = 'data/all_apartments.json'
    try:
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:1092","message":"save_apartment_to_file started","data":{"apartment_id":apartment_id},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        # #endregion
        from pathlib import Path
        Path(apartments_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Charger tous les appartements existants
        all_apartments = []
        if os.path.exists(apartments_file):
            try:
                with open(apartments_file, 'r', encoding='utf-8') as f:
                    all_apartments = json.load(f)
            except Exception as e:
                print(f"   ⚠️ Erreur lecture {apartments_file}: {e}")
                all_apartments = []
        
        # Créer un dict par ID pour faciliter la mise à jour
        apartments_by_id = {str(apt.get('id')): apt for apt in all_apartments if apt.get('id')}
        
        # Mettre à jour ou ajouter l'appartement
        apartments_by_id[str(apartment_id)] = apartment
        
        # Convertir en liste et trier par ID
        all_apartments = list(apartments_by_id.values())
        all_apartments.sort(key=lambda x: str(x.get('id', '')))
        
        # Sauvegarder
        save_start_time = time.time()
        with open(apartments_file, 'w', encoding='utf-8') as f:
            json.dump(all_apartments, f, ensure_ascii=False, indent=2, default=str)
            # Forcer l'écriture sur disque
            f.flush()
            try:
                os.fsync(f.fileno())
            except (AttributeError, OSError):
                pass  # fsync peut ne pas être disponible sur tous les systèmes
        save_end_time = time.time()
        file_mtime_after = os.path.getmtime(apartments_file) if os.path.exists(apartments_file) else 0
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:1123","message":"File saved to disk","data":{"apartment_id":apartment_id,"save_duration_ms":(save_end_time-save_start_time)*1000,"file_mtime":file_mtime_after},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        # #endregion
        
        # Invalider le cache pour forcer le rechargement
        invalidate_cache()
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:1133","message":"Cache invalidated after save","data":{"apartment_id":apartment_id},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
        # #endregion
        
        print(f"      💾 {apartment_id} sauvegardé dans {apartments_file}")
        return True
    except Exception as e:
        print(f"   ❌ Erreur sauvegarde {apartment_id}: {e}")
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            import json as json_module
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:1138","message":"Save error","data":{"apartment_id":apartment_id,"error":str(e)},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        # #endregion
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
            
            # MODIFICATION: Toujours prendre les N derniers (limit) pour forcer la réanalyse
            # même s'ils sont déjà analysés
            if limit > 0:
                apartments_to_enrich = apartments_sorted[:limit]
            else:
                # Si limit = 0, prendre tous les appartements sans données enrichies
                apartments_to_enrich = []
                for apartment in apartments_sorted:
                    missing = detect_missing_enriched_data(apartment)
                    if missing:  # Si au moins un critère manque
                        apartments_to_enrich.append(apartment)
            
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
                    # Vérifier les données avant enrichissement pour debug
                    before_style = apartment.get('style_analysis', {}).get('style', {}).get('type', 'N/A')
                    before_cuisine = apartment.get('style_analysis', {}).get('cuisine', {}).get('ouverte', 'N/A')
                    
                    # Enrichir les données formatées uniquement (sans score)
                    enriched_apartment = enrich_apartment_data_only(apartment)
                    
                    # Vérifier les données après enrichissement pour debug
                    after_style = enriched_apartment.get('style_analysis', {}).get('style', {}).get('type', 'N/A')
                    after_cuisine = enriched_apartment.get('style_analysis', {}).get('cuisine', {}).get('ouverte', 'N/A')
                    after_luminosite = enriched_apartment.get('style_analysis', {}).get('luminosite', {}).get('type', 'N/A')
                    after_hauteur = enriched_apartment.get('analyses', {}).get('hauteur_plafond', {}).get('hauteur_estimee', 'N/A')
                    after_piece_vie = enriched_apartment.get('piece_vie', {}).get('taille', 'N/A')
                    print(f"      📊 {apartment_id} - Style: {before_style} -> {after_style}, Cuisine: {before_cuisine} -> {after_cuisine}")
                    print(f"      📊 {apartment_id} - Luminosité: {after_luminosite}, Hauteur: {after_hauteur}, Pièce de vie: {after_piece_vie}")
                    
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
            import time
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:1225","message":"Enrichment complete, invalidating cache","data":{"enriched_count":enriched_count,"total":total},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            # #endregion
            invalidate_cache()
            
            print(f"✅ Enrichissement terminé: {enriched_count} appartement(s) enrichi(s)")
            
            # Envoyer le message final
            complete_msg = {'type': 'complete', 'enriched_count': enriched_count, 'total': total, 'message': f'{enriched_count} appartement(s) enrichi(s) avec succès'}
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                import json as json_module
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"apartments.py:1231","message":"Sending complete event","data":complete_msg,"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
            # #endregion
            yield f"data: {json.dumps(complete_msg)}\n\n"
            
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

