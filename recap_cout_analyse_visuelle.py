#!/usr/bin/env python3
"""
Script pour calculer le coût des analyses visuelles par appartement.
Analyse les coûts pour : style, baignoire, cuisine ouverte, hauteur plafond, taille pièce de vie, distance vis-à-vis
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

# Coûts estimés OpenAI Vision API (gpt-4o-mini)
# Prix approximatifs basés sur le nombre de photos analysées
COUT_PAR_PHOTO = 0.002  # ~$0.002 par photo analysée (estimation conservatrice)
COUT_MIN_PAR_ANALYSE = 0.005  # Coût minimum même pour 1 photo

# Types d'analyses visuelles
ANALYSES_VISUELLES = {
    'style': {
        'nom': 'Style',
        'description': 'Analyse du style (moderne, haussmannien, etc.)'
    },
    'cuisine': {
        'nom': 'Cuisine ouverte',
        'description': 'Détection si la cuisine est ouverte ou fermée'
    },
    'baignoire': {
        'nom': 'Baignoire',
        'description': 'Détection de la présence d\'une baignoire'
    },
    'hauteur_plafond': {
        'nom': 'Hauteur plafond',
        'description': 'Estimation de la hauteur sous plafond'
    },
    'large_piece_vie': {
        'nom': 'Taille pièce de vie',
        'description': 'Analyse de la taille de la pièce de vie'
    },
    'distance_vis_a_vis': {
        'nom': 'Distance vis-à-vis',
        'description': 'Estimation de la distance vis-à-vis'
    }
}


def compter_photos_analysees(analyse_data: Dict) -> int:
    """Compte le nombre de photos analysées dans une analyse."""
    if not analyse_data or not isinstance(analyse_data, dict):
        return 0
    
    # Chercher dans différents formats de données
    details = analyse_data.get('details')
    if details is None:
        details = {}
    elif not isinstance(details, dict):
        details = {}
    
    # Format pour cuisine
    if 'photo_validation' in details:
        photo_validation = details.get('photo_validation', {})
        if isinstance(photo_validation, dict):
            photo_result = photo_validation.get('photo_result', {})
            if isinstance(photo_result, dict) and 'photos_analyzed' in photo_result:
                return photo_result.get('photos_analyzed', 0)
    
    # Format pour baignoire
    if 'photo_validation' in details:
        photo_validation = details.get('photo_validation', {})
        if isinstance(photo_validation, dict):
            cross_validation = photo_validation.get('cross_validation', {})
            if isinstance(cross_validation, dict):
                photo_result = cross_validation.get('photo_result', {})
                if isinstance(photo_result, dict) and 'photos_analyzed' in photo_result:
                    return photo_result.get('photos_analyzed', 0)
    
    # Format pour style (dans style_analysis)
    if 'photos_analyzed' in analyse_data:
        return analyse_data.get('photos_analyzed', 0)
    
    if 'individual_analyses' in analyse_data:
        individual = analyse_data.get('individual_analyses', [])
        if isinstance(individual, list):
            return len(individual)
    
    # Si on trouve des detected_photos, utiliser leur nombre
    if 'detected_photos' in str(analyse_data):
        # Chercher dans les détails
        for key in ['photo_result', 'photo_validation', 'cross_validation']:
            if key in str(details):
                result = details.get(key, {})
                if isinstance(result, dict):
                    detected = result.get('detected_photos', [])
                    if detected:
                        return len(detected) if isinstance(detected, list) else 1
    
    return 0


def calculer_cout_analyse(nb_photos: int) -> float:
    """Calcule le coût d'une analyse en fonction du nombre de photos."""
    if nb_photos == 0:
        return 0.0
    cout = max(COUT_MIN_PAR_ANALYSE, nb_photos * COUT_PAR_PHOTO)
    return round(cout, 4)


