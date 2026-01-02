#!/usr/bin/env python3
"""
Test du critère "large pièce de vie" sur 3 appartements spécifiques:
- 780k Ménilmontant
- 770k Folie-Méricourt
- 590k Sainte-Marguerite
"""

import json
import os
import re
from scoring import score_large_piece_vie, load_scoring_config
from data_loader import load_apartments

def find_apartments_by_criteria():
    """Trouve les appartements correspondant aux critères (avec tolérance)"""
    apartments = load_apartments(prefer_api=True)
    
    target_apartments = []
    
    for apt in apartments:
        prix_str = apt.get('prix', '')
        localisation = apt.get('localisation', '').lower()
        map_info = apt.get('map_info', {}) or {}
        quartier = str(map_info.get('quartier', '')).lower()
        description = apt.get('description', '').lower()
        
        # Extraire le prix
        prix_match = re.search(r'([\d\s]+)', prix_str.replace(' ', '')) if prix_str else None
        prix_num = None
        if prix_match:
            try:
                prix_num = int(prix_match.group(1))
            except:
                pass
        
        if not prix_num:
            continue
        
        # Chercher les correspondances
        text_combined = f"{localisation} {quartier} {description}"
        
        # 780k Ménilmontant (tolérance: 700k-850k)
        if 700000 <= prix_num <= 850000:
            if 'menilmontant' in text_combined or 'ménilmontant' in text_combined:
                target_apartments.append({
                    'apt': apt,
                    'match': f'{prix_num//1000}k Ménilmontant (recherché: 780k)',
                    'prix': prix_num
                })
        
        # 770k Folie-Méricourt (déjà trouvé, mais on garde)
        if 765000 <= prix_num <= 775000:
            if 'folie' in text_combined and 'mericourt' in text_combined:
                target_apartments.append({
                    'apt': apt,
                    'match': '770k Folie-Méricourt',
                    'prix': prix_num
                })
        
        # 590k Sainte-Marguerite (tolérance: 550k-650k)
        if 550000 <= prix_num <= 650000:
            if 'sainte' in text_combined and 'marguerite' in text_combined:
                target_apartments.append({
                    'apt': apt,
                    'match': f'{prix_num//1000}k Sainte-Marguerite (recherché: 590k)',
                    'prix': prix_num
                })
    
    # Si on n'a pas trouvé exactement, prendre les plus proches
    if len(target_apartments) < 3:
        # Chercher le plus proche de 780k Ménilmontant
        menilmontant_found = any('ménilmontant' in t['match'].lower() for t in target_apartments)
        if not menilmontant_found:
            for apt in apartments:
                text = f"{apt.get('localisation', '')} {apt.get('map_info', {}).get('quartier', '')} {apt.get('description', '')}".lower()
                if 'menilmontant' in text or 'ménilmontant' in text:
                    prix_match = re.search(r'([\d\s]+)', apt.get('prix', '').replace(' ', ''))
                    if prix_match:
                        try:
                            prix = int(prix_match.group(1))
                            target_apartments.append({
                                'apt': apt,
                                'match': f'{prix//1000}k Ménilmontant (recherché: 780k)',
                                'prix': prix
                            })
                            break
                        except:
                            pass
        
        # Chercher le plus proche de 590k Sainte-Marguerite
        sainte_marguerite_found = any('sainte-marguerite' in t['match'].lower() for t in target_apartments)
        if not sainte_marguerite_found:
            for apt in apartments:
                text = f"{apt.get('localisation', '')} {apt.get('map_info', {}).get('quartier', '')} {apt.get('description', '')}".lower()
                if 'sainte' in text and 'marguerite' in text:
                    prix_match = re.search(r'([\d\s]+)', apt.get('prix', '').replace(' ', ''))
                    if prix_match:
                        try:
                            prix = int(prix_match.group(1))
                            # Prendre le plus proche de 590k
                            if 700000 <= prix <= 800000:  # Prendre un dans cette fourchette
                                target_apartments.append({
                                    'apt': apt,
                                    'match': f'{prix//1000}k Sainte-Marguerite (recherché: 590k)',
                                    'prix': prix
                                })
                                break
                        except:
                            pass
    
    return target_apartments

