#!/usr/bin/env python3
"""
Diagnostic du mega score - Vérifie le calcul du mega score pour tous les appartements
"""

import json
import os
# Ne pas importer BaignoireExtractor pour éviter les blocages lors du diagnostic


def load_scored_apartments():
    """Charge les appartements scorés"""
    try:
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Fichier data/scores/all_apartments_scores.json non trouvé")
        return []


def calculate_mega_score_new(apartment):
    """Calcule le mega score avec la nouvelle méthode (corrigée) - SEULEMENT 5 critères à 20pts chacun"""
    scores_detaille = apartment.get('scores_detaille', {})
    
    # SEULEMENT les 5 critères de scoring à 20pts chacun (exclure etage, surface, vue, baignoire qui sont des indices)
    scored_criteria = ['localisation', 'prix', 'style', 'ensoleillement', 'cuisine']
    mega_score = 0
    
    # Calculer depuis scores_detaille uniquement pour les critères de scoring
    for key in scored_criteria:
        if key in scores_detaille:
            criterion = scores_detaille[key]
            if isinstance(criterion, dict):
                mega_score += criterion.get('score', 0)
    
    # Ajouter les bonus/malus si disponibles
    bonus = apartment.get('bonus', 0)
    malus = apartment.get('malus', 0)
    mega_score += bonus - malus
    
    return round(mega_score, 1)


def calculate_mega_score_old(apartment):
    """Calcule le mega score avec l'ancienne méthode (buggée)"""
    scores_detaille = apartment.get('scores_detaille', {})
    mega_score = 0
    
    # Ancien calcul : seulement les critères dans criteria_mapping
    criteria_mapping = {
        'localisation': {'max': 20},
        'prix': {'max': 20},
        'style': {'max': 20},
        'ensoleillement': {'max': 10},
        'cuisine': {'max': 10},
        'baignoire': {'max': 10}
    }
    
    for key, info in criteria_mapping.items():
        if key == 'baignoire':
            # Utiliser directement depuis scores_detaille si disponible
            if key in scores_detaille:
                criterion = scores_detaille[key]
                mega_score += criterion.get('score', 0)
            # Sinon, ne pas appeler extract_baignoire_ultimate pour éviter les blocages
        elif key in scores_detaille:
            criterion = scores_detaille[key]
            mega_score += criterion.get('score', 0)
    
    return round(mega_score, 1)


def main():
    """Fonction principale de diagnostic"""
    print("🔍 Diagnostic du Mega Score")
    print("=" * 60)
    
    apartments = load_scored_apartments()
    if not apartments:
        return
    
    print(f"\n📊 Analyse de {len(apartments)} appartements\n")
    
    differences = []
    total_score_missing = 0
    
    for apt in apartments:
        apt_id = apt.get('id', 'Unknown')
        score_total = apt.get('score_total', None)
        
        # Calculer avec l'ancienne méthode
        old_score = calculate_mega_score_old(apt)
        
        # Calculer avec la nouvelle méthode
        new_score = calculate_mega_score_new(apt)
        
        # Vérifier la différence
        diff = new_score - old_score
        
        if diff != 0 or score_total != new_score:
            differences.append({
                'id': apt_id,
                'score_total': score_total,
                'old_mega_score': old_score,
                'new_mega_score': new_score,
                'difference': diff,
                'missing_criteria': []
            })
            
            # Identifier les critères incorrectement inclus (etage, surface, vue, baignoire ne doivent PAS être dans le score)
            scores_detaille = apt.get('scores_detaille', {})
            scored_criteria = ['localisation', 'prix', 'style', 'ensoleillement', 'cuisine']
            all_criteria = list(scores_detaille.keys())
            
            # Critères qui ne devraient PAS être comptés dans le score (mais sont des indices)
            incorrectly_included = [c for c in all_criteria if c not in scored_criteria]
            if incorrectly_included:
                differences[-1]['missing_criteria'] = incorrectly_included
            
            if score_total is not None and abs(score_total - new_score) > 0.1:
                total_score_missing += abs(score_total - new_score)
    
    # Afficher les résultats
    if differences:
        print(f"⚠️  {len(differences)} appartements avec des différences détectées:\n")
        
        for diff_info in differences[:10]:  # Afficher les 10 premiers
            print(f"📌 Appartement {diff_info['id']}:")
            print(f"   Score total (stored): {diff_info['score_total']}")
            print(f"   Ancien mega score: {diff_info['old_mega_score']}")
            print(f"   Nouveau mega score: {diff_info['new_mega_score']}")
            print(f"   Différence: {diff_info['difference']:+}")
            if diff_info['missing_criteria']:
                print(f"   Critères manquants dans l'ancien calcul: {', '.join(diff_info['missing_criteria'])}")
            print()
        
        if len(differences) > 10:
            print(f"   ... et {len(differences) - 10} autres appartements\n")
        
        print(f"📊 Résumé:")
        print(f"   - Appartements avec différences: {len(differences)}")
        print(f"   - Différence moyenne: {sum(d['difference'] for d in differences) / len(differences):.1f} points")
        print(f"   - Différence maximale: {max(d['difference'] for d in differences):.1f} points")
        if total_score_missing > 0:
            print(f"   - Écart total avec score_total: {total_score_missing:.1f} points")
    else:
        print("✅ Aucune différence détectée - tous les mega scores sont corrects!")
    
    # Statistiques générales
    print(f"\n📈 Statistiques générales:")
    new_scores = [calculate_mega_score_new(apt) for apt in apartments]
    old_scores = [calculate_mega_score_old(apt) for apt in apartments]
    
    print(f"   Ancien mega score moyen: {sum(old_scores) / len(old_scores):.1f}")
    print(f"   Nouveau mega score moyen: {sum(new_scores) / len(new_scores):.1f}")
    print(f"   Score total moyen (stored): {sum(apt.get('score_total', 0) for apt in apartments) / len(apartments):.1f}")


if __name__ == "__main__":
    main()

