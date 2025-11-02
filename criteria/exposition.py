"""
Critère Exposition - Formatage selon règles de vote par signal
Format: "Lumineux / Luminosité moyenne / Sombre (X% confiance) + indices"
"""

import re


def normalize_exposition(expo_text):
    """Normalise l'exposition: minuscules, sans accents, enlever espaces/traits"""
    if not expo_text:
        return None
    
    # Minuscules
    expo = expo_text.lower()
    
    # Enlever accents (approximation simple)
    expo = expo.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
    
    # Enlever espaces et traits
    expo = expo.replace(' ', '').replace('-', '').replace('_', '')
    
    return expo if expo else None


def classify_orientation(expo_dir):
    """Classe l'orientation: Lumineux / Moyen / Sombre"""
    if not expo_dir:
        return None
    
    expo_normalized = normalize_exposition(expo_dir)
    if not expo_normalized:
        return None
    
    # Lumineux: sud, sudouest, sudest
    if expo_normalized in ['sud', 'sudouest', 'sudest']:
        return 'Lumineux'
    
    # Moyen: est, ouest
    if expo_normalized in ['est', 'ouest']:
        return 'Moyen'
    
    # Sombre: nord, nordouest, nordest
    if expo_normalized in ['nord', 'nordouest', 'nordest']:
        return 'Sombre'
    
    return None


def classify_etage(etage_num):
    """Classe l'étage: Lumineux / Moyen / Sombre"""
    if etage_num is None:
        return None
    
    # Lumineux si étage >= 5
    if etage_num >= 5:
        return 'Lumineux'
    
    # Moyen si 2 <= étage <= 4
    if 2 <= etage_num <= 4:
        return 'Moyen'
    
    # Sombre si étage <= 1 ou RDC (0)
    if etage_num <= 1:
        return 'Sombre'
    
    return None


def classify_image_brightness(brightness_value):
    """Classe la luminosité image: Lumineux / Moyen / Sombre"""
    if brightness_value is None:
        return None
    
    # Lumineux si exp >= 0.70
    if brightness_value >= 0.70:
        return 'Lumineux'
    
    # Moyen si 0.40 <= exp < 0.70
    if 0.40 <= brightness_value < 0.70:
        return 'Moyen'
    
    # Sombre si exp < 0.40
    if brightness_value < 0.40:
        return 'Sombre'
    
    return None


def get_image_intensity(brightness_value):
    """Détermine l'intensité du signal image: Fort / Faible / Normal"""
    if brightness_value is None:
        return None
    
    # Fort si exp >= 0.85 ou exp <= 0.25
    if brightness_value >= 0.85 or brightness_value <= 0.25:
        return 'Fort'
    
    # Faible si 0.45 <= exp <= 0.55
    if 0.45 <= brightness_value <= 0.55:
        return 'Faible'
    
    # Sinon normal
    return 'Normal'


def vote_majority(votes):
    """Détermine la classe par vote majoritaire"""
    if not votes:
        return None
    
    # Compter les votes
    counts = {}
    for vote in votes:
        if vote:
            counts[vote] = counts.get(vote, 0) + 1
    
    if not counts:
        return None
    
    # Trouver le maximum
    max_count = max(counts.values())
    winners = [cls for cls, count in counts.items() if count == max_count]
    
    # Si égalité parfaite, retourner le premier (sera géré par l'appelant)
    if len(winners) == 1:
        return winners[0]
    
    # Égalité
    return winners  # Liste des classes ex aequo


def calculate_confidence(signals, final_class, image_intensity, signal_types):
    """Calcule la confiance selon les règles"""
    # Si aucun signal: classe Moyen, 50%
    if not signals:
        return 50
    
    # Base quand un seul signal: 60%
    base = 60
    
    # Compter les accords et désaccords
    agreement_count = 0
    disagreement_count = 0
    
    for signal_class in signals:
        if signal_class == final_class:
            agreement_count += 1
        else:
            disagreement_count += 1
    
    # Si un seul signal: base = 60%
    if len(signals) == 1:
        confidence = base
    else:
        # Base 60% + 20% pour chaque signal supplémentaire d'accord (au-delà du premier)
        # -15% pour chaque signal en désaccord
        additional_agreement = agreement_count - 1  # Signaux d'accord au-delà du premier
        confidence = base + (additional_agreement * 20) - (disagreement_count * 15)
    
    # +10% si le signal image est "fort" et d'accord avec la classe finale
    if image_intensity == 'Fort':
        # Trouver le signal image
        has_image = 'image' in signal_types
        if has_image:
            # Trouver l'index du signal image
            image_idx = None
            for i, sig_type in enumerate(signal_types):
                if sig_type == 'image':
                    image_idx = i
                    break
            if image_idx is not None and signals[image_idx] == final_class:
                confidence += 10
    
    # -10% si le signal image est "faible" (quelle que soit la classe)
    if image_intensity == 'Faible':
        confidence -= 10
    
    # Bornes: min 50%, max 95%
    confidence = max(50, min(95, confidence))
    
    return confidence


