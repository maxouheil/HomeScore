"""
Module criteria - Formatage des critères pour l'affichage HTML
Chaque fichier contient la logique de formatage pour un critère spécifique
"""

from .localisation import format_localisation, get_metro_name, get_quartier_name
from .prix import format_prix
from .style import format_style
from .exposition import format_exposition
from .cuisine import format_cuisine
from .baignoire import format_baignoire

__all__ = [
    'format_localisation',
    'format_prix',
    'format_style',
    'format_exposition',
    'format_cuisine',
    'format_baignoire',
    'get_metro_name',
    'get_quartier_name',
]

