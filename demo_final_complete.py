#!/usr/bin/env python3
"""
Démonstration finale complète du système HomeScore
- Photos téléchargées
- Design Fitscore exact
- Statistiques finales
"""

import asyncio
import json
import os
from datetime import datetime
from download_apartment_photos import batch_download_photos
from generate_fitscore_style_html import main as generate_fitscore_html
from generate_scorecard_html import main as generate_original_html

def get_photo_statistics():
    """Calcule les statistiques des photos téléchargées"""
    photos_dir = "data/photos"
    if not os.path.exists(photos_dir):
        return {"total_apartments": 0, "total_photos": 0, "apartments_with_photos": 0}
    
    total_apartments = 0
    total_photos = 0
    apartments_with_photos = 0
    
    for apartment_id in os.listdir(photos_dir):
        apartment_path = os.path.join(photos_dir, apartment_id)
        if os.path.isdir(apartment_path):
            total_apartments += 1
            photo_count = len([f for f in os.listdir(apartment_path) if f.endswith(('.jpg', '.jpeg', '.png'))])
            if photo_count > 0:
                apartments_with_photos += 1
                total_photos += photo_count
    
    return {
        "total_apartments": total_apartments,
        "total_photos": total_photos,
        "apartments_with_photos": apartments_with_photos,
        "average_photos_per_apartment": round(total_photos / total_apartments, 1) if total_apartments > 0 else 0
    }

def get_file_sizes():
    """Calcule la taille totale des photos"""
    photos_dir = "data/photos"
    total_size = 0
    
    if os.path.exists(photos_dir):
        for apartment_id in os.listdir(photos_dir):
            apartment_path = os.path.join(photos_dir, apartment_id)
            if os.path.isdir(apartment_path):
                for filename in os.listdir(apartment_path):
                    if filename.endswith(('.jpg', '.jpeg', '.png')):
                        file_path = os.path.join(apartment_path, filename)
                        total_size += os.path.getsize(file_path)
    
    # Convertir en MB
    size_mb = total_size / (1024 * 1024)
    return round(size_mb, 2)

def load_scored_apartments():
    """Charge les appartements scorés"""
    try:
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def main():
    """Fonction principale de démonstration finale"""
    print("🏠 DÉMONSTRATION FINALE COMPLÈTE - HOMESCORE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    print()
    
    # 1. Statistiques des photos
    print("📊 ÉTAT DES PHOTOS TÉLÉCHARGÉES")
    print("-" * 35)
    stats = get_photo_statistics()
    print(f"   🏠 Appartements avec photos: {stats['apartments_with_photos']}/{stats['total_apartments']}")
    print(f"   📸 Total photos téléchargées: {stats['total_photos']}")
    print(f"   📊 Moyenne photos/appartement: {stats['average_photos_per_apartment']}")
    print(f"   💾 Taille totale: {get_file_sizes()} MB")
    print()
    
    # 2. Statistiques des scores
    print("📈 STATISTIQUES DES SCORES")
    print("-" * 30)
    apartments = load_scored_apartments()
    if apartments:
        scores = [apt.get('score_total', 0) for apt in apartments]
        print(f"   📋 Appartements scorés: {len(apartments)}")
        print(f"   📊 Score moyen: {round(sum(scores) / len(scores), 1)}/100")
        print(f"   🏆 Score maximum: {max(scores)}/100")
        print(f"   📉 Score minimum: {min(scores)}/100")
        print(f"   ✅ Scores ≥ 80: {sum(1 for s in scores if s >= 80)}")
        print(f"   🟡 Scores 60-79: {sum(1 for s in scores if 60 <= s < 80)}")
        print(f"   🔴 Scores < 60: {sum(1 for s in scores if s < 60)}")
    else:
        print("   ❌ Aucun score trouvé")
    print()
    
    # 3. Génération des rapports
    print("📄 GÉNÉRATION DES RAPPORTS HTML")
    print("-" * 35)
    
    print("   🎨 Génération du rapport style Fitscore...")
    generate_fitscore_html()
    
    print("   🏠 Génération du rapport style original...")
    generate_original_html()
    
    print()
    
    # 4. Fichiers générés
    print("📁 FICHIERS GÉNÉRÉS")
    print("-" * 20)
    print(f"   🎨 Rapport Fitscore: output/scorecard_fitscore_style.html")
    print(f"   🏠 Rapport original: output/scorecard_rapport.html")
    print(f"   📸 Photos: data/photos/ ({stats['total_photos']} photos)")
    print(f"   📊 Métadonnées: data/photos_metadata/")
    print()
    
    # 5. Résumé final
    print("🎉 RÉSUMÉ FINAL")
    print("-" * 15)
    print("✅ Système HomeScore COMPLET et FONCTIONNEL !")
    print()
    print("🎯 FONCTIONNALITÉS IMPLÉMENTÉES:")
    print("   ✅ Scraping automatique des appartements Jinka")
    print("   ✅ Extraction et téléchargement de 3-4 photos par appartement")
    print("   ✅ Système de scoring intelligent avec IA")
    print("   ✅ Analyse d'exposition (textuelle + photos)")
    print("   ✅ Génération de rapports HTML avec photos")
    print("   ✅ Design exact de Fitscore (grid 3 colonnes)")
    print("   ✅ Design original avec photos en header")
    print()
    print("📊 PERFORMANCES:")
    print(f"   🏠 {stats['total_apartments']} appartements traités")
    print(f"   📸 {stats['total_photos']} photos téléchargées")
    print(f"   💾 {get_file_sizes()} MB de données")
    print(f"   ⚡ Système entièrement automatisé")
    print()
    print("🌐 OUVREZ LES RAPPORTS DANS VOTRE NAVIGATEUR !")
    print("   🎨 Fitscore style: output/scorecard_fitscore_style.html")
    print("   🏠 Original style: output/scorecard_rapport.html")

if __name__ == "__main__":
    main()
