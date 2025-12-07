#!/usr/bin/env python3
"""
Script pour analyser tous les screenshots de carte et extraire un quartier précis
pour chaque appartement, puis mettre à jour les JSON
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

class QuartierAnalyzer:
    """Analyseur de quartiers pour Paris 19e"""
    
    def __init__(self):
        # Base de données complète des quartiers du 19e avec leurs rues et métros caractéristiques
        self.quartiers_data = {
            "Buttes-Chaumont": {
                "rues": [
                    "Botzaris", "Secrétan", "Manin", "Crimée", "Armand-Carrel",
                    "Rue Botzaris", "Avenue Secrétan", "Rue Manin", "Rue de Crimée",
                    "Rue Armand-Carrel", "Square Botzaris", "Avenue Jean-Jaurès"
                ],
                "metros": ["Botzaris", "Crimée", "Jaurès"],
                "description": "Quartier autour du parc des Buttes-Chaumont"
            },
            "Place des Fêtes": {
                "rues": [
                    "Carducci", "Mélingue", "Alouettes", "Villette", "Pré-Saint-Gervais",
                    "Rue Carducci", "Rue Mélingue", "Rue des Alouettes", "Rue de la Villette",
                    "Rue du Pré-Saint-Gervais", "Place des Fêtes", "Rue Haxo"
                ],
                "metros": ["Place des Fêtes", "Pré-Saint-Gervais", "Télégraphe"],
                "description": "Quartier de la Place des Fêtes"
            },
            "Jourdain": {
                "rues": [
                    "Belleville", "Pelleport", "Mouzaïa", "Compans", "Jourdain",
                    "Rue de Belleville", "Rue Pelleport", "Rue de Mouzaïa", "Rue Compans",
                    "Rue du Jourdain", "Villa de Belleville"
                ],
                "metros": ["Jourdain", "Place des Fêtes", "Télégraphe"],
                "description": "Quartier du Jourdain"
            },
            "Pyrénées": {
                "rues": [
                    "Pradier", "Clavel", "Rébeval", "Levert", "Pyrénées",
                    "Rue Pradier", "Rue Clavel", "Rue Rébeval", "Rue Levert",
                    "Avenue des Pyrénées", "Rue de Belleville"
                ],
                "metros": ["Pyrénées", "Belleville", "Jourdain"],
                "description": "Quartier des Pyrénées"
            },
            "Belleville": {
                "rues": [
                    "Belleville", "Faubourg du Temple", "Villette", "Ménilmontant",
                    "Rue de Belleville", "Rue du Faubourg du Temple", "Boulevard de la Villette",
                    "Rue de Ménilmontant", "Boulevard Belleville"
                ],
                "metros": ["Belleville", "Couronnes", "Ménilmontant"],
                "description": "Quartier de Belleville (partie 19e)"
            },
            "Canal de l'Ourcq": {
                "rues": [
                    "Loire", "Seine", "Ourcq", "Quai de la Loire", "Quai de la Seine",
                    "Rue de l'Ourcq", "Canal de l'Ourcq", "Bassin de la Villette"
                ],
                "metros": ["Riquet", "Crimée", "Jaurès"],
                "description": "Quartier le long du Canal de l'Ourcq"
            },
            "Crimée": {
                "rues": [
                    "Crimée", "Rue de Crimée", "Avenue de Flandre", "Quai de la Loire",
                    "Rue de la Villette", "Boulevard de la Villette"
                ],
                "metros": ["Crimée", "Riquet", "Corentin Cariou"],
                "description": "Quartier de Crimée"
            },
            "Pont de Flandre": {
                "rues": [
                    "Flandre", "Avenue de Flandre", "Rue d'Aubervilliers", "Rue de l'Évangile",
                    "Boulevard Macdonald"
                ],
                "metros": ["Corentin Cariou", "Porte de la Villette"],
                "description": "Quartier Pont de Flandre"
            },
            "La Villette": {
                "rues": [
                    "Villette", "Rue de la Villette", "Boulevard de la Villette", "Avenue Jean-Jaurès",
                    "Rue de Flandre"
                ],
                "metros": ["Porte de la Villette", "Corentin Cariou", "Jaurès"],
                "description": "Quartier de La Villette"
            },
            "Amérique": {
                "rues": [
                    "Rue de l'Ourcq", "Rue d'Aubervilliers", "Rue de la Villette",
                    "Avenue de Flandre", "Rue de Meaux"
                ],
                "metros": ["Riquet", "Crimée", "Porte de la Villette"],
                "description": "Quartier de l'Amérique"
            }
        }
    
    def analyze_apartment_quartier(self, apartment_data: Dict) -> Optional[str]:
        """Analyse le quartier d'un appartement basé sur ses données"""
        
        map_info = apartment_data.get('map_info', {})
        streets = map_info.get('streets', [])
        metros = map_info.get('metros', [])
        transports = apartment_data.get('transports', [])
        localisation = apartment_data.get('localisation', '').lower()
        
        # Détecter l'arrondissement depuis la localisation
        arrondissement = None
        if '19e' in localisation or '75019' in localisation:
            arrondissement = 19
        elif '11e' in localisation or '75011' in localisation:
            arrondissement = 11
        elif '20e' in localisation or '75020' in localisation:
            arrondissement = 20
        elif '10e' in localisation or '75010' in localisation:
            arrondissement = 10
        
        # Si c'est le 11e arrondissement, ajouter les quartiers du 11e
        quartiers_to_check = self.quartiers_data
        if arrondissement == 11:
            # Quartiers du 11e arrondissement
            quartiers_to_check = {
                **self.quartiers_data,  # Garder les quartiers du 19e au cas où
                "Nation": {
                    "rues": ["Nation", "Avenue du Trône", "Place de la Nation", "Rue de Picpus"],
                    "metros": ["Nation"],
                    "description": "Quartier de la Nation (11e)"
                },
                "Charonne": {
                    "rues": ["Charonne", "Rue de Charonne", "Avenue Philippe-Auguste"],
                    "metros": ["Charonne", "Philippe Auguste"],
                    "description": "Quartier de Charonne (11e)"
                },
                "Popincourt": {
                    "rues": ["Popincourt", "Rue Popincourt", "Rue de la Roquette"],
                    "metros": ["Voltaire", "Bréguet-Sabin"],
                    "description": "Quartier Popincourt (11e)"
                },
                "Roquette": {
                    "rues": ["Roquette", "Rue de la Roquette", "Avenue de la République"],
                    "metros": ["Voltaire", "Rue des Boulets"],
                    "description": "Quartier de la Roquette (11e)"
                },
                "Oberkampf": {
                    "rues": ["Oberkampf", "Rue Oberkampf", "Rue de Ménilmontant"],
                    "metros": ["Oberkampf", "Ménilmontant", "Parmentier"],
                    "description": "Quartier Oberkampf (11e)"
                },
                "République": {
                    "rues": ["République", "Place de la République", "Avenue de la République"],
                    "metros": ["République", "Oberkampf"],
                    "description": "Quartier République (11e)"
                }
            }
        
        # Combiner tous les transports (métros)
        all_metros = metros + transports
        # Enlever les doublons et normaliser
        all_metros = list(dict.fromkeys([m.strip() for m in all_metros if m and isinstance(m, str)]))
        
        # Nettoyer les rues aussi
        streets = [s.strip() for s in streets if s and isinstance(s, str)]
        
        # Analyser la description pour des indices
        description = apartment_data.get('description', '').lower()
        localisation = apartment_data.get('localisation', '').lower()
        
        # Scores pour chaque quartier
        quartier_scores = {}
        
        # Analyser les rues
        for quartier_name, quartier_info in quartiers_to_check.items():
            score = 0
            
            # Chercher dans les rues trouvées
            for rue in streets:
                rue_lower = rue.lower()
                for rue_quartier in quartier_info['rues']:
                    if rue_quartier.lower() in rue_lower or rue_lower in rue_quartier.lower():
                        score += 2  # Les rues sont très importantes
                        break
            
            # Chercher dans les métros
            for metro in all_metros:
                metro_lower = metro.lower()
                for metro_quartier in quartier_info['metros']:
                    if metro_quartier.lower() in metro_lower or metro_lower in metro_quartier.lower():
                        score += 3  # Les métros sont très révélateurs
                        break
            
            # Chercher dans la description et localisation
            text_to_search = f"{description} {localisation}"
            for rue_quartier in quartier_info['rues']:
                if rue_quartier.lower() in text_to_search:
                    score += 1
            
            for metro_quartier in quartier_info['metros']:
                if metro_quartier.lower() in text_to_search:
                    score += 2
            
            # Bonus pour mentions directes
            if quartier_name.lower() in text_to_search:
                score += 5
            
            if score > 0:
                quartier_scores[quartier_name] = score
        
        # Trouver le quartier avec le score le plus élevé
        if quartier_scores:
            best_quartier = max(quartier_scores, key=quartier_scores.get)
            best_score = quartier_scores[best_quartier]
            
            # Si le score est suffisamment élevé, on retourne le quartier
            if best_score >= 3:
                return best_quartier
            elif best_score >= 1:
                # Score faible, on peut quand même retourner avec une note
                return f"{best_quartier} (probable, score: {best_score})"
        
        return None
    
    def get_quartier_details(self, quartier_name: str) -> Dict:
        """Retourne les détails d'un quartier"""
        # Enlever les notes si présentes
        base_name = quartier_name.split(' (')[0]
        return self.quartiers_data.get(base_name, {})