def analyser_appartement(apt: Dict) -> Dict:
    """Analyse les coûts d'analyse visuelle pour un appartement."""
    apt_id = apt.get('id', 'unknown')
    scores_detaille = apt.get('scores_detaille', {})
    style_analysis = apt.get('style_analysis', {})
    
    resultat = {
        'id': apt_id,
        'titre': apt.get('titre', ''),
        'url': apt.get('url', ''),
        'analyses': {},
        'total_photos_analysees': 0,
        'cout_total': 0.0
    }
    
    # Analyse du style
    if 'style' in scores_detaille or style_analysis:
        style_data = scores_detaille.get('style', {}) or style_analysis
        nb_photos = compter_photos_analysees(style_data)
        if nb_photos == 0 and style_analysis:
            # Essayer de compter depuis style_analysis
            nb_photos = style_analysis.get('photos_analyzed', 0)
            if nb_photos == 0 and 'individual_analyses' in style_analysis:
                nb_photos = len(style_analysis.get('individual_analyses', []))
        
        if nb_photos > 0:
            cout = calculer_cout_analyse(nb_photos)
            resultat['analyses']['style'] = {
                'nb_photos': nb_photos,
                'cout': cout,
                'present': True
            }
            resultat['total_photos_analysees'] += nb_photos
            resultat['cout_total'] += cout
    
    # Analyse de la cuisine
    if 'cuisine' in scores_detaille:
        cuisine_data = scores_detaille.get('cuisine', {})
        nb_photos = compter_photos_analysees(cuisine_data)
        if nb_photos > 0:
            cout = calculer_cout_analyse(nb_photos)
            resultat['analyses']['cuisine'] = {
                'nb_photos': nb_photos,
                'cout': cout,
                'present': True
            }
            resultat['total_photos_analysees'] += nb_photos
            resultat['cout_total'] += cout
    
    # Analyse de la baignoire
    if 'baignoire' in scores_detaille:
        baignoire_data = scores_detaille.get('baignoire', {})
        nb_photos = compter_photos_analysees(baignoire_data)
        if nb_photos > 0:
            cout = calculer_cout_analyse(nb_photos)
            resultat['analyses']['baignoire'] = {
                'nb_photos': nb_photos,
                'cout': cout,
                'present': True
            }
            resultat['total_photos_analysees'] += nb_photos
            resultat['cout_total'] += cout
    
    # Arrondir le coût total
    resultat['cout_total'] = round(resultat['cout_total'], 4)
    
    return resultat


def generer_recap(data_file: str, output_file: Optional[str] = None) -> Dict:
    """Génère un récapitulatif des coûts d'analyse visuelle."""
    print(f"📊 Lecture des données depuis {data_file}...")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        if isinstance(data, dict):
            data = list(data.values())
        else:
            print("❌ Format de données non reconnu")
            return {}
    
    print(f"✅ {len(data)} appartements trouvés\n")
    
    resultats = []
    total_cout = 0.0
    total_photos = 0
    stats_analyses = defaultdict(int)
    
    for apt in data:
        resultat = analyser_appartement(apt)
        resultats.append(resultat)
        total_cout += resultat['cout_total']
        total_photos += resultat['total_photos_analysees']
        
        for analyse_type in resultat['analyses']:
            stats_analyses[analyse_type] += 1
    
    # Trier par coût décroissant
    resultats.sort(key=lambda x: x['cout_total'], reverse=True)
    
    recap = {
        'date_generation': datetime.now().isoformat(),
        'fichier_source': data_file,
        'total_appartements': len(data),
        'appartements_avec_analyses': len([r for r in resultats if r['cout_total'] > 0]),
        'total_cout_usd': round(total_cout, 2),
        'total_photos_analysees': total_photos,
        'statistiques_analyses': dict(stats_analyses),
        'cout_moyen_par_appartement': round(total_cout / len(data), 4) if data else 0,
        'details_par_appartement': resultats
    }
    
    # Sauvegarder le récapitulatif
    if output_file is None:
        output_file = f"recap_cout_analyse_visuelle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recap, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Récapitulatif sauvegardé dans {output_file}\n")
    
    return recap


def afficher_recap(recap: Dict):
    """Affiche un récapitulatif formaté."""
    print("=" * 80)
    print("📊 RÉCAPITULATIF DES COÛTS D'ANALYSE VISUELLE PAR APPARTEMENT")
    print("=" * 80)
    print()
    
    print(f"📁 Fichier source: {recap['fichier_source']}")
    print(f"📅 Date de génération: {recap['date_generation']}")
    print()
    
    print("📈 STATISTIQUES GLOBALES")
    print("-" * 80)
    print(f"Total appartements analysés: {recap['total_appartements']}")
    print(f"Appartements avec analyses visuelles: {recap['appartements_avec_analyses']}")
    print(f"Total photos analysées: {recap['total_photos_analysees']}")
    print(f"💰 Coût total estimé: ${recap['total_cout_usd']:.2f} USD")
    print(f"💰 Coût moyen par appartement: ${recap['cout_moyen_par_appartement']:.4f} USD")
    print()
    
    print("📊 RÉPARTITION DES ANALYSES")
    print("-" * 80)
    for analyse_type, count in recap['statistiques_analyses'].items():
        nom = ANALYSES_VISUELLES.get(analyse_type, {}).get('nom', analyse_type)
        print(f"  • {nom}: {count} appartements")
    print()
    
    print("🏆 TOP 10 APPARTEMENTS PAR COÛT")
    print("-" * 80)
    top_10 = recap['details_par_appartement'][:10]
    for i, apt in enumerate(top_10, 1):
        print(f"{i:2d}. Appartement {apt['id']} - ${apt['cout_total']:.4f}")
        print(f"    {apt['titre'][:60]}...")
        analyses_str = ", ".join([f"{k}: {v['nb_photos']} photos" for k, v in apt['analyses'].items()])
        print(f"    Analyses: {analyses_str}")
        print()
    
    print("=" * 80)


