#!/usr/bin/env python3
"""
Test du critère "hauteur sous plafond"
Teste avec 3 appartements spécifiques
"""

import json
import os
import re
from scoring import score_hauteur_plafond, load_scoring_config
from data_loader import load_apartments

def find_apartments_by_price_and_location(apartments, price_target, location_keywords):
    """Trouve les appartements correspondant au prix et à la localisation"""
    matching = []
    
    for apt in apartments:
        # Vérifier le prix
        prix_str = apt.get('prix', '')
        prix_match = re.search(r'([\d\s]+)', prix_str.replace(' ', '')) if prix_str else None
        if not prix_match:
            continue
        
        try:
            prix = int(prix_match.group(1))
            # Tolérance de ±10k pour le prix
            if abs(prix - price_target) > 10000:
                continue
        except:
            continue
        
        # Vérifier la localisation
        localisation = str(apt.get('localisation', '')).lower()
        map_info = apt.get('map_info', {}) or {}
        quartier = str(map_info.get('quartier', '')).lower()
        metros = map_info.get('metros', []) or []
        metros_str = ' '.join([str(m).lower() for m in metros if m])
        
        # Chercher les mots-clés dans la localisation
        found = False
        for keyword in location_keywords:
            keyword_lower = keyword.lower()
            if (keyword_lower in localisation or 
                keyword_lower in quartier or 
                keyword_lower in metros_str):
                found = True
                break
        
        if found:
            matching.append(apt)
    
    return matching

def test_hauteur_plafond():
    """Test le scoring de hauteur sous plafond sur 3 appartements spécifiques"""
    print("🧪 TEST CRITÈRE 'HAUTEUR SOUS PLAFOND'")
    print("=" * 60)
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger la config")
        return
    
    # Charger les appartements
    apartments = load_apartments(prefer_api=True)
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"\n📊 {len(apartments)} appartements chargés")
    
    # Appartements à tester
    test_cases = [
        {
            'prix': 770000,
            'location': ['folie', 'mericourt'],
            'name': '770k folie mericourt'
        },
        {
            'prix': 750000,
            'location': ['sainte', 'marguerite'],
            'name': '750k sainte marguerite'
        },
        {
            'prix': 799000,
            'location': ['sainte', 'marguerite'],
            'name': '799k sainte marguerite'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"🏠 TEST: {test_case['name']}")
        print(f"{'='*60}")
        
        # Trouver les appartements correspondants
        matching = find_apartments_by_price_and_location(
            apartments, 
            test_case['prix'], 
            test_case['location']
        )
        
        if not matching:
            print(f"❌ Aucun appartement trouvé pour {test_case['name']}")
            print(f"   Recherche: prix ~{test_case['prix']}€, localisation: {', '.join(test_case['location'])}")
            continue
        
        # Prendre le premier qui a des photos
        test_apartment = None
        for apt in matching:
            photos = apt.get('photos', [])
            if photos and len(photos) > 0:
                test_apartment = apt
                break
        
        if not test_apartment:
            print(f"⚠️  Aucun appartement avec photos trouvé pour {test_case['name']}")
            if matching:
                print(f"   {len(matching)} appartement(s) trouvé(s) mais sans photos")
            continue
        
        print(f"\n📋 Appartement trouvé:")
        print(f"   ID: {test_apartment.get('id')}")
        print(f"   Prix: {test_apartment.get('prix')}")
        print(f"   Localisation: {test_apartment.get('localisation')}")
        print(f"   Surface: {test_apartment.get('surface')}")
        photos = test_apartment.get('photos', [])
        print(f"   Photos: {len(photos)} disponible(s)")
        
        # Afficher les URLs des premières photos
        if photos:
            print(f"\n   📸 Premières photos:")
            for i, photo in enumerate(photos[:3]):
                if isinstance(photo, dict):
                    url = photo.get('url', '')
                else:
                    url = photo
                if url:
                    print(f"      {i+1}. {url[:80]}...")
        
        # Tester le scoring
        print(f"\n📊 Analyse de la hauteur sous plafond...")
        result = score_hauteur_plafond(test_apartment, config)
        
        print(f"\n✅ RÉSULTAT:")
        print(f"   Score: {result.get('score')}/10")
        print(f"   Tier: {result.get('tier')}")
        print(f"   Justification: {result.get('justification')}")
        
        details = result.get('details', {})
        if details:
            print(f"\n📋 DÉTAILS:")
            if 'hauteur_estimate' in details:
                print(f"   Hauteur estimée: {details['hauteur_estimate']}m")
            if 'hauteur_category' in details:
                print(f"   Catégorie: {details['hauteur_category']}")
            if 'confidence' in details:
                print(f"   Confiance: {details['confidence']:.2f}")
            
            # Détails de l'analyse
            hauteur_analysis = details.get('hauteur_analysis', {})
            if hauteur_analysis:
                print(f"\n   📸 Analyse des photos:")
                print(f"      Photos analysées: {hauteur_analysis.get('photos_analyzed', 0)}")
                analysis_details = hauteur_analysis.get('details', {})
                if 'hauteurs' in analysis_details:
                    hauteurs = analysis_details['hauteurs']
                    print(f"      Hauteurs détectées: {hauteurs}")
                    print(f"      Min: {analysis_details.get('min_hauteur', 'N/A')}m")
                    print(f"      Max: {analysis_details.get('max_hauteur', 'N/A')}m")
                    print(f"      Moyenne: {details.get('hauteur_estimate', 'N/A')}m")
    
    print(f"\n{'='*60}")
    print(f"✅ Tests terminés!")

if __name__ == "__main__":
    test_hauteur_plafond()



