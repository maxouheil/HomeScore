# Règles d'affichage des critères

Ce document détaille les règles d'affichage pour chaque critère dans `ApartmentCard.jsx`.

## Structure générale

Chaque critère utilise le composant `Criterion` avec les propriétés suivantes :
- `title` : Titre du critère (affiché en gras)
- `description` : Description principale (affichée en gris sous le titre)
- `indices` : Indices supplémentaires (affichés avec une icône dans `criterion-sub-details`)
- `tier` : Niveau du critère (tier1/tier2/tier3) pour la couleur de l'emoji
- `confidence` : Niveau de confiance (optionnel, actuellement caché)

---

## 1. Localisation (`formatLocalisation`)

### Titre
- **Format** : `"Metro {nom_metro}"` si métro disponible, sinon `"Localisation"`
- **Source** : Fonction `getMetroName(apartment)`

### Description
- **Format** : Nom de la rue en minuscules (ex: `"166 rue saint maur"`)
- **Priorité des sources** :
  1. `map_info.streets[0]` (priorité absolue)
  2. `localisation_precise` (extraire avant la première virgule)
  3. `localisation` (extraire pattern avec numéro + type de rue)

### Indices
- **Aucun** : Les indices ne sont pas affichés pour ce critère

### Emoji
- **Standard** : 📍

---

## 2. Prix (`formatPrixCriterion`)

### Titre
- **Format** : `"{prix}k € /m2"` (ex: `"11,8k € /m2"`)
- **Calcul** :
  - Extraire depuis `prix_m2` ou calculer depuis `prix / surface`
  - Arrondir au 100€ près
  - Convertir en format "k" (ex: 11800 → 11,8k)

### Description
- **Format** : `"Moyenne {arr}e: {prix}k€ /m2"` (ex: `"Moyenne 11e: 11k€ /m2"`)
- **Fallback** : `"{arr}e"` si pas de prix médian disponible
- **Source** : `getArrondissementMedianPrice(postalCode)`

### Indices
- **Aucun** : Les indices ne sont pas affichés pour ce critère

### Emoji
- **Standard** : 💰
- **Alerte** : 💰

---

## 3. Style (`formatStyleCriterion`)

### Titre
- **Priorité 1** : Si année de construction disponible (`annee_construction`)
  - `< 1910` → `"Haussmannien"`
  - `1910-1980` → `"Années {décennie}"` (ex: 1976 → `"Années 70"`)
  - `> 1980` → `"Moderne"`
- **Priorité 2** : `formatted_data.style.main_value` (si disponible)
- **Priorité 3** : `style_analysis.style.type` (fallback)
  - Gérer cas spéciaux : "70s", "Haussmannien"

### Description
- **Format** : `"Construit en {année}"` si année disponible, sinon `null`
- **Note** : Si pas d'année, les indices sont affichés séparément

### Indices
- **Format** : `"Indices: {liste}"` avec virgules (ex: `"Indices: moulures, parquet, cheminée, éléments décoratifs, balcon fer forgé"`)
- **Priorité des sources** :
  1. `formatted_data.style.indices` (nettoyer préfixes "Style Indice:", "Style:", etc.)
  2. Fallback : Chercher keywords dans `style_analysis.style.details` et `justification`
     - Keywords recherchés : moulures, cheminée, parquet, balcon fer forgé, éléments décoratifs, hauteur sous plafond
- **Affichage** : Section `criterion-sub-details` avec icône (comme exposition)

### Emoji
- **Standard** : 🎨
- **Alerte haussmanien** : 🔑
- **Alerte neuf** : ✨

---

## 4. Exposition (`formatExpositionCriterion`)

### Titre
- **Format** : Selon `mainValue`
  - `"Lumineux"` si `mainValue === 'Lumineux'`
  - `"Luminosité normale"` si `mainValue === 'Luminosité moyenne'`
  - `"Sombre"` sinon
- **Source** : `formatted_data.exposition.main_value` ou déduit depuis `exposition.exposition` ou `style_analysis.luminosite`

### Description
- **Format** : `"{étage} · Vis à vis {distance}m{upgrade}"` (ex: `"1er étage · Vis à vis 10m (upgrade >20m)"`)
- **Composants** :
  - Étage : Formater "1e étage" → "1er étage"
  - Vis-à-vis : `exposition.details.visavis_distance` (priorité absolue)
  - Upgrade : Ajouter `"(upgrade >20m)"` si distance > 20m ou si présent dans indices originaux
- **Séparateur** : Point médian `·`

### Indices
- **Aucun séparé** : Les indices sont dans la description (pas de section séparée)

### Emoji
- **Standard** : ☀️
- **Alerte** : ☀️

---

## 5. Cuisine (`formatCuisineCriterion`)

### Titre
- **Format** : 
  - `"Cuisine ouverte"` si `tier === 'tier1'` ou `cuisineOuverte === true`
  - `"Cuisine fermée"` sinon
- **Source** : 
  - Priorité : `scores_detaille.cuisine.details.photo_validation.photo_result.ouverte`
  - Fallback : `style_analysis.cuisine.ouverte` ou déduit depuis `tier`

