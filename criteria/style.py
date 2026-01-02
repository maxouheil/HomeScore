"""
Critère Style - Formatage avec priorité date API > analyse photo
Format: "Haussmannien" / "Années XX" / "Moderne" (X% confiance) + Indices
Règle V2: Si <1910 = Haussmannien auto, sinon décennie. Priorité date API > analyse photo
"""

import re


def extract_construction_year(apartment):
    """
    Extrait l'année de construction depuis différentes sources
    
    Priorité:
    1. _api_data.features.year
    2. caracteristiques.annee_construction
    3. Extraction depuis texte (caracteristiques ou description)
    
    Returns:
        int: Année de construction ou None
    """
    # Priorité 1: _api_data.features.year
    api_data = apartment.get('_api_data', {})
    features = api_data.get('features', {})
    year = features.get('year')
    if year and year != 'null' and year is not None:
        try:
            return int(str(year))
        except:
            pass
    
    # Priorité 2: caracteristiques.annee_construction
    caracteristiques = apartment.get('caracteristiques', {})
    if isinstance(caracteristiques, dict):
        annee_construction = caracteristiques.get('annee_construction')
        if annee_construction:
            try:
                return int(str(annee_construction))
            except:
                pass
    
    # Priorité 3: Extraction depuis texte
    # Chercher dans caracteristiques (string)
    if isinstance(caracteristiques, str):
        # Pattern: "Année: 1880" ou "Année : 1880"
        year_match = re.search(r'année\s*:?\s*(\d{4})', caracteristiques, re.IGNORECASE)
        if year_match:
            try:
                return int(year_match.group(1))
            except:
                pass
        
        # Pattern: "Construit en 1909" ou "construction 1909"
        construit_match = re.search(r'(?:construit|construction)\s*(?:en|de)?\s*(\d{4})', caracteristiques, re.IGNORECASE)
        if construit_match:
            try:
                return int(construit_match.group(1))
            except:
                pass
    
    # Chercher dans description
    description = apartment.get('description', '')
    if description:
        year_match = re.search(r'(?:construit|construction|année)\s*(?:en|de|:)?\s*(\d{4})', description, re.IGNORECASE)
        if year_match:
            try:
                return int(year_match.group(1))
            except:
                pass
    
    return None


