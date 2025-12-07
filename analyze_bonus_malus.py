#!/usr/bin/env python3
"""
Analyse détaillée des bonus/malus pour évaluer leur pertinence
"""

import json
import re

# Charger les données
with open('data/scores/all_apartments_scores.json', 'r') as f:
    apts = json.load(f)

with open('scoring_config.json', 'r') as f:
    config = json.load(f)

with open('data/scraped_apartments.json', 'r') as f:
    scraped = json.load(f)
scraped_dict = {apt['id']: apt for apt in scraped}

print("=" * 80)
print("📋 RÉCAPITULATIF COMPLET DES BONUS/MALUS")
print("=" * 80)
print()

bonus_values = config['bonus']
malus_values = config['malus']

print("✅ BONUS ACTUELS:")
print("-" * 80)
print(f"{'Élément':<25} {'Valeur':<10} {'Fréquence':<15} {'Pertinence'}")
print("-" * 80)

bonus_analysis = {
    'balcon': {'value': bonus_values['balcon'], 'freq': 0, 'total_pts': 0, 'comment': 'Balcon extérieur'},
    'terrasse': {'value': bonus_values['terrasse'], 'freq': 0, 'total_pts': 0, 'comment': 'Terrasse (plus grand que balcon)'},
    'ascenseur': {'value': bonus_values['ascenseur'], 'freq': 0, 'total_pts': 0, 'comment': 'Confort, surtout étages élevés'},
    'parking': {'value': bonus_values['parking'], 'freq': 0, 'total_pts': 0, 'comment': 'Stationnement privé'},
    'cave': {'value': bonus_values['cave'], 'freq': 0, 'total_pts': 0, 'comment': 'Stockage supplémentaire'},
    'croisement_rue': {'value': bonus_values['croisement_rue'], 'freq': 0, 'total_pts': 0, 'comment': 'Luminosité double exposition'},
    'vue_degagee': {'value': bonus_values['vue_degagee'], 'freq': 0, 'total_pts': 0, 'comment': 'Vue dégagée (pas de vis-à-vis)'},
    'place_reunion': {'value': bonus_values['place_reunion'], 'freq': 0, 'total_pts': 0, 'comment': 'Zone premium spécifique'}
}

for apt in apts:
    apt_id = apt.get('id')
    scraped_apt = scraped_dict.get(apt_id, {})
    if not scraped_apt:
        continue
    
    text = (scraped_apt.get('caracteristiques', '') + ' ' + scraped_apt.get('description', '')).lower()
    localisation = scraped_apt.get('localisation', '').lower()
    
    if 'balcon' in text:
        bonus_analysis['balcon']['freq'] += 1
        bonus_analysis['balcon']['total_pts'] += bonus_analysis['balcon']['value']
    if 'terrasse' in text:
        bonus_analysis['terrasse']['freq'] += 1
        bonus_analysis['terrasse']['total_pts'] += bonus_analysis['terrasse']['value']
    if 'ascenseur' in text:
        bonus_analysis['ascenseur']['freq'] += 1
        bonus_analysis['ascenseur']['total_pts'] += bonus_analysis['ascenseur']['value']
    if 'parking' in text:
        bonus_analysis['parking']['freq'] += 1
        bonus_analysis['parking']['total_pts'] += bonus_analysis['parking']['value']
    if 'cave' in text:
        bonus_analysis['cave']['freq'] += 1
        bonus_analysis['cave']['total_pts'] += bonus_analysis['cave']['value']
    if 'croisement' in text or 'croise' in text:
        bonus_analysis['croisement_rue']['freq'] += 1
        bonus_analysis['croisement_rue']['total_pts'] += bonus_analysis['croisement_rue']['value']
    if 'vue dégagée' in text or 'vue degagee' in text:
        bonus_analysis['vue_degagee']['freq'] += 1
        bonus_analysis['vue_degagee']['total_pts'] += bonus_analysis['vue_degagee']['value']
    if 'place de la réunion' in localisation:
        bonus_analysis['place_reunion']['freq'] += 1
        bonus_analysis['place_reunion']['total_pts'] += bonus_analysis['place_reunion']['value']

for name, data in bonus_analysis.items():
    if data['freq'] == len(apts):
        pertinence = "⚠️  PROBLÈME: Trouvé partout"
    elif data['freq'] == 0:
        pertinence = "❌ Jamais trouvé"
    elif data['freq'] < len(apts) * 0.3:
        pertinence = "✅ Rare (pertinent)"
    else:
        pertinence = "✅ Fréquent"
    print(f"{name:<25} {data['value']:>3} pts   {data['freq']:>2}/{len(apts):<2} appartements  {pertinence}")
    print(f"  └─ {data['comment']}")

print()
print("❌ MALUS ACTUELS:")
print("-" * 80)
print(f"{'Élément':<30} {'Valeur':<10} {'Fréquence':<15} {'Pertinence'}")
print("-" * 80)

malus_analysis = {
    'vis_a_vis': {'value': malus_values['vis_a_vis'], 'freq': 0, 'total_pts': 0, 'comment': 'Vis-à-vis = moins de lumière'},
    'nord': {'value': malus_values['nord'], 'freq': 0, 'total_pts': 0, 'comment': 'Exposition Nord = peu de soleil'},
    'rdc': {'value': malus_values['rdc'], 'freq': 0, 'total_pts': 0, 'comment': 'Rez-de-chaussée = sécurité/privacy'},
    'sans_ascenseur_etage_eleve': {'value': malus_values['sans_ascenseur_etage_eleve'], 'freq': 0, 'total_pts': 0, 'comment': 'Étage élevé sans ascenseur'},
    'annees_60_70': {'value': malus_values['annees_60_70'], 'freq': 0, 'total_pts': 0, 'comment': 'Style années 60-70 = veto'}
}

