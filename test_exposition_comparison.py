#!/usr/bin/env python3
"""
Test de comparaison des différentes méthodes d'extraction d'exposition
Phase 1: Textuelle
Phase 2: Photos
Phase 3: Contextuelle
Phase 1+2+3: Ultimate
"""

import json
from extract_exposition import ExpositionExtractor

def test_exposition_methods():
    """Test de comparaison des méthodes d'exposition"""
    print("🧭 COMPARAISON DES MÉTHODES D'EXTRACTION D'EXPOSITION")
    print("=" * 70)
    
    # Charger les données de l'appartement test
    try:
        with open('data/appartements/90931157.json', 'r') as f:
            apartment_data = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier de données non trouvé")
        return
    
    extractor = ExpositionExtractor()
    
    # Extraire les données nécessaires
    description = apartment_data.get('description', '')
    caracteristiques = apartment_data.get('caracteristiques', '')
    photos = apartment_data.get('photos', [])
    
    print("📋 DONNÉES DE L'APPARTEMENT:")
    print(f"   ID: {apartment_data.get('id', 'N/A')}")
    print(f"   Prix: {apartment_data.get('prix', 'N/A')}€")
    print(f"   Surface: {apartment_data.get('surface', 'N/A')}")
    print(f"   Localisation: {apartment_data.get('localisation', 'N/A')}")
    print()
    
    # Phase 1: Analyse textuelle
    print("📝 PHASE 1 - ANALYSE TEXTUELLE:")
    print("-" * 40)
    text_result = extractor.extract_exposition_textuelle(description, caracteristiques)
    print(f"   Exposition: {text_result['exposition'] or 'Non spécifiée'}")
    print(f"   Score: {text_result['score']}/10")
    print(f"   Tier: {text_result['tier']}")
    print(f"   Luminosité: {text_result['luminosite']}")
    print(f"   Vue: {text_result['vue']}")
    print(f"   Justification: {text_result['justification']}")
    print()
    
    # Phase 2: Analyse des photos
    print("📸 PHASE 2 - ANALYSE DES PHOTOS:")
    print("-" * 40)
    photo_result = extractor.extract_exposition_photos(photos)
    print(f"   Exposition: {photo_result['exposition'] or 'Non spécifiée'}")
    print(f"   Score: {photo_result['score']}/10")
    print(f"   Tier: {photo_result['tier']}")
    print(f"   Photos analysées: {photo_result.get('photos_analyzed', 0)}")
    print(f"   Justification: {photo_result['justification']}")
    print()
    
    # Phase 3: Analyse contextuelle
    print("🏘️ PHASE 3 - ANALYSE CONTEXTUELLE:")
    print("-" * 40)
    contextual_result = extractor.extract_exposition_contextual(apartment_data)
    print(f"   Exposition: {contextual_result['exposition'] or 'Non spécifiée'}")
    print(f"   Score: {contextual_result['score']}/10")
    print(f"   Tier: {contextual_result['tier']}")
    print(f"   Confiance: {contextual_result.get('confidence', 0):.2f}")
    print(f"   Justification: {contextual_result['justification']}")
    print()
    
    # Phase 1+2+3: Analyse ultimate
    print("🚀 PHASE 1+2+3 - ANALYSE ULTIMATE:")
    print("-" * 40)
    ultimate_result = extractor.extract_exposition_ultimate(apartment_data)
    print(f"   Exposition: {ultimate_result['exposition'] or 'Non spécifiée'}")
    print(f"   Score: {ultimate_result['score']}/10")
    print(f"   Tier: {ultimate_result['tier']}")
    print(f"   Justification: {ultimate_result['justification']}")
    print()
    
    # Comparaison des résultats
    print("📊 COMPARAISON DES RÉSULTATS:")
    print("-" * 40)
    methods = [
        ("Textuelle", text_result),
        ("Photos", photo_result),
        ("Contextuelle", contextual_result),
        ("Ultimate", ultimate_result)
    ]
    
    print(f"{'Méthode':<15} {'Exposition':<12} {'Score':<8} {'Tier':<8} {'Confiance':<10}")
    print("-" * 60)
    
    for method_name, result in methods:
        exposition = result.get('exposition', 'N/A') or 'N/A'
        score = result.get('score', 0)
        tier = result.get('tier', 'N/A')
        confidence = result.get('confidence', 0) or 0
        
        print(f"{method_name:<15} {exposition:<12} {score:<8} {tier:<8} {confidence:<10.2f}")
    
    print()
    
    # Recommandation finale
    print("🎯 RECOMMANDATION FINALE:")
    print("-" * 40)
    
    final_exposition = ultimate_result['exposition']
    final_score = ultimate_result['score']
    final_tier = ultimate_result['tier']
    
    if final_tier == 'tier1':
        recommendation = "🌟 EXCELLENT - Candidat prioritaire"
        points_attribues = 10
    elif final_tier == 'tier2':
        recommendation = "👍 BON POTENTIEL"
        points_attribues = 7
    else:
        recommendation = "⚠️ À RECONSIDÉRER"
        points_attribues = 3
    
    print(f"   Exposition finale: {final_exposition}")
    print(f"   Score final: {final_score}/10")
    print(f"   Tier final: {final_tier}")
    print(f"   Points attribués: {points_attribues}/10")
    print(f"   {recommendation}")
    print()
    
    # Analyse des détails contextuels
    if 'details' in ultimate_result:
        print("🔍 DÉTAILS DE L'ANALYSE CONTEXTUELLE:")
        print("-" * 40)
        details = ultimate_result['details']
        
        if 'quartier' in details:
            quartier = details['quartier']
            print(f"   Quartier: {quartier.get('quartier', 'N/A')}")
            print(f"   Orientation typique: {quartier.get('orientation_typique', 'N/A')}")
            print(f"   Score quartier: {quartier.get('score', 0)}")
        
        if 'architectural' in details:
            arch = details['architectural']
            print(f"   Indices architecturaux: {arch.get('count', 0)}")
            print(f"   Score architectural: {arch.get('total_score', 0)}")
        
        if 'etage' in details:
            etage = details['etage']
            print(f"   Étage: {etage.get('etage', 'N/A')}")
            print(f"   Score étage: {etage.get('score_bonus', 0)}")
        
        if 'luminosite' in details:
            lum = details['luminosite']
            print(f"   Indices luminosité: {lum.get('count', 0)}")
            print(f"   Score luminosité: {lum.get('total_score', 0)}")
    
    print()
    print("✅ Test de comparaison terminé !")

if __name__ == "__main__":
    test_exposition_methods()
