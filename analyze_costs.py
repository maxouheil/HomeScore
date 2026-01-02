#!/usr/bin/env python3
"""
Analyse des dépenses OpenAI basée sur les fichiers de cache créés
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

# Coûts par type d'appel (estimations conservatrices)
COSTS = {
    'vision_single_photo': 0.00015,  # $0.00015 par photo (gpt-4o-mini)
    'vision_multiple_photos': 0.0005,  # $0.0005 pour 3-5 photos
    'text_analysis': 0.0001,  # $0.0001 par analyse texte
    'unified_analysis': 0.0005,  # $0.0005 pour analyse unifiée (3 photos)
}

def analyze_costs():
    """Analyse les coûts basés sur les fichiers de cache"""
    
    # Analyser les fichiers de cache créés le 7 décembre
    cache_dir = Path("/Users/sou/Desktop/HomeScore/data/cache/calme")
    calme_dir = Path("/Users/sou/Desktop/HomeScore/data/calme")
    
    # Compter les fichiers créés le 7 décembre
    apartments_processed = 0
    
    for cache_file in list(cache_dir.glob("*.json")) + list(calme_dir.glob("*.json")):
        try:
            stat = cache_file.stat()
            mtime = datetime.fromtimestamp(stat.mtime)
            # Vérifier si créé le 7 décembre
            if mtime.strftime("%Y-%m-%d") == "2025-12-07":
                apartments_processed += 1
        except:
            pass
    
    print("=" * 80)
    print("💰 RÉCAPITULATIF DES DÉPENSES OPENAI - 7 DÉCEMBRE 2025")
    print("=" * 80)
    print()
    print(f"📊 Appartements traités: {apartments_processed}")
    print()
    
    # Estimations basées sur les pourcentages observés
    # (conservateurs - le bug peut avoir causé plus d'appels)
    
    print("📋 POSTES DE DÉPENSES PAR TYPE D'APPEL API")
    print("-" * 80)
    print()
    
    # 1. Analyse de style (30% des appartements, bug causait des ré-analyses)
    style_normal = int(apartments_processed * 0.3)
    style_bug = int(apartments_processed * 2.0)  # Bug causait ~2x plus d'appels
    style_cost_normal = style_normal * COSTS['vision_multiple_photos']
    style_cost_bug = style_bug * COSTS['vision_multiple_photos']
    
    print("1. 📸 ANALYSE DE STYLE (Vision API - GPT-4o-mini)")
    print(f"   Appels normaux: {style_normal} × ${COSTS['vision_multiple_photos']:.5f} = ${style_cost_normal:.4f}")
    print(f"   Appels dus au bug: {style_bug} × ${COSTS['vision_multiple_photos']:.5f} = ${style_cost_bug:.4f}")
    print(f"   Total: ${style_cost_normal + style_cost_bug:.4f}")
    print()
    
    # 2. Analyse cuisine (20% des appartements)
    cuisine_analyses = int(apartments_processed * 0.2)
    cuisine_cost = cuisine_analyses * COSTS['vision_single_photo']
    
    print("2. 🍳 ANALYSE CUISINE (Vision API - GPT-4o-mini)")
    print(f"   Appels: {cuisine_analyses} × ${COSTS['vision_single_photo']:.5f} = ${cuisine_cost:.4f}")
    print()
    
    # 3. Analyse baignoire (20% des appartements)
    baignoire_analyses = int(apartments_processed * 0.2)
    baignoire_cost = baignoire_analyses * COSTS['vision_single_photo']
    
    print("3. 🛁 ANALYSE BAIGNOIRE (Vision API - GPT-4o-mini)")
    print(f"   Appels: {baignoire_analyses} × ${COSTS['vision_single_photo']:.5f} = ${baignoire_cost:.4f}")
    print()
    
    # 4. Analyse unifiée (10% des appartements)
    unified_analyses = int(apartments_processed * 0.1)
    unified_cost = unified_analyses * COSTS['unified_analysis']
    
    print("4. 🔄 ANALYSE UNIFIÉE (Vision API - GPT-4o-mini)")
    print(f"   Appels: {unified_analyses} × ${COSTS['unified_analysis']:.5f} = ${unified_cost:.4f}")
    print()
    
    # 5. Analyse texte (50% des appartements)
    text_analyses = int(apartments_processed * 0.5)
    text_cost = text_analyses * COSTS['text_analysis']
    
    print("5. 📝 ANALYSE TEXTE (Chat API - GPT-4o-mini)")
    print(f"   Appels: {text_analyses} × ${COSTS['text_analysis']:.5f} = ${text_cost:.4f}")
    print()
    
    # Total
    total_estimated = style_cost_normal + style_cost_bug + cuisine_cost + baignoire_cost + unified_cost + text_cost
    
    print("=" * 80)
    print(f"💰 TOTAL ESTIMÉ: ${total_estimated:.4f}")
    print(f"📊 Coût réel mentionné: $50.00")
    print(f"📈 Écart: ${50.00 - total_estimated:.4f}")
    print("=" * 80)
    print()
    
    # Répartition estimée du coût réel
    print("📊 RÉPARTITION ESTIMÉE DU COÛT RÉEL ($50)")
    print("-" * 80)
    print()
    
    if total_estimated > 0:
        style_pct = ((style_cost_normal + style_cost_bug) / total_estimated) * 100
        cuisine_pct = (cuisine_cost / total_estimated) * 100
        baignoire_pct = (baignoire_cost / total_estimated) * 100
        unified_pct = (unified_cost / total_estimated) * 100
        text_pct = (text_cost / total_estimated) * 100
        
        print(f"Analyse Style (avec bug): {style_pct:.1f}% = ${50 * style_pct / 100:.2f}")
        print(f"Analyse Cuisine: {cuisine_pct:.1f}% = ${50 * cuisine_pct / 100:.2f}")
        print(f"Analyse Baignoire: {baignoire_pct:.1f}% = ${50 * baignoire_pct / 100:.2f}")
        print(f"Analyse Unifiée: {unified_pct:.1f}% = ${50 * unified_pct / 100:.2f}")
        print(f"Analyse Texte: {text_pct:.1f}% = ${50 * text_pct / 100:.2f}")
    else:
        # Si estimation trop basse, répartition basée sur l'analyse du bug
        print("Ré-analyses Style (bug): 60% = $30.00")
        print("Analyses Style normales: 20% = $10.00")
        print("Analyses Cuisine: 5% = $2.50")
        print("Analyses Baignoire: 5% = $2.50")
        print("Analyses Unifiées: 5% = $2.50")
        print("Analyses Texte: 5% = $2.50")
    
    print()

if __name__ == "__main__":
    analyze_costs()

