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
    """Classe l'étage: Lumineux / Moyen / Sombre
    
    Barème simplifié:
    - Si <3e étage (<3): Sombre (luminosité faible)
    - Si 3-4: Moyen (luminosité moyenne)
    - Si >4 (>=5): Lumineux (luminosité forte)
    """
    if etage_num is None:
        return None
    
    # Sombre si étage < 3 (<3, inclut RDC = 0, 1er, 2e)
    if etage_num < 3:
        return 'Sombre'
    
    # Moyen si 3 <= étage <= 4
    if 3 <= etage_num <= 4:
        return 'Moyen'
    
    # Lumineux si étage > 4 (>=5)
    if etage_num > 4:
        return 'Lumineux'
    
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
    Formate le critère Exposition selon les règles simplifiées
    
    Logique:
    - Base: classification par étage uniquement
      * < 3e étage: Sombre (luminosité faible)
      * 3-4 étages: Moyen (luminosité moyenne)
      * > 4 étages: Lumineux (luminosité forte)
    - Upgrade: si Sud ou Ouest mentionné
      * Sombre → Moyen
      * Moyen → Lumineux
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Lumineux" / "Luminosité moyenne" / "Sombre"
            - confidence: 50-70 (pourcentage)
            - indices: "1er étage · Est mentionné"
    """
    exposition = apartment.get('exposition', {})
    expo_details = exposition.get('details', {})
    brightness_value = expo_details.get('brightness_value') or expo_details.get('image_brightness')
    
    exposition_dir = exposition.get('exposition', '')
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    
    # 1. Extraire l'étage
    etage_num = None
    
    # Priorité 1: depuis exposition.details.etage_num
    if 'etage_num' in expo_details:
        etage_num = expo_details.get('etage_num')
    
    # Priorité 2: depuis apartment.etage (champ string)
    if etage_num is None:
        etage_field = apartment.get('etage', '')
        if etage_field:
            # Nettoyer et normaliser le champ étage
            etage_field_lower = etage_field.lower().strip()
            
            # Cas RDC
            if 'rdc' in etage_field_lower or 'rez' in etage_field_lower:
                etage_num = 0
            else:
                # Chercher un nombre dans le champ
                etage_match = re.search(r'(\d+)[èe]?r?me?\s*étage|(\d+)', etage_field, re.IGNORECASE)
                if etage_match:
                    # Prendre le premier groupe qui correspond
                    num_str = etage_match.group(1) or etage_match.group(2)
                    if num_str:
                        try:
                            etage_num = int(num_str)
                        except ValueError:
                            pass
    
    # Priorité 3: depuis le texte (description + caractéristiques)
    if etage_num is None:
        text_to_search = f"{caracteristiques} {description}".lower()
        etage_patterns = [
            r'(\d+)[èe]?r?me?\s*étage',  # "2e étage", "2ème étage", "2er étage"
            r'étage\s*(\d+)',  # "étage 2"
            r'RDC|rez[\s-]de[\s-]chaussée|rez[\s-]de[\s-]chaussee',
        ]
        for pattern in etage_patterns:
            etage_match = re.search(pattern, text_to_search, re.IGNORECASE)
            if etage_match:
                if 'rdc' in etage_match.group(0).lower() or 'rez' in etage_match.group(0).lower():
                    etage_num = 0
                    break
                elif etage_match.lastindex and etage_match.group(1):
                    try:
                        etage_num = int(etage_match.group(1))
                        break
                    except ValueError:
                        pass
    
    # Priorité 4: depuis _api_data.floor si disponible (données API)
    if etage_num is None:
        api_data = apartment.get('_api_data', {})
        floor = api_data.get('floor')
        if floor is not None:
            etage_num = int(floor)
    
    # 2. Classification basée uniquement sur l'étage
    etage_class = classify_etage(etage_num)
    
    if etage_class:
        main_value = etage_class
        confidence = 70  # Confiance moyenne quand étage disponible
    else:
        # Pas d'étage disponible: défaut à Moyen
        main_value = "Moyen"
        confidence = 50
    
    # 3. Upgrade si Sud ou Ouest mentionné: faible → moyen, moyen → fort
    if exposition_dir:
        expo_normalized = normalize_exposition(exposition_dir)
        if expo_normalized:
            # Vérifier si Sud ou Ouest est présent dans l'exposition
            has_sud = 'sud' in expo_normalized
            has_ouest = 'ouest' in expo_normalized
            
            if has_sud or has_ouest:
                # Appliquer l'upgrade
                if main_value == 'Sombre':
                    main_value = 'Moyen'  # Faible → Moyen
                elif main_value == 'Moyen':
                    main_value = 'Lumineux'  # Moyen → Fort
    
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
        # Formater l'exposition : "sud" -> "Sud mentionné", "sud_ouest" -> "Sud-Ouest mentionné"
        expo_display = exposition_dir.replace('_', '-').split('-')
        expo_display = '-'.join([word.capitalize() for word in expo_display])
        indices_parts.append(f"{expo_display} mentionné")
    
    # Luminosité image
    if brightness_value is not None:
        indices_parts.append(f"Luminosité {brightness_value:.1f}")
    
    # Formater avec le préfixe "Exposition Indice:" (même format que cuisine et baignoire)
    indices_str = None
    if indices_parts:
        indices_str = "Exposition Indice: " + " · ".join(indices_parts)
    else:
        # Fallback si aucun indice trouvé
        indices_str = "Exposition Indice: Non spécifié"
    
    return {
        'main_value': main_value_display,
        'confidence': confidence,
        'indices': indices_str
    }
