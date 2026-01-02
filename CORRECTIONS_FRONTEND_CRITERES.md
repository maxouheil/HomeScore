# Corrections Frontend - Affichage des critères

## Problèmes corrigés

### 1. Hauteur plafond - Clé manquante ✅

**Problème**: Le frontend cherchait `formatted_data.hauteur_plafond` mais les données étaient stockées sous `hauteur` (ancien format).

**Solution appliquée**:
- Ajout d'un fallback pour chercher aussi `formatted_data.hauteur` si `hauteur_plafond` n'existe pas
- Amélioration de l'extraction de la hauteur depuis `main_value` ou `indices`
- Priorité: `formatted_data.hauteur_plafond` → `formatted_data.hauteur` → `analyses.hauteur_plafond`

**Fichier modifié**: `frontend/src/components/ApartmentCard.jsx`
- Lignes 2058-2067: Ajout du fallback pour `hauteur`
- Lignes 2179-2202: Amélioration de l'utilisation des indices depuis `formatted_data`

### 2. Pièce de vie - Affichage des indices ✅

**Problème**: La fonction utilisait les indices comme description au lieu de les distinguer correctement.

**Solution appliquée**:
- Utilisation du `main_value` comme titre (ex: "Grande pièce de vie")
- Distinction entre version courte (affichée en bleu dans indices) et version longue (affichée en gris dans description)
- Priorité: Utiliser `formatted_data.piece_vie` en premier

**Fichier modifié**: `frontend/src/components/ApartmentCard.jsx`
- Lignes 1915-1942: Refactorisation complète de `formatLargePieceVieCriterion`

### 3. Pièce de vie - Pourcentage manquant ✅

**Problème**: Le pourcentage "X% de la surface totale de l'appartement" ne s'affichait pas pour la pièce de vie.

**Cause**: 
- Le normalizer backend cherchait les données dans `scores_detaille.piece_vie` alors qu'elles sont stockées sous `scores_detaille.large_piece_vie`
- Le pourcentage n'était pas calculé depuis `piece_vie.taille_m2` et la surface totale

**Solution appliquée**:

**Backend** (`backend/normalizers/simple_normalizer.py`):
- Correction de `_normalize_criteria()` pour utiliser `large_piece_vie` au lieu de `piece_vie` (ligne 1083)
- Correction de `_build_display_data()` pour chercher le pourcentage dans `scores_detaille.large_piece_vie.details.pourcentage_salon` (ligne 1106)
- Ajout d'un calcul du pourcentage depuis `piece_vie.taille_m2` et `apartment.surface` si le pourcentage n'est pas trouvé (lignes 1123-1137)

**Frontend** (`frontend/src/components/ApartmentCard.jsx`):
- Ajout d'un fallback dans la branche `criteria.piece_vie.display` pour chercher le pourcentage dans `scores_detaille.large_piece_vie.details.pourcentage_salon` si les indices normalisés ne contiennent pas le pourcentage (lignes 1981-2003)

**Fichiers modifiés**:
- `backend/normalizers/simple_normalizer.py`: Lignes 1057-1095, 1081-1083
- `frontend/src/components/ApartmentCard.jsx`: Lignes 1975-2003

## Détails des modifications

### formatHauteurPlafondCriterion

**Avant**:
```javascript
// Cherchait seulement hauteur_plafond
if (apartment.formatted_data?.hauteur_plafond) {
  const hauteurFormatted = apartment.formatted_data.hauteur_plafond
  // ...
}
```

**Après**:
```javascript
// Cherche hauteur_plafond avec fallback sur hauteur
let hauteurFormatted = null
if (apartment.formatted_data?.hauteur_plafond) {
  hauteurFormatted = apartment.formatted_data.hauteur_plafond
} else if (apartment.formatted_data?.hauteur) {
  hauteurFormatted = apartment.formatted_data.hauteur
}

if (hauteurFormatted) {
  // Extraction améliorée depuis indices ou main_value
  // ...
}
```

### formatLargePieceVieCriterion

**Avant**:
```javascript
// Utilisait tout comme description
const description = indices.replace(/^Pièce de vie Indice:\s*/i, '').trim()
return {
  title: 'Pièce de vie',
  description,
  // ...
}
```

**Après**:
```javascript
// Distingue titre, indices (bleu) et description (gris)
const title = mainValue  // "Grande pièce de vie"
// Version courte → indices (bleu)
// Version longue → description (gris)
return {
  title,
  description,
  indices,
  // ...
}
```

## Résultat attendu

### Pour l'appartement 94739175

**Hauteur plafond**:
- ✅ Trouve les données sous `formatted_data.hauteur`
- ✅ Affiche "2,55m" comme titre
- ✅ Affiche "Moyenne 2,55m" dans les indices (bleu)

**Pièce de vie**:
- ✅ Utilise "Grande pièce de vie" comme titre (depuis main_value)
- ✅ Affiche les indices longs dans la description (gris) car c'est une version longue
- ✅ Si le backend retourne une version courte, elle sera affichée en bleu dans les indices
- ✅ Affiche le pourcentage "X% de la surface totale de l'appartement" depuis `piece_vie.taille_m2` et la surface totale

### Détails de la correction du pourcentage

**Ordre de recherche du pourcentage** (backend normalizer):
1. `formatted_data.piece_vie.indices` - si contient déjà "de l'appartement"
2. `scores_detaille.large_piece_vie.details.pourcentage_salon` (PRIORITÉ)
3. `score_data.details.pourcentage_salon` (compatibilité)
4. `style_analysis.piece_vie.details.pourcentage_salon` (fallback)
5. Calcul depuis `piece_vie.taille_m2` / `apartment.surface` (nouveau fallback)

**Exemple**: Pour un appartement avec surface 71 m² et pièce de vie 28 m²:
- Calcul: 28 / 71 * 100 = 39.4%
- Affichage: "39.4% de la surface totale de l'appartement"

## Compatibilité

Les modifications sont rétrocompatibles :
- Support de l'ancien format (`hauteur`) et du nouveau (`hauteur_plafond`)
- Gestion des deux formats d'indices pour pièce de vie (court et long)
- Fallbacks appropriés si les données manquent
- Support de `large_piece_vie` et `piece_vie` pour la compatibilité
