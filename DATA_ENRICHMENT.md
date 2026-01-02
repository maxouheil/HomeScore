# Documentation: Données Avant et Après Enrichissement

Ce document clarifie les données affichées pour chaque critère **AVANT** et **APRÈS** l'enrichissement par l'IA.

## Vue d'ensemble

- **AVANT enrichissement**: Données récupérées directement depuis les sources (scraping, API) et calculées automatiquement
- **APRÈS enrichissement**: Données enrichies par l'analyse IA (photos, texte) qui ajoutent des détails supplémentaires

---

## 1. Localisation

### AVANT enrichissement
- **Titre**: `"Metro [Nom du métro]"` (ex: "Metro Goncourt")
- **Description**: `"[Adresse]"` (ex: "166 rue Saint Maur")
- **Source**: Données récupérées directement depuis `map_info.metros` et `map_info.streets` ou `localisation_precise`

### APRÈS enrichissement
- **Aucun changement** - Les données de localisation ne sont pas enrichies par l'IA

---

## 2. Prix

### AVANT enrichissement
- **Titre**: `"[Prix]/m²"` formaté en k (ex: "11,8k € /m2")
- **Description**: `"Moyenne [Arrondissement]e: [Prix médian]k€ /m2"` (ex: "Moyenne 11e: 11k€ /m2")
- **Source**: Calculé depuis `prix` et `surface`, comparé avec prix médian de l'arrondissement

### APRÈS enrichissement
- **Aucun changement** - Les données de prix ne sont pas enrichies par l'IA

---

## 3. Ascenseur

### AVANT enrichissement
- **Titre**: `"Ascenseur"` ou `"Pas d'ascenseur"`
- **Description**: `"Ascenseur présent"`, `"Pas d'ascenseur"`, ou `"Non mentionné"`
- **Source**: Extrait depuis `caracteristiques.ascenseur`, `_api_data.features.lift`, ou `description`

### APRÈS enrichissement
- **Aucun changement** - Les données d'ascenseur ne sont pas enrichies par l'IA

---

## 4. Style architectural

### AVANT enrichissement
- **Titre**: `"Haussmannien"`, `"Années [XX]"`, `"Moderne"`, ou `"Style"`
- **Description**: `"Construit en [Année]"` (si année disponible depuis API)
- **Indices**: `null` ou non affichés
- **Source**: 
  - Date de construction depuis `caracteristiques.annee_construction` ou `_api_data.features.year`
  - Style détecté depuis `style_analysis.style.type` (si disponible)

### APRÈS enrichissement
- **Titre**: Identique à AVANT
- **Description**: Identique à AVANT (`"Construit en [Année]"` si disponible)
- **Indices**: **AJOUTÉ** - Liste de mots-clés très brefs séparés par des virgules
  - Exemples: `"moulures, parquet, cheminée, balcon fer forgé"`
  - Format: `"Indices: [mots-clés]"`
  - Source: Analyse IA des photos et du texte depuis `formatted_data.style.indices`
  - **Règle**: Être très bref (max 15-20 mots)

---

## 5. Luminosité / Exposition

### AVANT enrichissement
- **Titre**: `"Lumineux"`, `"Luminosité normale"`, ou `"Sombre"`
- **Description**: `"[Étage]"` (ex: "3e étage")
- **Source**: Calculé depuis l'étage (`etage`) avec logique:
  - `< 3e étage` → "Sombre"
  - `3e-4e étage` → "Luminosité normale"
  - `≥ 5e étage` → "Lumineux"

### APRÈS enrichissement
- **Titre**: Identique à AVANT
- **Description**: **ENRICHI** - Format: `"[Étage] · Vis à vis [Distance]m"`
  - Exemple: `"3e étage · Vis à vis 25m"`
  - Ajout du vis-à-vis en mètres depuis `exposition.details.visavis_distance`
  - Source: Analyse IA des photos pour estimer la distance vis-à-vis

---

## 6. Hauteur plafond

### AVANT enrichissement
- **Titre**: `"Hauteur plafond"`
- **Description**: `"Non analysé"`
- **Source**: Aucune donnée disponible

### APRÈS enrichissement
- **Titre**: **ENRICHI** - Format: `"Belle hauteur plafond"` ou `"[Hauteur]m"` (ex: "2,90m")
- **Description**: **AJOUTÉ** - Format: `"Moyenne [Hauteur]m"` (ex: "Moyenne 2,90m")
- **Source**: Analyse IA des photos pour estimer la hauteur depuis `formatted_data.hauteur.main_value` et `formatted_data.hauteur.indices`

---

## 7. Cuisine

### AVANT enrichissement
- **Titre**: `"Cuisine"`
- **Description**: `"Non analysée"`
- **Source**: Aucune donnée disponible

