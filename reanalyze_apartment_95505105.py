#!/usr/bin/env python3
"""
Script pour forcer la réanalyse complète de l'appartement 95505105
"""

import json
import os
from pathlib import Path
from analyze_apartment_unified import UnifiedApartmentAnalyzer
from data_loader import load_apartments

def reanalyze_apartment_95505105():
    """Force la réanalyse complète de l'appartement 95505105"""
    
    print("=" * 80)
    print("🔄 RÉANALYSE FORCÉE - APPARTEMENT 95505105")
    print("=" * 80)
    print()
    
    # Charger les données
    print("📥 Chargement des données...")
    apartments = load_apartments(prefer_api=False)  # Charger depuis scraped_apartments.json
    
    # Trouver l'appartement
    apartment = None
    for apt in apartments:
        if str(apt.get('id')) == '95505105':
            apartment = apt
            break
    
    if not apartment:
        print("❌ Appartement 95505105 non trouvé")
        return
    
    print(f"✅ Appartement trouvé: {apartment.get('titre', 'N/A')}")
    print(f"   Localisation: {apartment.get('localisation', 'N/A')}")
    print(f"   Photos: {len(apartment.get('photos', []))}")
    print()
    
    # Afficher l'état actuel
    if apartment.get('style_analysis'):
        sa = apartment['style_analysis']
        print("📊 ÉTAT ACTUEL DE L'ANALYSE:")
        print(f"   Style: {sa.get('style', {}).get('type', 'N/A')}")
        print(f"   Cuisine ouverte: {sa.get('cuisine', {}).get('ouverte')}")
        print(f"   Cuisine visible: {sa.get('cuisine', {}).get('visible')}")
        print(f"   Baignoire: {sa.get('baignoire', {}).get('presente')}")
        print(f"   Hauteur plafond: {sa.get('hauteur_plafond', {}).get('hauteur_estimee')}")
        print(f"   Piece vie: {sa.get('piece_vie', {}).get('taille_m2')}")
        print(f"   Visavis: {sa.get('visavis', {}).get('distance')}")
        print()
    
    # Supprimer l'ancienne analyse pour forcer la réanalyse
    if 'style_analysis' in apartment:
        del apartment['style_analysis']
        print("🗑️  Ancienne analyse supprimée (forçage réanalyse)")
        print()
    
    # Vérifier les photos
    photos = apartment.get('photos', [])
    if not photos:
        print("❌ Aucune photo disponible")
        return
    
    print(f"📸 {len(photos)} photos disponibles")
    for i, photo in enumerate(photos[:7], 1):
        local_path = photo.get('local_path', '')
        exists = os.path.exists(local_path) if local_path else False
        status = "✅" if exists else "❌"
        print(f"   {status} Photo {i}: {os.path.basename(local_path) if local_path else 'URL seulement'}")
    print()
    
    # Analyser avec force_reanalysis=True
    print("🤖 Démarrage de l'analyse unifiée (force_reanalysis=True)...")
    print()
    
    analyzer = UnifiedApartmentAnalyzer()
    result = analyzer.analyze_apartment_unified(
        apartment, 
        max_photos=7,  # Analyser jusqu'à 7 photos
        force_reanalysis=True  # FORCER la réanalyse
    )
    
    if result:
        print()
        print("=" * 80)
        print("✅ ANALYSE TERMINÉE")
        print("=" * 80)
        print()
        print("📊 RÉSULTATS:")
        print(f"   Style: {result.get('style', {}).get('type', 'N/A')}")
        print(f"   Cuisine ouverte: {result.get('cuisine', {}).get('ouverte')}")
        print(f"   Cuisine visible: {result.get('cuisine', {}).get('visible')}")
        print(f"   Baignoire: {result.get('baignoire', {}).get('presente')}")
        print(f"   Hauteur plafond: {result.get('hauteur_plafond', {}).get('hauteur_estimee')}")
        print(f"   Piece vie: {result.get('piece_vie', {}).get('taille_m2')}")
        print(f"   Visavis: {result.get('visavis', {}).get('distance')}")
        print(f"   Photos analysées: {result.get('photos_analyzed')}")
        print()
        
        # Afficher les détails de la cuisine
        cuisine = result.get('cuisine', {})
        print("🍳 DÉTAILS CUISINE:")
        print(f"   Ouverte: {cuisine.get('ouverte')}")
        print(f"   Visible: {cuisine.get('visible')}")
        print(f"   Confidence: {cuisine.get('confidence')}")
        print(f"   Justification: {cuisine.get('justification', 'N/A')}")
        print()
        
        # Sauvegarder dans l'appartement
        apartment['style_analysis'] = result
        apartment['_analysis_data'] = result
        
        # Sauvegarder dans scraped_apartments.json
        print("💾 Sauvegarde des résultats...")
        scraped_file = Path('data/scraped_apartments.json')
        
        # Backup
        backup_file = scraped_file.with_suffix('.json.backup_reanalyze_95505105')
        if scraped_file.exists():
            import shutil
            shutil.copy2(scraped_file, backup_file)
            print(f"   💾 Backup créé: {backup_file.name}")
        
        # Mettre à jour l'appartement dans la liste
        for i, apt in enumerate(apartments):
            if str(apt.get('id')) == '95505105':
                apartments[i] = apartment
                break
        
        # Sauvegarder
        with open(scraped_file, 'w', encoding='utf-8') as f:
            json.dump(apartments, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"   ✅ Données sauvegardées dans {scraped_file}")
        print()
        print("=" * 80)
        print("✅ RÉANALYSE COMPLÈTE TERMINÉE")
        print("=" * 80)
        
    else:
        print()
        print("❌ ÉCHEC DE L'ANALYSE")
        print("   Vérifiez les logs ci-dessus pour plus de détails")

if __name__ == "__main__":
    reanalyze_apartment_95505105()
