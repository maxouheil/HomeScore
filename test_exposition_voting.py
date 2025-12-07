#!/usr/bin/env python3
"""
Test de la nouvelle méthode extract_exposition_voting sur 3 appartements
"""

import json
import os
from extract_exposition import ExpositionExtractor

def test_voting_method():
    """Test la méthode extract_exposition_voting sur 3 appartements"""
    
    extractor = ExpositionExtractor()
    
    # Liste des 3 appartements à tester
    apartment_ids = ['90129925', '90931157', '89473319']
    
    print("🧭 TEST MÉTHODE EXTRACTION EXPOSITION VOTING")
    print("=" * 80)
    print()
    
    for apt_id in apartment_ids:
        file_path = f"data/appartements/{apt_id}.json"
        
        if not os.path.exists(file_path):
            print(f"❌ Fichier non trouvé: {file_path}")
            continue
        
        # Charger les données
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"🏠 APPARTEMENT {apt_id}")
        print("-" * 80)
        print(f"   Titre: {data.get('titre', 'N/A')}")
        print(f"   Description: {data.get('description', '')[:100]}...")
        print(f"   Caractéristiques: {data.get('caracteristiques', 'N/A')}")
        
        # Extraire étage depuis caractéristiques
        etage = ""
        if 'caracteristiques' in data:
            etage_match = data['caracteristiques'].split('Étage')[-1].strip() if 'Étage' in data['caracteristiques'] else ""
            etage = etage_match
        
        # Extraire les URLs des photos
        photos_urls = []
        if 'photos' in data:
            for photo in data['photos']:
                if isinstance(photo, dict):
                    photos_urls.append(photo.get('url'))
                elif isinstance(photo, str):
                    photos_urls.append(photo)
        
        print(f"   Nombre de photos: {len(photos_urls)}")
        print()
        
        # Appeler la nouvelle méthode
        print("📊 RÉSULTAT MÉTHODE VOTING:")
        print()
        
        result = extractor.extract_exposition_voting(
            description=data.get('description', ''),
            caracteristiques=data.get('caracteristiques', ''),
            etage=etage,
            photos_urls=photos_urls[:5] if photos_urls else None
        )
        
        # Afficher les résultats
        print(f"   Classe finale: {result.get('details', {}).get('final_class', 'N/A')}")
        print(f"   Score: {result.get('score', 'N/A')} points")
        print(f"   Tier: {result.get('tier', 'N/A')}")
        print(f"   Confiance: {result.get('confidence', 'N/A')}%")
        print(f"   Exposition: {result.get('exposition', 'N/A')}")
        print(f"   Luminosité: {result.get('luminosite', 'N/A')}")
        print()
        
        # Afficher les signaux
        signals = result.get('details', {}).get('signals', [])
        print("   📡 Signaux détectés:")
        for signal in signals:
            print(f"      • {signal.get('name', 'N/A')}: {signal.get('class', 'N/A')}")
        
        if not signals:
            print("      (Aucun signal)")
        
        print()
        
        # Afficher détails image
        details = result.get('details', {})
        if details.get('image_brightness') is not None:
            print(f"   📸 Image:")
            print(f"      • Brightness: {details.get('image_brightness', 'N/A'):.3f}")
            print(f"      • Intensité: {details.get('image_intensity', 'N/A')}")
        
        if details.get('etage_num') is not None:
            print(f"   🏢 Étage:")
            print(f"      • Numéro: {details.get('etage_num', 'N/A')}")
        
        print()
        print(f"   Justification: {result.get('justification', 'N/A')}")
        print()
        
        # Comparer avec l'ancienne méthode si disponible
        if 'exposition' in data:
            old_result = data['exposition']
            print("   📊 COMPARAISON AVEC ANCIENNE MÉTHODE:")
            print(f"      Ancien score: {old_result.get('score', 'N/A')}")
            print(f"      Ancien tier: {old_result.get('tier', 'N/A')}")
            print(f"      Ancienne exposition: {old_result.get('exposition', 'N/A')}")
            print()
        
        print("=" * 80)
        print()

if __name__ == "__main__":
    test_voting_method()

