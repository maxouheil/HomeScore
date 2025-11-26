#!/usr/bin/env python3
"""
Script pour relancer l'analyse du vis-à-vis depuis les photos
sur tous les appartements existants
"""

import json
import os
from extract_exposition import ExpositionExtractor
from datetime import datetime

def reanalyze_visavis_batch(input_file="data/scraped_apartments.json", output_file=None):
    """Relance l'analyse du vis-à-vis sur tous les appartements"""
    
    print("🔄 RE-ANALYSE DU VIS-À-VIS")
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
        'visavis_good': 0,
        'visavis_moyen': 0,
        'visavis_bad': 0,
        'visavis_none': 0,
        'no_photos': 0,
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
            # Extraire les URLs des photos
            photos = apartment.get('photos', [])
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
                print(f"   ⚠️  Aucune photo disponible")
                print()
                continue
            
            print(f"   📸 {len(photo_urls)} photos disponibles")
            
            # Analyser le vis-à-vis
            visavis_result = extractor.photo_analyzer.analyze_photos_visavis(photo_urls)
            
            if visavis_result and visavis_result.get('photos_analyzed', 0) > 0:
                visavis_value = visavis_result.get('visavis')
                confidence = visavis_result.get('confidence', 0.0)
                justification = visavis_result.get('justification', '')
                
                # Mettre à jour l'exposition avec le vis-à-vis
                if 'exposition' not in apartment:
                    apartment['exposition'] = {}
                if 'details' not in apartment['exposition']:
                    apartment['exposition']['details'] = {}
                
                apartment['exposition']['details']['visavis'] = visavis_value
                apartment['exposition']['details']['visavis_confidence'] = confidence
                apartment['exposition']['details']['visavis_justification'] = justification
                
                # Statistiques
                if visavis_value == 'good':
                    stats['visavis_good'] += 1
                    emoji = '✅'
                elif visavis_value == 'moyen':
                    stats['visavis_moyen'] += 1
                    emoji = '⚠️'
                elif visavis_value == 'bad':
                    stats['visavis_bad'] += 1
                    emoji = '❌'
                else:
                    stats['visavis_none'] += 1
                    emoji = '❓'
                
                print(f"   {emoji} Vis-à-vis: {visavis_value} (confiance: {confidence:.0%})")
                print(f"   💬 {justification[:80]}...")
            else:
                stats['visavis_none'] += 1
                print(f"   ❓ Vis-à-vis non déterminé")
            
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
    backup_file = f"{input_file}.backup_visavis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
    print(f"✅ Vis-à-vis good: {stats['visavis_good']} ({stats['visavis_good']/stats['total']*100:.1f}%)")
    print(f"⚠️  Vis-à-vis moyen: {stats['visavis_moyen']} ({stats['visavis_moyen']/stats['total']*100:.1f}%)")
    print(f"❌ Vis-à-vis bad: {stats['visavis_bad']} ({stats['visavis_bad']/stats['total']*100:.1f}%)")
    print(f"❓ Vis-à-vis non déterminé: {stats['visavis_none']} ({stats['visavis_none']/stats['total']*100:.1f}%)")
    print(f"📸 Sans photos: {stats['no_photos']} ({stats['no_photos']/stats['total']*100:.1f}%)")
    if stats['errors'] > 0:
        print(f"❌ Erreurs: {stats['errors']}")
    print()
    
    # Générer un récapitulatif détaillé
    generate_recap(apartments, stats)
    
    return True