### Description
- **Format** : `"Détectée sur photo {num}"` (ex: `"Détectée sur photo 7"`)
- **Source** :
  - Priorité : `photo_validation.photo_result.detected_photos[0]`
  - Fallback : Extraire depuis `formatted_data.cuisine.indices` (pattern "image {num}")

### Indices
- **Aucun** : Les indices ne sont pas affichés pour ce critère

### Emoji
- **Standard** : 👨‍🍳
- **Alerte** : 👨‍🍳

---

## 6. Baignoire (`formatBaignoireCriterion`)

### Titre
- **Format** :
  - `"Baignoire non spécifiée"` si `tier === 'tier2'` ou (`tier === 'tier3'` et pas de baignoire)
  - `"Baignoire"` sinon

### Description
- **Format** : Selon disponibilité des données
  - `"Baignoire trouvée dans image {num}"` si photos analysées et baignoire détectée
  - `"Douche trouvée dans image {num}"` si photos analysées et douche détectée
  - `"info non disponible"` si pas de données ou tier2
- **Source** :
  - Priorité : `formatted_data.baignoire.indices` (nettoyer préfixes)
  - Fallback : `photo_validation.photo_result.detected_photos`
  - Fallback 2 : `justification` depuis `scores_detaille.baignoire`

### Indices
- **Aucun** : Les indices ne sont pas affichés pour ce critère

### Emoji
- **Standard** : 🛁
- **Alerte** : 🛁

---

## 7. Calme (`formatCalmeCriterion`)

### Titre
- **Format** : Selon `tier`
  - `"Calme"` si `tier === 'tier1'`
  - `"Moyennement calme"` si `tier === 'tier2'`
  - `"Animé"` sinon

### Description
- **Format** : `justification` depuis `scores_detaille.calme` ou `formatted_data.calme.indices`
- **Fallback** : `"Non spécifié"`

### Indices
- **Aucun** : Les indices ne sont pas affichés pour ce critère

### Emoji
- **Standard** : 🔇

---

## 8. Pièce de vie (`formatLargePieceVieCriterion`)

### Titre
- **Format** : Selon `tier`
  - `"Grande pièce de vie"` si `tier === 'tier1'`
  - `"Pièce de vie correcte"` si `tier === 'tier2'`
  - `"Petite pièce de vie"` sinon

### Description
- **Format** : 
  - `"{taille}m² ({pourcentage}% de la surface totale)"` si détails disponibles
  - Sinon : `justification` depuis `scores_detaille.large_piece_vie`
  - Fallback : `"Non spécifié"`

### Indices
- **Aucun** : Les indices ne sont pas affichés pour ce critère

### Emoji
- **Standard** : 🛋️
- **Alerte** : 🛋️

---

## 9. Critères simples (ascenseur, hauteur_plafond, renove)

### Titre
- **Format** : Nom du critère depuis `ALERT_CRITERIA_TO_DISPLAY`
  - `"Ascenseur"`
  - `"Hauteur plafond"`
  - `"Rénové"`

### Description
- **Format** : `justification` depuis `scores_detaille.{critere}` ou `"Non spécifié"`

### Indices
- **Aucun** : Les indices ne sont pas affichés pour ces critères

### Emoji
- **Ascenseur** : 🛗
- **Hauteur plafond** : 📏
- **Rénové** : 🔨

---

## Règles générales d'affichage

### Structure du composant `Criterion`
```
<div className="criterion">
  <div className="criterion-content">
    <div className="criterion-header">
      <span className="criterion-emoji">{emoji}</span>
      <div className="criterion-text-wrapper">
        <div className="criterion-name">{title}</div>
        {description && (
          <div className="criterion-description">{description}</div>
        )}
        {indices && (
          <div className="criterion-sub-details">
            <div className="indices-icon-wrapper">
              {/* Icône SVG */}
            </div>
            <div className="indices-text-wrapper">
              <span className="indices-text">{indices}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  </div>
</div>
```

### Couleurs des emojis selon tier
- **tier1** : Vert (`criterion-emoji green`)
- **tier2** : Jaune (`criterion-emoji yellow`)
- **tier3** : Rouge (`criterion-emoji red`)
- **Gris** : Si `isGray={true}` (`criterion-emoji gray`)

### Nettoyage des indices
Les indices sont nettoyés pour enlever les préfixes suivants :
- `"Style Indice:"`
- `"Expo Indice:"`
- `"Exposition Indice:"`
- `"Cuisine Indice:"`
- `"Baignoire Indice:"`
- `"Baignoire:"`

### Formatage spécial
- **m²** : Converti en `m<sup>2</sup>` dans la description
- **1e étage** : Converti en `"1er étage"` pour l'exposition

---

## Ordre d'affichage dans les alertes

1. **Critères de l'alerte** (top 5) - affichés en couleur
   - Sans bordure entre eux (sauf le dernier s'il y a d'autres critères)
2. **Autres critères** - affichés en gris
   - Avec bordures entre eux

---

## Notes importantes

- **Style** : Seul critère avec indices affichés séparément dans `criterion-sub-details` (comme exposition dans certaines vues)
- **Exposition** : Les indices sont dans la description, pas séparés
- **Prix** : Format "k" pour les milliers (ex: 11,8k au lieu de 11800)
- **Localisation** : Description toujours en minuscules
- **Cuisine/Baignoire** : Utilisent la validation croisée texte + photos
