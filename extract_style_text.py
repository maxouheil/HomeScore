#!/usr/bin/env python3
"""
Extracteur de texte pour détecter les indices de style depuis description et caractéristiques
Détection spécifique d'indices architecturaux pour Ancien et Neuf
"""

import re
from typing import Dict, List, Tuple


class StyleTextExtractor:
    """Extracteur de texte pour détecter les indices de style"""
    
    def __init__(self):
        # Indices pour Ancien (Haussmannien)
        self.indices_ancien = {
            'moulures': [
                r'moulures?', r'moldings?', r'corniche', r'rosace', 
                r'plafond à moulures', r'plafond mouluré'
            ],
            'parquet_pointe_hongrie': [
                r'parquet.*point[es]?.*hongrie', r'parquet.*chevron', 
                r'parquet.*point de hongrie', r'parquet.*hongrie',
                r'point de hongrie'
            ],
            'balcon_fer_forge': [
                r'balcon.*fer.*forgé', r'balcon.*fer.*forge', 
                r'balcon.*ferronnerie', r'garde.*corps.*fer.*forgé',
                r'fer.*forgé.*balcon'
            ],
            'cheminee': [
                r'cheminée', r'cheminée.*marbre', r'cheminée.*bois',
                r'cheminée.*fonctionnelle', r'cheminée.*décorative'
            ]
        }
        
        # Indices pour Neuf (Moderne)
        self.indices_neuf = {
            'terrasse_metal': [
                r'terrasse.*métal', r'terrasse.*metal', r'terrasse.*aluminium',
                r'balcon.*métal', r'balcon.*metal'
            ],
            'hauteur_sous_plafond': [
                r'hauteur.*sous.*plafond', r'hauteur.*plafond', 
                r'plafond.*haut', r'hauteur.*plafond.*\d+', r'hsp.*\d+'
            ],
            'sol_moderne': [
                r'sol.*moderne', r'carrelage.*moderne', r'sol.*carrelage',
                r'parquet.*stratifié', r'sol.*stratifié', r'carrelage.*grand.*format'
            ],
            'etage_eleve': [
                r'\d+e?\s*étage', r'étage.*\d+', r'dernier.*étage',
                r'avant.*dernier.*étage', r'étage.*élevé'
            ],
            'vue_paris': [
                r'vue.*paris', r'vue.*sur.*paris', r'panorama.*paris',
                r'vue.*dégagée', r'vue.*panoramique', r'vue.*imprenable'
            ]
        }
    
    def extract_indices(self, description: str, caracteristiques: str = "") -> Dict:
        """
        Extrait les indices de style depuis le texte
        
        Returns:
            Dict avec:
                - indices_ancien: List[Tuple[str, str]] - (indice, source)
                - indices_neuf: List[Tuple[str, str]] - (indice, source)
        """
        text_combined = f"{description} {caracteristiques}".lower()
        
        indices_ancien = []
        indices_neuf = []
        
        # Chercher indices Ancien
        for indice_name, patterns in self.indices_ancien.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_combined, re.IGNORECASE)
                for match in matches:
                    # Vérifier le contexte pour éviter les faux positifs
                    context_start = max(0, match.start() - 20)
                    context_end = min(len(text_combined), match.end() + 20)
                    context = text_combined[context_start:context_end]
                    
                    # Éviter les faux positifs
                    if not self._is_false_positive(context, indice_name, 'ancien'):
                        indices_ancien.append((indice_name, match.group(0)))
                        break  # Une seule détection par indice
        
        # Chercher indices Neuf
        for indice_name, patterns in self.indices_neuf.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_combined, re.IGNORECASE)
                for match in matches:
                    context_start = max(0, match.start() - 20)
                    context_end = min(len(text_combined), match.end() + 20)
                    context = text_combined[context_start:context_end]
                    
                    if not self._is_false_positive(context, indice_name, 'neuf'):
                        indices_neuf.append((indice_name, match.group(0)))
                        break
        
        return {
            'indices_ancien': list(set(indices_ancien)),  # Dédupliquer
            'indices_neuf': list(set(indices_neuf))
        }
    
    def _is_false_positive(self, context: str, indice_name: str, style_type: str) -> bool:
        """Vérifie si c'est un faux positif"""
        context_lower = context.lower()
        
        # Faux positifs généraux
        false_positives = [
            'non', 'pas de', 'sans', 'aucun', 'aucune',
            'manque', 'absence', 'exclu'
        ]
        
        for fp in false_positives:
            if fp in context_lower:
                return True
        
        # Faux positifs spécifiques
        if indice_name == 'hauteur_sous_plafond':
            # Éviter "hauteur sous plafond réduite" ou "plafond bas"
            if 'réduite' in context_lower or 'bas' in context_lower or 'faible' in context_lower:
                return True
        
        if indice_name == 'etage_eleve':
            # Éviter "1er étage" ou "RDC" qui ne sont pas élevés
            if re.search(r'(1er|r\.?d\.?c|rez)', context_lower):
                return True
        
        return False
    
    def format_indice_name(self, indice_name: str) -> str:
        """Formate le nom de l'indice pour l'affichage"""
        mapping = {
            'moulures': 'Moulures',
            'parquet_pointe_hongrie': 'Parquet pointe de Hongrie',
            'balcon_fer_forge': 'Balcon fer forgé',
            'cheminee': 'Cheminée',
            'terrasse_metal': 'Terrasse métal',
            'hauteur_sous_plafond': 'Hauteur sous plafond',
            'sol_moderne': 'Sol moderne',
            'etage_eleve': 'Étage élevé',
            'vue_paris': 'Vue sur Paris'
        }
        return mapping.get(indice_name, indice_name.replace('_', ' ').title())

