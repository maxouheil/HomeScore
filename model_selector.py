#!/usr/bin/env python3
"""
Sélection automatique du modèle Gemini approprié selon le type d'analyse
"""

def select_gemini_model(analysis_type: str) -> str:
    """
    Sélectionne le modèle Gemini approprié selon le type d'analyse
    
    Args:
        analysis_type: Type d'analyse ('baignoire', 'cuisine', 'exposition', 'style', 'visavis', 'hauteur_plafond', 'salon_size')
    
    Returns:
        Nom du modèle Gemini ('gemini-1.5-flash' ou 'gemini-1.5-pro')
    """
    # Analyses simples → Gemini Flash (économique)
    simple_analyses = [
        'baignoire',
        'cuisine', 
        'exposition',
        'luminosite'
    ]
    
    # Analyses complexes → Gemini Pro (meilleure qualité)
    complex_analyses = [
        'style',
        'visavis',
        'vis_a_vis',
        'hauteur_plafond',
        'salon_size',
        'large_piece_vie'
    ]
    
    analysis_type_lower = analysis_type.lower()
    
    if analysis_type_lower in simple_analyses:
        return "gemini-1.5-flash"
    elif analysis_type_lower in complex_analyses:
        return "gemini-1.5-pro"
    else:
        # Par défaut, utiliser Flash pour économiser
        return "gemini-1.5-flash"


def get_model_cost_per_image(model: str) -> float:
    """
    Retourne le coût par image pour un modèle donné
    
    Args:
        model: Nom du modèle ('gemini-1.5-flash' ou 'gemini-1.5-pro')
    
    Returns:
        Coût par image en dollars
    """
    costs = {
        'gemini-1.5-flash': 0.000075,  # $0.000075 par image
        'gemini-1.5-pro': 0.001315,    # $0.001315 par image
    }
    
    return costs.get(model.lower(), 0.000075)  # Par défaut Flash

