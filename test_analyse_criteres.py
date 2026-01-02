#!/usr/bin/env python3
"""
Script de test pour analyser un appartement et afficher chaque critère
avec le format exact spécifié dans generate_scorecard_html.py
"""

import json
import sys
from project_config import APARTMENTS_FILE
from generate_scorecard_html import (
    format_localisation_criterion,
    format_prix_criterion,
    format_style_criterion,
    format_exposition_criterion,
    format_cuisine_criterion,
    format_baignoire_criterion,
    _get_baignoire_extractor
)


def afficher_critere(nom, resultat):
    """Affiche un critère formaté"""
    print(f"\n{'='*80}")
    print(f"CRITÈRE: {nom.upper()}")
    print(f"{'='*80}")
    print(f"Valeur principale: {resultat.get('main_value', 'N/A')}")
    if resultat.get('confidence') is not None:
        print(f"Confiance: {resultat.get('confidence')}%")
    if resultat.get('indices'):
        print(f"Indices:\n{resultat.get('indices')}")
    print(f"{'='*80}")


def analyser_appartement_test(apartment_id=None, recherche="Paris 20e - 69m² - 3p", apartment_data=None):
    """Analyse un appartement et affiche tous les critères formatés"""
    
    # Si des données d'appartement sont fournies directement, les utiliser
    if apartment_data:
        apartment = apartment_data
        print("ℹ️  Utilisation des données fournies directement")
    else:
        # Charger les données
        with open(APARTMENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Trouver l'appartement
        apartment = None
        if apartment_id:
            apartment = next((a for a in data if str(a.get('id')) == str(apartment_id)), None)
        else:
            # Chercher par critères - chercher d'abord exact, puis proche
            recherche_lower = recherche.lower()
            candidats = []
            
            for apt in data:
                localisation = str(apt.get('localisation', '')).lower()
                surface_str = str(apt.get('surface', ''))
                pieces = str(apt.get('pieces', ''))
                
                # Extraire la surface en nombre
                import re
                surface_match = re.search(r'(\d+)', surface_str)
                surface_num = int(surface_match.group(1)) if surface_match else 0
                
                # Vérifier les critères
                is_20e = '20' in localisation or '20e' in localisation
                is_3p = '3' in pieces
                is_69 = surface_num == 69
                is_proche_69 = 65 <= surface_num <= 75  # Proche de 69m²
                
                if is_20e and is_3p:
                    if is_69:
                        # Exact match - priorité
                        apartment = apt
                        break
                    elif is_proche_69:
                        # Proche de 69m² - ajouter aux candidats
                        candidats.append((abs(surface_num - 69), apt))
            
            # Si pas d'exact match, prendre le plus proche
            if not apartment and candidats:
                candidats.sort(key=lambda x: x[0])
                apartment = candidats[0][1]
                print(f"ℹ️  Aucun appartement exactement 69m² trouvé, utilisation du plus proche: {apartment.get('surface')}")
        
        if not apartment:
            print(f"❌ Aucun appartement trouvé pour: {recherche}")
            print("\nAppartements disponibles dans le 20e avec 3 pièces:")
            for apt in data:
                if '20' in str(apt.get('localisation', '')).lower() and '3' in str(apt.get('pieces', '')):
                    print(f"  - ID: {apt.get('id')}, {apt.get('titre')}, Surface: {apt.get('surface')}")
            return
    
    print("="*80)
    print(f"🏠 ANALYSE TEST - FORMAT EXACT DES CRITÈRES")
    print("="*80)
    print(f"ID: {apartment.get('id')}")
    print(f"Titre: {apartment.get('titre')}")
    print(f"Localisation: {apartment.get('localisation')}")
    print(f"Surface: {apartment.get('surface')}")
    print(f"Pièces: {apartment.get('pieces')}")
    print(f"Prix: {apartment.get('prix')}")
    print("="*80)
    
    # 1. Localisation
    try:
        resultat = format_localisation_criterion(apartment)
        afficher_critere("Localisation", resultat)
    except Exception as e:
        print(f"\n❌ Erreur formatage Localisation: {e}")
    
    # 2. Prix
    try:
        resultat = format_prix_criterion(apartment)
        afficher_critere("Prix", resultat)
    except Exception as e:
        print(f"\n❌ Erreur formatage Prix: {e}")
    
    # 3. Style
    try:
        resultat = format_style_criterion(apartment)
        afficher_critere("Style", resultat)
    except Exception as e:
        print(f"\n❌ Erreur formatage Style: {e}")
    
    # 4. Exposition
    try:
        resultat = format_exposition_criterion(apartment)
        afficher_critere("Exposition", resultat)
    except Exception as e:
        print(f"\n❌ Erreur formatage Exposition: {e}")
    
    # 5. Cuisine
    try:
        resultat = format_cuisine_criterion(apartment)
        afficher_critere("Cuisine", resultat)
    except Exception as e:
        print(f"\n❌ Erreur formatage Cuisine: {e}")
    
    # 6. Baignoire
    try:
        BaignoireExtractor = _get_baignoire_extractor()
        baignoire_extractor = BaignoireExtractor() if BaignoireExtractor else None
        resultat = format_baignoire_criterion(apartment, baignoire_extractor)
        afficher_critere("Baignoire", resultat)
    except Exception as e:
        print(f"\n❌ Erreur formatage Baignoire: {e}")
    
    print("\n" + "="*80)
    print("✅ ANALYSE TERMINÉE")
    print("="*80)


if __name__ == "__main__":
    # Test avec l'appartement spécifique fourni par l'utilisateur
    if len(sys.argv) > 1 and sys.argv[1] == '--test-69m2':
        # Créer un appartement de test avec les données fournies
        test_apartment = {
            'id': 'TEST_69M2_20E',
            'titre': 'Paris 20e - 69 m² - 3 pièces - 2 chambres',
            'localisation': 'Paris 20e (75020)',
            'surface': '69 m²',
            'pieces': '3 pièces',
            'prix': '707 000 €',
            'prix_m2': '10 246 € / m²',
            'url': 'https://www.jinka.fr/test',
            'description': '',
            'caracteristiques': '',
            'etage': '',
            'transports': [],
            'photos': [],
            'scores_detaille': {},
            'style_analysis': {}
        }
        print("🧪 MODE TEST - Appartement Paris 20e - 69m² - 3p - 707 000€")
        print("="*80)
        analyser_appartement_test(apartment_data=test_apartment)
    elif len(sys.argv) > 1:
        # Si un ID est fourni en argument
        apartment_id = sys.argv[1]
        analyser_appartement_test(apartment_id=apartment_id)
    else:
        # Sinon chercher par critères
        analyser_appartement_test(recherche="Paris 20e - 69m² - 3p")

