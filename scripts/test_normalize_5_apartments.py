#!/usr/bin/env python3
"""
Script de test pour normaliser les 5 derniers appartements récupérés
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire parent pour importer le normaliseur
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.normalizers import normalize_apartment

# IDs des 5 derniers appartements
TARGET_APARTMENTS = [
    '52346005',  # Scraping - 2025-12-23
    '70396623',  # API - 2025-11-19
    '71975021',  # API - 2025-09-08
    '71996556',  # API - 2025-09-05
    '72244077',  # Scraping - 2025-12-10
]


def load_apartments():
    """Charge tous les appartements depuis all_apartments.json"""
    apartments_file = 'data/all_apartments.json'
    if not os.path.exists(apartments_file):
        print(f"❌ Fichier {apartments_file} non trouvé")
        return []
    
    with open(apartments_file, 'r', encoding='utf-8') as f:
        apartments = json.load(f)
    
    return apartments


def find_target_apartments(apartments):
    """Trouve les 5 appartements cibles"""
    target_dict = {apt_id: None for apt_id in TARGET_APARTMENTS}
    
    for apt in apartments:
        apt_id = apt.get('id')
        if apt_id in target_dict:
            target_dict[apt_id] = apt
    
    # Vérifier qu'on a trouvé tous les appartements
    missing = [apt_id for apt_id, apt in target_dict.items() if apt is None]
    if missing:
        print(f"⚠️ Appartements non trouvés: {missing}")
    
    return [apt for apt in target_dict.values() if apt is not None]


def test_normalization():
    """Teste la normalisation des 5 appartements"""
    print("🔍 Chargement des appartements...")
    all_apartments = load_apartments()
    print(f"✅ {len(all_apartments)} appartements chargés")
    
    print("\n🔍 Recherche des 5 appartements cibles...")
    target_apartments = find_target_apartments(all_apartments)
    print(f"✅ {len(target_apartments)} appartements trouvés")
    
    if len(target_apartments) == 0:
        print("❌ Aucun appartement trouvé, arrêt du test")
        return
    
    print("\n" + "=" * 60)
    print("NORMALISATION DES APPARTEMENTS")
    print("=" * 60)
    
    normalized_apartments = []
    errors = []
    
    for apt in target_apartments:
        apt_id = apt.get('id', 'N/A')
        print(f"\n📦 Normalisation de l'appartement {apt_id}...")
        
        try:
            normalized = normalize_apartment(apt)
            normalized_apartments.append(normalized)
            
            # Afficher un résumé
            print(f"   ✅ Normalisé avec succès")
            print(f"   - Prix: {normalized.get('prix_formatted', 'N/A')}")
            print(f"   - Surface: {normalized.get('surface_formatted', 'N/A')}")
            print(f"   - Localisation: {normalized.get('localisation', {}).get('metro', 'N/A')}")
            print(f"   - Critères: {len(normalized.get('criteria', {}))} critères")
            print(f"   - Photos: {len(normalized.get('photos', []))} photos")
            
            # Vérifier les données essentielles
            issues = []
            if not normalized.get('prix'):
                issues.append("Prix manquant")
            if not normalized.get('surface'):
                issues.append("Surface manquante")
            if not normalized.get('localisation', {}).get('coordinates'):
                issues.append("Coordonnées manquantes")
            if len(normalized.get('photos', [])) == 0:
                issues.append("Pas de photos")
            
            if issues:
                print(f"   ⚠️ Problèmes détectés: {', '.join(issues)}")
            else:
                print(f"   ✅ Toutes les données essentielles présentes")
                
        except Exception as e:
            print(f"   ❌ Erreur lors de la normalisation: {e}")
            import traceback
            traceback.print_exc()
            errors.append((apt_id, str(e)))
    
    # Sauvegarder les résultats
    output_file = 'data/normalized_5_apartments.json'
    print(f"\n💾 Sauvegarde dans {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(normalized_apartments, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {len(normalized_apartments)} appartements normalisés sauvegardés")
    
    # Résumé final
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"✅ Appartements normalisés: {len(normalized_apartments)}/{len(target_apartments)}")
    if errors:
        print(f"❌ Erreurs: {len(errors)}")
        for apt_id, error in errors:
            print(f"   - {apt_id}: {error}")
    else:
        print("✅ Aucune erreur")
    
    # Afficher un exemple de structure normalisée
    if normalized_apartments:
        print("\n📋 Exemple de structure normalisée (premier appartement):")
        example = normalized_apartments[0]
        print(json.dumps({
            'id': example.get('id'),
            'prix': example.get('prix'),
            'prix_formatted': example.get('prix_formatted'),
            'surface': example.get('surface'),
            'localisation': {
                'metro': example.get('localisation', {}).get('metro'),
                'quartier': example.get('localisation', {}).get('quartier'),
                'has_coordinates': bool(example.get('localisation', {}).get('coordinates'))
            },
            'criteria_count': len(example.get('criteria', {})),
            'photos_count': len(example.get('photos', [])),
            'metadata': example.get('metadata', {})
        }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    test_normalization()
