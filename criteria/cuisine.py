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
    # PRIORITÉ: Utiliser le résultat final depuis scores_detaille (après validation croisée texte + photos)
    scores_detaille = apartment.get('scores_detaille', {})
    cuisine_score = scores_detaille.get('cuisine', {})
    cuisine_details = cuisine_score.get('details', {})
    photo_validation = cuisine_details.get('photo_validation', {})
    
    # Chercher la valeur depuis photo_result (résultat final après validation)
    cuisine_ouverte = None
    confidence = cuisine_details.get('confidence')
    photo_result = {}
    validation_status = cuisine_details.get('validation_status', '')
    
    if isinstance(photo_validation, dict):
        photo_result = photo_validation.get('photo_result', {})
        # Si pas de conflit, utiliser photo_result.ouverte
        # Si conflit, le tier représente le résultat final (texte peut gagner)
        if validation_status != 'conflict':
            cuisine_ouverte = photo_result.get('ouverte')
    
    # Fallback: utiliser style_analysis si pas trouvé
    style_analysis = apartment.get('style_analysis', {})
    cuisine_data = style_analysis.get('cuisine', {})
    details = cuisine_data.get('details', '')
    
    if cuisine_ouverte is None:
        cuisine_ouverte = cuisine_data.get('ouverte', False)
        if confidence is None:
            confidence = cuisine_data.get('confidence')
    
    # Si toujours None OU si conflit, vérifier le tier pour déduire (tier = résultat final après validation)
    if cuisine_ouverte is None or validation_status == 'conflict':
        tier = cuisine_score.get('tier', 'tier3')
        # tier1 = ouverte (10pts), tier3 = fermée (0pts)
        # En cas de conflit, le tier représente le résultat final après validation croisée
        cuisine_ouverte = (tier == 'tier1')
    
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
    
    # Extraire les indices - format: "Cuisine Indice: ..."
    indices_parts = []
    
    # Chercher les détections photo depuis scores_detaille
    scores_detaille = apartment.get('scores_detaille', {})
    cuisine_score = scores_detaille.get('cuisine', {})
    cuisine_details = cuisine_score.get('details', {})
    photo_validation = cuisine_details.get('photo_validation', {})
    
    # Récupérer les numéros d'images détectées et le résultat photo
    detected_photos = []
    photo_result = {}
    photo_ouverte_result = None
    
    if isinstance(photo_validation, dict):
        # Le chemin correct est directement photo_validation.photo_result
        photo_result = photo_validation.get('photo_result', {})
        detected_photos = photo_result.get('detected_photos', [])
        photo_ouverte_result = photo_result.get('ouverte')
    
    # Vérifier le statut de validation pour savoir si on peut utiliser detected_photos
    validation_status = cuisine_details.get('validation_status', '')
    
    # Si détecté par photos ET que le résultat photo correspond au résultat final
    # (pas de conflit ou photos gagnent)
    if detected_photos and validation_status != 'conflict':
        # Pas de conflit → utiliser detected_photos avec main_value
        photos_str = ", ".join([f"image {p}" for p in sorted(detected_photos)])
        if main_value == "Ouverte":
            indices_parts.append(f"Cuisine ouverte détectée {photos_str}")
        else:
            indices_parts.append(f"Cuisine fermée détectée {photos_str}")
    elif detected_photos and validation_status == 'conflict':
        # Conflit détecté → vérifier si photo_result correspond au résultat final
        # Si photo_result.ouverte correspond à main_value, on peut utiliser detected_photos
        # Sinon, ne pas utiliser detected_photos car elles contredisent le résultat final
        if (photo_ouverte_result is True and main_value == "Ouverte") or \
           (photo_ouverte_result is False and main_value == "Fermée"):
            # Les photos confirment le résultat final → utiliser detected_photos
            photos_str = ", ".join([f"image {p}" for p in sorted(detected_photos)])
            if main_value == "Ouverte":
                indices_parts.append(f"Cuisine ouverte détectée {photos_str}")
            else:
                indices_parts.append(f"Cuisine fermée détectée {photos_str}")
        else:
            # Les photos contredisent le résultat final → ne pas afficher detected_photos
            # Afficher seulement que c'est détecté sans numéros d'images
            if main_value == "Ouverte":
                indices_parts.append("Cuisine ouverte détectée")
            else:
                indices_parts.append("Cuisine fermée détectée")
    elif photo_ouverte_result is not None:
        # Fallback si detected_photos n'est pas disponible mais qu'on a un résultat photo
        if photo_ouverte_result is True:
            indices_parts.append("Cuisine ouverte détectée")
        else:
            indices_parts.append("Cuisine fermée détectée")
    
    # Vérifier aussi dans details pour d'autres indices
    if details:
        if 'bar' in details.lower() or 'comptoir' in details.lower():
            indices_parts.append('bar détecté')
        if 'comptoir' in details.lower():
            indices_parts.append('comptoir détecté')
    
    # Formater avec le préfixe "Cuisine Indice:"
    indices_str = None
    if indices_parts:
        indices_str = "Cuisine Indice: " + " · ".join(indices_parts)
    else:
        # Fallback si aucun indice trouvé
        indices_str = "Cuisine Indice: Non spécifié"
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str
    }

