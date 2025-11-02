#!/usr/bin/env python3
"""
Script pour relancer les analyses d'exposition avec la nouvelle logique
sur tous les appartements existants
"""

import json
import os
from extract_exposition import ExpositionExtractor
from datetime import datetime

def reanalyze_exposition_batch(input_file="data/scraped_apartments.json", output_file=None):
    """Relance les analyses d'exposition sur tous les appartements"""
    
    print("🔄 RE-ANALYSE DE L'EXPOSITION")
    print("=" * 60)
    
    # Charger les données
    if not os.path.exists(input_file):
        print(f"❌ Fichier {input_file} non trouvé")
        return False
    
    with open(input_file, 'r', encoding='utf-8') as f:
        apartments = json.load(f)
    
    print(f"📋 {len(apartments)} appartements trouvés")
    print()
    
    # Initialiser l'extracteur
    extractor = ExpositionExtractor()
    
    # Statistiques
    stats = {
        'total': len(apartments),
        'exposition_explicite': 0,
        'exposition_photos': 0,
        'exposition_inconnue': 0,
        'avec_bonus_etage': 0,
        'errors': 0
    }
    
    # Réanalyser chaque appartement
    for i, apartment in enumerate(apartments, 1):
        apt_id = apartment.get('id', 'N/A')
        localisation = apartment.get('localisation', 'N/A')
        
        print(f"🏠 Appartement {i}/{len(apartments)}")
        print(f"   ID: {apt_id}")
        print(f"   Localisation: {localisation}")
        
        try:
            # Réanalyser l'exposition avec la nouvelle logique
            exposition_result = extractor.extract_exposition_ultimate(apartment)
            
            # Mettre à jour l'appartement
            apartment['exposition'] = exposition_result
            
            # Statistiques
            if exposition_result.get('exposition_explicite'):
                stats['exposition_explicite'] += 1
                print(f"   ✅ Exposition explicite: {exposition_result.get('exposition')}")
            elif exposition_result.get('photos_analyzed', 0) > 0:
                stats['exposition_photos'] += 1
                print(f"   📸 Exposition depuis photos: {exposition_result.get('exposition')}")
            else:
                stats['exposition_inconnue'] += 1
                print(f"   ❓ Exposition inconnue")
            
            if exposition_result.get('bonus_etage', 0) > 0:
                stats['avec_bonus_etage'] += 1
                print(f"   🏢 Bonus étage: +{exposition_result.get('bonus_etage')}")
            
            score = exposition_result.get('score', 0)
            tier = exposition_result.get('tier', 'tier3')
            print(f"   📊 Score: {score}/10 - Tier: {tier}")
            print(f"   💬 Justification: {exposition_result.get('justification', 'N/A')[:60]}...")
            
        except Exception as e:
            stats['errors'] += 1
            print(f"   ❌ Erreur: {e}")
        
        print()
    
    # Sauvegarder les résultats
    if output_file is None:
        output_file = input_file
    
    # Créer backup
    backup_file = f"{input_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    print(f"💾 Backup créé: {backup_file}")
    
    # Sauvegarder les nouveaux résultats
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    print(f"✅ Résultats sauvegardés: {output_file}")
    print()
    
    # Afficher les statistiques
    print("📊 STATISTIQUES FINALES")
    print("=" * 60)
    print(f"Total analysé: {stats['total']}")
    print(f"✅ Exposition explicite: {stats['exposition_explicite']} ({stats['exposition_explicite']/stats['total']*100:.1f}%)")
    print(f"📸 Exposition depuis photos: {stats['exposition_photos']} ({stats['exposition_photos']/stats['total']*100:.1f}%)")
    print(f"❓ Exposition inconnue: {stats['exposition_inconnue']} ({stats['exposition_inconnue']/stats['total']*100:.1f}%)")
    print(f"🏢 Avec bonus étage >=4: {stats['avec_bonus_etage']} ({stats['avec_bonus_etage']/stats['total']*100:.1f}%)")
    if stats['errors'] > 0:
        print(f"❌ Erreurs: {stats['errors']}")
    print()
    
    return True

def reanalyze_single_apartment(apartment_id, input_file="data/scraped_apartments.json"):
    """Réanalyse l'exposition d'un seul appartement"""
    
    if not os.path.exists(input_file):
        print(f"❌ Fichier {input_file} non trouvé")
        return None
    
    with open(input_file, 'r', encoding='utf-8') as f:
        apartments = json.load(f)
    
    # Trouver l'appartement
    apartment = None
    for apt in apartments:
        if str(apt.get('id', '')) == str(apartment_id):
            apartment = apt
            break
    
    if not apartment:
        print(f"❌ Appartement {apartment_id} non trouvé")
        return None
    
    print(f"🏠 Réanalyse appartement {apartment_id}")
    print(f"   Localisation: {apartment.get('localisation', 'N/A')}")
    print(f"   Prix: {apartment.get('prix', 'N/A')}")
    print()
    
    # Réanalyser
    extractor = ExpositionExtractor()
    exposition_result = extractor.extract_exposition_ultimate(apartment)
    
    # Afficher le résultat
    print("📊 RÉSULTAT")
    print("=" * 60)
    print(f"Exposition: {exposition_result.get('exposition') or 'Inconnue'}")
    print(f"Score: {exposition_result.get('score', 0)}/10")
    print(f"Tier: {exposition_result.get('tier', 'tier3')}")
    print(f"Bonus étage: {exposition_result.get('bonus_etage', 0)}")
    print(f"Exposition explicite: {exposition_result.get('exposition_explicite', False)}")
    print(f"Photos analysées: {exposition_result.get('photos_analyzed', 0)}")
    print(f"Justification: {exposition_result.get('justification', 'N/A')}")
    print()
    
    if exposition_result.get('details'):
        print("📋 DÉTAILS:")
        details = exposition_result['details']
        for key, value in details.items():
            print(f"   {key}: {value}")
        print()
    
    # Mettre à jour l'appartement
    apartment['exposition'] = exposition_result
    
    # Sauvegarder
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Appartement mis à jour dans {input_file}")
    
    return exposition_result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all' or sys.argv[1] == '-a':
            # Réanalyser tous les appartements (pas de confirmation)
            reanalyze_exposition_batch()
        elif sys.argv[1] == '--force' or sys.argv[1] == '-f':
            # Force mode (pas de confirmation)
            reanalyze_exposition_batch()
        else:
            # Réanalyser un seul appartement
            apartment_id = sys.argv[1]
            reanalyze_single_apartment(apartment_id)
    else:
        # Réanalyser tous les appartements
        print("⚠️  ATTENTION: Ce script va réanalyser TOUS les appartements")
        print("   Un backup sera créé automatiquement")
        print("   Utilisez --all ou -a pour lancer directement sans confirmation")
        print()
        try:
            response = input("Continuer ? (o/N): ")
            if response.lower() == 'o':
                reanalyze_exposition_batch()
            else:
                print("❌ Annulé")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Annulé (mode non-interactif)")
            print("   Utilisez: python3 reanalyze_exposition.py --all")
