#!/usr/bin/env python3
"""
Script pour analyser la présence de baignoire sur tous les appartements
Logique:
- Main: analyse texte (description + caractéristiques)
- Fallback: analyse images avec OpenAI Vision pour trouver douche ou baignoire
- Si douche: BAD / Si baignoire: GOOD
"""

import json
import os
from extract_baignoire import BaignoireExtractor
from datetime import datetime

def analyze_baignoire_batch(input_file="data/scraped_apartments.json", output_file=None):
    """Analyse la présence de baignoire sur tous les appartements"""
    
    print("🛁 ANALYSE DE LA BAIGNOIRE")
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
    extractor = BaignoireExtractor()
    
    # Statistiques
    stats = {
        'total': len(apartments),
        'baignoire_texte': 0,
        'baignoire_photos': 0,
        'douche_texte': 0,
        'douche_photos': 0,
        'non_detecte': 0,
        'errors': 0
    }
    
    # Analyser chaque appartement
    for i, apartment in enumerate(apartments, 1):
        apt_id = apartment.get('id', 'N/A')
        localisation = apartment.get('localisation', 'N/A')
        
        print(f"🏠 Appartement {i}/{len(apartments)}")
        print(f"   ID: {apt_id}")
        print(f"   Localisation: {localisation}")
        
        try:
            # Analyser la baignoire
            baignoire_result = extractor.extract_baignoire_ultimate(apartment)
            
            # Mettre à jour l'appartement
            apartment['baignoire'] = baignoire_result
            
            # Statistiques
            if baignoire_result.get('has_baignoire'):
                if baignoire_result.get('detected_from_text'):
                    stats['baignoire_texte'] += 1
                    print(f"   ✅ Baignoire détectée dans le texte")
                else:
                    stats['baignoire_photos'] += 1
                    print(f"   ✅ Baignoire détectée depuis photos")
            elif baignoire_result.get('has_douche'):
                if baignoire_result.get('detected_from_text'):
                    stats['douche_texte'] += 1
                    print(f"   ❌ Douche détectée dans le texte (pas de baignoire)")
                else:
                    stats['douche_photos'] += 1
                    print(f"   ❌ Douche détectée depuis photos (pas de baignoire)")
            else:
                stats['non_detecte'] += 1
                print(f"   ❓ Non détecté")
            
            score = baignoire_result.get('score', 0)
            tier = baignoire_result.get('tier', 'tier3')
            confidence = baignoire_result.get('confidence', 0)
            print(f"   📊 Score: {score}/10 - Tier: {tier} - Confiance: {confidence}%")
            print(f"   💬 Justification: {baignoire_result.get('justification', 'N/A')[:60]}...")
            
        except Exception as e:
            stats['errors'] += 1
            print(f"   ❌ Erreur: {e}")
        
        print()
    
    # Sauvegarder les résultats
    if output_file is None:
        output_file = input_file
    
    # Créer backup
    backup_file = f"{input_file}.backup_baignoire_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
    print(f"✅ Baignoire (texte): {stats['baignoire_texte']} ({stats['baignoire_texte']/stats['total']*100:.1f}%)")
    print(f"✅ Baignoire (photos): {stats['baignoire_photos']} ({stats['baignoire_photos']/stats['total']*100:.1f}%)")
    print(f"❌ Douche (texte): {stats['douche_texte']} ({stats['douche_texte']/stats['total']*100:.1f}%)")
    print(f"❌ Douche (photos): {stats['douche_photos']} ({stats['douche_photos']/stats['total']*100:.1f}%)")
    print(f"❓ Non détecté: {stats['non_detecte']} ({stats['non_detecte']/stats['total']*100:.1f}%)")
    if stats['errors'] > 0:
        print(f"❌ Erreurs: {stats['errors']}")
    
    total_baignoire = stats['baignoire_texte'] + stats['baignoire_photos']
    total_douche = stats['douche_texte'] + stats['douche_photos']
    print()
    print(f"📈 RÉSUMÉ:")
    print(f"   Baignoire (GOOD): {total_baignoire} ({total_baignoire/stats['total']*100:.1f}%)")
    print(f"   Douche (BAD): {total_douche} ({total_douche/stats['total']*100:.1f}%)")
    print()
    
    return True

def analyze_single_apartment(apartment_id, input_file="data/scraped_apartments.json"):
    """Analyse la baignoire d'un seul appartement"""
    
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
    
    print(f"🏠 Analyse appartement {apartment_id}")
    print(f"   Localisation: {apartment.get('localisation', 'N/A')}")
    print(f"   Prix: {apartment.get('prix', 'N/A')}")
    print()
    
    # Analyser
    extractor = BaignoireExtractor()
    baignoire_result = extractor.extract_baignoire_ultimate(apartment)
    
    # Afficher le résultat
    print("📊 RÉSULTAT")
    print("=" * 60)
    print(f"Baignoire: {baignoire_result.get('has_baignoire', False)}")
    print(f"Douche: {baignoire_result.get('has_douche', False)}")
    print(f"Score: {baignoire_result.get('score', 0)}/10")
    print(f"Tier: {baignoire_result.get('tier', 'tier3')}")
    print(f"Détecté depuis texte: {baignoire_result.get('detected_from_text', False)}")
    print(f"Photos analysées: {baignoire_result.get('photos_analyzed', 0)}")
    print(f"Confiance: {baignoire_result.get('confidence', 0)}%")
    print(f"Justification: {baignoire_result.get('justification', 'N/A')}")
    print()
    
    if baignoire_result.get('details'):
        print("📋 DÉTAILS:")
        details = baignoire_result['details']
        for key, value in details.items():
            if key != 'photo_results':  # Ne pas afficher tous les résultats photos
                print(f"   {key}: {value}")
        print()
    
    # Mettre à jour l'appartement
    apartment['baignoire'] = baignoire_result
    
    # Sauvegarder
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Appartement mis à jour dans {input_file}")
    
    return baignoire_result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all' or sys.argv[1] == '-a':
            # Analyser tous les appartements (pas de confirmation)
            analyze_baignoire_batch()
        elif sys.argv[1] == '--force' or sys.argv[1] == '-f':
            # Force mode (pas de confirmation)
            analyze_baignoire_batch()
        else:
            # Analyser un seul appartement
            apartment_id = sys.argv[1]
            analyze_single_apartment(apartment_id)
    else:
        # Analyser tous les appartements
        print("⚠️  ATTENTION: Ce script va analyser TOUS les appartements pour la baignoire")
        print("   Un backup sera créé automatiquement")
        print("   Utilisez --all ou -a pour lancer directement sans confirmation")
        print()
        try:
            response = input("Continuer ? (o/N): ")
            if response.lower() == 'o':
                analyze_baignoire_batch()
            else:
                print("❌ Annulé")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Annulé (mode non-interactif)")
            print("   Utilisez: python3 analyze_baignoire.py --all")

