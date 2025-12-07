#!/usr/bin/env python3
"""
Analyse le style de TOUS les appartements scrapés
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
    
    # Source 2: data/appartements/*.json (pour éviter les doublons)
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
    
    return apartment_file

def analyze_all_apartments_style():
    """Analyse le style de tous les appartements"""
    print("=" * 80)
    print("🎨 ANALYSE DE STYLE - TOUS LES APPARTEMENTS")
    print("=" * 80)
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
    
    # Statistiques
    results = {
        'total': len(apartments),
        'success': 0,
        'failed': 0,
        'already_has_style': 0,
        'no_photos': 0,
        'styles_detected': {}
    }
    
    updated_apartments = []
    
    # Analyser chaque appartement
    for i, apartment in enumerate(apartments, 1):
        apartment_id = apartment.get('id', 'unknown')
        
        print("\n" + "=" * 80)
        print(f"🏠 APPARTEMENT {i}/{len(apartments)}: {apartment_id}")
        print("=" * 80)
        print(f"   📍 Localisation: {apartment.get('localisation', 'N/A')}")
        print(f"   💰 Prix: {apartment.get('prix', 'N/A')}")
        
        # Vérifier si style_analysis existe déjà
        if apartment.get('style_analysis'):
            print(f"   ⏭️  Style déjà analysé (skippé)")
            results['already_has_style'] += 1
            continue
        
        # Vérifier les photos
        photos = apartment.get('photos', [])
        if not photos:
            print(f"   ⚠️  Aucune photo dans les données")
            results['no_photos'] += 1
            continue
        
        # Vérifier les photos locales
        photos_dir_v2 = f"data/photos/{apartment_id}"
        photos_dir = f"data/photos/{apartment_id}"
        has_local_photos = os.path.exists(photos_dir_v2) or os.path.exists(photos_dir)
        
        if has_local_photos:
            print(f"   ✅ Photos locales disponibles")
        else:
            print(f"   📸 {len(photos)} photos dans les données (téléchargement si nécessaire)")
        
        # Analyser le style
        try:
            style_analysis = analyzer.analyze_apartment_photos_from_data(apartment)
            
            if style_analysis:
                print(f"\n   ✅ Style analysé avec succès!")
                style_type = style_analysis.get('style', {}).get('type', 'inconnu')
                style_score = style_analysis.get('style', {}).get('score', 0)
                print(f"      🏛️  Style: {style_type.upper()} ({style_score}/20 pts)")
                
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
    print(f"✅ Nouveaux analyses réussis: {results['success']}")
    print(f"⏭️  Déjà analysés (skippés): {results['already_has_style']}")
    print(f"⚠️  Sans photos: {results['no_photos']}")
    print(f"❌ Échecs: {results['failed']}")
    
    if results['success'] > 0:
        print(f"\n📈 STYLES DÉTECTÉS:")
        for style_type, count in sorted(results['styles_detected'].items(), key=lambda x: x[1], reverse=True):
            print(f"   - {style_type}: {count}")
        
        print(f"\n💾 {len(updated_apartments)} appartements mis à jour:")
        for apt_id in updated_apartments:
            print(f"   - {apt_id}")
        
        # Sauvegarder le résumé
        summary_file = "data/style_analysis_all_results.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résumé sauvegardé dans {summary_file}")
    
    print("\n✅ Analyse terminée!")

if __name__ == "__main__":
    analyze_all_apartments_style()

