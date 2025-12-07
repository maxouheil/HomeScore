#!/usr/bin/env python3
"""
Test spécifique de l'exposition avec l'appartement test
Analyse détaillée des données extraites
"""

import json
from extract_exposition import ExpositionExtractor

def test_appartement_exposition():
    """Test de l'exposition avec l'appartement test"""
    print("🏠 TEST D'EXPOSITION - APPARTEMENT TEST")
    print("=" * 60)
    
    # Charger les données de l'appartement test
    try:
        with open('data/appartements/90931157.json', 'r') as f:
            apartment_data = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier de données non trouvé. Lancez d'abord le scraper.")
        return
    
    print(f"📋 DONNÉES DE L'APPARTEMENT:")
    print(f"   ID: {apartment_data.get('id', 'N/A')}")
    print(f"   Titre: {apartment_data.get('titre', 'N/A')}")
    print(f"   Prix: {apartment_data.get('prix', 'N/A')}€")
    print(f"   Surface: {apartment_data.get('surface', 'N/A')}")
    print(f"   Localisation: {apartment_data.get('localisation', 'N/A')}")
    print()
    
    # Analyser l'exposition
    description = apartment_data.get('description', '')
    caracteristiques = apartment_data.get('caracteristiques', '')
    photos = apartment_data.get('photos', [])
    
    print(f"📝 DESCRIPTION:")
    print(f"   {description[:200]}...")
    print()
    
    print(f"🏗️ CARACTÉRISTIQUES:")
    print(f"   {caracteristiques}")
    print()
    
    print(f"📸 PHOTOS:")
    print(f"   Nombre: {len(photos)}")
    if photos:
        print(f"   Première: {photos[0][:80]}...")
    print()
    
    # Test avec l'extracteur d'exposition
    extractor = ExpositionExtractor()
    
    print("🧭 ANALYSE D'EXPOSITION DÉTAILLÉE:")
    print("-" * 40)
    
    # Phase 1: Analyse textuelle
    print("📝 Phase 1 - Analyse textuelle:")
    text_result = extractor.extract_exposition_textuelle(description, caracteristiques)
    print(f"   Exposition: {text_result['exposition'] or 'Non spécifiée'}")
    print(f"   Score: {text_result['score']}/10")
    print(f"   Tier: {text_result['tier']}")
    print(f"   Luminosité: {text_result['luminosite']}")
    print(f"   Vue: {text_result['vue']}")
    print(f"   Justification: {text_result['justification']}")
    print()
    
    # Phase 2: Analyse complète (textuelle + photos)
    print("🔄 Phase 1+2 - Analyse complète:")
    complete_result = extractor.extract_exposition_complete(description, caracteristiques, photos)
    print(f"   Exposition: {complete_result['exposition'] or 'Non spécifiée'}")
    print(f"   Score: {complete_result['score']}/10")
    print(f"   Tier: {complete_result['tier']}")
    print(f"   Luminosité: {complete_result['luminosite']}")
    print(f"   Vue: {complete_result['vue']}")
    print(f"   Photos analysées: {complete_result.get('photos_analyzed', 0)}")
    print(f"   Justification: {complete_result['justification']}")
    print()
    
    # Analyse des détails
    print("📊 DÉTAILS DE L'ANALYSE:")
    details = complete_result.get('details', {})
    for key, value in details.items():
        print(f"   {key}: {value}")
    print()
    
    # Score pour le système de scoring
    print("🎯 INTÉGRATION AVEC LE SCORING:")
    ensoleillement_score = complete_result['score']
    ensoleillement_tier = complete_result['tier']
    
    print(f"   Score Ensoleillement: {ensoleillement_score}/10")
    print(f"   Tier: {ensoleillement_tier}")
    
    if ensoleillement_tier == 'tier1':
        points_attribues = 10
        emoji = "🌟"
        status = "Excellent - Candidat prioritaire"
    elif ensoleillement_tier == 'tier2':
        points_attribues = 7
        emoji = "👍"
        status = "Bon potentiel"
    else:
        points_attribues = 3
        emoji = "⚠️"
        status = "À reconsidérer"
    
    print(f"   Points attribués: {points_attribues}/10")
    print(f"   {emoji} {status}")
    print()
    
    # Analyse des mots-clés détectés
    print("🔍 ANALYSE DES MOTS-CLÉS DÉTECTÉS:")
    text_combined = f"{description} {caracteristiques}".lower()
    
    # Mots-clés d'exposition
    exposition_keywords = ['sud', 'nord', 'est', 'ouest', 'exposition', 'orientation']
    found_exposition = [kw for kw in exposition_keywords if kw in text_combined]
    print(f"   Exposition: {found_exposition if found_exposition else 'Aucun'}")
    
    # Mots-clés de luminosité
    luminosite_keywords = ['lumineux', 'clair', 'ensoleillé', 'luminosité', 'éclairé']
    found_luminosite = [kw for kw in luminosite_keywords if kw in text_combined]
    print(f"   Luminosité: {found_luminosite if found_luminosite else 'Aucun'}")
    
    # Mots-clés de vue
    vue_keywords = ['vue', 'dégagée', 'panoramique', 'vis-à-vis', 'obstruée']
    found_vue = [kw for kw in vue_keywords if kw in text_combined]
    print(f"   Vue: {found_vue if found_vue else 'Aucun'}")
    
    print()
    
    # Recommandations
    print("💡 RECOMMANDATIONS:")
    if not complete_result['exposition']:
        print("   ⚠️ Aucune exposition spécifiée - difficile à évaluer")
        print("   💡 Suggérer d'ajouter l'exposition dans la description")
    
    if complete_result['luminosite'] == 'inconnue':
        print("   ⚠️ Luminosité non spécifiée")
        print("   💡 Analyser les photos pour déterminer la luminosité")
    
    if complete_result['vue'] == 'inconnue':
        print("   ⚠️ Qualité de vue non spécifiée")
        print("   💡 Analyser les photos pour évaluer la vue")
    
    if complete_result.get('photos_analyzed', 0) == 0:
        print("   ⚠️ Aucune photo analysée")
        print("   💡 Configurer la clé API OpenAI pour l'analyse des photos")
    
    print()
    print("✅ Test terminé !")

if __name__ == "__main__":
    test_appartement_exposition()
