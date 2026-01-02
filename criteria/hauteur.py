"""
Critère Hauteur Plafond - Classification selon seuils
Format: "[hauteur] m" + classification Good/Moyen/Bad
Règle V2: Bad < 2.50m, Moyen < 2.80m (≥2.50m), Good ≥ 2.80m
"""


def format_hauteur(apartment):
    """
    Formate le critère Hauteur Plafond selon les règles V2
    
    Règles:
    - Bad: < 2.50m
    - Moyen: < 2.80m (≥ 2.50m et < 2.80m)
    - Good: ≥ 2.80m
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "2.8 m" | "Non spécifié"
            - confidence: 70-90
            - indices: "Hauteur Indice:\nHauteur estimée 2.8m (Good)"
    """
    # Chercher la hauteur depuis analyses.hauteur_plafond
    analyses = apartment.get('analyses', {})
    hauteur_data = analyses.get('hauteur_plafond', {})
    
    # Fallback: chercher dans style_analysis.style.hauteur_plafond_estimee
    if not hauteur_data:
        style_analysis = apartment.get('style_analysis', {})
        style_data = style_analysis.get('style', {})
        hauteur_estimee = style_data.get('hauteur_plafond_estimee')
        if hauteur_estimee:
            hauteur_data = {
                'hauteur_estimee': hauteur_estimee,
                'confiance': style_data.get('confidence', 70)
            }
    
    hauteur_estimee = hauteur_data.get('hauteur_estimee')
    confidence = hauteur_data.get('confiance') or hauteur_data.get('confidence')
    
    if hauteur_estimee is None:
        return {
            'main_value': "Non spécifié",
            'confidence': None,
            'indices': "Hauteur Indice:\nNon spécifié"
        }
    
    # Convertir en float si nécessaire
    try:
        hauteur_estimee = float(hauteur_estimee)
    except (ValueError, TypeError):
        return {
            'main_value': "Non spécifié",
            'confidence': None,
            'indices': "Hauteur Indice:\nNon spécifié"
        }
    
    # Classification selon les seuils V2
    if hauteur_estimee < 2.50:
        classification = "Bad"
        tier = "tier3"
    elif hauteur_estimee < 2.80:
        classification = "Moyen"
        tier = "tier2"
    else:  # ≥ 2.80
        classification = "Good"
        tier = "tier1"
    
    # Formater la valeur principale selon la documentation
    # Titre: "Belle hauteur plafond" (si ≥ 2.80m) ou "[Hauteur]m" (ex: "2,90m")
    if hauteur_estimee >= 2.80:
        main_value = "Belle hauteur plafond"
    else:
        # Format avec virgule pour les décimales (format français)
        main_value = f"{hauteur_estimee:.2f}m".replace('.', ',')
    
    # Convertir confiance en pourcentage
    confidence_pct = 75  # Confiance par défaut
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # Formater les indices selon la documentation
    # Description: "Moyenne [Hauteur]m" (ex: "Moyenne 2,90m")
    hauteur_formatted = f"{hauteur_estimee:.2f}m".replace('.', ',')
    indices_str = f"Moyenne {hauteur_formatted}"
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str,
        'tier': tier  # Pour scoring
    }

