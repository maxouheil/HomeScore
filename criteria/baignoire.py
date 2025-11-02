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
    # PRIORITÉ: Utiliser le résultat final depuis scores_detaille (après validation croisée texte + photos)
    scores_detaille = apartment.get('scores_detaille', {})
    baignoire_score = scores_detaille.get('baignoire', {})
    baignoire_details = baignoire_score.get('details', {})
    photo_validation = baignoire_details.get('photo_validation', {})
    
    # Chercher la valeur depuis photo_result (résultat final après validation)
    has_baignoire = None
    confidence = baignoire_details.get('confidence')
    photo_result = {}
    validation_status = baignoire_details.get('validation_status', '')
    
    if isinstance(photo_validation, dict):
        photo_result = photo_validation.get('photo_result', {})
        # PRIORITÉ: Utiliser photo_result.has_baignoire/has_douche comme source de vérité
        # Si photos ont analysé, utiliser leur résultat même en cas de conflit avec tier
        photo_has_baignoire = photo_result.get('has_baignoire')
        photo_has_douche = photo_result.get('has_douche')
        
        if photo_has_baignoire is not None:
            # Photos ont analysé → utiliser leur résultat
            has_baignoire = photo_has_baignoire
        elif photo_has_douche is True:
            # Douche détectée = pas de baignoire
            has_baignoire = False
    
    # Fallback: utiliser baignoire_data si pas trouvé
    if has_baignoire is None:
        baignoire_data = apartment.get('baignoire_data', {})
        has_baignoire = baignoire_data.get('has_baignoire', False)
        if confidence is None:
            confidence = baignoire_data.get('confidence')
    
    # Si toujours None, vérifier le tier pour déduire (seulement si pas de résultats photos)
    if has_baignoire is None:
        tier = baignoire_score.get('tier', 'tier3')
        # tier1 = baignoire présente (10pts), tier3 = pas de baignoire (0pts)
        has_baignoire = (tier == 'tier1')
    
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
    
    # Extraire les indices - format: "Baignoire Indice: ..."
    indices_parts = []
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    text = f"{description} {caracteristiques}"
    
    # Chercher les détections photo depuis scores_detaille (PRIORITÉ sur le texte)
    scores_detaille = apartment.get('scores_detaille', {})
    baignoire_score = scores_detaille.get('baignoire', {})
    baignoire_details = baignoire_score.get('details', {})
    photo_validation = baignoire_details.get('photo_validation', {})
    
    # Récupérer les numéros d'images détectées et le résultat photo
    detected_photos = []
    photo_result = {}
    photo_has_baignoire = None
    photo_has_douche = None
    
    if isinstance(photo_validation, dict) and photo_validation:
        # Le chemin correct est directement photo_validation.photo_result
        photo_result = photo_validation.get('photo_result', {})
        if isinstance(photo_result, dict):
            detected_photos = photo_result.get('detected_photos', []) or []
            photo_has_baignoire = photo_result.get('has_baignoire')
            photo_has_douche = photo_result.get('has_douche')
    
    # Vérifier le statut de validation pour savoir si on peut utiliser detected_photos
    validation_status = baignoire_details.get('validation_status', '')
    
    # PRIORITÉ: Utiliser uniquement les résultats des photos (pas de texte)
    # Si aucune photo ne détecte de baignoire ni douche → "Non spécifié"
    photo_detected = False
    
    # Vérifier si des photos ont été analysées
    # Si photo_result existe et contient has_baignoire ou has_douche (même si False), alors photos analysées
    photos_analyzed = (
        isinstance(photo_result, dict) and 
        len(photo_result) > 0 and 
        ('has_baignoire' in photo_result or 'has_douche' in photo_result)
    )
    
    if detected_photos and validation_status != 'conflict':
        # Pas de conflit → utiliser detected_photos avec photo_result pour déterminer baignoire vs douche
        photos_str = ", ".join([f"image {p}" for p in sorted(detected_photos)])
        # Utiliser photo_result.has_baignoire/has_douche plutôt que main_value pour être précis
        if photo_has_baignoire is True:
            indices_parts.append(f"Baignoire détectée {photos_str}")
            photo_detected = True
        elif photo_has_douche is True:
            indices_parts.append(f"Douche détectée {photos_str}")
            photo_detected = True
    elif detected_photos and validation_status == 'conflict':
        # Conflit détecté → vérifier si photo_result correspond au résultat final
        if (photo_has_baignoire is True and main_value == "Oui") or \
           (photo_has_douche is True and main_value == "Non"):
            # Les photos confirment le résultat final → utiliser detected_photos
            photos_str = ", ".join([f"image {p}" for p in sorted(detected_photos)])
            if photo_has_baignoire is True:
                indices_parts.append(f"Baignoire détectée {photos_str}")
                photo_detected = True
            elif photo_has_douche is True:
                indices_parts.append(f"Douche détectée {photos_str}")
                photo_detected = True
        else:
            # Les photos contredisent le résultat final → afficher seulement que c'est détecté sans numéros d'images
            if photo_has_baignoire is True:
                indices_parts.append("Baignoire détectée")
                photo_detected = True
            elif photo_has_douche is True:
                indices_parts.append("Douche détectée")
                photo_detected = True
    elif photo_has_baignoire is not None or photo_has_douche is not None:
        # Fallback si detected_photos n'est pas disponible mais qu'on a un résultat photo
        if photo_has_baignoire is True:
            indices_parts.append("Baignoire détectée")
            photo_detected = True
        elif photo_has_douche is True:
            indices_parts.append("Douche détectée")
            photo_detected = True
    
    # Si aucune photo n'a détecté de baignoire ni douche (même si photos analysées)
    if not photo_detected:
        if photos_analyzed:
            # Photos analysées mais rien détecté → "Non spécifié"
            indices_parts.append("Non spécifié")
        else:
            # Pas de photos analysées → "Non spécifié"
            indices_parts.append("Non spécifié")
    
    # Formater avec le préfixe "Baignoire Indice:"
    indices_str = None
    if indices_parts:
        indices_str = "Baignoire Indice: " + " · ".join(indices_parts)
    else:
        # Fallback si aucun indice trouvé
        indices_str = "Baignoire Indice: Non spécifié"
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str
    }

