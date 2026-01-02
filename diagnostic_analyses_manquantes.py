#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier si les analyses (cuisine, baignoire, pièce de vie, style) sont présentes
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def load_apartments():
    """Charge tous les appartements depuis data/all_apartments.json"""
    apartments_file = 'data/all_apartments.json'
    if not os.path.exists(apartments_file):
        print(f"❌ Fichier {apartments_file} non trouvé")
        return []
    
    with open(apartments_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_apartment_analyses(apartment):
    """Vérifie si un appartement a les analyses nécessaires"""
    apartment_id = apartment.get('id', 'unknown')
    results = {
        'id': apartment_id,
        'cuisine': False,
        'baignoire': False,
        'piece_vie': False,
        'style': False,
        'details': {}
    }
    
    # Vérifier cuisine
    style_analysis = apartment.get('style_analysis', {})
    cuisine_data = style_analysis.get('cuisine', {})
    if cuisine_data and cuisine_data.get('ouverte') is not None:
        results['cuisine'] = True
        results['details']['cuisine'] = f"Ouverte: {cuisine_data.get('ouverte')}"
    else:
        results['details']['cuisine'] = "Non analysée"
    
    # Vérifier baignoire
    baignoire_data = apartment.get('baignoire_data', {}) or apartment.get('baignoire', {})
    if baignoire_data and baignoire_data.get('has_baignoire') is not None:
        results['baignoire'] = True
        results['details']['baignoire'] = f"Présente: {baignoire_data.get('has_baignoire')}"
    else:
        results['details']['baignoire'] = "Non analysée"
    
    # Vérifier pièce de vie
    piece_vie_data = apartment.get('piece_vie', {})
    if piece_vie_data and piece_vie_data.get('taille'):
        results['piece_vie'] = True
        results['details']['piece_vie'] = f"Taille: {piece_vie_data.get('taille')}"
    else:
        results['details']['piece_vie'] = "Non analysée"
    
    # Vérifier style
    style_data = style_analysis.get('style', {})
    if style_data and style_data.get('type'):
        results['style'] = True
        results['details']['style'] = f"Type: {style_data.get('type')}"
    else:
        results['details']['style'] = "Non analysée"
    
    return results

def main():
    print("🔍 DIAGNOSTIC DES ANALYSES MANQUANTES")
    print("=" * 60)
    
    apartments = load_apartments()
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"📊 {len(apartments)} appartements à vérifier\n")
    
    stats = defaultdict(int)
    missing_analyses = []
    
    for apartment in apartments:
        results = check_apartment_analyses(apartment)
        
        # Compter les analyses présentes
        analyses_count = sum([
            results['cuisine'],
            results['baignoire'],
            results['piece_vie'],
            results['style']
        ])
        
        stats['total'] += 1
        stats['with_cuisine'] += 1 if results['cuisine'] else 0
        stats['with_baignoire'] += 1 if results['baignoire'] else 0
        stats['with_piece_vie'] += 1 if results['piece_vie'] else 0
        stats['with_style'] += 1 if results['style'] else 0
        
        if analyses_count < 4:
            missing_analyses.append(results)
    
    # Afficher les statistiques
    print("📊 STATISTIQUES:")
    print(f"   Total appartements: {stats['total']}")
    print(f"   Avec cuisine analysée: {stats['with_cuisine']} ({stats['with_cuisine']/stats['total']*100:.1f}%)")
    print(f"   Avec baignoire analysée: {stats['with_baignoire']} ({stats['with_baignoire']/stats['total']*100:.1f}%)")
    print(f"   Avec pièce de vie analysée: {stats['with_piece_vie']} ({stats['with_piece_vie']/stats['total']*100:.1f}%)")
    print(f"   Avec style analysé: {stats['with_style']} ({stats['with_style']/stats['total']*100:.1f}%)")
    print()
    
    # Afficher les appartements avec analyses manquantes
    if missing_analyses:
        print(f"⚠️  {len(missing_analyses)} appartements avec analyses manquantes:")
        print()
        for result in missing_analyses[:10]:  # Afficher les 10 premiers
            print(f"   🏠 {result['id']}:")
            for key in ['cuisine', 'baignoire', 'piece_vie', 'style']:
                status = "✅" if result[key] else "❌"
                print(f"      {status} {key.capitalize()}: {result['details'][key]}")
            print()
        
        if len(missing_analyses) > 10:
            print(f"   ... et {len(missing_analyses) - 10} autres")
    else:
        print("✅ Tous les appartements ont toutes les analyses !")
    
    print()
    print("💡 SOLUTION:")
    print("   Pour enrichir les appartements manquants, utilisez:")
    print("   POST /apartments/enrich/stream?limit=0")
    print("   (limit=0 pour enrichir tous les appartements manquants)")

if __name__ == "__main__":
    main()
