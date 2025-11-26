#!/usr/bin/env python3
"""
Script pour relancer l'analyse du vis-à-vis avec distance en mètres,
cuisine et baignoire depuis les photos sur tous les appartements existants
"""

import json
import os
from extract_exposition import ExpositionExtractor
from datetime import datetime
from typing import Dict, List, Any

def reanalyze_visavis_distance_batch(input_file="data/scraped_apartments.json", output_file=None):
    """Relance l'analyse du vis-à-vis (distance), cuisine et baignoire sur tous les appartements"""

    print("🔄 RE-ANALYSE COMPLÈTE: VIS-À-VIS, CUISINE ET BAIGNOIRE")
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
        'visavis': {
            'good': 0,  # >20m
            'moyen': 0,  # 10-20m
            'bad': 0,  # <10m
            'not_determined': 0
        },
        'cuisine': {
            'ouverte': 0,
            'fermee': 0,
            'not_determined': 0
        },
        'baignoire': {
            'has_baignoire': 0,
            'has_douche': 0,
            'not_determined': 0
        },
        'no_photos': 0,
        'errors': 0
    }

    # Réanalyser chaque appartement
    for i, apartment in enumerate(apartments, 1):
        apt_id = apartment.get('id', 'N/A')
        localisation = apartment.get('localisation', 'N/A')
        photos = apartment.get('photos', [])

        print(f"🏠 Appartement {i}/{len(apartments)}")
        print(f"   ID: {apt_id}")
        print(f"   Localisation: {localisation}")

        if not photos:
            stats['no_photos'] += 1
            print(f"   📸 Aucune photo disponible")
            # Initialiser les champs pour éviter les erreurs
            if 'exposition' not in apartment:
                apartment['exposition'] = {}
            if 'details' not in apartment['exposition']:
                apartment['exposition']['details'] = {}
            apartment['exposition']['details']['visavis_distance'] = None
            apartment['exposition']['details']['visavis_category'] = None
            apartment['exposition']['details']['visavis_confidence'] = 0.0
            apartment['exposition']['details']['visavis_justification'] = 'Aucune photo disponible'
            print(f"   ❓ Vis-à-vis: None | Cuisine: None | Baignoire: None")
            print()
            continue

        # Extraire les URLs des photos (peut être une liste de strings ou une liste de dicts)
        photo_urls = []
        for photo in photos:
            if isinstance(photo, str):
                photo_urls.append(photo)
            elif isinstance(photo, dict):
                photo_url = photo.get('url')
                if photo_url:
                    photo_urls.append(photo_url)

        if not photo_urls:
            stats['no_photos'] += 1
            print(f"   📸 Aucune photo disponible")
            print(f"   ❓ Vis-à-vis: None | Cuisine: None | Baignoire: None")
            print()
            continue

        print(f"   📸 {len(photo_urls)} photos disponibles")

        try:
            # Analyser le vis-à-vis, la cuisine et la baignoire
            print(f"   🔍 Analyse vis-à-vis...")
            visavis_result = extractor.photo_analyzer.analyze_photos_visavis(photo_urls)
            
            print(f"   🔍 Analyse cuisine...")
            cuisine_result = extractor.photo_analyzer.analyze_photos_cuisine(photo_urls)
            
            print(f"   🔍 Analyse baignoire...")
            baignoire_result = extractor.photo_analyzer.analyze_photos_baignoire(photo_urls)

            # Mettre à jour l'exposition avec le vis-à-vis
            if 'exposition' not in apartment:
                apartment['exposition'] = {}
            if 'details' not in apartment['exposition']:
                apartment['exposition']['details'] = {}

            apartment['exposition']['details']['visavis_distance'] = visavis_result.get('visavis_distance')
            apartment['exposition']['details']['visavis_category'] = visavis_result.get('visavis_category')
            apartment['exposition']['details']['visavis_confidence'] = visavis_result.get('confidence', 0.0)
            apartment['exposition']['details']['visavis_justification'] = visavis_result.get('justification', '')

            # Mettre à jour la cuisine
            if cuisine_result and cuisine_result.get('photos_analyzed', 0) > 0:
                if 'cuisine' not in apartment:
                    apartment['cuisine'] = {}
                apartment['cuisine']['ouverte'] = cuisine_result.get('ouverte')
                apartment['cuisine']['confidence'] = cuisine_result.get('confidence', 0.0)
                apartment['cuisine']['justification'] = cuisine_result.get('justification', '')
                apartment['cuisine']['photos_analyzed'] = cuisine_result.get('photos_analyzed', 0)
                apartment['cuisine']['detected_photos'] = cuisine_result.get('detected_photos', [])

            # Mettre à jour la baignoire
            if baignoire_result and baignoire_result.get('photos_analyzed', 0) > 0:
                if 'baignoire' not in apartment:
                    apartment['baignoire'] = {}
                apartment['baignoire']['has_baignoire'] = baignoire_result.get('has_baignoire')
                apartment['baignoire']['has_douche'] = baignoire_result.get('has_douche')
                apartment['baignoire']['confidence'] = baignoire_result.get('confidence', 0.0)
                apartment['baignoire']['justification'] = baignoire_result.get('justification', '')
                apartment['baignoire']['photos_analyzed'] = baignoire_result.get('photos_analyzed', 0)
                apartment['baignoire']['detected_photos'] = baignoire_result.get('detected_photos', [])

            # Afficher les résultats
            visavis_distance = visavis_result.get('visavis_distance')
            visavis_category = visavis_result.get('visavis_category')
            visavis_confidence = visavis_result.get('confidence', 0.0)

            if visavis_category == 'good':
                stats['visavis']['good'] += 1
                visavis_display = f"✅ {visavis_distance}m (good)"
            elif visavis_category == 'moyen':
                stats['visavis']['moyen'] += 1
                visavis_display = f"⚠️ {visavis_distance}m (moyen)"
            elif visavis_category == 'bad':
                stats['visavis']['bad'] += 1
                visavis_display = f"❌ {visavis_distance}m (bad)"
            else:
                stats['visavis']['not_determined'] += 1
                visavis_display = "❓ None"

            # Cuisine
            cuisine_ouverte = cuisine_result.get('ouverte') if cuisine_result else None
            if cuisine_ouverte is True:
                stats['cuisine']['ouverte'] += 1
                cuisine_display = "✅ Ouverte"
            elif cuisine_ouverte is False:
                stats['cuisine']['fermee'] += 1
                cuisine_display = "❌ Fermée"
            else:
                stats['cuisine']['not_determined'] += 1
                cuisine_display = "❓ Non déterminé"

            # Baignoire
            has_baignoire = baignoire_result.get('has_baignoire') if baignoire_result else None
            has_douche = baignoire_result.get('has_douche') if baignoire_result else None
            if has_baignoire:
                stats['baignoire']['has_baignoire'] += 1
                baignoire_display = "✅ Baignoire"
            elif has_douche:
                stats['baignoire']['has_douche'] += 1
                baignoire_display = "🚿 Douche"
            else:
                stats['baignoire']['not_determined'] += 1
                baignoire_display = "❓ Non déterminé"

            print(f"   📊 Vis-à-vis: {visavis_display} | Cuisine: {cuisine_display} | Baignoire: {baignoire_display}")

        except Exception as e:
            stats['errors'] += 1
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

        print()

    # Sauvegarder les résultats
    if output_file is None:
        output_file = input_file

    # Créer backup
    backup_file = f"{input_file}.backup_analyses_photos_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    print(f"💾 Backup créé: {backup_file}")

    # Sauvegarder les nouveaux résultats
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(apartments, f, ensure_ascii=False, indent=2)
    print(f"✅ Résultats sauvegardés: {output_file}")
    print()

    # Générer le récapitulatif Markdown
    recap_filename = f"RECAP_ANALYSES_PHOTOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    generate_complete_recap(apartments, stats, recap_filename)
    print(f"📄 Récapitulatif détaillé généré: {recap_filename}")

    # Afficher les statistiques
    print("📊 STATISTIQUES FINALES")
    print("=" * 60)
    print(f"Total analysé: {stats['total']}")
    print()
    print("VIS-À-VIS:")
    print(f"  ✅ Good (>20m): {stats['visavis']['good']} ({stats['visavis']['good']/stats['total']*100:.1f}%)")
    print(f"  ⚠️ Moyen (10-20m): {stats['visavis']['moyen']} ({stats['visavis']['moyen']/stats['total']*100:.1f}%)")
    print(f"  ❌ Bad (<10m): {stats['visavis']['bad']} ({stats['visavis']['bad']/stats['total']*100:.1f}%)")
    print(f"  ❓ Non déterminé: {stats['visavis']['not_determined']} ({stats['visavis']['not_determined']/stats['total']*100:.1f}%)")
    print()
    print("CUISINE:")
    print(f"  ✅ Ouverte: {stats['cuisine']['ouverte']} ({stats['cuisine']['ouverte']/stats['total']*100:.1f}%)")
    print(f"  ❌ Fermée: {stats['cuisine']['fermee']} ({stats['cuisine']['fermee']/stats['total']*100:.1f}%)")
    print(f"  ❓ Non déterminé: {stats['cuisine']['not_determined']} ({stats['cuisine']['not_determined']/stats['total']*100:.1f}%)")
    print()
    print("BAIGNOIRE:")
    print(f"  ✅ Baignoire: {stats['baignoire']['has_baignoire']} ({stats['baignoire']['has_baignoire']/stats['total']*100:.1f}%)")
    print(f"  🚿 Douche: {stats['baignoire']['has_douche']} ({stats['baignoire']['has_douche']/stats['total']*100:.1f}%)")
    print(f"  ❓ Non déterminé: {stats['baignoire']['not_determined']} ({stats['baignoire']['not_determined']/stats['total']*100:.1f}%)")
    print()
    print(f"📸 Sans photos: {stats['no_photos']} ({stats['no_photos']/stats['total']*100:.1f}%)")
    if stats['errors'] > 0:
        print(f"❌ Erreurs: {stats['errors']}")
    print()

    return True

