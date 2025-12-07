#!/usr/bin/env python3
"""
Module d'analyse contextuelle de l'exposition
Utilise les indices géographiques et architecturaux pour déduire l'exposition
"""

import json
import re
from typing import Dict, List, Optional, Tuple

class ContextualExpositionAnalyzer:
    """Analyseur contextuel de l'exposition"""
    
    def __init__(self):
        # Base de données des quartiers et leurs orientations typiques
        self.quartier_orientations = {
            'Buttes-Chaumont': {
                'orientation_typique': 'Sud-Est',
                'exposition_preferee': 'Sud-Est',
                'score': 8,
                'description': 'Proximité du parc Buttes-Chaumont, orientation Sud-Est typique'
            },
            'Belleville': {
                'orientation_typique': 'Sud',
                'exposition_preferee': 'Sud',
                'score': 9,
                'description': 'Quartier en hauteur, exposition Sud privilégiée'
            },
            'Pyrénées': {
                'orientation_typique': 'Sud-Ouest',
                'exposition_preferee': 'Sud-Ouest',
                'score': 8,
                'description': 'Quartier résidentiel, exposition Sud-Ouest'
            },
            'Jourdain': {
                'orientation_typique': 'Sud',
                'exposition_preferee': 'Sud',
                'score': 8,
                'description': 'Quartier populaire, exposition Sud'
            }
        }
        
        # Indices architecturaux
        self.architectural_clues = {
            'duplex': {
                'orientation_probable': 'extérieure',
                'score_bonus': 2,
                'description': 'Duplex souvent orienté vers l\'extérieur'
            },
            'cuisine_americaine': {
                'orientation_probable': 'extérieure',
                'score_bonus': 2,
                'description': 'Cuisine ouverte vers l\'extérieur'
            },
            'balcon': {
                'orientation_probable': 'extérieure',
                'score_bonus': 1,
                'description': 'Balcon = orientation extérieure'
            },
            'terrasse': {
                'orientation_probable': 'extérieure',
                'score_bonus': 1,
                'description': 'Terrasse = orientation extérieure'
            },
            'jardin': {
                'orientation_probable': 'extérieure',
                'score_bonus': 1,
                'description': 'Jardin = orientation extérieure'
            }
        }
        
        # Indices d'étage
        self.etage_clues = {
            '4ème étage': {'score_bonus': 2, 'description': 'Bon étage pour la luminosité'},
            '5ème étage': {'score_bonus': 2, 'description': 'Bon étage pour la luminosité'},
            '6ème étage': {'score_bonus': 1, 'description': 'Étage élevé, bonne luminosité'},
            '3ème étage': {'score_bonus': 2, 'description': 'Étage optimal'},
            '2ème étage': {'score_bonus': 1, 'description': 'Étage correct'},
            '1er étage': {'score_bonus': 0, 'description': 'Étage bas'},
            'rdc': {'score_bonus': 0, 'description': 'Rez-de-chaussée'}
        }
    
    def analyze_contextual_exposition(self, apartment_data: Dict) -> Dict:
        """Analyse l'exposition basée sur le contexte géographique et architectural"""
        try:
            description = apartment_data.get('description', '')
            caracteristiques = apartment_data.get('caracteristiques', '')
            localisation = apartment_data.get('localisation', '')
            
            # Analyser le quartier
            quartier_analysis = self._analyze_quartier(description, localisation)
            
            # Analyser les indices architecturaux
            architectural_analysis = self._analyze_architectural_clues(description, caracteristiques)
            
            # Analyser l'étage
            etage_analysis = self._analyze_etage(caracteristiques)
            
            # Analyser la luminosité mentionnée
            luminosite_analysis = self._analyze_luminosite_context(description)
            
            # Calculer l'exposition probable
            exposition_probable = self._calculate_probable_exposition(
                quartier_analysis, architectural_analysis, etage_analysis, luminosite_analysis
            )
            
            return {
                'exposition': exposition_probable['exposition'],
                'score': exposition_probable['score'],
                'tier': exposition_probable['tier'],
                'justification': exposition_probable['justification'],
                'confidence': exposition_probable['confidence'],
                'details': {
                    'quartier': quartier_analysis,
                    'architectural': architectural_analysis,
                    'etage': etage_analysis,
                    'luminosite': luminosite_analysis
                }
            }
            
        except Exception as e:
            return {
                'exposition': None,
                'score': 3,
                'tier': 'tier3',
                'justification': f'Erreur analyse contextuelle: {e}',
                'confidence': 0.0,
                'details': {}
            }
    
    def _analyze_quartier(self, description: str, localisation: str) -> Dict:
        """Analyse le quartier pour déduire l'exposition"""
        text = f"{description} {localisation}".lower()
        
        for quartier, info in self.quartier_orientations.items():
            if quartier.lower() in text:
                return {
                    'quartier': quartier,
                    'orientation_typique': info['orientation_typique'],
                    'score': info['score'],
                    'description': info['description'],
                    'found': True
                }
        
        # Chercher des indices de proximité
        if 'buttes' in text and 'chaumont' in text:
            return {
                'quartier': 'Buttes-Chaumont (proximité)',
                'orientation_typique': 'Sud-Est',
                'score': 7,
                'description': 'Proximité Buttes-Chaumont détectée',
                'found': True
            }
        
        return {
            'quartier': 'Non identifié',
            'orientation_typique': None,
            'score': 0,
            'description': 'Quartier non identifié',
            'found': False
        }
    
    def _analyze_architectural_clues(self, description: str, caracteristiques: str) -> Dict:
        """Analyse les indices architecturaux"""
        text = f"{description} {caracteristiques}".lower()
        found_clues = []
        total_score = 0
        
        for clue, info in self.architectural_clues.items():
            if clue in text:
                found_clues.append({
                    'clue': clue,
                    'score_bonus': info['score_bonus'],
                    'description': info['description']
                })
                total_score += info['score_bonus']
        
        return {
            'clues_found': found_clues,
            'total_score': total_score,
            'count': len(found_clues)
        }
    
    def _analyze_etage(self, caracteristiques: str) -> Dict:
        """Analyse l'étage pour déduire la luminosité"""
        text = caracteristiques.lower()
        
        for etage, info in self.etage_clues.items():
            if etage in text:
                return {
                    'etage': etage,
                    'score_bonus': info['score_bonus'],
                    'description': info['description'],
                    'found': True
                }
        
        return {
            'etage': 'Non spécifié',
            'score_bonus': 0,
            'description': 'Étage non spécifié',
            'found': False
        }
    
    def _analyze_luminosite_context(self, description: str) -> Dict:
        """Analyse la luminosité dans le contexte"""
        text = description.lower()
        
        luminosite_keywords = {
            'très lumineux': {'score': 3, 'description': 'Très lumineux mentionné'},
            'lumineux': {'score': 2, 'description': 'Lumineux mentionné'},
            'clair': {'score': 2, 'description': 'Clair mentionné'},
            'spacieux': {'score': 1, 'description': 'Spacieux = bonne luminosité'},
            'grand salon': {'score': 1, 'description': 'Grand salon = bonne luminosité'}
        }
        
        found_keywords = []
        total_score = 0
        
        for keyword, info in luminosite_keywords.items():
            if keyword in text:
                found_keywords.append({
                    'keyword': keyword,
                    'score': info['score'],
                    'description': info['description']
                })
                total_score += info['score']
        
        return {
            'keywords_found': found_keywords,
            'total_score': total_score,
            'count': len(found_keywords)
        }
    
    def _calculate_probable_exposition(self, quartier, architectural, etage, luminosite) -> Dict:
        """Calcule l'exposition probable basée sur tous les indices"""
        # Score de base
        base_score = 5
        
        # Ajouter les scores des différents indices
        total_score = base_score
        justifications = []
        
        # Quartier
        if quartier['found']:
            total_score += quartier['score']
            justifications.append(f"Quartier: {quartier['description']}")
            exposition_quartier = quartier['orientation_typique']
        else:
            exposition_quartier = None
        
        # Architectural
        if architectural['count'] > 0:
            total_score += architectural['total_score']
            justifications.append(f"Indices architecturaux: {architectural['count']} trouvés")
        
        # Étage
        if etage['found']:
            total_score += etage['score_bonus']
            justifications.append(f"Étage: {etage['description']}")
        
        # Luminosité
        if luminosite['count'] > 0:
            total_score += luminosite['total_score']
            justifications.append(f"Luminosité: {luminosite['count']} indices")
        
        # Déterminer l'exposition
        if exposition_quartier:
            exposition = exposition_quartier
        elif architectural['count'] >= 2:
            exposition = 'Sud-Est'  # Orientation probable pour duplex
        else:
            exposition = 'Est'  # Orientation par défaut
        
        # Déterminer le tier
        if total_score >= 12:
            tier = 'tier1'
        elif total_score >= 8:
            tier = 'tier2'
        else:
            tier = 'tier3'
        
        # Calculer la confiance
        confidence = min(0.9, (total_score - 5) / 15)
        
        return {
            'exposition': exposition,
            'score': min(10, total_score),
            'tier': tier,
            'justification': f"Analyse contextuelle: {'; '.join(justifications)}",
            'confidence': confidence
        }

