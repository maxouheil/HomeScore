#!/usr/bin/env python3
"""
Script pour analyser le vis-à-vis de tous les appartements
Utilise l'analyse d'image pour déterminer la distance du vis-à-vis depuis les fenêtres
"""

import json
import os
from pathlib import Path
from datetime import datetime
from data_loader import load_apartments
from analyze_photos import PhotoAnalyzer

def analyze_visavis_all_apartments():
    """Analyse le vis-à-vis pour tous les appartements"""
    print("🏠 ANALYSE DU VIS-À-VIS POUR TOUS LES APPARTEMENTS")
    print("=" * 70)
    
    # Charger tous les appartements
    apartments = load_apartments(prefer_api=True)
    
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"📋 {len(apartments)} appartements à analyser\n")
    
    # Initialiser l'analyseur
    photo_analyzer = PhotoAnalyzer()
    
    # Statistiques
    stats = {
        'total': len(apartments),
        'analyzed': 0,
        'skipped': 0,
        'errors': 0,
        'results': {
            'good': 0,
            'moyen': 0,
            'bad': 0,
            'none': 0
        }
    }
    
    # Résultats détaillés
    results = []
    
    # Analyser chaque appartement
    for i, apartment in enumerate(apartments, 1):
        apartment_id = apartment.get('id', 'unknown')
        print(f"\n🏠 Appartement {i}/{len(apartments)}: {apartment_id}")
        print(f"   📍 {apartment.get('localisation', 'N/A')}")
        
        # Extraire les URLs des photos
        photos = apartment.get('photos', [])
        if not photos:
            print(f"   ⏭️  Aucune photo disponible")
            stats['skipped'] += 1
            results.append({
                'id': apartment_id,
                'visavis': None,
                'status': 'no_photos'
            })
            continue
        
        # Extraire les URLs
        photo_urls = []
        for photo in photos:
            if isinstance(photo, dict):
                url = photo.get('url')
            else:
                url = photo
            if url:
                photo_urls.append(url)
        
        if not photo_urls:
            print(f"   ⏭️  Aucune URL de photo valide")
            stats['skipped'] += 1
            results.append({
                'id': apartment_id,
                'visavis': None,
                'status': 'no_valid_photos'
            })
            continue
        
        print(f"   📸 {len(photo_urls)} photos disponibles")
        
        # Analyser le vis-à-vis
        try:
            visavis_result = photo_analyzer.analyze_photos_visavis(photo_urls)
            
            visavis_value = visavis_result.get('visavis')
            confidence = visavis_result.get('confidence', 0.0)
            justification = visavis_result.get('justification', '')
            
            print(f"   ✅ Vis-à-vis: {visavis_value} (confiance: {confidence:.0%})")
            print(f"   📝 {justification}")
            
            # Mettre à jour les statistiques
            stats['analyzed'] += 1
            if visavis_value:
                stats['results'][visavis_value] = stats['results'].get(visavis_value, 0) + 1
            else:
                stats['results']['none'] += 1
            
            # Sauvegarder le résultat dans l'appartement
            # Mettre à jour l'objet exposition si existant
            if 'exposition' not in apartment:
                apartment['exposition'] = {}
            
            if 'details' not in apartment['exposition']:
                apartment['exposition']['details'] = {}
            
            apartment['exposition']['details']['visavis'] = visavis_value
            apartment['exposition']['details']['visavis_confidence'] = confidence
            apartment['exposition']['details']['visavis_justification'] = justification
            apartment['exposition']['details']['visavis_analysis_date'] = datetime.now().isoformat()
            
            # Ajouter les détails complets
            apartment['exposition']['details']['visavis_details'] = visavis_result.get('details', {})
            
            results.append({
                'id': apartment_id,
                'visavis': visavis_value,
                'confidence': confidence,
                'justification': justification,
                'status': 'success',
                'photos_analyzed': visavis_result.get('photos_analyzed', 0)
            })
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            stats['errors'] += 1
            results.append({
                'id': apartment_id,
                'visavis': None,
                'status': 'error',
                'error': str(e)
            })
    
    # Sauvegarder les résultats mis à jour
    print(f"\n💾 Sauvegarde des résultats...")
    
    # Déterminer le fichier source
    data_dir = Path('data')
    api_files = sorted(
        data_dir.glob('scraped_apartments_api_*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if api_files:
        output_file = api_files[0]  # Mettre à jour le fichier existant
        print(f"   📁 Fichier: {output_file.name}")
    else:
        # Créer un nouveau fichier avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = data_dir / f'scraped_apartments_api_{timestamp}.json'
        print(f"   📁 Nouveau fichier: {output_file.name}")
    
    # Sauvegarder
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Données sauvegardées")
    
    # Sauvegarder le récapitulatif
    recap_file = data_dir / 'visavis_analysis_recap.json'
    recap_data = {
        'analysis_date': datetime.now().isoformat(),
        'stats': stats,
        'results': results
    }
    
    with open(recap_file, 'w', encoding='utf-8') as f:
        json.dump(recap_data, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Récapitulatif sauvegardé: {recap_file.name}")
    
    # Afficher le récapitulatif
    print(f"\n📊 RÉCAPITULATIF DE L'ANALYSE")
    print("=" * 70)
    print(f"Total: {stats['total']} appartements")
    print(f"Analysés: {stats['analyzed']}")
    print(f"Passés: {stats['skipped']}")
    print(f"Erreurs: {stats['errors']}")
    print(f"\nRésultats vis-à-vis:")
    print(f"  ✅ Good: {stats['results']['good']}")
    print(f"  ⚠️  Moyen: {stats['results']['moyen']}")
    print(f"  ❌ Bad: {stats['results']['bad']}")
    print(f"  ❓ Non déterminé: {stats['results']['none']}")
    
    return recap_data

if __name__ == "__main__":
    analyze_visavis_all_apartments()