def generate_recap(apartments, stats):
    """Génère un récapitulatif détaillé des résultats"""
    recap_file = f"RECAP_VISAVIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(recap_file, 'w', encoding='utf-8') as f:
        f.write("# 📊 Récapitulatif - Analyse du Vis-à-vis\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 📈 Statistiques Globales\n\n")
        f.write(f"- **Total analysé**: {stats['total']}\n")
        f.write(f"- **✅ Vis-à-vis good**: {stats['visavis_good']} ({stats['visavis_good']/stats['total']*100:.1f}%)\n")
        f.write(f"- **⚠️ Vis-à-vis moyen**: {stats['visavis_moyen']} ({stats['visavis_moyen']/stats['total']*100:.1f}%)\n")
        f.write(f"- **❌ Vis-à-vis bad**: {stats['visavis_bad']} ({stats['visavis_bad']/stats['total']*100:.1f}%)\n")
        f.write(f"- **❓ Non déterminé**: {stats['visavis_none']} ({stats['visavis_none']/stats['total']*100:.1f}%)\n")
        f.write(f"- **📸 Sans photos**: {stats['no_photos']} ({stats['no_photos']/stats['total']*100:.1f}%)\n\n")
        
        if stats['errors'] > 0:
            f.write(f"- **❌ Erreurs**: {stats['errors']}\n\n")
        
        f.write("## 🏠 Détails par Appartement\n\n")
        
        # Grouper par vis-à-vis
        by_visavis = {
            'good': [],
            'moyen': [],
            'bad': [],
            'none': []
        }
        
        for apt in apartments:
            visavis = apt.get('exposition', {}).get('details', {}).get('visavis')
            if visavis in by_visavis:
                by_visavis[visavis].append(apt)
            else:
                by_visavis['none'].append(apt)
        
        # Écrire les détails par catégorie
        for category, apts in by_visavis.items():
            if not apts:
                continue
            
            emoji_map = {'good': '✅', 'moyen': '⚠️', 'bad': '❌', 'none': '❓'}
            emoji = emoji_map.get(category, '❓')
            title_map = {'good': 'Good (pas de vis-à-vis ou très lointain)', 
                        'moyen': 'Moyen (vis-à-vis >20m, rue large)',
                        'bad': 'Bad (vis-à-vis très proche, rue étroite)',
                        'none': 'Non déterminé'}
            title = title_map.get(category, category)
            
            f.write(f"### {emoji} {title} ({len(apts)} appartements)\n\n")
            
            for apt in apts[:20]:  # Limiter à 20 par catégorie
                apt_id = apt.get('id', 'N/A')
                localisation = apt.get('localisation', 'N/A')
                visavis_details = apt.get('exposition', {}).get('details', {})
                visavis_value = visavis_details.get('visavis', 'N/A')
                confidence = visavis_details.get('visavis_confidence', 0.0)
                justification = visavis_details.get('visavis_justification', 'N/A')
                
                f.write(f"- **{apt_id}** - {localisation}\n")
                f.write(f"  - Vis-à-vis: {visavis_value} (confiance: {confidence:.0%})\n")
                f.write(f"  - {justification[:100]}\n\n")
            
            if len(apts) > 20:
                f.write(f"*... et {len(apts) - 20} autres*\n\n")
        
        f.write("## 📝 Notes\n\n")
        f.write("- **Good**: pas de vis-à-vis, ou très lointain\n")
        f.write("- **Moyen**: vis-à-vis visible mais plus de 20m, rue large\n")
        f.write("- **Bad**: vis-à-vis très proche, rue étroite\n\n")
    
    print(f"📄 Récapitulatif détaillé généré: {recap_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all' or sys.argv[1] == '-a':
            # Réanalyser tous les appartements (pas de confirmation)
            reanalyze_visavis_batch()
        elif sys.argv[1] == '--force' or sys.argv[1] == '-f':
            # Force mode (pas de confirmation)
            reanalyze_visavis_batch()
        else:
            # Utiliser un fichier spécifique
            input_file = sys.argv[1]
            reanalyze_visavis_batch(input_file=input_file)
    else:
        # Réanalyser tous les appartements
        print("⚠️  ATTENTION: Ce script va réanalyser le vis-à-vis pour TOUS les appartements")
        print("   Un backup sera créé automatiquement")
        print("   Utilisez --all ou -a pour lancer directement sans confirmation")
        print()
        try:
            response = input("Continuer ? (o/N): ")
            if response.lower() == 'o':
                reanalyze_visavis_batch()
            else:
                print("❌ Annulé")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Annulé (mode non-interactif)")
            print("   Utilisez: python3 reanalyze_visavis.py --all")