def analyze_all_quartiers():
    """Analyse tous les appartements et met à jour les quartiers"""
    print("🏘️ ANALYSE DES QUARTIERS")
    print("=" * 70)
    
    # Charger tous les appartements
    scraped_file = Path("data/scraped_apartments.json")
    if not scraped_file.exists():
        print(f"❌ Fichier {scraped_file} non trouvé")
        return
    
    print(f"📋 Chargement des appartements depuis {scraped_file}...")
    with open(scraped_file, 'r', encoding='utf-8') as f:
        all_apartments = json.load(f)
    
    print(f"✅ {len(all_apartments)} appartements chargés\n")
    
    # Initialiser l'analyseur
    analyzer = QuartierAnalyzer()
    
    # Analyser chaque appartement
    results = {
        'updated': [],
        'already_has_quartier': [],
        'no_quartier_found': []
    }
    
    print("🔍 ANALYSE DES QUARTIERS...")
    print("=" * 70)
    
    for i, apt in enumerate(all_apartments, 1):
        apt_id = apt.get('id', 'N/A')
        map_info = apt.get('map_info', {})
        current_quartier = map_info.get('quartier', '')
        
        # Vérifier si le quartier est déjà précis (pas "Non identifié" ou avec score)
        if current_quartier and current_quartier != 'Non identifié' and current_quartier != 'Quartier non identifié' and not '(score:' in current_quartier:
            results['already_has_quartier'].append((apt_id, current_quartier))
            print(f"✅ Appartement {i}/{len(all_apartments)} ({apt_id}): Quartier déjà identifié: {current_quartier}")
            continue
        
        # Analyser le quartier
        quartier = analyzer.analyze_apartment_quartier(apt)
        
        if quartier:
            # Mettre à jour map_info
            map_info['quartier'] = quartier
            apt['map_info'] = map_info
            
            # Ajouter des détails si disponibles
            quartier_details = analyzer.get_quartier_details(quartier)
            if quartier_details:
                map_info['quartier_description'] = quartier_details.get('description', '')
            
            results['updated'].append((apt_id, quartier))
            print(f"✅ Appartement {i}/{len(all_apartments)} ({apt_id}): Quartier identifié: {quartier}")
        else:
            results['no_quartier_found'].append(apt_id)
            print(f"⚠️ Appartement {i}/{len(all_apartments)} ({apt_id}): Quartier non identifié")
    
    # Sauvegarder tous les appartements mis à jour
    print(f"\n{'='*70}")
    print(f"💾 Sauvegarde des appartements mis à jour...")
    with open(scraped_file, 'w', encoding='utf-8') as f:
        json.dump(all_apartments, f, ensure_ascii=False, indent=2)
    print(f"✅ Tous les appartements sauvegardés dans {scraped_file}")
    
    # Sauvegarder aussi chaque appartement individuellement
    appartements_dir = Path("data/appartements")
    appartements_dir.mkdir(exist_ok=True)
    
    for apt in all_apartments:
        apt_id = apt.get('id')
        if apt_id:
            apt_file = appartements_dir / f"{apt_id}.json"
            with open(apt_file, 'w', encoding='utf-8') as f:
                json.dump(apt, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Tous les appartements individuels sauvegardés\n")
    
    # Résumé
    print(f"{'='*70}")
    print("📊 RÉSUMÉ")
    print(f"{'='*70}")
    total = len(all_apartments)
    updated = len(results['updated'])
    already_has = len(results['already_has_quartier'])
    no_quartier = len(results['no_quartier_found'])
    
    print(f"Total d'appartements: {total}")
    print(f"✅ Quartiers identifiés/mis à jour: {updated}")
    print(f"✅ Quartiers déjà précis: {already_has}")
    print(f"⚠️ Quartiers non identifiés: {no_quartier}")
    
    if updated > 0:
        print(f"\n📋 QUARTIERS IDENTIFIÉS:")
        quartier_counts = {}
        for apt_id, quartier in results['updated']:
            base_quartier = quartier.split(' (')[0]
            quartier_counts[base_quartier] = quartier_counts.get(base_quartier, 0) + 1
        
        for quartier, count in sorted(quartier_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   🏘️ {quartier}: {count} appartement(s)")
    
    if no_quartier > 0:
        print(f"\n⚠️ APPARTEMENTS SANS QUARTIER IDENTIFIÉ:")
        for apt_id in results['no_quartier_found'][:10]:
            print(f"   ⚠️ {apt_id}")
        if len(results['no_quartier_found']) > 10:
            print(f"   ... et {len(results['no_quartier_found']) - 10} autres")
    
    if updated == 0 and already_has == total:
        print("\n🎉 Tous les appartements ont déjà un quartier précis !")
    elif updated > 0:
        print(f"\n🎉 {updated} quartier(s) identifié(s) et mis à jour avec succès !")

if __name__ == "__main__":
    analyze_all_quartiers()

