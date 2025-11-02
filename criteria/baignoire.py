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
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Oui" ou "Non"
            - confidence: 90 (pourcentage)
            - indices: "Analyse photo : Baignoire détectée" ou "Analyse photo : Douche détectée"
    """
    # Vérifier si baignoire_data est déjà dans les données (pré-calculé)
    if 'baignoire_data' in apartment:
        baignoire_data = apartment['baignoire_data']
    else:
        # Fallback rapide: analyse texte uniquement pour éviter les blocages
        # L'analyse IA complète devrait être faite lors du scraping, pas à la volée
        description = apartment.get('description', '').lower()
        caracteristiques = apartment.get('caracteristiques', '').lower()
        text = f"{description} {caracteristiques}"
        
        has_baignoire = any(kw in text for kw in ['baignoire', 'baignoir', 'salle de bain', 'salle de bains'])
        has_douche = 'douche' in text and not has_baignoire
        
        baignoire_data = {
            'has_baignoire': has_baignoire,
            'has_douche': has_douche,
            'confidence': 0.5 if has_baignoire or has_douche else 0.3,
            'justification': 'Analyse texte rapide' if has_baignoire or has_douche else 'Non détecté'
        }
    
    try:
        
        has_baignoire = baignoire_data.get('has_baignoire', False)
        has_douche = baignoire_data.get('has_douche', False)
        confidence = baignoire_data.get('confidence', 0)
        justification = baignoire_data.get('justification', '')
        
        # Déterminer la valeur principale
        if has_baignoire:
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
        
        # Extraire les indices depuis justification
        indices = None
        if justification:
            if 'photo' in justification.lower() or 'détectée' in justification.lower() or 'analysée' in justification.lower():
                if has_baignoire:
                    indices = "Analyse photo : Baignoire détectée"
                elif has_douche:
                    indices = "Analyse photo : Douche détectée"
            elif 'description' in justification.lower() or 'caractéristiques' in justification.lower():
                # Détecté depuis texte
                if has_baignoire:
                    indices = "Baignoire mentionnée dans le texte"
                elif has_douche:
                    indices = "Douche mentionnée dans le texte"
            else:
                # Utiliser la justification comme indices si elle est courte
                if len(justification) < 100:
                    indices = justification
        
        return {
            'main_value': main_value,
            'confidence': confidence_pct,
            'indices': indices
        }
    except Exception as e:
        # Fallback si erreur
        return {
            'main_value': "Non",
            'confidence': None,
            'indices': None
        }