def main():
    """Fonction principale."""
    import sys
    
    # Chercher le fichier de données
    data_file = None
    
    # Essayer plusieurs emplacements possibles
    possible_paths = [
        '/Users/sou/Desktop/CURSOR/HomeScore/data/scores/all_apartments_scores.json',
        '/Users/sou/Desktop/CURSOR/HomeScore/data/paris_apartments.json',
        'data/scores/all_apartments_scores.json',
        'data/paris_apartments.json'
    ]
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        for path in possible_paths:
            if os.path.exists(path):
                data_file = path
                break
    
    if not data_file or not os.path.exists(data_file):
        print("❌ Fichier de données non trouvé")
        print("Usage: python recap_cout_analyse_visuelle.py [chemin_vers_fichier.json]")
        return
    
    # Générer le récapitulatif
    recap = generer_recap(data_file)
    
    # Afficher le récapitulatif
    afficher_recap(recap)
    
    # Générer aussi un fichier markdown lisible
    output_md = f"RECAP_COUT_ANALYSE_VISUELLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(f"# 📊 Récapitulatif des coûts d'analyse visuelle par appartement\n\n")
        f.write(f"**Date de génération:** {recap['date_generation']}\n")
        f.write(f"**Fichier source:** {recap['fichier_source']}\n\n")
        
        f.write(f"## 📈 Statistiques globales\n\n")
        f.write(f"- **Total appartements analysés:** {recap['total_appartements']}\n")
        f.write(f"- **Appartements avec analyses visuelles:** {recap['appartements_avec_analyses']}\n")
        f.write(f"- **Total photos analysées:** {recap['total_photos_analysees']}\n")
        f.write(f"- **💰 Coût total estimé:** ${recap['total_cout_usd']:.2f} USD\n")
        f.write(f"- **💰 Coût moyen par appartement:** ${recap['cout_moyen_par_appartement']:.4f} USD\n\n")
        
        f.write(f"## 📊 Répartition des analyses\n\n")
        for analyse_type, count in recap['statistiques_analyses'].items():
            nom = ANALYSES_VISUELLES.get(analyse_type, {}).get('nom', analyse_type)
            f.write(f"- **{nom}:** {count} appartements\n")
        f.write("\n")
        
        f.write(f"## 🏠 Détails par appartement\n\n")
        f.write("| ID | Titre | Style | Cuisine | Baignoire | Total Photos | Coût (USD) |\n")
        f.write("|----|-------|-------|---------|-----------|--------------|------------|\n")
        
        for apt in recap['details_par_appartement']:
            if apt['cout_total'] > 0:
                style_info = apt['analyses'].get('style', {})
                cuisine_info = apt['analyses'].get('cuisine', {})
                baignoire_info = apt['analyses'].get('baignoire', {})
                
                style_str = f"{style_info.get('nb_photos', 0)} photos" if style_info else "-"
                cuisine_str = f"{cuisine_info.get('nb_photos', 0)} photos" if cuisine_info else "-"
                baignoire_str = f"{baignoire_info.get('nb_photos', 0)} photos" if baignoire_info else "-"
                
                titre_court = apt['titre'][:50] + "..." if len(apt['titre']) > 50 else apt['titre']
                
                f.write(f"| {apt['id']} | {titre_court} | {style_str} | {cuisine_str} | {baignoire_str} | {apt['total_photos_analysees']} | ${apt['cout_total']:.4f} |\n")
    
    print(f"📄 Récapitulatif Markdown sauvegardé dans {output_md}")


if __name__ == '__main__':
    main()

