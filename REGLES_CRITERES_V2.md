# 📋 Règles Critères HomeScore V2

## 🎯 Règle Globale

**Chaque critère compte pour 1 PT maximum**

- **GOOD** = 1pt
- **MOYEN** = 0.5pt  
- **BAD** = 0pt

---

## 1️⃣ STYLE

### Règles d'analyse

1. **Si année de construction < 1910** : Rank automatique en **Haussmannien**
2. **Sinon** : Donner la décennie
   - Années 70 → "Années 70"
   - Après 80 → "Moderne"

### Priorité des sources

1. **Priorité 1** : Date de construction récupérée dans l'API
   - `_api_data.features.year`
   - `caracteristiques.annee_construction`
   - Extraction depuis texte : "Construit en XXXX" ou "Année: XXXX"

2. **Priorité 2** : Analyse photo avec les indices
   - `style_analysis.style` (analyse IA images)
   - Classification : haussmannien / décennies_jusque_80 / moderne

### Output attendu

```json
{
  "main_value": "Haussmannien" | "Années 70" | "Années 80" | "Moderne",
  "confidence": 70-95,  // Plus élevé si date API disponible
  "indices": "Style Indice:\nConstruit en 1880" | "Style Indice:\n[moulures, parquet, cheminée...]"
}
```

### Scoring

- **GOOD (1pt)** : Haussmannien (< 1910)
- **MOYEN (0.5pt)** : Années 70-80
- **BAD (0pt)** : Moderne (après 1980)

---

## 2️⃣ LOCALISATION

### Règles

**RAS** - Aucun changement par rapport à la version précédente

### Output attendu

```json
{
  "main_value": "Metro Ménilmontant · Quartier Sorbier",
  "confidence": null,
  "indices": null
}
```

### Scoring

- **GOOD (1pt)** : Tier 1 zones (Belleville, Ménilmontant, Avron, Place de la Réunion...)
- **MOYEN (0.5pt)** : Tier 2 zones (Goncourt, Pyrénées, Jourdain...)
- **BAD (0pt)** : Tier 3 zones (reste du 10e, 20e, 19e)

---

## 3️⃣ LUMINOSITÉ / EXPOSITION

### Règles d'analyse

1. **Priorité à l'étage** (classification de base)
   - **Sombre** : < 3e étage (RDC, 1er, 2e)
   - **Moyen** : 3e-4e étage
   - **Lumineux** : > 4e étage (≥5e)

2. **Upgrade si** :
   - **Sud/Ouest** mentionné → Upgrade d'un niveau (Sombre→Moyen, Moyen→Lumineux)
   - **Vis-à-vis > 20m** (NOUVEAU) → Upgrade d'un niveau

### Output attendu

```json
{
  "main_value": "Lumineux" | "Luminosité moyenne" | "Sombre",
  "confidence": 50-70,
  "indices": "Exposition Indice:\n3e étage · Vis-à-vis 25m · Sud mentionné"
}
```

### Scoring

- **GOOD (1pt)** : Lumineux
- **MOYEN (0.5pt)** : Luminosité moyenne
- **BAD (0pt)** : Sombre

---

## 4️⃣ CUISINE

### Règles d'analyse

- **Validation photos ONLY** (pas de texte)
- Format : `"Cuisine détectée image 3"`
- Si douche détectée : `"Douche détectée image 3"`

### Output attendu

```json
{
  "main_value": "Ouverte" | "Fermée" | "Non spécifié",
  "confidence": 80-95,  // Confiance élevée si détecté par photos
  "indices": "Cuisine Indice:\nCuisine ouverte détectée image 3"
}
```

### Scoring

- **GOOD (1pt)** : Cuisine ouverte
- **MOYEN (0.5pt)** : Non spécifié (non trouvée)
- **BAD (0pt)** : Cuisine fermée

---

## 5️⃣ BAIGNOIRE

### Règles d'analyse

- **Validation photos ONLY** (pas de texte)
- Format : `"Baignoire détectée image 3"`
- Si douche : `"Douche détectée image 3"`

### Output attendu

```json
{
  "main_value": "Oui" | "Non" | "Non spécifié",
  "confidence": 80-95,  // Confiance élevée si détecté par photos
  "indices": "Baignoire Indice:\nBaignoire détectée image 3"
}
```

### Scoring

- **GOOD (1pt)** : Baignoire présente
- **MOYEN (0.5pt)** : Non spécifié (non trouvée)
- **BAD (0pt)** : Pas de baignoire (douche seulement)

---

## 6️⃣ HAUTEUR PLAFOND

### Règles d'analyse

- **Bad** : < 2.50m
- **Moyen** : < 2.80m (≥ 2.50m et < 2.80m)
- **Good** : ≥ 2.80m

### Output attendu

