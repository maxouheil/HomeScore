#!/usr/bin/env python3
"""
Script de debug pour tester la détection de localisation
"""

import json
import os
from scoring import score_localisation, load_scoring_config
from criteria.localisation import get_all_metro_stations

def test_localisation_detection():
    """Test la détection de localisation pour des appartements avec Rue des Boulets ou Nation"""
    
    print("🔍 TEST DE DÉTECTION LOCALISATION")
    print("=" * 60)
    
    # Charger la config
    config = load_scoring_config()
    if not config:
        print("❌ Impossible de charger scoring_config.json")
        return
    
    # Chercher des appartements avec "boulets" ou "nation"
    scored_file = 'data/scores/all_apartments_scores.json'
    if not os.path.exists(scored_file):
        print(f"❌ Fichier {scored_file} non trouvé")
        return
    
    with open(scored_file, 'r', encoding='utf-8') as f:
        scored_apartments = json.load(f)
    
    # Chercher les appartements problématiques
    problem_apartments = []
    for apt in scored_apartments:
        localisation = apt.get('localisation', '').lower()
        description = apt.get('description', '').lower()
        caracteristiques = apt.get('caracteristiques', '').lower()
        text = f"{localisation} {description} {caracteristiques}"
        
        if 'boulets' in text or 'nation' in text:
            problem_apartments.append(apt)
    
    print(f"📋 Trouvé {len(problem_apartments)} appartements avec 'boulets' ou 'nation'\n")
    
    if not problem_apartments:
        print("⚠️  Aucun appartement trouvé avec 'boulets' ou 'nation'")
        return
    
    # Tester les 3 premiers
    for i, apt in enumerate(problem_apartments[:3], 1):
        apt_id = apt.get('id', 'Unknown')
        print(f"\n{'='*60}")
        print(f"APPARTEMENT {i}: {apt_id}")
        print(f"{'='*60}")
        
        # Afficher les données pertinentes
        print(f"\n📝 DONNÉES:")
        print(f"   Localisation: {apt.get('localisation', 'N/A')}")
        print(f"   Description: {apt.get('description', 'N/A')[:200]}...")
        print(f"   Caractéristiques: {apt.get('caracteristiques', 'N/A')}")
        
        # Stations de métro
        all_stations = get_all_metro_stations(apt)
        print(f"\n🚇 STATIONS DE MÉTRO TROUVÉES:")
        for station in all_stations:
            print(f"   - {station}")
        
        # Quartier
        from criteria.localisation import get_quartier_name
        quartier = get_quartier_name(apt)
        print(f"\n📍 QUARTIER: {quartier or 'Non trouvé'}")
        
        # Score actuel
        scores_detaille = apt.get('scores_detaille', {})
        loc_score = scores_detaille.get('localisation', {})
        print(f"\n📊 SCORE ACTUEL:")
        print(f"   Score: {loc_score.get('score', 'N/A')}")
        print(f"   Tier: {loc_score.get('tier', 'N/A')}")
        print(f"   Justification: {loc_score.get('justification', 'N/A')}")
        
        # Recalculer avec la nouvelle fonction
        print(f"\n🔄 RECALCUL AVEC NOUVELLE FONCTION:")
        new_score = score_localisation(apt, config)
        print(f"   Score: {new_score.get('score', 'N/A')}")
        print(f"   Tier: {new_score.get('tier', 'N/A')}")
        print(f"   Justification: {new_score.get('justification', 'N/A')}")
        
        # Debug détaillé
        print(f"\n🔍 DEBUG DÉTAILLÉ:")
        localisation = apt.get('localisation', '').lower()
        description = apt.get('description', '').lower()
        caracteristiques = apt.get('caracteristiques', '').lower()
        text_combined = f"{localisation} {description} {caracteristiques}"
        
        tier2_zones = ['rue des boulets', 'nation']
        for zone in tier2_zones:
            in_localisation = zone in localisation
            in_text = zone in text_combined
            in_stations = any(zone in s.lower() or s.lower() in zone for s in all_stations)
            in_quartier = quartier and zone in quartier.lower() if quartier else False
            
            print(f"\n   Zone '{zone}':")
            print(f"      Dans localisation: {in_localisation}")
            print(f"      Dans texte combiné: {in_text}")
            print(f"      Dans stations: {in_stations}")
            print(f"      Dans quartier: {in_quartier}")
            
            if in_localisation or in_text or in_stations or in_quartier:
                print(f"      ✅ DÉTECTÉ!")
            else:
                print(f"      ❌ NON DÉTECTÉ")
                # Afficher le texte autour pour debug
                if zone in text_combined:
                    idx = text_combined.find(zone)
                    print(f"      Contexte: ...{text_combined[max(0, idx-50):idx+len(zone)+50]}...")

if __name__ == "__main__":
    test_localisation_detection()


