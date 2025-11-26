#!/usr/bin/env python3
"""
Script de débogage pour comprendre pourquoi certains appartements reçoivent 20 points
alors qu'ils devraient être en Tier 2 (10 points)
"""

import json
import os
from scoring import score_localisation, load_scoring_config
from criteria.localisation import get_quartier_name, get_all_metro_stations


def debug_apartment_scoring(apartment_data, apartment_id="test"):
    """Débogue le scoring d'un appartement"""
    print(f"\n{'='*60}")
    print(f"🔍 DÉBOGAGE SCORING LOCALISATION - Appartement {apartment_id}")
    print(f"{'='*60}\n")
    
    config = load_scoring_config()
    tier_config = config['axes']['localisation']['tiers']
    
    # Afficher la configuration
    print("📋 CONFIGURATION:")
    print(f"   Tier 1 zones: {tier_config['tier1']['zones']}")
    print(f"   Tier 2 zones: {tier_config['tier2']['zones']}")
    print()
    
    # Extraire les données
    localisation = apartment_data.get('localisation', '').lower()
    description = apartment_data.get('description', '').lower()
    caracteristiques = apartment_data.get('caracteristiques', '').lower()
    text_combined = f"{localisation} {description} {caracteristiques}"
    
    quartier = get_quartier_name(apartment_data)
    if quartier:
        quartier = quartier.lower()
    
    all_stations = get_all_metro_stations(apartment_data)
    all_stations_lower = [s.lower() for s in all_stations] if all_stations else []
    
    print("📊 DONNÉES DE L'APPARTEMENT:")
    print(f"   Localisation: '{apartment_data.get('localisation', '')}'")
    print(f"   Quartier: '{quartier if quartier else 'Non trouvé'}'")
    print(f"   Stations de métro: {all_stations}")
    print(f"   Description (extrait): '{description[:100]}...'")
    print()
    
    # Vérifier Tier 1
    print("🔍 VÉRIFICATION TIER 1:")
    tier1_zones = [z.lower() for z in tier_config['tier1']['zones']]
    tier1_matches = []
    
    for zone in tier1_zones:
        matched = False
        match_reason = []
        
        # Vérifier dans localisation
        if zone in localisation:
            matched = True
            match_reason.append(f"zone '{zone}' trouvée dans localisation")
        
        # Vérifier dans texte combiné
        if zone in text_combined:
            matched = True
            match_reason.append(f"zone '{zone}' trouvée dans description/caractéristiques")
        
        # Vérifier dans quartier
        if quartier and zone in quartier:
            matched = True
            match_reason.append(f"zone '{zone}' trouvée dans quartier")
        
        # Vérifier dans stations
        for station in all_stations_lower:
            if zone in station or station in zone:
                matched = True
                match_reason.append(f"zone '{zone}' matche avec station '{station}'")
                break
        
        if matched:
            tier1_matches.append({
                'zone': zone,
                'reasons': match_reason
            })
            print(f"   ✅ MATCH: '{zone}'")
            for reason in match_reason:
                print(f"      → {reason}")
    
    if not tier1_matches:
        print("   ❌ Aucun match Tier 1")
    
    print()
    
    # Vérifier Tier 2
    print("🔍 VÉRIFICATION TIER 2:")
    tier2_zones = [z.lower() for z in tier_config['tier2']['zones']]
    tier2_matches = []
    
    for zone in tier2_zones:
        matched = False
        match_reason = []
        
        # Vérifier dans localisation
        if zone in localisation:
            matched = True
            match_reason.append(f"zone '{zone}' trouvée dans localisation")
        
        # Vérifier dans texte combiné
        if zone in text_combined:
            matched = True
            match_reason.append(f"zone '{zone}' trouvée dans description/caractéristiques")
        
        # Vérifier dans quartier
        if quartier and zone in quartier:
            matched = True
            match_reason.append(f"zone '{zone}' trouvée dans quartier")
        
        # Vérifier dans stations
        for station in all_stations_lower:
            if zone in station or station in zone:
                matched = True
                match_reason.append(f"zone '{zone}' matche avec station '{station}'")
                break
        
        if matched:
            tier2_matches.append({
                'zone': zone,
                'reasons': match_reason
            })
            print(f"   ✅ MATCH: '{zone}'")
            for reason in match_reason:
                print(f"      → {reason}")
    
    if not tier2_matches:
        print("   ❌ Aucun match Tier 2")
    
    print()
    
    # Calculer le score réel
    print("📊 RÉSULTAT DU SCORING:")
    result = score_localisation(apartment_data, config)
    print(f"   Score: {result['score']} points")
    print(f"   Tier: {result['tier']}")
    print(f"   Justification: {result['justification']}")
    print()
    
    # Analyse du problème
    if result['tier'] == 'tier1' and tier2_matches:
        print("⚠️  PROBLÈME DÉTECTÉ:")
        print(f"   L'appartement devrait être Tier 2 (zones trouvées: {[m['zone'] for m in tier2_matches]})")
        print(f"   Mais il reçoit Tier 1 (score: {result['score']} points)")
        if tier1_matches:
            print(f"   Raison: Match Tier 1 trouvé en premier: {[m['zone'] for m in tier1_matches]}")
            print(f"   → Le système vérifie Tier 1 AVANT Tier 2, donc le premier match gagne")
        else:
            print(f"   ⚠️  Aucun match Tier 1 trouvé mais score Tier 1 attribué - BUG!")
    elif result['tier'] == 'tier2' and result['score'] == 20:
        print("⚠️  PROBLÈME DÉTECTÉ:")
        print(f"   Tier 2 mais score de 20 points (devrait être 10 points)")
    elif result['tier'] == 'tier1' and not tier1_matches:
        print("⚠️  PROBLÈME DÉTECTÉ:")
        print(f"   Tier 1 attribué mais aucun match Tier 1 trouvé - BUG!")
    
    return result


