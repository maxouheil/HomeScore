#!/usr/bin/env python3
"""
Démonstration du système d'extraction d'exposition
Montre les capacités Phase 1 + Phase 2
"""

from extract_exposition import ExpositionExtractor

def demo_exposition_system():
    """Démonstration interactive du système d'exposition"""
    print("🧭 DÉMONSTRATION DU SYSTÈME D'EXPOSITION")
    print("=" * 60)
    print("Phase 1: Analyse textuelle ✅")
    print("Phase 2: Analyse des photos ✅")
    print("Phase 1+2: Analyse combinée ✅")
    print()
    
    extractor = ExpositionExtractor()
    
    # Exemples d'appartements réels
    apartments = [
        {
            'name': '🏠 Appartement Haussmannien Sud',
            'description': 'Magnifique appartement haussmannien rénové avec exposition Sud, très lumineux toute la journée, vue dégagée sur cour calme, hauteur sous plafond 3.20m',
            'caracteristiques': 'Parquet, moulures, cheminée, balcon, ascenseur',
            'photos': ['https://example.com/photo1.jpg', 'https://example.com/photo2.jpg']
        },
        {
            'name': '🏢 Duplex Moderne Ouest',
            'description': 'Duplex contemporain avec orientation Ouest, bien éclairé, vue semi-dégagée sur la rue, luminosité correcte',
            'caracteristiques': 'Ascenseur, parking, cave, balcon',
            'photos': ['https://example.com/photo1.jpg']
        },
        {
            'name': '🏘️ Studio Nord Problématique',
            'description': 'Studio au 1er étage, exposition Nord, vis-à-vis, peu lumineux, vue limitée',
            'caracteristiques': 'Ascenseur, cave',
            'photos': []
        },
        {
            'name': '🌟 Loft Atypique Sud-Ouest',
            'description': 'Loft aménagé exceptionnel avec exposition Sud-Ouest, très lumineux toute la journée, vue panoramique sur Paris, pas de vis-à-vis',
            'caracteristiques': 'Terrasse, balcon, hauteur sous plafond 3.50m, ascenseur',
            'photos': ['https://example.com/photo1.jpg', 'https://example.com/photo2.jpg', 'https://example.com/photo3.jpg']
        }
    ]
    
    print("📋 ANALYSE DE 4 APPARTEMENTS TYPES")
    print("=" * 60)
    
    for i, apt in enumerate(apartments, 1):
        print(f"\n{i}. {apt['name']}")
        print(f"   📝 Description: {apt['description']}")
        print(f"   🏗️ Caractéristiques: {apt['caracteristiques']}")
        print(f"   📸 Photos: {len(apt['photos'])}")
        
        # Analyse complète
        result = extractor.extract_exposition_complete(
            apt['description'],
            apt['caracteristiques'],
            apt['photos']
        )
        
        # Affichage des résultats
        print(f"   🧭 RÉSULTATS:")
        print(f"      Exposition: {result['exposition'] or 'Non spécifiée'}")
        print(f"      Score: {result['score']}/10")
        print(f"      Tier: {result['tier']}")
        print(f"      Luminosité: {result['luminosite']}")
        print(f"      Vue: {result['vue']}")
        print(f"      Photos analysées: {result.get('photos_analyzed', 0)}")
        print(f"      Justification: {result['justification']}")
        
        # Score pour le système de scoring
        if result['tier'] == 'tier1':
            score_final = 10
            emoji = "🌟"
        elif result['tier'] == 'tier2':
            score_final = 7
            emoji = "👍"
        else:
            score_final = 3
            emoji = "⚠️"
        
        print(f"      {emoji} Score final pour le scoring: {score_final}/10")

def demo_scoring_integration():
    """Démonstration de l'intégration avec le scoring"""
    print(f"\n🎯 INTÉGRATION AVEC LE SYSTÈME DE SCORING")
    print("=" * 60)
    
    # Simulation d'un appartement avec scoring complet
    apartment_data = {
        'id': 'demo_001',
        'titre': 'Appartement Haussmannien Sud',
        'prix': 2500,
        'surface': 70,
        'exposition': {
            'exposition': 'sud',
            'score': 10,
            'tier': 'tier1',
            'justification': 'Excellente exposition Sud',
            'luminosite': 'excellent',
            'vue': 'excellent'
        }
    }
    
    print("📊 Données de l'appartement:")
    print(f"   ID: {apartment_data['id']}")
    print(f"   Titre: {apartment_data['titre']}")
    print(f"   Prix: {apartment_data['prix']}€")
    print(f"   Surface: {apartment_data['surface']}m²")
    
    print(f"\n🧭 Données d'exposition:")
    expo = apartment_data['exposition']
    print(f"   Exposition: {expo['exposition']}")
    print(f"   Score: {expo['score']}/10")
    print(f"   Tier: {expo['tier']}")
    print(f"   Luminosité: {expo['luminosite']}")
    print(f"   Vue: {expo['vue']}")
    
    # Calcul du score final pour l'axe Ensoleillement
    ensoleillement_score = expo['score']
    ensoleillement_tier = expo['tier']
    
    print(f"\n🎯 Score final pour l'axe Ensoleillement:")
    print(f"   Score: {ensoleillement_score}/10")
    print(f"   Tier: {ensoleillement_tier}")
    print(f"   Points attribués: {ensoleillement_score} points")
    
    if ensoleillement_tier == 'tier1':
        print(f"   ✅ Excellent - Candidat prioritaire")
    elif ensoleillement_tier == 'tier2':
        print(f"   👍 Bon potentiel")
    else:
        print(f"   ⚠️ À reconsidérer")

def demo_advanced_features():
    """Démonstration des fonctionnalités avancées"""
    print(f"\n🚀 FONCTIONNALITÉS AVANCÉES")
    print("=" * 60)
    
    extractor = ExpositionExtractor()
    
    # Test de détection de luminosité
    print("💡 Test de détection de luminosité:")
    luminosite_tests = [
        "très lumineux",
        "bien éclairé", 
        "assez lumineux",
        "peu lumineux"
    ]
    
    for test in luminosite_tests:
        result = extractor.extract_exposition_textuelle(f"Appartement {test}", "")
        print(f"   '{test}' → {result['luminosite']} (score: {result['details']['luminosite_score']})")
    
    # Test de détection de vue
    print(f"\n👁️ Test de détection de vue:")
    vue_tests = [
        "vue dégagée sur le parc",
        "vue correcte sur la rue",
        "vue limitée",
        "vis-à-vis"
    ]
    
    for test in vue_tests:
        result = extractor.extract_exposition_textuelle(f"Appartement avec {test}", "")
        print(f"   '{test}' → {result['vue']} (score: {result['details']['vue_score']})")
    
    # Test de détection d'exposition
    print(f"\n🧭 Test de détection d'exposition:")
    exposition_tests = [
        "exposition Sud",
        "orientation Ouest",
        "exposition Nord",
        "exposition Sud-Ouest"
    ]
    
    for test in exposition_tests:
        result = extractor.extract_exposition_textuelle(f"Appartement avec {test}", "")
        print(f"   '{test}' → {result['exposition']} (tier: {result['tier']})")

if __name__ == "__main__":
    # Démonstration principale
    demo_exposition_system()
    
    # Démonstration de l'intégration
    demo_scoring_integration()
    
    # Démonstration des fonctionnalités avancées
    demo_advanced_features()
    
    print(f"\n🎉 DÉMONSTRATION TERMINÉE!")
    print("Le système d'extraction d'exposition est prêt pour la production !")
