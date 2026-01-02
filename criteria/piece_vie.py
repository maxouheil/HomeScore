"""
Critère Pièce de vie - Formatage depuis analyse IA
Format: "Grande pièce de vie" / "Moyenne pièce de vie" / "Petite pièce de vie" + indices
"""


def format_piece_vie(apartment):
    """
    Formate le critère Pièce de vie depuis l'analyse IA
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Grande pièce de vie" | "Moyenne pièce de vie" | "Petite pièce de vie"
            - confidence: 0-100 (pourcentage)
            - indices: Description de la taille
    """
    # Chercher depuis différentes sources (priorité: piece_vie > style_analysis.piece_vie > analyses.piece_vie)
    piece_vie_data = apartment.get('piece_vie', {})
    
    # Fallback: chercher dans style_analysis.piece_vie
    if not piece_vie_data or not piece_vie_data.get('taille'):
        style_analysis = apartment.get('style_analysis', {})
        piece_vie_style = style_analysis.get('piece_vie', {})
        if piece_vie_style:
            piece_vie_data = piece_vie_style
    
    # Fallback: chercher dans analyses.piece_vie
    if not piece_vie_data or not piece_vie_data.get('taille'):
        analyses = apartment.get('analyses', {})
        piece_vie_analyses = analyses.get('piece_vie', {})
        if piece_vie_analyses:
            piece_vie_data = piece_vie_analyses
    
    taille = piece_vie_data.get('taille', '').lower() if piece_vie_data.get('taille') else None
    
    # Si on a une taille depuis style_analysis mais pas de format texte, extraire depuis les détails
    if not taille and piece_vie_data:
        # Chercher dans les détails ou justification
        details = piece_vie_data.get('details', {})
        salon_size = details.get('salon_size_estimate')
        if salon_size:
            # Classifier selon la taille
            try:
                size_float = float(salon_size)
                if size_float >= 28:
                    taille = 'grande'
                elif size_float >= 20:
                    taille = 'moyenne'
                else:
                    taille = 'petite'
            except (ValueError, TypeError):
                pass
        
        # Fallback: chercher dans la justification
        if not taille:
            justification = piece_vie_data.get('justification', '')
            if 'grande' in justification.lower() or 'large' in justification.lower():
                taille = 'grande'
            elif 'moyenne' in justification.lower() or 'moyen' in justification.lower():
                taille = 'moyenne'
            elif 'petite' in justification.lower() or 'small' in justification.lower():
                taille = 'petite'
    
    if not taille:
        return {
            'main_value': 'Non spécifié',
            'confidence': None,
            'indices': 'Pièce de vie Indice:\nNon spécifié'
        }
    
    # Mapper les valeurs de l'IA au format attendu
    if 'grande' in taille or 'large' in taille:
        main_value = "Grande pièce de vie"
        confidence_pct = 75
    elif 'moyenne' in taille or 'moyen' in taille:
        main_value = "Moyenne pièce de vie"
        confidence_pct = 70
    elif 'petite' in taille or 'small' in taille:
        main_value = "Petite pièce de vie"
        confidence_pct = 70
    else:
        main_value = "Moyenne pièce de vie"
        confidence_pct = 60
    
    # Utiliser la confiance depuis les données si disponible
    confidence = piece_vie_data.get('confidence')
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # Formater les indices avec la taille en m² et le pourcentage si disponible
    taille_m2 = piece_vie_data.get('taille_m2')
    justification = piece_vie_data.get('justification', '')
    
    # Construire les indices avec taille et pourcentage
    indices_parts = []
    
    # Ajouter la taille en m² si disponible
    if taille_m2:
        try:
            taille_m2_float = float(taille_m2)
            indices_parts.append(f"{taille_m2_float:.0f}m²")
        except (ValueError, TypeError):
            pass
    
    # Ajouter le pourcentage si disponible (depuis les détails)
    details = piece_vie_data.get('details', {})
    pourcentage = details.get('pourcentage_salon') or details.get('pourcentage')
    if pourcentage:
        try:
            pourcentage_float = float(pourcentage)
            indices_parts.append(f"{pourcentage_float:.1f}% de la surface totale de l'appartement")
        except (ValueError, TypeError):
            pass
    
    # Si pas de taille ni pourcentage, utiliser la justification
    if not indices_parts and justification:
        indices_parts.append(justification)
    elif not indices_parts:
        indices_parts.append(main_value)
    
    indices_str = "Pièce de vie Indice:\n" + " · ".join(indices_parts)
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str
    }
