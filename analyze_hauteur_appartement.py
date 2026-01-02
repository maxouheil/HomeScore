#!/usr/bin/env python3
"""
Script pour analyser la hauteur sous plafond d'un appartement spécifique
"""

import json
import sys
from analyze_photos import PhotoAnalyzer
from data_loader import load_apartments

def analyze_apartment_hauteur(apt_id):
    """Analyse la hauteur sous plafond d'un appartement"""
    print(f"🔍 Analyse de la hauteur sous plafond pour l'appartement {apt_id}")
    print("="*60)
    
    # Charger l'appartement
    apartments = load_apartments(prefer_api=True)
    apt = None
    for a in apartments:
        if str(a.get('id')) == apt_id:
            apt = a
            break
    
    if not apt:
        print(f"❌ Appartement {apt_id} non trouvé")
        return None
    
    print(f"\n🏠 Appartement trouvé:")
    print(f"   Prix: {apt.get('prix')}")
    print(f"   Surface: {apt.get('surface')}")
    print(f"   Localisation: {apt.get('localisation')}")
    
    # Extraire les URLs des photos
    photos = apt.get('photos', [])
    photos_urls = []
    for photo in photos:
        if isinstance(photo, dict):
            url = photo.get('url', '')
        elif isinstance(photo, str):
            url = photo
        if url:
            photos_urls.append(url)
    
    print(f"\n📸 Photos disponibles: {len(photos_urls)}")
    if photos_urls:
        print(f"   Analyse des 5 premières photos...")
        for i, url in enumerate(photos_urls[:5], 1):
            print(f"      {i}. {url[:80]}...")
    
    if not photos_urls:
        print("❌ Aucune photo disponible")
        return None
    
    # Analyser avec PhotoAnalyzer
    try:
        analyzer = PhotoAnalyzer()
        result = analyzer.analyze_photos_hauteur_plafond(photos_urls)
        
        print(f"\n✅ RÉSULTAT DE L'ANALYSE:")
        print(f"   Hauteur estimée: {result.get('hauteur_estimate', 'N/A')}m")
        print(f"   Catégorie: {result.get('hauteur_category', 'N/A')}")
        print(f"   Confiance: {result.get('confidence', 0):.2f}")
        print(f"   Justification: {result.get('justification', 'N/A')}")
        print(f"   Photos analysées: {result.get('photos_analyzed', 0)}")
        
        details = result.get('details', {})
        if details:
            if 'hauteurs' in details:
                hauteurs = details['hauteurs']
                print(f"\n   📊 Détails:")
                print(f"      Hauteurs détectées: {hauteurs}")
                if hauteurs:
                    print(f"      Min: {min(hauteurs):.2f}m")
                    print(f"      Max: {max(hauteurs):.2f}m")
                    print(f"      Moyenne: {sum(hauteurs)/len(hauteurs):.2f}m")
            
            if 'photos_plafond' in details:
                print(f"      Photos avec plafond visible: {details['photos_plafond']}")
        
        # Comparer avec la description
        description = apt.get('description', '')
        if '3,30' in description or '3.30' in description or '3,3' in description:
            print(f"\n   📝 Note: La description mentionne une hauteur de ~3.30m")
            if result.get('hauteur_estimate'):
                diff = abs(result.get('hauteur_estimate') - 3.30)
                if diff > 0.5:
                    print(f"      ⚠️  Écart significatif avec l'analyse IA ({diff:.2f}m)")
                else:
                    print(f"      ✅ Cohérent avec l'analyse IA")
        
        # Calculer le tier avec les nouveaux seuils
        hauteur_estimate = result.get('hauteur_estimate')
        if hauteur_estimate:
            print(f"\n   🎯 ÉVALUATION (nouveaux seuils):")
            if hauteur_estimate > 2.80:
                tier = 'tier1 (good)'
                score = 10
            elif hauteur_estimate >= 2.50:
                tier = 'tier2 (moyen)'
                score = 5
            else:
                tier = 'tier3 (bad)'
                score = 0
            print(f"      Tier: {tier}")
            print(f"      Score: {score}/10")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    apt_id = sys.argv[1] if len(sys.argv) > 1 else '93083514'
    analyze_apartment_hauteur(apt_id)


