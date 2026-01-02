#!/usr/bin/env python3
"""
Script pour extraire et afficher les dates de création des annonces
depuis les fichiers JSON existants
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def extraire_date_creation(apt_data: dict) -> str:
    """
    Extrait la date de création de l'annonce depuis les données d'un appartement
    
    Args:
        apt_data: Dictionnaire avec les données de l'appartement
        
    Returns:
        Date de création au format ISO ou None
    """
    # Chercher dans _api_data.created_at (format Jinka)
    if '_api_data' in apt_data:
        api_data = apt_data.get('_api_data', {})
        if isinstance(api_data, dict) and 'created_at' in api_data:
            created_at = api_data.get('created_at')
            if created_at:
                return created_at
    
    # Chercher dans les autres champs possibles
    date_fields = ['date_creation_annonce', 'created_at', 'date_creation', 'date']
    for field in date_fields:
        if field in apt_data and apt_data[field]:
            return apt_data[field]
    
    return None


def analyser_fichier(fichier_path: str):
    """
    Analyse un fichier JSON et affiche les dates de création
    
    Args:
        fichier_path: Chemin vers le fichier JSON
    """
    try:
        with open(fichier_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Normaliser en liste
        if isinstance(data, list):
            apartments = data
        elif isinstance(data, dict):
            if 'details_par_appartement' in data:
                apartments = data['details_par_appartement']
            else:
                apartments = list(data.values())
        else:
            print(f"❌ Format de données non reconnu dans {fichier_path}")
            return
        
        print(f"📊 Analyse de {len(apartments)} appartements dans {fichier_path}")
        print("=" * 80)
        
        dates_trouvees = 0
        dates_manquantes = 0
        
        for i, apt in enumerate(apartments[:10], 1):  # Limiter à 10 pour l'affichage
            apt_id = apt.get('id', 'N/A')
            titre = apt.get('titre', 'N/A')[:50]
            
            date_creation = extraire_date_creation(apt)
            
            if date_creation:
                dates_trouvees += 1
                print(f"{i}. ID: {apt_id}")
                print(f"   Titre: {titre}...")
                print(f"   ✅ Date création: {date_creation}")
                
                # Afficher aussi les autres dates disponibles
                if 'date_scoring' in apt:
                    print(f"   📅 Date scoring: {apt.get('date_scoring')}")
                if 'scraped_at' in apt:
                    print(f"   📅 Scraped at: {apt.get('scraped_at')}")
                print()
            else:
                dates_manquantes += 1
                print(f"{i}. ID: {apt_id} - ⚠️  Date de création non trouvée")
        
        # Statistiques globales
        print("=" * 80)
        print(f"📈 Statistiques:")
        print(f"   Total analysé: {min(10, len(apartments))}")
        print(f"   Dates trouvées: {dates_trouvees}")
        print(f"   Dates manquantes: {dates_manquantes}")
        
        # Vérifier tous les appartements pour les stats complètes
        total_dates = sum(1 for apt in apartments if extraire_date_creation(apt))
        print(f"\n📊 Sur {len(apartments)} appartements au total:")
        print(f"   Dates de création disponibles: {total_dates} ({total_dates/len(apartments)*100:.1f}%)")
        
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {fichier_path}")
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Fonction principale"""
    from project_config import APARTMENTS_FILE
    
    if len(sys.argv) > 1:
        fichier = sys.argv[1]
    else:
        # Utiliser le fichier standard depuis PROJECT_ROOT
        fichier = str(APARTMENTS_FILE)
        
        if not Path(fichier).exists():
            print("❌ Fichier non trouvé. Usage:")
            print("   python extraire_dates_creation.py [chemin_vers_fichier.json]")
            print(f"   Fichier attendu: {fichier}")
            sys.exit(1)
    
    print(f"🔍 Analyse du fichier: {fichier}")
    print()
    analyser_fichier(fichier)


if __name__ == "__main__":
    main()