def test_contextual_analysis():
    """Test de l'analyse contextuelle"""
    analyzer = ContextualExpositionAnalyzer()
    
    # Charger les données de l'appartement test
    try:
        with open('data/appartements/90931157.json', 'r') as f:
            apartment_data = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier de données non trouvé")
        return
    
    print("🔍 TEST D'ANALYSE CONTEXTUELLE")
    print("=" * 60)
    
    result = analyzer.analyze_contextual_exposition(apartment_data)
    
    print(f"Exposition: {result['exposition']}")
    print(f"Score: {result['score']}/10")
    print(f"Tier: {result['tier']}")
    print(f"Confiance: {result['confidence']:.2f}")
    print(f"Justification: {result['justification']}")
    print()
    
    print("📊 DÉTAILS:")
    details = result['details']
    
    print(f"Quartier: {details['quartier']['quartier']} ({details['quartier']['score']} pts)")
    print(f"Architectural: {details['architectural']['count']} indices ({details['architectural']['total_score']} pts)")
    print(f"Étage: {details['etage']['etage']} ({details['etage']['score_bonus']} pts)")
    print(f"Luminosité: {details['luminosite']['count']} indices ({details['luminosite']['total_score']} pts)")

if __name__ == "__main__":
    test_contextual_analysis()
