"""
Critère Baignoire - Formatage depuis extract_baignoire (IA images si nécessaire)
Format: "Oui / Non (X% confiance) + indices"
"""

# Import lazy pour éviter les blocages au chargement
_BaignoireExtractor = None

def _get_extractor():
    """Import lazy de BaignoireExtractor"""
    global _BaignoireExtractor
    if _BaignoireExtractor is None:
        try:
            from extract_baignoire import BaignoireExtractor
            _BaignoireExtractor = BaignoireExtractor
        except:
            _BaignoireExtractor = False  # Marquer comme échec
    return _BaignoireExtractor if _BaignoireExtractor else None


def format_baignoire(apartment):
    """
    Formate le critère Baignoire: "Oui / Non (X% confiance) + indices"
    Même logique que format_cuisine
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Oui" ou "Non"
            - confidence: 90 (pourcentage)
            - indices: "Baignoire Indice: Baignoire mentionné · Baignoire détectée image 1, image 3"
    """
    # RÈGLE V2: Validation photos ONLY (pas de texte)
    scores_detaille = apartment.get('scores_detaille', {})
    baignoire_score = scores_detaille.get('baignoire', {})
    baignoire_details = baignoire_score.get('details', {})
    photo_validation = baignoire_details.get('photo_validation', {})
    
    # Chercher la valeur depuis photo_result UNIQUEMENT
    has_baignoire = None
    has_douche = None
    confidence = None
    photo_result = {}
    detected_photos = []
    
    if isinstance(photo_validation, dict):
        photo_result = photo_validation.get('photo_result', {})
        has_baignoire = photo_result.get('has_baignoire')
        has_douche = photo_result.get('has_douche')
        detected_photos = photo_result.get('detected_photos', [])
        confidence = photo_result.get('confidence')
    
    # Fallback: utiliser baignoire_data si pas trouvé dans photo_validation
    if has_baignoire is None:
        baignoire_data = apartment.get('baignoire', {}) or apartment.get('baignoire_data', {})
        has_baignoire = baignoire_data.get('has_baignoire')
        if has_douche is None:
            has_douche = baignoire_data.get('has_douche')
        if confidence is None:
            confidence = baignoire_data.get('confidence')
        if not detected_photos:
            detected_photos = baignoire_data.get('detected_photos', [])
    
    # Si douche détectée mais pas de baignoire → pas de baignoire
    if has_douche is True and has_baignoire is None:
        has_baignoire = False
    
    # Déterminer main_value
    if has_baignoire is None:
        # Pas de détection photo → "Non spécifié"
        main_value = "Non spécifié"
    elif has_baignoire:
        main_value = "Oui"
    else:
        main_value = "Non"
    
    # Convertir confiance en pourcentage
    confidence_pct = None
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # Extraire les indices - format: "Baignoire Indice: Baignoire détectée image 3" ou "Douche détectée image 3"
    indices_parts = []
    
    # RÈGLE V2: Format "Baignoire détectée image 3" ou "Douche détectée image 3" (photos ONLY)
    if detected_photos:
        photos_str = ", ".join([f"image {p}" for p in sorted(detected_photos)])
        if has_baignoire is True:
            indices_parts.append(f"Baignoire détectée {photos_str}")
        elif has_douche is True:
            indices_parts.append(f"Douche détectée {photos_str}")
    elif has_baignoire is not None:
        # Pas de numéros d'images mais résultat disponible
        if has_baignoire:
            indices_parts.append("Baignoire détectée")
        elif has_douche:
            indices_parts.append("Douche détectée")
    else:
        # Pas de détection
        indices_parts.append("Non spécifié")
    
    # Formater avec le préfixe "Baignoire Indice:" sur une ligne séparée
    indices_str = "Baignoire Indice:\n" + " · ".join(indices_parts)
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str
    }

