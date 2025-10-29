#!/usr/bin/env python3
"""
Test complet du système d'extraction d'exposition
Phase 1: Analyse textuelle
Phase 2: Analyse des photos (simulée)
"""

import json
from extract_exposition import ExpositionExtractor

def test_exposition_system():
    """Test complet du système d'exposition"""
    extractor = ExpositionExtractor()
    
    print("🧭 TEST COMPLET DU SYSTÈME D'EXPOSITION")
    print("=" * 60)
    
    # Cas de test avec différentes descriptions
    test_cases = [
        {
            'name': 'Appartement Sud parfait',
            'description': 'Magnifique appartement très lumineux avec exposition Sud, vue dégagée sur le parc, pas de vis-à-vis',
            'caracteristiques': 'Balcon, terrasse, hauteur sous plafond 3.20m',
            'photos': ['https://example.com/photo1.jpg', 'https://example.com/photo2.jpg']
        },
        {
            'name': 'Duplex Ouest correct',
            'description': 'Duplex avec orientation Ouest, bien éclairé, vue semi-dégagée',
            'caracteristiques': 'Ascenseur, parking',
            'photos': ['https://example.com/photo1.jpg']
        },
        {
            'name': 'Appartement Nord problématique',
            'description': 'Appartement au 4e étage, exposition Nord, vis-à-vis',
            'caracteristiques': 'Ascenseur, cave',
            'photos': []
        },
        {
            'name': 'Appartement sans exposition spécifiée',
            'description': 'Magnifique appartement haussmannien rénové, très lumineux',
            'caracteristiques': 'Parking, cave, balcon',
            'photos': ['https://example.com/photo1.jpg']
        },
        {
            'name': 'Appartement Sud-Ouest excellent',
            'description': 'Appartement exceptionnel avec exposition Sud-Ouest, très lumineux toute la journée, vue panoramique',
            'caracteristiques': 'Terrasse, balcon, hauteur sous plafond 3.50m',
            'photos': ['https://example.com/photo1.jpg', 'https://example.com/photo2.jpg', 'https://example.com/photo3.jpg']
        }
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   Description: {case['description']}")
        print(f"   Caractéristiques: {case['caracteristiques']}")
        print(f"   Photos: {len(case['photos'])}")
        
        # Test Phase 1: Analyse textuelle uniquement
        text_result = extractor.extract_exposition_textuelle(
            case['description'], 
            case['caracteristiques']
        )
        
        # Test Phase 2: Analyse complète (textuelle + photos)
        complete_result = extractor.extract_exposition_complete(
            case['description'], 
            case['caracteristiques'], 
            case['photos']
        )
        
        print(f"   📝 Phase 1 (Texte):")
        print(f"      Exposition: {text_result['exposition']}")
        print(f"      Score: {text_result['score']}/10")
        print(f"      Tier: {text_result['tier']}")
        print(f"      Luminosité: {text_result['luminosite']}")
        print(f"      Vue: {text_result['vue']}")
        
        print(f"   🔄 Phase 1+2 (Complet):")
        print(f"      Exposition: {complete_result['exposition']}")
        print(f"      Score: {complete_result['score']}/10")
        print(f"      Tier: {complete_result['tier']}")
        print(f"      Photos analysées: {complete_result.get('photos_analyzed', 0)}")
        print(f"      Justification: {complete_result['justification']}")
        
        results.append({
            'case': case['name'],
            'text_result': text_result,
            'complete_result': complete_result
        })
    
    # Résumé des résultats
    print(f"\n📊 RÉSUMÉ DES RÉSULTATS")
    print("=" * 60)
    
    tier1_count = sum(1 for r in results if r['complete_result']['tier'] == 'tier1')
    tier2_count = sum(1 for r in results if r['complete_result']['tier'] == 'tier2')
    tier3_count = sum(1 for r in results if r['complete_result']['tier'] == 'tier3')
    
    print(f"Tier 1 (Excellent): {tier1_count}/{len(results)}")
    print(f"Tier 2 (Bon): {tier2_count}/{len(results)}")
    print(f"Tier 3 (Moyen/Problématique): {tier3_count}/{len(results)}")
    
    # Score moyen
    avg_score = sum(r['complete_result']['score'] for r in results) / len(results)
    print(f"Score moyen: {avg_score:.1f}/10")
    
    # Expositions détectées
    expositions = [r['complete_result']['exposition'] for r in results if r['complete_result']['exposition']]
    if expositions:
        print(f"Expositions détectées: {', '.join(set(expositions))}")
    else:
        print("Aucune exposition spécifique détectée")
    
    return results

def test_scoring_integration():
    """Test de l'intégration avec le système de scoring"""
    print(f"\n🎯 TEST D'INTÉGRATION AVEC LE SCORING")
    print("=" * 60)
    
    # Charger la configuration de scoring
    try:
        with open('scoring_config.json', 'r') as f:
            scoring_config = json.load(f)
        
        # Trouver l'axe Ensoleillement
        ensoleillement_axe = None
        for axe in scoring_config['axes']:
            if axe['nom'] == 'Ensoleillement':
                ensoleillement_axe = axe
                break
        
        if ensoleillement_axe:
            print("✅ Configuration de scoring trouvée")
            print(f"   Axe: {ensoleillement_axe['nom']}")
            print(f"   Poids: {ensoleillement_axe['poids']} points")
            print("   Tiers:")
            for tier, details in ensoleillement_axe['tiers'].items():
                print(f"      {tier}: {details['score']} pts - {details['description']}")
        else:
            print("❌ Axe Ensoleillement non trouvé dans la configuration")
            
    except FileNotFoundError:
        print("❌ Fichier scoring_config.json non trouvé")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")

if __name__ == "__main__":
    # Test du système d'exposition
    results = test_exposition_system()
    
    # Test d'intégration avec le scoring
    test_scoring_integration()
    
    print(f"\n✅ Tests terminés avec succès!")