for apt in apts:
    apt_id = apt.get('id')
    scraped_apt = scraped_dict.get(apt_id, {})
    if not scraped_apt:
        continue
    
    text = (scraped_apt.get('caracteristiques', '') + ' ' + scraped_apt.get('description', '')).lower()
    etage = scraped_apt.get('etage', '')
    style_analysis = scraped_apt.get('style_analysis', {})
    style_type = style_analysis.get('style', {}).get('type', '').lower()
    
    if 'vis-à-vis' in text or 'vis à vis' in text:
        malus_analysis['vis_a_vis']['freq'] += 1
        malus_analysis['vis_a_vis']['total_pts'] += abs(malus_analysis['vis_a_vis']['value'])
    if 'nord' in text and ('exposition' in text or 'orientation' in text):
        malus_analysis['nord']['freq'] += 1
        malus_analysis['nord']['total_pts'] += abs(malus_analysis['nord']['value'])
    if 'rdc' in text or 'rez' in text:
        malus_analysis['rdc']['freq'] += 1
        malus_analysis['rdc']['total_pts'] += abs(malus_analysis['rdc']['value'])
    # Vérifier étage élevé sans ascenseur
    etage_match = re.search(r'(\d+)', str(etage))
    if etage_match:
        etage_num = int(etage_match.group(1))
        if etage_num >= 5 and 'ascenseur' not in text:
            malus_analysis['sans_ascenseur_etage_eleve']['freq'] += 1
            malus_analysis['sans_ascenseur_etage_eleve']['total_pts'] += abs(malus_analysis['sans_ascenseur_etage_eleve']['value'])
    if '70' in style_type or '60' in style_type or 'seventies' in style_type:
        malus_analysis['annees_60_70']['freq'] += 1
        malus_analysis['annees_60_70']['total_pts'] += abs(malus_analysis['annees_60_70']['value'])

for name, data in malus_analysis.items():
    if data['freq'] == 0:
        pertinence = "❌ Jamais appliqué"
    elif data['freq'] < len(apts) * 0.2:
        pertinence = "✅ Rare (pertinent)"
    else:
        pertinence = "✅ Fréquent"
    print(f"{name:<30} {data['value']:>4} pts   {data['freq']:>2}/{len(apts):<2} appartements  {pertinence}")
    print(f"  └─ {data['comment']}")

print()
print("=" * 80)
print("💡 ANALYSE DE PERTINENCE")
print("=" * 80)
print()

total_bonus_pts = sum(data['total_pts'] for data in bonus_analysis.values())
total_malus_pts = sum(data['total_pts'] for data in malus_analysis.values())

print(f"📊 IMPACT TOTAL:")
print(f"   Bonus moyen par appartement: {total_bonus_pts / len(apts):.1f} pts")
print(f"   Malus moyen par appartement: {total_malus_pts / len(apts):.1f} pts")
print(f"   Net moyen: {(total_bonus_pts - total_malus_pts) / len(apts):.1f} pts")
print()

print("⚠️  PROBLÈMES MAJEURS DÉTECTÉS:")
print("  1. ⚠️  TOUS les appartements ont balcon/terrasse/ascenseur/parking/cave")
print("     → Le champ 'caractéristiques' semble être une liste complète")
print("       de TOUTES les caractéristiques possibles, pas seulement celles présentes")
print("     → Résultat: Bonus systématique de +10 pts pour tous les appartements")
print()
print("  2. ❌ Bonus jamais trouvés:")
print("     - vue_degagee: 0 fois (2 pts)")
print("     - place_reunion: 0 fois (5 pts)")
print()
print("  3. ❌ Malus jamais appliqués:")
print("     - sans_ascenseur_etage_eleve: Logique non implémentée")
print("     - annees_60_70: Déjà géré dans score_style (0 pts), double pénalité évitée")
print()

print("💡 RECOMMANDATIONS:")
print("=" * 80)
print()
print("1. 🔍 VÉRIFIER LA STRUCTURE DES DONNÉES")
print("   → Examiner si 'caractéristiques' est une liste de cases à cocher")
print("   → Peut-être parser différemment (regex, split, etc.)")
print()
print("2. ✅ BONUS PERTINENTS À GARDER:")
print("   - croisement_rue: 2 pts (1/17) ✅")
print("   - place_reunion: 5 pts (0/17 mais zone spécifique) ✅")
print()
print("3. ⚠️  BONUS À CORRIGER:")
print("   - balcon/terrasse/ascenseur/parking/cave:")
print("     → Soit corriger la détection")
print("     → Soit réduire les valeurs (actuellement +10 pts systématiques)")
print()
print("4. ❌ MALUS À REVOIR:")
print("   - annees_60_70: Déjà dans score_style (0 pts), peut supprimer")
print("   - sans_ascenseur_etage_eleve: Implémenter la logique")
print()
print("5. 📊 ÉQUILIBRAGE:")
print("   → Actuellement: +10 pts bonus moyen pour tous (pas discriminant)")
print("   → Suggestion: Bonus uniquement si vraiment présents")
print("   → Ou réduire valeurs si détection systématique")










