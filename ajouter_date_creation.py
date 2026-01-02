#!/usr/bin/env python3
"""
Script pour ajouter le champ date_creation_annonce à tous les appartements
en extrayant la valeur depuis _api_data.created_at
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def ajouter_date_creation(fichier_entree: str, fichier_sortie: str = None):
    """
    Ajoute le champ date_creation_annonce à tous les appartements
    
    Args:
        fichier_entree: Chemin vers le fichier JSON d'entrée
        fichier_sortie: Chemin vers le fichier JSON de sortie (si None, remplace l'entrée)
    """
    print(f"📂 Lecture du fichier: {fichier_entree}")
    
    try:
        with open(fichier_entree, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {fichier_entree}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON: {e}")
        return False
    
    # Normaliser en liste
    if isinstance(data, list):
        apartments = data
    elif isinstance(data, dict):
        if 'details_par_appartement' in data:
            apartments = data['details_par_appartement']
        else:
            apartments = list(data.values())
    else:
        print("❌ Format de données non reconnu")
        return False
    
    print(f"📊 {len(apartments)} appartements trouvés")
    print()
    
    # Traiter chaque appartement
    ajoutes = 0
    deja_presents = 0
    manquants = 0
    
    for apt in apartments:
        apt_id = apt.get('id', 'N/A')
        
        # Vérifier si date_creation_annonce existe déjà
        if 'date_creation_annonce' in apt:
            deja_presents += 1
            continue
        
        # Extraire depuis _api_data.created_at
        api_data = apt.get('_api_data', {})
        if isinstance(api_data, dict) and 'created_at' in api_data:
            created_at = api_data.get('created_at')
            if created_at:
                apt['date_creation_annonce'] = created_at
                ajoutes += 1
            else:
                manquants += 1
        else:
            manquants += 1
    
    # Sauvegarder
    if fichier_sortie is None:
        fichier_sortie = fichier_entree
    
    # Sauvegarder dans le même format que l'entrée
    if isinstance(data, list):
        output_data = apartments
    elif isinstance(data, dict):
        if 'details_par_appartement' in data:
            data['details_par_appartement'] = apartments
            output_data = data
        else:
            output_data = {k: v for k, v in zip(range(len(apartments)), apartments)}
    else:
        output_data = apartments
    
    # Créer une sauvegarde
    backup_file = f"{fichier_entree}.backup_before_date_creation"
    print(f"💾 Création d'une sauvegarde: {backup_file}")
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  Impossible de créer la sauvegarde: {e}")
        reponse = input("Continuer quand même? (o/n): ")
        if reponse.lower() != 'o':
            return False
    
    # Sauvegarder le fichier modifié
    print(f"💾 Sauvegarde dans: {fichier_sortie}")
    try:
        with open(fichier_sortie, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False
    
    # Résumé
    print()
    print("=" * 80)
    print("📊 RÉSUMÉ")
    print("=" * 80)
    print(f"✅ Dates ajoutées: {ajoutes}")
    print(f"ℹ️  Déjà présentes: {deja_presents}")
    print(f"⚠️  Manquantes (_api_data.created_at absent): {manquants}")
    print(f"📁 Fichier sauvegardé: {fichier_sortie}")
    
    return True


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
            print("   python ajouter_date_creation.py [chemin_vers_fichier.json]")
            print(f"   Fichier attendu: {fichier}")
            sys.exit(1)
    
    print("=" * 80)
    print("🔧 AJOUT DE LA DATE DE CRÉATION D'ANNONCE")
    print("=" * 80)
    print()
    
    success = ajouter_date_creation(fichier)
    
    if success:
        print()
        print("✅ Terminé avec succès!")
    else:
        print()
        print("❌ Échec")
        sys.exit(1)


if __name__ == "__main__":
    main()

