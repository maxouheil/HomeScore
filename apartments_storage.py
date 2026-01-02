#!/usr/bin/env python3
"""
Module centralisé pour gérer le stockage des appartements
Tous les appartements sont maintenant dans un seul fichier: data/all_apartments.json
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

APARTMENTS_FILE = 'data/all_apartments.json'


def load_all_apartments() -> List[Dict[str, Any]]:
    """
    Charge tous les appartements depuis le fichier unique
    
    Returns:
        Liste de tous les appartements
    """
    if not os.path.exists(APARTMENTS_FILE):
        return []
    
    try:
        with open(APARTMENTS_FILE, 'r', encoding='utf-8') as f:
            apartments = json.load(f)
        return apartments
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {APARTMENTS_FILE}: {e}")
        return []


def save_all_apartments(apartments: List[Dict[str, Any]]) -> bool:
    """
    Sauvegarde tous les appartements dans le fichier unique
    
    Args:
        apartments: Liste de tous les appartements à sauvegarder
        
    Returns:
        True si sauvegarde réussie, False sinon
    """
    try:
        Path(APARTMENTS_FILE).parent.mkdir(parents=True, exist_ok=True)
        
        # Trier par ID pour cohérence
        apartments_sorted = sorted(apartments, key=lambda x: str(x.get('id', '')))
        
        with open(APARTMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(apartments_sorted, f, ensure_ascii=False, indent=2, default=str)
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de {APARTMENTS_FILE}: {e}")
        return False


def get_apartment(apartment_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un appartement par son ID
    
    Args:
        apartment_id: ID de l'appartement
        
    Returns:
        Données de l'appartement ou None si non trouvé
    """
    apartments = load_all_apartments()
    for apt in apartments:
        if str(apt.get('id')) == str(apartment_id):
            return apt
    return None


def save_apartment(apartment: Dict[str, Any]) -> bool:
    """
    Sauvegarde ou met à jour un appartement dans le fichier unique
    
    Args:
        apartment: Données de l'appartement à sauvegarder
        
    Returns:
        True si sauvegarde réussie, False sinon
    """
    apartment_id = apartment.get('id')
    if not apartment_id:
        print(f"⚠️ Pas d'ID pour l'appartement, skip")
        return False
    
    # Charger tous les appartements
    apartments = load_all_apartments()
    
    # Créer un dict par ID pour faciliter la mise à jour
    apartments_by_id = {str(apt.get('id')): apt for apt in apartments if apt.get('id')}
    
    # Mettre à jour ou ajouter l'appartement
    apartments_by_id[str(apartment_id)] = apartment
    
    # Convertir en liste et sauvegarder
    apartments_list = list(apartments_by_id.values())
    return save_all_apartments(apartments_list)


def save_apartments(apartments: List[Dict[str, Any]], merge: bool = True) -> bool:
    """
    Sauvegarde plusieurs appartements dans le fichier unique
    
    Args:
        apartments: Liste d'appartements à sauvegarder
        merge: Si True, fusionne avec les appartements existants (par défaut)
               Si False, remplace tous les appartements
        
    Returns:
        True si sauvegarde réussie, False sinon
    """
    if not merge:
        return save_all_apartments(apartments)
    
    # Charger les appartements existants
    existing_apartments = load_all_apartments()
    
    # Créer un dict par ID
    apartments_by_id = {str(apt.get('id')): apt for apt in existing_apartments if apt.get('id')}
    
    # Ajouter ou mettre à jour les nouveaux appartements
    for apt in apartments:
        apt_id = apt.get('id')
        if apt_id:
            apartments_by_id[str(apt_id)] = apt
    
    # Convertir en liste et sauvegarder
    apartments_list = list(apartments_by_id.values())
    return save_all_apartments(apartments_list)


def delete_apartment(apartment_id: str) -> bool:
    """
    Supprime un appartement du fichier unique
    
    Args:
        apartment_id: ID de l'appartement à supprimer
        
    Returns:
        True si suppression réussie, False sinon
    """
    apartments = load_all_apartments()
    apartments = [apt for apt in apartments if str(apt.get('id')) != str(apartment_id)]
    return save_all_apartments(apartments)


def get_apartments_count() -> int:
    """
    Retourne le nombre total d'appartements
    
    Returns:
        Nombre d'appartements
    """
    return len(load_all_apartments())
