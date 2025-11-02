# 📋 BONUS/MALUS - STATUT

## ❌ SUPPRIMÉS - JAMAIS VALIDÉS

**Date de suppression:** 2024-12-XX

Tous les bonus et malus ont été **supprimés** car ils n'ont jamais été validés.

### Raison de la suppression

1. **Format standardisé des caractéristiques**
   - Le champ `caractéristiques` contient un format template qui liste TOUTES les caractéristiques possibles
   - Résultat: Bonus systématique de +10 pts pour tous les appartements (pas discriminant)

2. **Jamais validés**
   - Les bonus/malus n'ont jamais été approuvés pour la production
   - Problèmes de détection et de pertinence identifiés

### Impact

- **Avant:** Score = 6 critères + bonus/malus (+10 pts moyen, -3 pts moyen)
- **Après:** Score = 6 critères uniquement (arrondi au multiple de 5 le plus proche)

### Code modifié

- `scoring.py`: Bonus/malus mis à 0 (fonction `calculate_bonus_malus` conservée mais non utilisée)
- `generate_scorecard_html.py`: Bonus/malus ignorés dans le calcul du megascore
- `fix_all_scores.py`: Recalcul sans bonus/malus

---

## 📊 HISTORIQUE (pour référence)

### Bonus qui étaient considérés (supprimés)

| Élément | Valeur | Statut |
|---------|--------|--------|
| balcon | 2 pts | ❌ Supprimé |
| terrasse | 3 pts | ❌ Supprimé |
| ascenseur | 2 pts | ❌ Supprimé |
| parking | 2 pts | ❌ Supprimé |
| cave | 1 pts | ❌ Supprimé |
| croisement_rue | 2 pts | ❌ Supprimé |
| vue_degagee | 2 pts | ❌ Supprimé |
| place_reunion | 5 pts | ❌ Supprimé |

### Malus qui étaient considérés (supprimés)

| Élément | Valeur | Statut |
|---------|--------|--------|
| vis_a_vis | -3 pts | ❌ Supprimé |
| nord | -2 pts | ❌ Supprimé |
| rdc | -2 pts | ❌ Supprimé |
| sans_ascenseur_etage_eleve | -3 pts | ❌ Supprimé |
| annees_60_70 | -5 pts | ❌ Supprimé |

---

## ✅ SCORING ACTUEL

Le scoring se base uniquement sur **6 critères** :

1. **Localisation** (20 pts max)
2. **Prix** (20 pts max)
3. **Style** (20 pts max)
4. **Ensoleillement** (10 pts max)
5. **Cuisine ouverte** (10 pts max)
6. **Baignoire** (10 pts max)

**Score total max:** 95 pts (90 pts base + 5 pts bonus Place de la Réunion intégré dans localisation, arrondi au multiple de 5 le plus proche)

**Note:** Le bonus Place de la Réunion (+5) est toujours appliqué mais intégré directement dans le score de localisation (20 → 25 pts max pour cette zone spécifique).
