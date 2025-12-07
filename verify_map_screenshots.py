#!/usr/bin/env python3
"""
Script pour vérifier que les screenshots de carte sont bien associés aux bons appartements
"""

import json
import os
import re
from pathlib import Path

def verify_map_screenshots():
    """Vérifie que les screenshots de carte sont bien associés aux bons appartements"""
    print("🔍 VÉRIFICATION DES ASSOCIATIONS SCREENSHOT-APPARTEMENT")
    print("=" * 70)
    
    apartments_dir = Path("data/appartements")
    screenshots_dir = Path("data/screenshots")
    
    if not apartments_dir.exists():
        print("❌ Dossier data/appartements non trouvé")
        return
    
    if not screenshots_dir.exists():
        print("❌ Dossier data/screenshots non trouvé")
        return
    
    # Récupérer tous les fichiers JSON d'appartements
    apartment_files = list(apartments_dir.glob("*.json"))
    print(f"📋 {len(apartment_files)} fichiers d'appartements trouvés\n")
    
    results = {
        'correct': [],
        'incorrect': [],
        'missing': [],
        'old_format': []
    }
    
    for apt_file in apartment_files:
        try:
            with open(apt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            apt_id = data.get('id', 'unknown')
            screenshot_path = data.get('map_info', {}).get('screenshot')
            
            if not screenshot_path or screenshot_path == 'N/A':
                results['missing'].append((apt_id, apt_file.name, 'Aucun screenshot'))
                continue
            
            # Extraire le nom du fichier du screenshot
            screenshot_filename = os.path.basename(screenshot_path)
            
            # Vérifier si c'est l'ancien format (sans ID) ou le nouveau format (avec ID)
            if re.match(r'map_\d{8}_\d{6}\.png$', screenshot_filename):
                # Ancien format : map_YYYYMMDD_HHMMSS.png
                results['old_format'].append((apt_id, apt_file.name, screenshot_filename))
            elif re.match(r'map_\d+_\d{8}_\d{6}\.png$', screenshot_filename):
                # Nouveau format : map_ID_YYYYMMDD_HHMMSS.png
                # Extraire l'ID du nom du fichier
                match = re.match(r'map_(\d+)_(\d{8}_\d{6})\.png$', screenshot_filename)
                if match:
                    screenshot_id = match.group(1)
                    
                    # Vérifier que l'ID correspond
                    if apt_id == screenshot_id:
                        # Vérifier que le fichier existe
                        full_path = screenshots_dir / screenshot_filename
                        if full_path.exists():
                            size = full_path.stat().st_size
                            results['correct'].append((apt_id, apt_file.name, screenshot_filename, size))
                        else:
                            results['missing'].append((apt_id, apt_file.name, f"Screenshot non trouvé: {screenshot_filename}"))
                    else:
                        results['incorrect'].append((apt_id, apt_file.name, screenshot_filename, f"ID mismatch: appartement={apt_id}, screenshot={screenshot_id}"))
                else:
                    results['incorrect'].append((apt_id, apt_file.name, screenshot_filename, "Format invalide"))
            else:
                results['incorrect'].append((apt_id, apt_file.name, screenshot_filename, "Format inconnu"))
                
        except Exception as e:
            print(f"⚠️ Erreur lecture {apt_file.name}: {e}")
    
    # Afficher les résultats
    print(f"✅ ASSOCIATIONS CORRECTES: {len(results['correct'])}")
    if results['correct']:
        for apt_id, filename, screenshot, size in results['correct']:
            print(f"   ✅ {filename} (ID: {apt_id}) → {screenshot} ({size:,} bytes)")
    
    print(f"\n⚠️ ANCIEN FORMAT (sans ID): {len(results['old_format'])}")
    if results['old_format']:
        for apt_id, filename, screenshot in results['old_format'][:5]:
            print(f"   ⚠️ {filename} (ID: {apt_id}) → {screenshot} (ancien format)")
        if len(results['old_format']) > 5:
            print(f"   ... et {len(results['old_format']) - 5} autres")
    
    print(f"\n❌ ASSOCIATIONS INCORRECTES: {len(results['incorrect'])}")
    if results['incorrect']:
        for apt_id, filename, screenshot, reason in results['incorrect']:
            print(f"   ❌ {filename} (ID: {apt_id}) → {screenshot}")
            print(f"      Raison: {reason}")
    
    print(f"\n⚠️ SCREENSHOTS MANQUANTS: {len(results['missing'])}")
    if results['missing']:
        for apt_id, filename, reason in results['missing']:
            print(f"   ⚠️ {filename} (ID: {apt_id}) → {reason}")
    
    # Résumé
    print(f"\n{'='*70}")
    print("📊 RÉSUMÉ")
    print(f"{'='*70}")
    total = len(apartment_files)
    correct = len(results['correct'])
    old_format = len(results['old_format'])
    incorrect = len(results['incorrect'])
    missing = len(results['missing'])
    
    print(f"Total: {total}")
    print(f"✅ Correct (nouveau format avec ID): {correct} ({100*correct/total:.1f}%)")
    print(f"⚠️ Ancien format (sans ID): {old_format} ({100*old_format/total:.1f}%)")
    print(f"❌ Incorrect: {incorrect} ({100*incorrect/total:.1f}%)")
    print(f"⚠️ Manquant: {missing} ({100*missing/total:.1f}%)")
    
    if correct == total - old_format - incorrect - missing:
        print("\n🎉 Tous les nouveaux screenshots sont correctement associés !")
        if old_format > 0:
            print(f"💡 {old_format} appartements ont encore l'ancien format (scrapés avant la correction)")
    else:
        print("\n⚠️ Certaines associations sont incorrectes")
    
    return results

if __name__ == "__main__":
    verify_map_screenshots()

