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

## Compatibilité

Les modifications sont rétrocompatibles :
- Support de l'ancien format (`hauteur`) et du nouveau (`hauteur_plafond`)
- Gestion des deux formats d'indices pour pièce de vie (court et long)
- Fallbacks appropriés si les données manquent
