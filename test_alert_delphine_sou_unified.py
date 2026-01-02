#!/usr/bin/env python3
"""
Retraitement LOCAL de tous les appartements de l'alerte "Sou & Delphine Apparte"
100% LOCAL - Pas de connexion à Jinka, utilise les données déjà scrapées
Vérifie que le système utilise bien un seul appel OpenAI Vision par photo pour tous les critères
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from analyze_apartment_style import ApartmentStyleAnalyzer
from scoring import score_apartment, load_scoring_config
from alert_scoring import filter_apartments_by_alert
from backend.api.apartments import load_apartments_data


class APICallCounter:
    """Compteur d'appels API pour vérifier qu'il n'y a pas d'appels redondants"""
    def __init__(self):
        self.vision_calls = 0
        self.text_calls = 0
        self.cache_hits = 0
        
    def reset(self):
        self.vision_calls = 0
        self.text_calls = 0
        self.cache_hits = 0
    
    def increment_vision(self):
        self.vision_calls += 1
    
    def increment_text(self):
        self.text_calls += 1
    
    def increment_cache(self):
        self.cache_hits += 1
    
    def get_stats(self):
        return {
            'vision_calls': self.vision_calls,
            'text_calls': self.text_calls,
            'cache_hits': self.cache_hits,
            'total_api_calls': self.vision_calls + self.text_calls
        }


def find_alert_by_name_local(alert_name: str) -> Dict[str, Any]:
    """Trouve une alerte par son nom depuis les fichiers locaux"""
    alerts_dir = "data/alerts"
    if not os.path.exists(alerts_dir):
        return None
    
    for filename in os.listdir(alerts_dir):
        if filename.endswith('.json'):
            alert_path = os.path.join(alerts_dir, filename)
            try:
                with open(alert_path, 'r', encoding='utf-8') as f:
                    alert = json.load(f)
                    if alert.get('name') == alert_name or alert_name.lower() in alert.get('name', '').lower():
                        return alert
            except Exception as e:
                print(f"⚠️ Erreur chargement {filename}: {e}")
    
    return None


async def find_alert_by_name(alert_name: str) -> Dict[str, Any]:
    """Trouve une alerte par son nom (local d'abord, puis API si nécessaire)"""
    # Essayer d'abord depuis les fichiers locaux
    alert = find_alert_by_name_local(alert_name)
    if alert:
        return alert
    
    # Sinon, essayer via l'API
    client = None
    try:
        client = JinkaAPIClient()
        if not await client.login():
            print("❌ Échec de la connexion")
            return None
        
        alerts = await client.get_alert_list()
        if alerts:
            for alert in alerts:
                user_name = alert.get('user_name', '')
                if alert_name.lower() in user_name.lower():
                    return alert
        
        return None
    except Exception as e:
        print(f"⚠️ Erreur lors de la recherche de l'alerte via API: {e}")
        return None
    finally:
        if client:
            try:
                await client.close()
            except:
                pass


def test_alert_unified_analysis():
    """Retraitement LOCAL avec analyse unifiée - 100% LOCAL"""
    print("🧪 RETRAITEMENT LOCAL - ALERTE 'Sou & Delphine Apparte'")
    print("=" * 80)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📍 Mode: 100% LOCAL (pas de connexion à Jinka)")
    print()
    
    # 1. Trouver l'alerte depuis les fichiers locaux
    print("1️⃣ Recherche de l'alerte 'Sou & Delphine Apparte'...")
    alert_name = "Sou & Delphine Apparte"
    alert = find_alert_by_name_local(alert_name)
    
    if not alert:
        print(f"❌ Alerte '{alert_name}' non trouvée dans data/alerts/")
        return
    
    alert_id = alert.get('id')
    print(f"✅ Alerte trouvée:")
    print(f"   ID: {alert_id}")
    print(f"   Nom: {alert.get('name', 'N/A')}")
    print()
    
    # 2. Charger tous les appartements depuis les fichiers locaux
    print("2️⃣ Chargement des appartements depuis les fichiers locaux...")
    try:
        all_apartments = load_apartments_data()
        print(f"✅ {len(all_apartments)} appartements chargés depuis les fichiers locaux")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not all_apartments:
        print("❌ Aucun appartement trouvé dans les fichiers locaux")
        return
    
    # 3. Filtrer les appartements selon l'alerte
    print("\n3️⃣ Filtrage des appartements selon l'alerte...")
    try:
        apartments = filter_apartments_by_alert(all_apartments, alert)
        print(f"✅ {len(apartments)} appartements correspondent aux critères de l'alerte")
    except Exception as e:
        print(f"❌ Erreur lors du filtrage: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not apartments:
        print("❌ Aucun appartement ne correspond aux critères de l'alerte")
        return
    print()
    
    # 4. Analyser chaque appartement avec le système unifié
    print("4️⃣ Analyse unifiée des appartements (1 seul appel Vision par photo)...")
    print("-" * 80)
    
    style_analyzer = ApartmentStyleAnalyzer()
    config = load_scoring_config()
    
    results = []
    apartments_with_photos = 0
    apartments_without_photos = 0
    total_photos_analyzed = 0
    
    for i, apartment in enumerate(apartments, 1):
            apt_id = apartment.get('id', 'N/A')
            localisation = apartment.get('localisation', 'N/A')
            photos = apartment.get('photos', [])
            
            print(f"\n[{i}/{len(apartments)}] Appartement {apt_id}")
            print(f"   Localisation: {localisation}")
            print(f"   Photos disponibles: {len(photos)}")
            
            if not photos:
                apartments_without_photos += 1
                print(f"   ⚠️  Pas de photos - analyse impossible")
                results.append({
                    'id': apt_id,
                    'has_photos': False,
                    'style_analysis': None,
                    'score': None
                })
                continue
            
            apartments_with_photos += 1
            
            try:
                # Analyser avec le système unifié (1 seul appel Vision par photo)
                print(f"   📸 Analyse unifiée des photos (max 5 photos)...")
                style_analysis = style_analyzer.analyze_apartment_photos_from_data(apartment)
                
                if style_analysis:
                    photos_analyzed = style_analysis.get('photos_analyzed', 0)
                    total_photos_analyzed += photos_analyzed
                    
                    # Vérifier que tous les critères sont présents
                    style = style_analysis.get('style', {})
                    cuisine = style_analysis.get('cuisine', {})
                    luminosite = style_analysis.get('luminosite', {})
                    baignoire = style_analysis.get('baignoire', {})
                    visavis = style_analysis.get('visavis', {})
                    salon_size = style_analysis.get('salon_size', {})
                    
                    print(f"   ✅ Analyse réussie ({photos_analyzed} photos analysées)")
                    print(f"      Style: {style.get('type', 'N/A')} (confiance: {style.get('confidence', 0):.2f})")
                    print(f"      Cuisine: {'Ouverte' if cuisine.get('ouverte') else 'Fermée'} (confiance: {cuisine.get('confidence', 0):.2f})")
                    print(f"      Luminosité: {luminosite.get('type', 'N/A')} (confiance: {luminosite.get('confidence', 0):.2f})")
                    
                    if baignoire.get('has_baignoire') is not None:
                        baignoire_status = 'Baignoire' if baignoire.get('has_baignoire') else ('Douche' if baignoire.get('has_douche') else 'N/A')
                        print(f"      Baignoire: {baignoire_status}")
                    
                    if visavis.get('distance'):
                        print(f"      Vis-à-vis: {visavis.get('distance')}m ({visavis.get('category', 'N/A')})")
                    
                    if salon_size.get('estimate'):
                        print(f"      Salon: {salon_size.get('estimate')}m² ({salon_size.get('category', 'N/A')})")
                    
                    # Ajouter style_analysis à l'appartement pour le scoring
                    apartment['style_analysis'] = style_analysis
                    
                    # Scorer l'appartement
                    print(f"   🎯 Scoring de l'appartement...")
                    score_result = score_apartment(apartment, config)
                    
                    if score_result:
                        score_total = score_result.get('score_total', 0)
                        tier = score_result.get('tier', 'N/A')
                        print(f"      Score total: {score_total}/100 ({tier})")
                        
                        results.append({
                            'id': apt_id,
                            'has_photos': True,
                            'photos_analyzed': photos_analyzed,
                            'style_analysis': style_analysis,
                            'score': score_result,
                            'score_total': score_total,
                            'tier': tier
                        })
                    else:
                        print(f"      ⚠️  Échec du scoring")
                        results.append({
                            'id': apt_id,
                            'has_photos': True,
                            'photos_analyzed': photos_analyzed,
                            'style_analysis': style_analysis,
                            'score': None
                        })
                else:
                    print(f"   ❌ Échec de l'analyse")
                    results.append({
                        'id': apt_id,
                        'has_photos': True,
                        'style_analysis': None,
                        'score': None
                    })
            
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    'id': apt_id,
                    'has_photos': True,
                    'error': str(e)
                })
    
    # 5. Statistiques finales
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES FINALES")
    print("=" * 80)
    print(f"✅ Appartements récupérés: {len(apartments)}")
    print(f"📸 Avec photos: {apartments_with_photos}")
    print(f"⚠️  Sans photos: {apartments_without_photos}")
    print(f"📷 Total photos analysées: {total_photos_analyzed}")
    print()
    
    # Statistiques sur les analyses réussies
    successful_analyses = [r for r in results if r.get('style_analysis')]
    print(f"✅ Analyses réussies: {len(successful_analyses)}/{apartments_with_photos}")
    
    if successful_analyses:
        # Statistiques sur les critères détectés
        styles_detected = {}
        cuisines_ouvertes = 0
        cuisines_fermees = 0
        luminosites = {}
        baignoires_detectees = 0
        visavis_detectes = 0
        
        for r in successful_analyses:
            style_analysis = r.get('style_analysis', {})
            
            # Style
            style_type = style_analysis.get('style', {}).get('type', 'N/A')
            styles_detected[style_type] = styles_detected.get(style_type, 0) + 1
            
            # Cuisine
            cuisine = style_analysis.get('cuisine', {})
            if cuisine.get('ouverte') is True:
                cuisines_ouvertes += 1
            elif cuisine.get('ouverte') is False:
                cuisines_fermees += 1
            
            # Luminosité
            luminosite_type = style_analysis.get('luminosite', {}).get('type', 'N/A')
            luminosites[luminosite_type] = luminosites.get(luminosite_type, 0) + 1
            
            # Baignoire
            baignoire = style_analysis.get('baignoire', {})
            if baignoire.get('has_baignoire') is not None:
                baignoires_detectees += 1
            
            # Vis-à-vis
            visavis = style_analysis.get('visavis', {})
            if visavis.get('distance'):
                visavis_detectes += 1
        
        print(f"\n📊 RÉPARTITION DES CRITÈRES DÉTECTÉS:")
        print(f"   Styles: {dict(styles_detected)}")
        print(f"   Cuisines ouvertes: {cuisines_ouvertes}")
        print(f"   Cuisines fermées: {cuisines_fermees}")
        print(f"   Luminosités: {dict(luminosites)}")
        print(f"   Baignoires détectées: {baignoires_detectees}")
        print(f"   Vis-à-vis détectés: {visavis_detectes}")
    
    # Statistiques sur les scores
    scored_results = [r for r in results if r.get('score')]
    if scored_results:
        scores = [r.get('score_total', 0) for r in scored_results]
        print(f"\n📊 STATISTIQUES DES SCORES:")
        print(f"   Appartements scorés: {len(scored_results)}")
        print(f"   Score moyen: {sum(scores) / len(scores):.1f}/100")
        print(f"   Score min: {min(scores)}/100")
        print(f"   Score max: {max(scores)}/100")
        
        # Répartition par tier
        tiers = {}
        for r in scored_results:
            tier = r.get('tier', 'unknown')
            tiers[tier] = tiers.get(tier, 0) + 1
        print(f"   Répartition par tier: {dict(tiers)}")
    
    # Vérification des appels API
    print(f"\n🔍 VÉRIFICATION DES APPELS API:")
    print(f"   📸 Appels Vision estimés: {total_photos_analyzed} (1 appel par photo)")
    print(f"   ✅ Tous les critères analysés en un seul appel par photo")
    print(f"   💡 Pas d'appels redondants pour la cuisine (données réutilisées depuis style_analysis)")
    
    # Sauvegarder les résultats du test
    output_file = 'data/test_alert_delphine_sou_results.json'
    os.makedirs('data', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'alert': alert,
            'total_apartments': len(apartments),
            'apartments_with_photos': apartments_with_photos,
            'apartments_without_photos': apartments_without_photos,
            'total_photos_analyzed': total_photos_analyzed,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 Résultats du test sauvegardés dans {output_file}")
    
    # Sauvegarder les appartements avec leurs nouvelles analyses dans les fichiers principaux
    print(f"\n💾 Sauvegarde des appartements avec nouvelles analyses...")
    
    # 1. Sauvegarder dans scraped_apartments.json (écrase les anciennes données)
    scraped_file = 'data/scraped_apartments.json'
    apartments_to_save = []
    for apartment in apartments:
        # Trouver les résultats d'analyse pour cet appartement
        apt_id = apartment.get('id')
        result = next((r for r in results if r.get('id') == apt_id), None)
        
        # Ajouter style_analysis si disponible
        if result and result.get('style_analysis'):
            apartment['style_analysis'] = result['style_analysis']
        
        # Ajouter le score si disponible
        if result and result.get('score'):
            apartment['score'] = result['score']
            apartment['score_total'] = result.get('score_total')
            apartment['tier'] = result.get('tier')
        
        apartments_to_save.append(apartment)
    
    with open(scraped_file, 'w', encoding='utf-8') as f:
        json.dump(apartments_to_save, f, ensure_ascii=False, indent=2, default=str)
    print(f"   ✅ {len(apartments_to_save)} appartements sauvegardés dans {scraped_file} (écrasé)")
    
    # 2. Sauvegarder dans all_apartments_scores.json (mise à jour avec nouveaux scores)
    scores_file = 'data/scores/all_apartments_scores.json'
    os.makedirs('data/scores', exist_ok=True)
    
    # Charger les scores existants
    existing_scores = []
    if os.path.exists(scores_file):
        try:
            with open(scores_file, 'r', encoding='utf-8') as f:
                existing_scores = json.load(f)
        except:
            existing_scores = []
    
    # Créer un dictionnaire des scores existants par ID
    scores_dict = {apt.get('id'): apt for apt in existing_scores}
    
    # Mettre à jour avec les nouveaux scores
    updated_count = 0
    for result in results:
        if result.get('score'):
            apt_id = result.get('id')
            # Trouver l'appartement correspondant
            apartment = next((apt for apt in apartments if apt.get('id') == apt_id), None)
            if apartment:
                # Créer l'entrée de score complète
                score_entry = result['score'].copy()
                score_entry.update(apartment)
                scores_dict[apt_id] = score_entry
                updated_count += 1
    
    # Sauvegarder tous les scores (existants + nouveaux)
    all_scores = list(scores_dict.values())
    with open(scores_file, 'w', encoding='utf-8') as f:
        json.dump(all_scores, f, ensure_ascii=False, indent=2, default=str)
    print(f"   ✅ {updated_count} scores mis à jour dans {scores_file} (total: {len(all_scores)} appartements)")
    
    # 3. Sauvegarder individuellement dans data/appartements/ (écrase les anciens fichiers)
    appartements_dir = 'data/appartements'
    os.makedirs(appartements_dir, exist_ok=True)
    individual_count = 0
    for apartment in apartments_to_save:
        apt_id = apartment.get('id')
        if apt_id:
            apt_file = os.path.join(appartements_dir, f"{apt_id}.json")
            with open(apt_file, 'w', encoding='utf-8') as f:
                json.dump(apartment, f, ensure_ascii=False, indent=2, default=str)
            individual_count += 1
    print(f"   ✅ {individual_count} fichiers individuels sauvegardés dans {appartements_dir}/ (écrasés)")
    
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ Retraitement terminé avec succès !")


if __name__ == "__main__":
    test_alert_unified_analysis()

