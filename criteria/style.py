"""
Critère Style - Formatage depuis style_analysis (IA images)
Format: "Ancien/Atypique/Neuf (X% confiance) + Indices: [tags séparés par virgules]"
"""


def format_style(apartment):
    """
    Formate le critère Style: "Ancien/Atypique/Neuf (X% confiance) + tags séparés par virgules"
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Ancien", "Atypique" ou "Neuf"
            - confidence: 70 (pourcentage)
            - indices: "Style Indice: [tags séparés par virgules, ex: 'moulures, parquet, cheminée']"
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
        elif '70' in justification or 'seventies' in justification or 'moderne' in justification or 'contemporain' in justification:
            style_type = 'moderne'
        else:
            style_type = 'Non spécifié'
    
    # Ancien / Atypique / Neuf
    style_type_lower = style_type.lower()
    
    # Vérifier aussi dans les scores_detaille pour détecter "Atypique" depuis texte
    scores_detaille = apartment.get('scores_detaille', {})
    style_score = scores_detaille.get('style', {})
    justification = style_score.get('justification', '').lower()
    
    if 'haussmann' in style_type_lower:
        style_name = "Ancien"
    elif 'loft' in style_type_lower or 'atypique' in style_type_lower or 'unique' in style_type_lower or 'original' in style_type_lower or 'atypique' in justification:
        style_name = "Atypique"
    else:
        # Tout le reste = Neuf
        style_name = "Neuf"
    
    # Convertir confiance en pourcentage
    confidence_pct = None
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # PRIORITÉ 1: Utiliser la justification du style depuis l'analyse des photos
    justification = style_data.get('justification', '')
    
    # Formater la chaîne d'indices avec la justification
    indices_str = None
    if justification:
        indices_str = f"Style Indice: {justification}"
    
    return {
        'main_value': style_name,
        'confidence': confidence_pct,
        'indices': indices_str
    }