### APRÈS enrichissement
- **Titre**: **ENRICHI** - Format: `"Cuisine ouverte"` ou `"Cuisine fermée"`
- **Description**: **AJOUTÉ** - Format: `"Détectée sur photo [Numéro]"` (ex: "Détectée sur photo 5")
- **Source**: Analyse IA des photos depuis `scores_detaille.cuisine.details.photo_validation.photo_result` ou `formatted_data.cuisine.indices`

---

## 8. Baignoire

### AVANT enrichissement
- **Titre**: `"Baignoire"`
- **Description**: `"Non analysé"`
- **Source**: Aucune donnée disponible

### APRÈS enrichissement
- **Titre**: **ENRICHI** - Format: `"Baignoire"` ou `"Baignoire non spécifiée"`
- **Description**: **AJOUTÉ** - Format: 
  - `"Baignoire trouvée dans image [Numéro]"` (si baignoire détectée)
  - `"Douche trouvée dans image [Numéro]"` (si seulement douche détectée)
  - `"info non disponible"` (si non détectée)
- **Source**: Analyse IA des photos depuis `scores_detaille.baignoire.details.photo_validation.photo_result` ou `formatted_data.baignoire.indices`

---

## 9. Pièce de vie (Salon)

### AVANT enrichissement
- **Titre**: `"Taille pièce de vie"`
- **Description**: `"Analyse manquante"`
- **Source**: Aucune donnée disponible

### APRÈS enrichissement
- **Titre**: **ENRICHI** - Format: `"Large pièce de vie"`, `"Pièce de vie correcte"`, ou `"Petite pièce de vie"`
- **Description**: **AJOUTÉ** - Format: `"[Pourcentage]% de l'appartement"` (ex: "35% de l'appartement")
- **Source**: Analyse IA des photos pour estimer la taille du salon vs surface totale depuis `scores_detaille.large_piece_vie.details.pourcentage_salon`

---

## Résumé des enrichissements

| Critère | AVANT | APRÈS |
|---------|-------|-------|
| **Localisation** | Metro + Adresse | Identique |
| **Prix** | Prix/m² + Moyenne arrondissement | Identique |
| **Ascenseur** | Si mentionné ou non | Identique |
| **Style** | Date construction (si API) | + Indices par mots-clés (moulures, parquet, cheminée, etc.) |
| **Luminosité** | Via l'étage | + Vis-à-vis en mètres |
| **Hauteur plafond** | Non analysé | + Moyenne en mètres |
| **Cuisine** | Non analysée | + Si ouverte détectée sur image |
| **Baignoire** | Non analysé | + Si baignoire/douche détectée sur image |
| **Pièce de vie** | Analyse manquante | + Taille salon vs m² appartement (%) |

---

## Format des données dans le code

### Structure `formatted_data` (backend)

```python
apartment['formatted_data'] = {
    'style': {
        'main_value': 'Haussmannien',  # Titre
        'indices': 'moulures, parquet, cheminée, balcon fer forgé',  # Description enrichie
        'confidence': 0.85
    },
    'exposition': {
        'main_value': 'Lumineux',  # Titre
        'indices': '3e étage · Vis à vis 25m',  # Description enrichie
        'confidence': 0.80
    },
    'hauteur': {
        'main_value': 'Belle hauteur plafond',  # Titre
        'indices': 'Moyenne 2,90m',  # Description enrichie
        'confidence': 0.75
    },
    'cuisine': {
        'indices': 'Détectée sur photo 5'  # Description enrichie
    },
    'baignoire': {
        'main_value': 'Oui',  # Titre
        'indices': 'Baignoire trouvée dans image 3',  # Description enrichie
        'confidence': 0.90
    }
}
```

### Structure frontend (ApartmentCard.jsx)

Les fonctions de formatage utilisent:
- `formatStyleCriterion()` → Extrait `formatted_data.style.indices` pour les indices
- `formatExpositionCriterion()` → Extrait `exposition.details.visavis_distance` pour le vis-à-vis
- `formatHauteurCriterion()` → Extrait `formatted_data.hauteur.main_value` et `indices` pour la moyenne
- `formatCuisineCriterion()` → Extrait `scores_detaille.cuisine.details.photo_validation` pour la détection
- `formatBaignoireCriterion()` → Extrait `scores_detaille.baignoire.details.photo_validation` pour la détection
- `formatLargePieceVieCriterion()` → Extrait `scores_detaille.large_piece_vie.details.pourcentage_salon` pour le pourcentage

---

## Notes importantes

1. **Style - Indices**: Les indices doivent être **très brefs** (max 15-20 mots), séparés par des virgules
2. **Luminosité - Vis-à-vis**: Format systématique `"[Étage] · Vis à vis [Distance]m"`
3. **Hauteur plafond**: Format `"Moyenne [Hauteur]m"` dans la description
4. **Cuisine**: Format `"Détectée sur photo [Numéro]"` dans la description
5. **Baignoire**: Format `"[Type] trouvée dans image [Numéro]"` dans la description
6. **Pièce de vie**: Format `"[Pourcentage]% de l'appartement"` dans la description
