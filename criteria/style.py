"""
Critère Style - Formatage depuis style_analysis (IA images)
Format: "70's/Haussmannien/Moderne (X% confiance) + Indices: ..."
"""


def format_style(apartment):
    """
    Formate le critère Style: "70's/Haussmannien/Moderne (X% confiance) + indices"
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Haussmannien"
            - confidence: 70 (pourcentage)
            - indices: "Indices: Moulures · cheminée · parquet"
    """
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    
    style_type = style_data.get('type', '')
    confidence = style_data.get('confidence')
    
    # Formater le nom du style
    if not style_type or style_type == 'autre' or style_type == 'inconnu':
        # Fallback: chercher dans scores_detaille
        scores_detaille = apartment.get('scores_detaille', {})
        style_score = scores_detaille.get('style', {})
        justification = style_score.get('justification', '').lower()
        
        if 'haussmann' in justification or 'moulures' in justification:
            style_type = 'haussmannien'
        elif '70' in justification or 'seventies' in justification:
            style_type = '70s'
        elif 'moderne' in justification or 'contemporain' in justification:
            style_type = 'moderne'
        else:
            style_type = 'Non spécifié'
    
    # Capitaliser et formater
    if '70' in style_type.lower() or 'seventies' in style_type.lower():
        style_name = "70's"
    elif 'haussmann' in style_type.lower():
        style_name = "Haussmannien"
    elif 'moderne' in style_type.lower():
        style_name = "Moderne"
    else:
        style_name = style_type.capitalize()
    
    # Convertir confiance en pourcentage
    confidence_pct = None
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # Extraire les indices
    indices = []
    details = style_data.get('details', '')
    if details:
        # Chercher des mots-clés dans les détails
        keywords = ['moulures', 'cheminée', 'parquet', 'hauteur sous plafond', 'moldings', 'fireplace']
        found_keywords = [kw for kw in keywords if kw.lower() in details.lower()]
        if found_keywords:
            indices = found_keywords[:3]  # Limiter à 3 indices
    
    # Si pas d'indices dans details, chercher dans style_haussmannien
    if not indices:
        style_haussmannien = apartment.get('style_haussmannien', {})
        if isinstance(style_haussmannien, dict):
            elements = style_haussmannien.get('elements', {})
            if isinstance(elements, dict):
                architectural = elements.get('architectural', [])
                if architectural and isinstance(architectural, list):
                    indices = architectural[:3]
    
    indices_str = None
    if indices:
        indices_str = "Indices: " + " · ".join(indices)
    
    return {
        'main_value': style_name,
        'confidence': confidence_pct,
        'indices': indices_str
    }

