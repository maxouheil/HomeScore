#!/usr/bin/env python3
"""
Régénère les analyses de style pour TOUS les appartements avec le nouveau système
Force la régénération même si style_analysis existe déjà
"""

import json
import os
from analyze_apartment_style import ApartmentStyleAnalyzer

def load_apartments():
    """Charge tous les appartements depuis différentes sources"""
    apartments = []
    
    # Source 1: scraped_apartments.json
    scraped_file = "data/scraped_apartments.json"
    if os.path.exists(scraped_file):
        with open(scraped_file, 'r', encoding='utf-8') as f:
            apartments.extend(json.load(f))
            print(f"   ✅ {len(apartments)} appartements chargés depuis scraped_apartments.json")
    
    # Source 2: data/appartements/*.json
    appartements_dir = "data/appartements"
    if os.path.exists(appartements_dir):
        for filename in os.listdir(appartements_dir):
            if filename.endswith('.json') and not filename.startswith('test'):
                apt_id = filename.replace('.json', '')
                # Vérifier si pas déjà dans la liste
                if not any(apt.get('id') == apt_id for apt in apartments):
                    apt_file = os.path.join(appartements_dir, filename)
                    try:
                        with open(apt_file, 'r', encoding='utf-8') as f:
                            apartment = json.load(f)
                            apartments.append(apartment)
                    except:
                        pass
    
    # Dédupliquer par ID
    seen_ids = set()
    unique_apartments = []
    for apt in apartments:
        apt_id = apt.get('id')
        if apt_id and apt_id not in seen_ids:
            seen_ids.add(apt_id)
            unique_apartments.append(apt)
    
    return unique_apartments

def save_apartment(apartment_data, apartment_id):
    """Sauvegarde un appartement mis à jour"""
    # Sauvegarder dans data/appartements/
    appartements_dir = "data/appartements"
    os.makedirs(appartements_dir, exist_ok=True)
    
    apartment_file = os.path.join(appartements_dir, f"{apartment_id}.json")
    with open(apartment_file, 'w', encoding='utf-8') as f:
        json.dump(apartment_data, f, indent=2, ensure_ascii=False)
    
    # Mettre à jour aussi scraped_apartments.json si présent
    scraped_file = "data/scraped_apartments.json"
    if os.path.exists(scraped_file):
        try:
            with open(scraped_file, 'r', encoding='utf-8') as f:
                scraped_apartments = json.load(f)
            
            # Trouver et mettre à jour l'appartement
            for i, apt in enumerate(scraped_apartments):
                if apt.get('id') == apartment_id:
                    scraped_apartments[i] = apartment_data
                    break
            else:
                # Si pas trouvé, ajouter
                scraped_apartments.append(apartment_data)
            
            with open(scraped_file, 'w', encoding='utf-8') as f:
                json.dump(scraped_apartments, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"   ⚠️  Erreur mise à jour scraped_apartments.json: {e}")
    
    return apartment_file

