"""
Critère Exposition - Formatage depuis style_analysis.luminosite (IA images)
Format: "Lumineux / Luminosité moyenne / Sombre (X% confiance) + indices"
"""

import re


def format_exposition(apartment):
    """
    Formate le critère Exposition: "Lumineux / Luminosité moyenne / Sombre (X% confiance) + indices"
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Lumineux"
            - confidence: 50 (pourcentage)
            - indices: "3e étage · pas de vis à vis · Exposition Sud détectée"
    """
    style_analysis = apartment.get('style_analysis', {})
    luminosite_data = style_analysis.get('luminosite', {})
    
    luminosite_type = luminosite_data.get('type', '')
    confidence = luminosite_data.get('confidence')
    
    # Mapping luminosité
    if 'excellente' in luminosite_type.lower():
        main_value = "Lumineux"
    elif 'bonne' in luminosite_type.lower() or 'moyenne' in luminosite_type.lower():
        main_value = "Luminosité moyenne"
    else:
        main_value = "Sombre"
    
    # Convertir confiance en pourcentage
    confidence_pct = None
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # Extraire les indices depuis exposition
    indices_parts = []
    exposition = apartment.get('exposition', {})
    
    # Étage
    etage = apartment.get('etage', '')
    if etage:
        etage_match = re.search(r'(\d+(?:er?|e|ème?))\s*étage|RDC|rez-de-chaussée|rez de chaussée', str(etage), re.IGNORECASE)
        if etage_match:
            etage_text = etage_match.group(0)
            if 'rdc' in etage_text.lower() or 'rez' in etage_text.lower():
                indices_parts.append("RDC")
            else:
                num_match = re.search(r'(\d+)', etage_text)
                if num_match:
                    num = num_match.group(1)
                    if num == '1':
                        indices_parts.append("1er étage")
                    else:
                        indices_parts.append(f"{num}e étage")
    
    # Vis-à-vis depuis description ou exposition
    description = apartment.get('description', '').lower()
    if 'vis-à-vis' in description or 'vis à vis' in description or 'pas de vis' in description:
        if 'pas de vis' in description:
            indices_parts.append("pas de vis à vis")
        else:
            indices_parts.append("vis à vis")
    
    # Exposition directionnelle
    exposition_dir = exposition.get('exposition', '')
    if exposition_dir and exposition_dir.lower() not in ['inconnue', 'inconnu', 'non spécifiée']:
        indices_parts.append(f"Exposition {exposition_dir} détectée")
    
    indices_str = " · ".join(indices_parts) if indices_parts else None
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str
    }

