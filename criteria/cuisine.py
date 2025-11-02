"""
Critère Cuisine - Formatage depuis style_analysis.cuisine (IA images)
Format: "Ouverte / Semi Ouverte / Fermée (X% confiance) + indices"
"""


def format_cuisine(apartment):
    """
    Formate le critère Cuisine: "Ouverte / Semi Ouverte / Fermée (X% confiance) + indices"
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Ouverte" ou "Semi Ouverte" ou "Fermée"
            - confidence: 90 (pourcentage)
            - indices: "Analyse photo : Cuisine ouverte détectée" ou "bar détecté · séparation partielle"
    """
    style_analysis = apartment.get('style_analysis', {})
    cuisine_data = style_analysis.get('cuisine', {})
    
    cuisine_ouverte = cuisine_data.get('ouverte', False)
    confidence = cuisine_data.get('confidence')
    details = cuisine_data.get('details', '')
    
    # Simplifié: seulement Ouverte ou Fermée (plus de Semi Ouverte)
    if cuisine_ouverte:
        main_value = "Ouverte"
    else:
        main_value = "Fermée"
    
    # Convertir confiance en pourcentage
    confidence_pct = None
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # Extraire les indices
    indices = None
    if details:
        # Chercher des mots-clés dans les détails pour les indices
        if 'analyse photo' in details.lower() or 'photo' in details.lower():
            indices = f"Analyse photo : Cuisine {main_value.lower()} détectée"
        else:
            # Extraire des indices pertinents depuis details
            keywords_found = []
            if 'bar' in details.lower() or 'comptoir' in details.lower():
                keywords_found.append('bar détecté')
            if 'ouverte' in details.lower() and main_value == "Ouverte":
                keywords_found.append('cuisine intégrée')
            
            if keywords_found:
                indices = " · ".join(keywords_found[:3])
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices
    }