def regenerate_all_style_analysis():
    """Régénère les analyses de style pour tous les appartements"""
    print("=" * 80)
    print("🔄 RÉGÉNÉRATION DES ANALYSES DE STYLE")
    print("=" * 80)
    print("   Nouveau système avec indices précis et numéros d'images")
    print()
    
    # Charger tous les appartements
    print("📋 Chargement des appartements...")
    apartments = load_apartments()
    
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"✅ {len(apartments)} appartements uniques trouvés\n")
    
    # Initialiser l'analyseur
    analyzer = ApartmentStyleAnalyzer()
    
    if not analyzer.openai_api_key or analyzer.openai_api_key == 'votre_clé_openai':
        print("❌ Clé API OpenAI non configurée")
        print("   Configurez OPENAI_API_KEY dans le fichier .env")
        return
    
    # Vider le cache des photos de style pour forcer la régénération avec le nouveau format
    print("🗑️  Vidage du cache des photos de style pour forcer la régénération...")
    cache = analyzer.cache
    cache_cleared = False
    if hasattr(cache, 'cache') and isinstance(cache.cache, dict):
        keys_to_remove = []
        for key, value in cache.cache.items():
            if isinstance(value, dict) and value.get('analysis_type') == 'style_photo':
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del cache.cache[key]
        if keys_to_remove:
            cache._save_cache()
            print(f"   ✅ {len(keys_to_remove)} entrées de cache style_photo supprimées")
            cache_cleared = True
    if not cache_cleared:
        print("   ℹ️  Aucune entrée de cache style_photo trouvée")
    print()
    
    # Statistiques
    results = {
        'total': len(apartments),
        'success': 0,
        'failed': 0,
        'no_photos': 0,
        'styles_detected': {}
    }
    
    updated_apartments = []
    
    # Analyser chaque appartement (FORCER la régénération)
    for i, apartment in enumerate(apartments, 1):
        apartment_id = apartment.get('id', 'unknown')
        
        print("\n" + "=" * 80)
        print(f"🏠 APPARTEMENT {i}/{len(apartments)}: {apartment_id}")
        print("=" * 80)
        print(f"   📍 Localisation: {apartment.get('localisation', 'N/A')}")
        print(f"   💰 Prix: {apartment.get('prix', 'N/A')}")
        
        # FORCER la régénération - supprimer l'ancienne analyse
        if apartment.get('style_analysis'):
            print(f"   🔄 Régénération forcée (ancienne analyse supprimée)")
            del apartment['style_analysis']
        
        # Vérifier les photos
        photos = apartment.get('photos', [])
        if not photos:
            print(f"   ⚠️  Aucune photo dans les données")
            results['no_photos'] += 1
            continue
        
        print(f"   📸 {len(photos)} photos disponibles")
        
        # Analyser le style avec le nouveau système
        try:
            style_analysis = analyzer.analyze_apartment_photos_from_data(apartment)
            
            if style_analysis:
                print(f"\n   ✅ Style analysé avec succès!")
                style_type = style_analysis.get('style', {}).get('type', 'inconnu')
                style_score = style_analysis.get('style', {}).get('score', 0)
                style_confidence = style_analysis.get('style', {}).get('confidence', 0)
                
                # Afficher les indices détectés avec numéros d'images
                indices_precis = style_analysis.get('style', {}).get('indices_precis', {})
                if indices_precis:
                    print(f"      📍 Indices détectés:")
                    for indice_name, indice_data in indices_precis.items():
                        if isinstance(indice_data, dict) and indice_data.get('present'):
                            image_numbers = indice_data.get('image_numbers', [])
                            if image_numbers:
                                images_str = ", ".join([f"image {n}" for n in sorted(image_numbers)])
                                print(f"         - {indice_name.replace('_', ' ').title()}: {images_str}")
                            else:
                                print(f"         - {indice_name.replace('_', ' ').title()}")
                
                print(f"      🏛️  Style: {style_type.upper()} ({style_score}/20 pts, confiance: {style_confidence:.0%})")
                
                # Ajouter style_analysis à l'appartement
                apartment['style_analysis'] = style_analysis
                
                # Sauvegarder l'appartement mis à jour
                save_apartment(apartment, apartment_id)
                
                results['success'] += 1
                results['styles_detected'][style_type] = results['styles_detected'].get(style_type, 0) + 1
                updated_apartments.append(apartment_id)
            else:
                print(f"   ❌ Aucune analyse de style retournée")
                results['failed'] += 1
        
        except Exception as e:
            print(f"   ❌ Erreur lors de l'analyse: {e}")
            import traceback
            traceback.print_exc()
            results['failed'] += 1
    
    # Résumé final
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"\n✅ Total appartements: {results['total']}")
    print(f"✅ Analyses réussis: {results['success']}")
    print(f"⚠️  Sans photos: {results['no_photos']}")
    print(f"❌ Échecs: {results['failed']}")
    
    if results['success'] > 0:
        print(f"\n📈 STYLES DÉTECTÉS:")
        for style_type, count in sorted(results['styles_detected'].items(), key=lambda x: x[1], reverse=True):
            print(f"   - {style_type}: {count}")
        
        print(f"\n💾 {len(updated_apartments)} appartements mis à jour")
        
        # Sauvegarder le résumé
        summary_file = "data/style_analysis_regeneration_results.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résumé sauvegardé dans {summary_file}")
    
    print("\n✅ Régénération terminée!")

if __name__ == "__main__":
    regenerate_all_style_analysis()

