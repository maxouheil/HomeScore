"""
Critère Prix - Calcul et formatage
Format: "X / m² · Good/Moyen/Bad"
"""

import re


def format_prix(apartment):
    """
    Formate le critère Prix: "X / m² · Good/Moyen/Bad"
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "11,500 / m² · Moyen"
            - confidence: None (données factuelles)
            - indices: None
    """
    scores_detaille = apartment.get('scores_detaille', {})
    prix_score = scores_detaille.get('prix', {})
    tier = prix_score.get('tier', 'tier3')
    
    # Calculer prix/m²
    prix = apartment.get('prix', '')
    surface = apartment.get('surface', '')
    prix_m2 = None
    
    # Extraire le prix en nombre
    prix_match = re.search(r'([\d\s]+)', prix.replace(' ', '')) if prix else None
    if prix_match:
        try:
            prix_num = int(prix_match.group(1))
            # Extraire la surface
            surface_match = re.search(r'(\d+)', surface) if surface else None
            if surface_match:
                surface_num = int(surface_match.group(1))
                if surface_num > 0:
                    prix_m2 = prix_num // surface_num
        except:
            pass
    
    # Si pas calculé, essayer depuis prix_m2 directement
    if prix_m2 is None:
        prix_m2_str = apartment.get('prix_m2', '')
        if prix_m2_str:
            prix_m2_match = re.search(r'(\d+)', prix_m2_str.replace(' ', ''))
            if prix_m2_match:
                try:
                    prix_m2 = int(prix_m2_match.group(1))
                except:
                    pass
    
    # Formater avec virgule comme séparateur de milliers et m² avec superscript
    if prix_m2:
        prix_formatted = f"{prix_m2:,}".replace(',', ' ')
        main_value = f"{prix_formatted} / m<sup>2</sup>"
    else:
        main_value = "Prix/m<sup>2</sup> non disponible"
    
    # Mapping tiers avec couleurs
    tier_mapping = {
        'tier1': ('Good', 'good'),
        'tier2': ('Moyen', 'moyen'),
        'tier3': ('Bad', 'bad')
    }
    tier_label, tier_class = tier_mapping.get(tier, ('Bad', 'bad'))
    
    return {
        'main_value': f"{main_value} · <span class=\"tier-label {tier_class}\">{tier_label}</span>",
        'confidence': None,  # Données factuelles
        'indices': None
    }

