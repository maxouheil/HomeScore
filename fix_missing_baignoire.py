#!/usr/bin/env python3
"""
Script pour corriger les analyses baignoire manquantes
Analyse les appartements qui n'ont pas d'analyse baignoire
"""

import json
import os
from pathlib import Path
from extract_baignoire import BaignoireExtractor
from datetime import datetime

def get_apartments_missing_baignoire():
    """Récupère la liste des appartements sans analyse baignoire"""
    missing_ids = [
        "85467731", "87336337", "88305405", "90931157", "91153576", 
        "91419570", "91644200", "91652882", "91673409", "91901126", 
        "92385257", "92656309", "92656320", "92708756", "92724395", 
        "92732956", "92913102", "93005222"
    ]
    return missing_ids

def load_apartment(apartment_id):
    """Charge un appartement depuis son fichier JSON"""
    apt_file = Path(f'data/appartements/{apartment_id}.json')
    if not apt_file.exists():
        return None
    
    try:
        with open(apt_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"   ❌ Erreur lecture {apartment_id}: {e}")
        return None

def save_apartment(apartment, apartment_id):
    """Sauvegarde un appartement dans son fichier JSON"""
    apt_file = Path(f'data/appartements/{apartment_id}.json')
    
    try:
        with open(apt_file, 'w', encoding='utf-8') as f:
            json.dump(apartment, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"   ❌ Erreur sauvegarde {apartment_id}: {e}")
        return False

