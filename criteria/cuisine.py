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
    # RÈGLE V2: Validation photos ONLY (pas de texte)
    scores_detaille = apartment.get('scores_detaille', {})
    cuisine_score = scores_detaille.get('cuisine', {})
    cuisine_details = cuisine_score.get('details', {})
    photo_validation = cuisine_details.get('photo_validation', {})
    
    # Chercher la valeur depuis photo_result UNIQUEMENT
    cuisine_ouverte = None
    confidence = None
    photo_result = {}
    detected_photos = []
    
    if isinstance(photo_validation, dict):
        photo_result = photo_validation.get('photo_result', {})
        cuisine_ouverte = photo_result.get('ouverte')
        detected_photos = photo_result.get('detected_photos', [])
        confidence = photo_result.get('confidence')
    
    # Fallback: utiliser style_analysis.cuisine si pas trouvé dans photo_validation
    if cuisine_ouverte is None:
        style_analysis = apartment.get('style_analysis', {})
        cuisine_data = style_analysis.get('cuisine', {})
        cuisine_ouverte = cuisine_data.get('ouverte', False)
        if confidence is None:
            confidence = cuisine_data.get('confidence')
        # Chercher detected_photos dans cuisine_data
        if not detected_photos:
            detected_photos = cuisine_data.get('detected_photos', [])
    
    # Déterminer main_value
    if cuisine_ouverte is None:
        # Pas de détection photo → "Non spécifié"
        main_value = "Non spécifié"
    elif cuisine_ouverte:
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
    
    # Extraire les indices - format: "Cuisine Indice: Cuisine détectée image X"
    indices_parts = []
    
    # RÈGLE V2: Format "Cuisine détectée image 3" (photos ONLY)
    if detected_photos:
        photos_str = ", ".join([f"image {p}" for p in sorted(detected_photos)])
        if main_value == "Ouverte":
            indices_parts.append(f"Cuisine ouverte détectée {photos_str}")
        elif main_value == "Fermée":
            indices_parts.append(f"Cuisine fermée détectée {photos_str}")
    elif cuisine_ouverte is not None:
        # Pas de numéros d'images mais résultat disponible
        if cuisine_ouverte:
            indices_parts.append("Cuisine ouverte détectée")
        else:
            indices_parts.append("Cuisine fermée détectée")
    else:
        # Pas de détection
        indices_parts.append("Non spécifié")
    
    # Formater avec le préfixe "Cuisine Indice:" sur une ligne séparée
    indices_str = "Cuisine Indice:\n" + " · ".join(indices_parts)
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str
    }