```json
{
  "main_value": "2.8 m" | "Non spécifié",
  "confidence": 70-90,
  "indices": "Hauteur Indice:\nHauteur estimée 2.8m (Good)"
}
```

### Scoring

- **GOOD (1pt)** : ≥ 2.80m
- **MOYEN (0.5pt)** : 2.50m - 2.79m
- **BAD (0pt)** : < 2.50m

---

## 7️⃣ PIÈCE DE VIE

### Règles d'analyse

Classification basée sur le **pourcentage de la surface totale** :

- **Bad** : < 30% de la surface totale
- **Moyen** : 30-40% de la surface totale
- **Good** : > 40% de la surface totale

### Output attendu

```json
{
  "main_value": "42.5 m² (88.5% de la surface totale)",
  "confidence": 70-85,
  "indices": "Pièce de vie Indice:\nSurface estimée 42.5m² (88.5% du total) - Good"
}
```

### Scoring

- **GOOD (1pt)** : > 40% de la surface totale
- **MOYEN (0.5pt)** : 30-40% de la surface totale
- **BAD (0pt)** : < 30% de la surface totale

---

## 8️⃣ PRIX MARCHÉ

### Règles d'analyse

1. **Récupérer le prix moyen de l'arrondissement** et l'utiliser comme médian
2. **Comparer** le prix/m² de l'appartement avec ce médian :
   - **Good** : Prix/m² < médian (bon marché)
   - **Moyen** : Prix/m² ≈ médian (±10%)
   - **Bad** : Prix/m² > médian (cher)

### Output attendu

```json
{
  "main_value": "11 500 / m² · Moyen (médian arrondissement: 11 200 €/m²)",
  "confidence": null,  // Données factuelles
  "indices": "Prix Indice:\nPrix/m²: 11 500€ · Médian arrondissement: 11 200€"
}
```

### Scoring

- **GOOD (1pt)** : Prix/m² < médian arrondissement
- **MOYEN (0.5pt)** : Prix/m² ≈ médian (±10%)
- **BAD (0pt)** : Prix/m² > médian arrondissement

---

## 9️⃣ CALME

### Règles d'analyse

**Pondération égale** :
- **50%** : Type de rue
- **50%** : Densité de bars

### Type de rue (50%)

- **Good** : Rue piétonne (pedestrian)
- **Moyen** : Rue résidentielle (residential)
- **Bad** : Axe routier (primary, secondary, tertiary, trunk, motorway)

### Densité de bars (50%)

- **Good** : 0 bar/resto dans 100m
- **Moyen** : 1-2 bars/restos dans 100m
- **Bad** : > 2 bars/restos dans 100m

### Output attendu

```json
{
  "main_value": "Calme" | "Moyennement calme" | "Animé",
  "confidence": 70-90,
  "indices": "Calme Indice:\nRue résidentielle · 1 bar/resto dans 100m"
}
```

### Scoring

- **GOOD (1pt)** : Quartier très calme (rue piétonne, 0 bar/resto)
- **MOYEN (0.5pt)** : Quartier moyennement calme
- **BAD (0pt)** : Quartier animé (axe routier, nombreux bars/restos)

---

## 📊 Récapitulatif Scoring

| Critère | GOOD (1pt) | MOYEN (0.5pt) | BAD (0pt) |
|---------|------------|---------------|-----------|
| **Style** | Haussmannien (<1910) | Années 70-80 | Moderne (>1980) |
| **Localisation** | Tier 1 zones | Tier 2 zones | Tier 3 zones |
| **Luminosité** | Lumineux | Moyen | Sombre |
| **Cuisine** | Ouverte | Non spécifié | Fermée |
| **Baignoire** | Présente | Non spécifié | Absente |
| **Hauteur** | ≥ 2.80m | 2.50-2.79m | < 2.50m |
| **Pièce de vie** | > 40% surface | 30-40% surface | < 30% surface |
| **Prix** | < médian | ≈ médian | > médian |
| **Calme** | Très calme | Moyennement calme | Animé |

**Score total maximum** : 9 pts (tous les critères à GOOD)

---

## 🔄 Changements par rapport à V1

1. ✅ **Scoring unifié** : Tous les critères = 1pt max (GOOD/MOYEN/BAD)
2. ✅ **Style** : Priorité date API > analyse photo
3. ✅ **Luminosité** : Upgrade si vis-à-vis >20m (NOUVEAU)
4. ✅ **Cuisine/Baignoire** : Photos ONLY (pas de texte)
5. ✅ **Hauteur** : Seuils précis (2.50m / 2.80m)
6. ✅ **Pièce de vie** : Classification par pourcentage (<30% / 30-40% / >40%)
7. ✅ **Prix** : Comparaison avec médian arrondissement
8. ✅ **Calme** : 50% type rue + 50% densité bars (simplifié)

---

*Document créé le : 2025-01-XX*
*Version : 2.0*