def update_scraped_apartments(apartment_id, baignoire_data):
    """Met à jour aussi le fichier scraped_apartments.json"""
    scraped_file = Path('data/scraped_apartments.json')
    if not scraped_file.exists():
        return False
    
    try:
        with open(scraped_file, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        
        # Trouver et mettre à jour l'appartement
        updated = False
        for apt in apartments:
            if str(apt.get('id', '')) == str(apartment_id):
                apt['baignoire'] = baignoire_data
                updated = True
                break
        
        if updated:
            # Créer backup
            backup_file = f"data/scraped_apartments.json.backup_baignoire_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(apartments, f, ensure_ascii=False, indent=2)
            
            # Sauvegarder
            with open(scraped_file, 'w', encoding='utf-8') as f:
                json.dump(apartments, f, ensure_ascii=False, indent=2)
            
            return True
    except Exception as e:
        print(f"   ⚠️ Erreur mise à jour scraped_apartments.json: {e}")
        return False
    
    return False

def analyze_missing_baignoire():
    """Analyse la baignoire pour tous les appartements manquants"""
    
    print("🛁 CORRECTION DES ANALYSES BAIGNOIRE MANQUANTES")
    print("=" * 80)
    print()
    
    # Récupérer la liste des appartements manquants
    missing_ids = get_apartments_missing_baignoire()
    print(f"📋 {len(missing_ids)} appartements à analyser")
    print()
    
    # Initialiser l'extracteur
    extractor = BaignoireExtractor()
    
    # Statistiques
    stats = {
        'total': len(missing_ids),
        'success': 0,
        'has_baignoire': 0,
        'has_douche': 0,
        'no_bathroom': 0,
        'errors': 0,
        'missing_files': 0
    }
    
    # Analyser chaque appartement
    for i, apartment_id in enumerate(missing_ids, 1):
        print(f"🏠 Appartement {i}/{len(missing_ids)}: {apartment_id}")
        
        # Charger l'appartement
        apartment = load_apartment(apartment_id)
        if not apartment:
            stats['missing_files'] += 1
            print(f"   ❌ Fichier non trouvé")
            print()
            continue
        
        # Vérifier si déjà analysé
        if 'baignoire' in apartment and apartment.get('baignoire'):
            existing = apartment['baignoire']
            if existing.get('has_baignoire') is not None or existing.get('has_douche') is not None:
                print(f"   ⏭️  Déjà analysé (skip)")
                print()
                continue
        
        # Afficher les infos de base
        localisation = apartment.get('localisation', 'N/A')
        prix = apartment.get('prix', 'N/A')
        print(f"   📍 {localisation}")
        print(f"   💰 {prix}")
        
        # Analyser la baignoire
        try:
            print(f"   🔍 Analyse en cours...")
            baignoire_result = extractor.extract_baignoire_ultimate(apartment)
            
            # Mettre à jour l'appartement
            apartment['baignoire'] = baignoire_result
            
            # Sauvegarder
            if save_apartment(apartment, apartment_id):
                print(f"   ✅ Fichier mis à jour")
            else:
                print(f"   ⚠️ Erreur sauvegarde")
            
            # Mettre à jour aussi scraped_apartments.json
            update_scraped_apartments(apartment_id, baignoire_result)
            
            # Afficher le résultat
            has_baignoire = baignoire_result.get('has_baignoire', False)
            has_douche = baignoire_result.get('has_douche', False)
            score = baignoire_result.get('score', 0)
            tier = baignoire_result.get('tier', 'tier3')
            confidence = baignoire_result.get('confidence', 0)
            photos_analyzed = baignoire_result.get('photos_analyzed', 0)
            
            if has_baignoire:
                stats['has_baignoire'] += 1
                print(f"   ✅ Baignoire détectée")
            elif has_douche:
                stats['has_douche'] += 1
                print(f"   ❌ Douche seulement (pas de baignoire)")
            else:
                stats['no_bathroom'] += 1
                print(f"   ❓ Salle de bain non détectée")
            
            print(f"   📊 Score: {score}/10 | Tier: {tier} | Confiance: {confidence}%")
            if photos_analyzed > 0:
                print(f"   📸 Photos analysées: {photos_analyzed}")
            
            justification = baignoire_result.get('justification', '')[:80]
            print(f"   💬 {justification}...")
            
            stats['success'] += 1
            
        except Exception as e:
            stats['errors'] += 1
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Afficher les statistiques finales
    print("=" * 80)
    print("📊 STATISTIQUES FINALES")
    print("=" * 80)
    print(f"Total: {stats['total']}")
    print(f"✅ Succès: {stats['success']}")
    print(f"❌ Erreurs: {stats['errors']}")
    print(f"📁 Fichiers manquants: {stats['missing_files']}")
    print()
    print(f"✅ Baignoire détectée: {stats['has_baignoire']} ({stats['has_baignoire']/stats['success']*100:.1f}%)" if stats['success'] > 0 else "✅ Baignoire détectée: 0")
    print(f"❌ Douche seulement: {stats['has_douche']} ({stats['has_douche']/stats['success']*100:.1f}%)" if stats['success'] > 0 else "❌ Douche seulement: 0")
    print(f"❓ Salle de bain non détectée: {stats['no_bathroom']} ({stats['no_bathroom']/stats['success']*100:.1f}%)" if stats['success'] > 0 else "❓ Salle de bain non détectée: 0")
    print()
    
    if stats['success'] == stats['total']:
        print("✅ Tous les appartements ont été analysés avec succès!")
    elif stats['success'] > 0:
        print(f"⚠️ {stats['success']}/{stats['total']} appartements analysés avec succès")
    else:
        print("❌ Aucun appartement n'a pu être analysé")
    
    return stats['success'] > 0

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--all', '-a', '--force', '-f']:
        # Mode non-interactif
        analyze_missing_baignoire()
    else:
        # Mode interactif avec confirmation
        print("⚠️  ATTENTION: Ce script va analyser la baignoire pour 18 appartements")
        print("   Les fichiers seront mis à jour directement")
        print("   Utilisez --all ou -a pour lancer directement sans confirmation")
        print()
        try:
            response = input("Continuer ? (o/N): ")
            if response.lower() == 'o':
                analyze_missing_baignoire()
            else:
                print("❌ Annulé")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Annulé (mode non-interactif)")
            print("   Utilisez: python3 fix_missing_baignoire.py --all")