def generate_complete_recap(apartments: List[Dict[str, Any]], stats: Dict, filename: str):
    """Génère un fichier Markdown récapitulatif complet des analyses."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    content = f"# 📊 Récapitulatif - Analyses Complètes (Vis-à-vis, Cuisine, Baignoire)\n\n"
    content += f"**Date**: {now}\n\n"
    content += f"## 📈 Statistiques Globales\n\n"
    content += f"- **Total analysé**: {stats['total']}\n"
    content += f"- **📸 Sans photos**: {stats['no_photos']} ({stats['no_photos']/stats['total']*100:.1f}%)\n\n"
    
    content += f"### Vis-à-vis\n"
    content += f"- **✅ Good (>20m)**: {stats['visavis']['good']} ({stats['visavis']['good']/stats['total']*100:.1f}%)\n"
    content += f"- **⚠️ Moyen (10-20m)**: {stats['visavis']['moyen']} ({stats['visavis']['moyen']/stats['total']*100:.1f}%)\n"
    content += f"- **❌ Bad (<10m)**: {stats['visavis']['bad']} ({stats['visavis']['bad']/stats['total']*100:.1f}%)\n"
    content += f"- **❓ Non déterminé**: {stats['visavis']['not_determined']} ({stats['visavis']['not_determined']/stats['total']*100:.1f}%)\n\n"
    
    content += f"### Cuisine\n"
    content += f"- **✅ Ouverte**: {stats['cuisine']['ouverte']} ({stats['cuisine']['ouverte']/stats['total']*100:.1f}%)\n"
    content += f"- **❌ Fermée**: {stats['cuisine']['fermee']} ({stats['cuisine']['fermee']/stats['total']*100:.1f}%)\n"
    content += f"- **❓ Non déterminé**: {stats['cuisine']['not_determined']} ({stats['cuisine']['not_determined']/stats['total']*100:.1f}%)\n\n"
    
    content += f"### Baignoire\n"
    content += f"- **✅ Baignoire**: {stats['baignoire']['has_baignoire']} ({stats['baignoire']['has_baignoire']/stats['total']*100:.1f}%)\n"
    content += f"- **🚿 Douche**: {stats['baignoire']['has_douche']} ({stats['baignoire']['has_douche']/stats['total']*100:.1f}%)\n"
    content += f"- **❓ Non déterminé**: {stats['baignoire']['not_determined']} ({stats['baignoire']['not_determined']/stats['total']*100:.1f}%)\n\n"
    
    content += f"## 🏠 Détails par Appartement\n\n"
    
    # Lister tous les appartements avec leurs analyses
    for apt in apartments:
        apt_id = apt.get('id', 'N/A')
        localisation = apt.get('localisation', 'N/A')
        
        content += f"### {apt_id} - {localisation}\n\n"
        
        # Vis-à-vis
        visavis_data = apt.get('exposition', {}).get('details', {})
        visavis_distance = visavis_data.get('visavis_distance')
        visavis_category = visavis_data.get('visavis_category')
        if visavis_distance is not None:
            content += f"- **Vis-à-vis**: {visavis_distance}m ({visavis_category})\n"
        else:
            content += f"- **Vis-à-vis**: Non déterminé\n"
        
        # Cuisine
        cuisine_data = apt.get('cuisine', {})
        cuisine_ouverte = cuisine_data.get('ouverte')
        if cuisine_ouverte is True:
            content += f"- **Cuisine**: ✅ Ouverte\n"
        elif cuisine_ouverte is False:
            content += f"- **Cuisine**: ❌ Fermée\n"
        else:
            content += f"- **Cuisine**: ❓ Non déterminé\n"
        
        # Baignoire
        baignoire_data = apt.get('baignoire', {})
        has_baignoire = baignoire_data.get('has_baignoire')
        has_douche = baignoire_data.get('has_douche')
        if has_baignoire:
            content += f"- **Baignoire**: ✅ Baignoire\n"
        elif has_douche:
            content += f"- **Baignoire**: 🚿 Douche\n"
        else:
            content += f"- **Baignoire**: ❓ Non déterminé\n"
        
        content += "\n"

    content += f"## 📝 Notes\n\n"
    content += f"- **Vis-à-vis**: Analyse effectuée uniquement depuis les fenêtres de la pièce principale (salon/séjour)\n"
    content += f"  - Good (>20m): pas de vis-à-vis ou très lointain\n"
    content += f"  - Moyen (10-20m): vis-à-vis visible mais distance confortable\n"
    content += f"  - Bad (<10m): vis-à-vis très proche, rue étroite\n"
    content += f"- **Cuisine**: Analyse des photos pour détecter si la cuisine est ouverte sur le salon\n"
    content += f"- **Baignoire**: Analyse des photos pour détecter la présence de baignoire ou douche\n\n"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--all' or sys.argv[1] == '-a':
            reanalyze_visavis_distance_batch()
        else:
            print("Usage: python3 reanalyze_visavis_distance.py [--all|-a]")
    else:
        print("⚠️  ATTENTION: Ce script va réanalyser TOUS les appartements pour:")
        print("   - Vis-à-vis (distance en mètres depuis la pièce principale)")
        print("   - Cuisine (ouverte/fermée)")
        print("   - Baignoire (présence baignoire/douche)")
        print("   Un backup sera créé automatiquement")
        print("   Utilisez --all ou -a pour lancer directement sans confirmation")
        print()
        try:
            response = input("Continuer ? (o/N): ")
            if response.lower() == 'o':
                reanalyze_visavis_distance_batch()
            else:
                print("❌ Annulé")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Annulé (mode non-interactif)")
            print("   Utilisez: python3 reanalyze_visavis_distance.py --all")

