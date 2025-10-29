#!/usr/bin/env python3
"""
Analyse honnête de l'exposition
Ne fait que des déductions basées sur des faits concrets
"""

import json
import re
from typing import Dict, List, Optional

class HonestExpositionAnalyzer:
    """Analyseur honnête de l'exposition - pas de suppositions"""
    
    def __init__(self):
        # Mots-clés d'exposition explicites uniquement
        self.explicit_exposition = {
            'sud': ['exposition sud', 'plein sud', 'orientation sud', 'sud'],
            'sud_ouest': ['exposition sud-ouest', 'sud-ouest', 'sud ouest'],
            'ouest': ['exposition ouest', 'ouest', 'couchant'],
            'est': ['exposition est', 'est', 'levant'],
            'nord': ['exposition nord', 'nord'],
            'nord_est': ['exposition nord-est', 'nord-est', 'nord est']
        }
        
        # Mots-clés de luminosité
        self.luminosite_keywords = {
            'excellent': ['très lumineux', 'très clair', 'plein de lumière', 'très ensoleillé'],
            'bon': ['lumineux', 'clair', 'bien éclairé', 'ensoleillé'],
            'moyen': ['assez lumineux', 'correctement éclairé'],
            'faible': ['peu lumineux', 'sombre', 'peu éclairé']
        }
        
        # Mots-clés de vue
        self.vue_keywords = {
            'excellent': ['vue dégagée', 'vue panoramique', 'vue sur parc', 'pas de vis-à-vis'],
            'bon': ['vue correcte', 'vue agréable', 'vue sur rue calme'],
            'moyen': ['vue limitée', 'vue partiellement obstruée'],
            'faible': ['vis-à-vis', 'vue obstruée', 'pas de vue']
        }
    
    def analyze_honest_exposition(self, apartment_data: Dict) -> Dict:
        """Analyse honnête de l'exposition - uniquement des faits"""
        try:
            description = apartment_data.get('description', '')
            caracteristiques = apartment_data.get('caracteristiques', '')
            localisation = apartment_data.get('localisation', '')
            
            # Combiner tous les textes
            text = f"{description} {caracteristiques} {localisation}".lower()
            
            # 1. Chercher une exposition explicite
            exposition_explicite = self._find_explicit_exposition(text)
            
            # 2. Analyser la luminosité mentionnée
            luminosite = self._analyze_luminosite(text)
            
            # 3. Analyser la vue mentionnée
            vue = self._analyze_vue(text)
            
            # 4. Analyser les indices architecturaux (sans suppositions)
            indices_architecturaux = self._analyze_architectural_facts(text)
            
            # 5. Calculer le score basé sur les faits uniquement
            score, tier, justification = self._calculate_honest_score(
                exposition_explicite, luminosite, vue, indices_architecturaux
            )
            
            return {
                'exposition': exposition_explicite,
                'score': score,
                'tier': tier,
                'justification': justification,
                'confidence': 1.0 if exposition_explicite else 0.3,
                'details': {
                    'exposition_explicite': exposition_explicite,
                    'luminosite': luminosite,
                    'vue': vue,
                    'indices_architecturaux': indices_architecturaux,
                    'method': 'honest_analysis'
                }
            }
            
        except Exception as e:
            return {
                'exposition': None,
                'score': 3,
                'tier': 'tier3',
                'justification': f'Erreur analyse honnête: {e}',
                'confidence': 0.0,
                'details': {}
            }
    
    def _find_explicit_exposition(self, text: str) -> Optional[str]:
        """Trouve une exposition explicitement mentionnée"""
        for exposition, keywords in self.explicit_exposition.items():
            for keyword in keywords:
                if keyword in text:
                    return exposition
        return None
    
    def _analyze_luminosite(self, text: str) -> Dict:
        """Analyse la luminosité mentionnée"""
        for level, keywords in self.luminosite_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return {
                        'level': level,
                        'keyword': keyword,
                        'score': self._get_luminosite_score(level)
                    }
        return {'level': 'inconnue', 'keyword': None, 'score': 5}
    
    def _analyze_vue(self, text: str) -> Dict:
        """Analyse la vue mentionnée"""
        for level, keywords in self.vue_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return {
                        'level': level,
                        'keyword': keyword,
                        'score': self._get_vue_score(level)
                    }
        return {'level': 'inconnue', 'keyword': None, 'score': 5}
    
    def _analyze_architectural_facts(self, text: str) -> Dict:
        """Analyse les faits architecturaux (sans suppositions)"""
        facts = {
            'duplex': 'duplex' in text,
            'balcon': 'balcon' in text,
            'terrasse': 'terrasse' in text,
            'jardin': 'jardin' in text,
            'cuisine_ouverte': 'cuisine américaine' in text or 'cuisine ouverte' in text,
            'etage_eleve': any(etage in text for etage in ['4ème', '5ème', '6ème', '7ème', '8ème'])
        }
        
        # Compter les faits positifs
        positive_facts = sum(1 for fact in facts.values() if fact)
        
        return {
            'facts': facts,
            'count': positive_facts,
            'score': min(10, positive_facts * 2)  # 2 points par fait
        }
    
    def _get_luminosite_score(self, level: str) -> int:
        """Retourne le score de luminosité"""
        scores = {'excellent': 10, 'bon': 7, 'moyen': 5, 'faible': 3}
        return scores.get(level, 5)
    
    def _get_vue_score(self, level: str) -> int:
        """Retourne le score de vue"""
        scores = {'excellent': 10, 'bon': 7, 'moyen': 5, 'faible': 3}
        return scores.get(level, 5)
    
    def _calculate_honest_score(self, exposition, luminosite, vue, indices) -> tuple:
        """Calcule le score honnête basé sur les faits"""
        if exposition:
            # Exposition explicite trouvée
            exposition_scores = {
                'sud': 10, 'sud_ouest': 10, 'ouest': 7, 'est': 7, 'nord': 3, 'nord_est': 3
            }
            score = exposition_scores.get(exposition, 5)
            tier = 'tier1' if score >= 10 else 'tier2' if score >= 7 else 'tier3'
            justification = f"Exposition {exposition} explicitement mentionnée"
        else:
            # Pas d'exposition explicite - basé sur luminosité et indices
            luminosite_score = luminosite['score']
            vue_score = vue['score']
            architectural_score = indices['score']
            
            # Score basé sur ce qu'on sait vraiment
            score = max(luminosite_score, vue_score, architectural_score)
            
            if score >= 8:
                tier = 'tier2'
            elif score >= 5:
                tier = 'tier3'
            else:
                tier = 'tier3'
            
            # Justification honnête
            justifications = []
            if luminosite['keyword']:
                justifications.append(f"Luminosité: {luminosite['keyword']}")
            if vue['keyword']:
                justifications.append(f"Vue: {vue['keyword']}")
            if indices['count'] > 0:
                justifications.append(f"Indices architecturaux: {indices['count']}")
            
            if justifications:
                justification = f"Basé sur: {'; '.join(justifications)}. Exposition non spécifiée."
            else:
                justification = "Aucune information sur l'exposition disponible"
        
        return score, tier, justification

def test_honest_analysis():
    """Test de l'analyse honnête"""
    analyzer = HonestExpositionAnalyzer()
    
    # Charger les données de l'appartement test
    try:
        with open('data/appartements/90931157.json', 'r') as f:
            apartment_data = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier de données non trouvé")
        return
    
    print("🔍 ANALYSE HONNÊTE DE L'EXPOSITION")
    print("=" * 60)
    
    result = analyzer.analyze_honest_exposition(apartment_data)
    
    print(f"Exposition: {result['exposition'] or 'Non spécifiée'}")
    print(f"Score: {result['score']}/10")
    print(f"Tier: {result['tier']}")
    print(f"Confiance: {result['confidence']:.2f}")
    print(f"Justification: {result['justification']}")
    print()
    
    print("📊 DÉTAILS:")
    details = result['details']
    print(f"   Exposition explicite: {details['exposition_explicite']}")
    print(f"   Luminosité: {details['luminosite']['level']} ({details['luminosite']['keyword']})")
    print(f"   Vue: {details['vue']['level']} ({details['vue']['keyword']})")
    print(f"   Indices architecturaux: {details['indices_architecturaux']['count']}")
    print(f"   Méthode: {details['method']}")

if __name__ == "__main__":
    test_honest_analysis()