def format_style(apartment):
    """
    Formate le critère Style selon les règles V2
    
    Règles:
    - Si < 1910: Rank automatique en Haussmannien
    - Sinon: Donner la décennie (Années 70, après 80 = Moderne)
    - Priorité: Date API > Analyse photo
    
    Args:
        apartment: Dict contenant les données de l'appartement
        
    Returns:
        Dict avec:
            - main_value: "Haussmannien" | "Années 70" | "Années 80" | "Moderne"
            - confidence: 70-95 (plus élevé si date API disponible)
            - indices: "Style Indice:\nConstruit en 1880" ou indices photo
    """
    # PRIORITÉ 1: Extraire l'année de construction depuis l'API
    construction_year = extract_construction_year(apartment)
    
    # PRIORITÉ 1B: Vérifier si on a une analyse photo avec éléments détectés
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    elements_detectes = style_data.get('details', {}).get('elements_detectes', [])
    
    if construction_year:
        # Classification basée sur l'année
        if construction_year < 1910:
            style_name = "Haussmannien"
            confidence = 95  # Très haute confiance si date API disponible
        elif construction_year >= 1910 and construction_year <= 1980:
            # Calculer la décennie (ex: 1976 -> années 70)
            decade = (construction_year // 10) * 10
            decade_str = str(decade)[-2:]  # "70" pour 1970
            style_name = f"Années {decade_str}"
            confidence = 90  # Haute confiance si date API disponible
        else:  # > 1980
            style_name = "Moderne"
            confidence = 90  # Haute confiance si date API disponible
        
        # Utiliser les éléments détectés depuis l'image si disponibles (au lieu de répéter "Construit en X")
        if elements_detectes and isinstance(elements_detectes, list) and len(elements_detectes) > 0:
            # Formater les éléments détectés en mots-clés (max 3 lignes)
            elements_to_show = elements_detectes[:9]  # Max 9 éléments pour 3 lignes de 3
            lines = []
            current_line = []
            for i, elem in enumerate(elements_to_show):
                current_line.append(str(elem))
                if len(current_line) >= 3:  # 3 éléments par ligne
                    lines.append(', '.join(current_line))
                    current_line = []
            if current_line:
                lines.append(', '.join(current_line))
            
            # Limiter à 3 lignes max
            lines = lines[:3]
            indices_str = "Style Indice:\n" + "\n".join(lines)
        else:
            # Fallback: utiliser l'année seulement si pas d'éléments détectés
            indices_str = f"Style Indice:\nConstruit en {construction_year}"
        
        return {
            'main_value': style_name,
            'confidence': confidence,
            'indices': indices_str
        }
    
    # PRIORITÉ 2: Analyse photo (fallback si pas de date API)
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    
    style_type = style_data.get('type', '')
    confidence = style_data.get('confidence')
    
    # Formater le nom du style depuis analyse photo
    if not style_type or style_type == 'autre' or style_type == 'inconnu':
        # Fallback: chercher dans scores_detaille
        scores_detaille = apartment.get('scores_detaille', {})
        style_score = scores_detaille.get('style', {})
        justification = style_score.get('justification', '').lower()
        
        if 'haussmann' in justification or 'moulures' in justification:
            style_type = 'haussmannien'
        elif '70' in justification or 'seventies' in justification:
            style_type = 'annees_70'
        elif 'moderne' in justification or 'contemporain' in justification:
            style_type = 'moderne'
        else:
            style_type = 'Non spécifié'
    
    style_type_lower = style_type.lower()
    
    # Classification depuis analyse photo
    if 'haussmann' in style_type_lower:
        style_name = "Haussmannien"
    elif '70' in style_type_lower or 'seventies' in style_type_lower:
        style_name = "Années 70"
    elif '80' in style_type_lower:
        style_name = "Années 80"
    elif 'moderne' in style_type_lower or 'contemporain' in style_type_lower:
        style_name = "Moderne"
    else:
        style_name = "Moderne"  # Par défaut
    
    # Convertir confiance en pourcentage (moins élevée que date API)
    confidence_pct = 70  # Confiance moyenne pour analyse photo
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
        # Limiter à 85% max pour analyse photo (vs 95% pour date API)
        confidence_pct = min(85, confidence_pct)
    
    # Utiliser la justification depuis scores_detaille ou style_data
    scores_detaille = apartment.get('scores_detaille', {})
    style_score = scores_detaille.get('style', {})
    justification = style_score.get('justification', '')
    
    if not justification:
        justification = style_data.get('justification', '')
    
    # Extraire les éléments détectés depuis style_data.details.elements_detectes
    elements_detectes = style_data.get('details', {}).get('elements_detectes', [])
    if not elements_detectes or not isinstance(elements_detectes, list):
        # Fallback: essayer d'extraire depuis la justification
        # Extraire les mots-clés de la justification
        keywords = []
        if justification:
            # Nettoyer et extraire les mots-clés pertinents
            text = justification.lower()
            # Mots-clés à chercher
            keyword_patterns = [
                r'\b(?:îlot|ilot)\s+(?:de\s+)?cuisine\b',
                r'\bcuisine\s+(?:moderne|ouverte|fermée)\b',
                r'\bchaises?\s+(?:en\s+)?rotin\b',
                r'\bdesign\s+contemporain\b',
                r'\bpanneaux?\s+(?:décoratifs?|en\s+bois|lamellé)\b',
                r'\bbois\s+lamellé\b',
                r'\bmobilier\b',
                r'\bagencement\s+ouvert\b',
                r'\bsuspension\b',
                r'\bmoulures?\b',
                r'\bparquet\s+(?:ancien|haussmanien)\b',
                r'\bcaractéristiques?\s+haussmaniennes?\b',
                r'\béléments?\s+(?:des\s+)?années\b',
            ]
            for pattern in keyword_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    keywords.extend(matches)
        
        # Si pas de mots-clés trouvés, utiliser les premiers éléments de la justification
        if not keywords and justification:
            # Extraire les premiers mots significatifs (max 10 mots)
            words = justification.split()[:10]
            keywords = [w for w in words if len(w) > 3]  # Filtrer les mots trop courts
        
        # Limiter à 5-6 mots-clés max
        keywords = keywords[:6]
        elements_detectes = keywords
    
    # Formater les indices en mots-clés (max 3 lignes)
    indices_parts = []
    if elements_detectes:
        # Prendre les premiers éléments détectés
        elements_to_show = elements_detectes[:9]  # Max 9 éléments pour 3 lignes de 3
        # Formater en 3 lignes max
        lines = []
        current_line = []
        for i, elem in enumerate(elements_to_show):
            current_line.append(str(elem))
            if len(current_line) >= 3:  # 3 éléments par ligne
                lines.append(', '.join(current_line))
                current_line = []
        if current_line:
            lines.append(', '.join(current_line))
        
        # Limiter à 3 lignes max
        lines = lines[:3]
        indices_parts = lines
    elif justification:
        # Fallback: extraire les mots-clés de la justification
        # Simplifier la justification en mots-clés
        text = justification.lower()
        # Extraire les phrases courtes ou mots-clés
        sentences = re.split(r'[.,;]', justification)
        keywords = []
        for sent in sentences[:3]:  # Max 3 phrases
            sent = sent.strip()
            if len(sent) > 5 and len(sent) < 50:  # Phrases de taille raisonnable
                keywords.append(sent)
        if keywords:
            indices_parts = keywords[:3]  # Max 3 lignes
        else:
            indices_parts = [justification[:60]]  # Limiter à 60 caractères
    else:
        indices_parts = [f"Analyse photo: {style_type}"]
    
    # Formater avec le préfixe "Style Indice:" sur une ligne séparée
    indices_str = "Style Indice:\n" + "\n".join(indices_parts[:3])  # Max 3 lignes
    
    return {
        'main_value': style_name,
        'confidence': confidence_pct,
        'indices': indices_str
    }