def test_specific_cases():
    """Test des cas spécifiques du problème"""
    
    # Cas 1: Pyrénées + Combat (devrait être Tier 2 = 10 points)
    print("\n" + "="*60)
    print("TEST 1: Pyrénées + Combat")
    print("="*60)
    
    apt1 = {
        'id': 'test1',
        'localisation': 'Paris (75020)',
        'map_info': {
            'quartier': 'Combat',
            'metros': ['Pyrénées']
        },
        'transports': ['Métro Pyrénées'],
        'description': 'Appartement proche du métro Pyrénées dans le quartier Combat',
        'caracteristiques': ''
    }
    
    debug_apartment_scoring(apt1, "Pyrénées + Combat")
    
    # Cas 2: Ménilmontant (devrait être Tier 1 = 20 points) ✓
    print("\n" + "="*60)
    print("TEST 2: Ménilmontant")
    print("="*60)
    
    apt2 = {
        'id': 'test2',
        'localisation': 'Paris (75020)',
        'map_info': {
            'quartier': 'Ménilmontant',
            'metros': ['Ménilmontant']
        },
        'transports': ['Métro Ménilmontant'],
        'description': 'Appartement proche du métro Ménilmontant',
        'caracteristiques': ''
    }
    
    debug_apartment_scoring(apt2, "Ménilmontant")
    
    # Cas 3: Pere Lachaise + Rue Saint-Maur (devrait vérifier)
    print("\n" + "="*60)
    print("TEST 3: Pere Lachaise + Rue Saint-Maur")
    print("="*60)
    
    apt3 = {
        'id': 'test3',
        'localisation': 'Paris (75020)',
        'map_info': {
            'quartier': 'Pere lachaise',
            'metros': ['Rue Saint-Maur']
        },
        'transports': ['Métro Rue Saint-Maur'],
        'description': 'Appartement proche du métro Rue Saint-Maur dans le quartier Pere Lachaise',
        'caracteristiques': ''
    }
    
    debug_apartment_scoring(apt3, "Pere Lachaise + Rue Saint-Maur")


if __name__ == "__main__":
    test_specific_cases()