def format_exposition(apartment):
    """
    Formate le critère Exposition selon les règles de vote par signal
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Lumineux" / "Luminosité moyenne" / "Sombre"
            - confidence: 50-95 (pourcentage)
            - indices: "4e étage · Exposé Est · Luminosité 0.6"
    """
    exposition = apartment.get('exposition', {})
    expo_details = exposition.get('details', {})
    brightness_value = expo_details.get('brightness_value') or expo_details.get('image_brightness')
    
    exposition_dir = exposition.get('exposition', '')
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    
    # 1. Extraire l'étage
    etage_num = None
    if 'etage_num' in expo_details:
        etage_num = expo_details.get('etage_num')
    else:
        etage_field = apartment.get('etage', '')
        if etage_field:
            etage_match = re.search(r'(\d+)[èe]?me?\s*étage|RDC|rez[\s-]de[\s-]chaussée|rez[\s-]de[\s-]chaussee', etage_field, re.IGNORECASE)
            if etage_match:
                etage_text = etage_match.group(0)
                if 'rdc' in etage_text.lower() or 'rez' in etage_text.lower():
                    etage_num = 0
                else:
                    num_match = re.search(r'(\d+)', etage_text)
                    if num_match:
                        etage_num = int(num_match.group(1))
        
        if etage_num is None:
            text_to_search = f"{caracteristiques} {description}".lower()
            etage_patterns = [
                r'étage\s*(\d+)[èe]?me?\s*étage',
                r'étage\s*(\d+)',
                r'(\d+)[èe]?me?\s*étage',
                r'RDC|rez[\s-]de[\s-]chaussée|rez[\s-]de[\s-]chaussee',
            ]
            for pattern in etage_patterns:
                etage_match = re.search(pattern, text_to_search, re.IGNORECASE)
                if etage_match:
                    etage_text = etage_match.group(0)
                    if 'rdc' in etage_text.lower() or 'rez' in etage_text.lower():
                        etage_num = 0
                        break
                    else:
                        num_match = re.search(r'(\d+)', etage_text)
                        if num_match:
                            etage_num = int(num_match.group(1))
                            break
    
    # 2. Classifier chaque signal
    signals = []
    signal_types = []
    
    # Signal orientation
    orientation_class = classify_orientation(exposition_dir)
    if orientation_class:
        signals.append(orientation_class)
        signal_types.append('orientation')
    
    # Signal étage
    etage_class = classify_etage(etage_num)
    if etage_class:
        signals.append(etage_class)
        signal_types.append('etage')
    
    # Signal image
    image_class = classify_image_brightness(brightness_value)
    image_intensity = get_image_intensity(brightness_value)
    if image_class:
        signals.append(image_class)
        signal_types.append('image')
    
    # 3. Décision finale par vote majoritaire
    if not signals:
        # Si aucun signal: classe Moyen, 50%
        main_value = "Moyen"
        confidence = 50
    elif len(signals) == 1 and signal_types[0] == 'image':
        # Si seulement le signal luminosité est disponible, rester sur luminosité moyenne
        main_value = "Moyen"
        confidence = 60  # Base 60% pour un seul signal
    else:
        # Vote majoritaire
        vote_result = vote_majority(signals)
        
        if isinstance(vote_result, list):
            # Égalité parfaite: tranche avec l'image
            if image_class:
                # Si l'image est "faible", prendre Moyen
                if image_intensity == 'Faible':
                    main_value = "Moyen"
                else:
                    main_value = image_class
            else:
                # Pas d'image, prendre le premier (ou Moyen par défaut)
                main_value = vote_result[0] if vote_result else "Moyen"
        else:
            main_value = vote_result
        
        # Vérifier les règles strictes : Lumineux et Sombre nécessitent au moins 2 signaux
        if main_value == 'Lumineux':
            lumineux_count = sum(1 for s in signals if s == 'Lumineux')
            if lumineux_count < 2:
                main_value = "Moyen"
        elif main_value == 'Sombre':
            sombre_count = sum(1 for s in signals if s == 'Sombre')
            if sombre_count < 2:
                main_value = "Moyen"
        
        # Calculer la confiance
        confidence = calculate_confidence(signals, main_value, image_intensity, signal_types)
    
    # Normaliser main_value pour correspondre au format attendu
    if main_value == 'Lumineux':
        main_value_display = "Lumineux"
    elif main_value == 'Moyen':
        main_value_display = "Luminosité moyenne"
    elif main_value == 'Sombre':
        main_value_display = "Sombre"
    else:
        main_value_display = "Luminosité moyenne"
    
    # 4. Construire les indices
    indices_parts = []
    
    # Étage
    if etage_num is not None:
        if etage_num == 0:
            indices_parts.append("RDC")
        elif etage_num == 1:
            indices_parts.append("1er étage")
        else:
            indices_parts.append(f"{etage_num}e étage")
    
    # Exposition - UNIQUEMENT si explicitement mentionnée dans le texte
    exposition_explicite = exposition.get('exposition_explicite', False)
    if exposition_explicite and exposition_dir and exposition_dir.lower() not in ['inconnue', 'inconnu', 'non spécifiée', 'none', 'null']:
        expo_display = exposition_dir.replace('_', '-').title()
        indices_parts.append(f"Exposé {expo_display}")
    
    # Luminosité image
    if brightness_value is not None:
        indices_parts.append(f"Luminosité {brightness_value:.1f}")
    
    indices_str = " · ".join(indices_parts) if indices_parts else None
    
    return {
        'main_value': main_value_display,
        'confidence': confidence,
        'indices': indices_str
    }