def test_large_piece_vie_on_apartments():
    """Test le scoring de large pièce de vie sur les 3 appartements"""
    print("🧪 TEST CRITÈRE 'LARGE PIÈCE DE VIE'")
    print("=" * 70)
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger la config")
        return
    
    # Trouver les appartements
    print("\n🔍 Recherche des appartements...")
    target_apartments = find_apartments_by_criteria()
    
    if not target_apartments:
        print("❌ Aucun appartement trouvé correspondant aux critères")
        print("\n💡 Vérification de tous les appartements disponibles...")
        
        # Afficher tous les appartements pour debug
        apartments = load_apartments(prefer_api=True)
        print(f"\n📋 {len(apartments)} appartements disponibles:")
        for apt in apartments[:10]:  # Afficher les 10 premiers
            prix = apt.get('prix', 'N/A')
            loc = apt.get('localisation', 'N/A')
            quartier = apt.get('map_info', {}).get('quartier', 'N/A')
            print(f"   - {prix} | {loc} | {quartier}")
        return
    
    print(f"✅ {len(target_apartments)} appartement(s) trouvé(s)\n")
    
    # Tester chaque appartement
    for i, target in enumerate(target_apartments, 1):
        apt = target['apt']
        match = target['match']
        prix = target['prix']
        
        print(f"\n{'='*70}")
        print(f"🏠 APPARTEMENT {i}: {match}")
        print(f"{'='*70}")
        print(f"   ID: {apt.get('id')}")
        print(f"   Prix: {apt.get('prix')}")
        print(f"   Surface: {apt.get('surface')}")
        print(f"   Localisation: {apt.get('localisation')}")
        quartier = apt.get('map_info', {}).get('quartier', 'N/A')
        print(f"   Quartier: {quartier}")
        
        photos = apt.get('photos', [])
        print(f"   Photos: {len(photos)} disponible(s)")
        
        if not photos:
            print(f"\n   ⚠️  Pas de photos disponibles pour cet appartement")
            continue
        
        # Tester le scoring
        print(f"\n   📊 Analyse de la taille du salon...")
        try:
            result = score_large_piece_vie(apt, config)
            
            print(f"\n   ✅ RÉSULTAT:")
            print(f"      Score: {result.get('score')}/10")
            print(f"      Tier: {result.get('tier')}")
            print(f"      Justification: {result.get('justification')}")
            
            details = result.get('details', {})
            if details:
                print(f"\n   📋 DÉTAILS:")
                if 'salon_size_estimate' in details:
                    print(f"      Taille salon estimée: {details['salon_size_estimate']}m²")
                if 'surface_totale' in details:
                    print(f"      Surface totale: {details['surface_totale']}m²")
                if 'pourcentage_salon' in details:
                    print(f"      Pourcentage salon: {details['pourcentage_salon']}%")
                if 'salon_category' in details:
                    print(f"      Catégorie salon: {details['salon_category']}")
                if 'confidence' in details:
                    print(f"      Confiance: {details['confidence']:.2f}")
                
                # Afficher les détails de l'analyse
                salon_analysis = details.get('salon_analysis', {})
                if salon_analysis:
                    print(f"\n   🔍 ANALYSE DÉTAILLÉE:")
                    print(f"      Photos analysées: {salon_analysis.get('photos_analyzed', 0)}")
                    analysis_details = salon_analysis.get('details', {})
                    if analysis_details:
                        if 'photos_salon' in analysis_details:
                            print(f"      Photos de salon identifiées: {analysis_details['photos_salon']}")
                        if 'sizes' in analysis_details:
                            print(f"      Estimations individuelles: {analysis_details['sizes']}m²")
        except Exception as e:
            print(f"\n   ❌ Erreur lors de l'analyse: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"✅ Test terminé!")
    print(f"{'='*70}")

if __name__ == "__main__":
    test_large_piece_vie_on_apartments()

