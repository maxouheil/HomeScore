# 📋 Récapitulatif Complet - Système d'Analyse HomeScore

## Vue d'ensemble

Ce document décrit les règles d'analyse et les outputs attendus pour chaque critère du système HomeScore.

---

## 1️⃣ STYLE

### Source de données
- **Analyse IA images** : `style_analysis.style` (via Gemini 2.5 Flash)
- **Fallback** : `scores_detaille.style.justification` (analyse texte)

### Règles d'analyse
- **Classification** : 3 catégories possibles
  - `"haussmannien"` : Immeubles parisiens typiques 1850-1870, hauts plafonds, moulures, parquet, cheminées
  - `"decennies_jusque_80"` : Années 50-80, style fonctionnel, moins d'ornements, matériaux modernes
  - `"moderne"` : Années 90+, design contemporain, matériaux modernes, ouvertures, espaces ouverts

- **Indice de style** : Nombre entre 0-100
  - 0 = très haussmannien
  - 50 = décennies jusqu'à 80
  - 100 = très moderne

### Output attendu
```json
{
  "main_value": "Ancien" | "Atypique" | "Neuf",
  "confidence": 70,  // Pourcentage (0-100)
  "indices": "Style Indice:\n[justification avec détails: moulures, parquet, cheminée, etc.]"
}
```

### Mapping classification → affichage
- `haussmannien` → **"Ancien"**
- `loft/atypique/unique/original` → **"Atypique"**
- Tout le reste → **"Neuf"**

### Scoring (scoring_config.json)
- **Tier 1** (20 pts) : Style ancien (Haussmannien)
- **Tier 2** (10 pts) : Style atypique (Loft, Atypique, Unique, Original)
- **Tier 3** (0 pts) : Style neuf (Moderne, Contemporain, Récent, Années 20-70)

---

## 2️⃣ LOCALISATION

### Source de données
- **Priorité 1** : `scores_detaille.localisation.justification` (extrait par IA)
- **Priorité 2** : `map_info.metros` et `map_info.quartier`
- **Priorité 3** : `exposition.details.photo_details.quartier`
- **Priorité 4** : `transports` et `description`

### Règles d'analyse

#### Métro
- Extraction de toutes les stations mentionnées
- Classification par **tier** selon `scoring_config.json` :
  - **Tier 1** : Alexandre Dumas, Philippe Auguste, Belleville, Ménilmontant, Avron, Place de la Réunion
  - **Tier 2** : Goncourt, Pyrénées, Jourdain, Rue des Boulets, Nation
  - **Tier 3** : Reste du 10e, 20e, 19e
- **Sélection** : Retourne la première station du meilleur tier disponible

#### Quartier
- Extraction depuis `map_info.quartier` (nettoyé des scores)
- Fallback sur justification IA si quartier non identifié
- Nettoyage des suffixes "(proximité)" et "(score: XX)"

### Output attendu
```json
{
  "main_value": "Metro Ménilmontant · Quartier Sorbier",
  "confidence": null,  // Données factuelles, pas de confiance
  "indices": null
}
```

### Format
- Format : `"Metro [station] · [quartier]"`
- Si métro seul : `"Metro [station]"`
- Si quartier seul : `"[quartier]"`
- Si aucun : `"Non spécifié"`

### Scoring (scoring_config.json)
- **Tier 1** (20 pts) : Zones premium (Place de la Réunion, Belleville-Avron ligne 2, etc.)
- **Tier 2** (10 pts) : Bonnes zones avec potentiel (Goncourt, Pyrénées, etc.)
- **Tier 3** (0 pts) : Zones correctes (reste du 10e, 20e, 19e)
- **Bonus** : +5 pts pour Place de la Réunion

---

## 3️⃣ LUMINOSITÉ / EXPOSITION

### Source de données
- **Étage** : `exposition.details.etage_num` ou `apartment.etage` ou texte
- **Exposition** : `exposition.exposition` (direction)
- **Vis-à-vis** : `exposition.details.visavis_distance` (analyse image)
- **Luminosité image** : `exposition.details.brightness_value` (analyse image)

### Règles d'analyse

#### Classification par étage (base)
- **Sombre** : < 3e étage (RDC, 1er, 2e)
- **Moyen** : 3e-4e étage
- **Lumineux** : > 4e étage (≥5e)

#### Upgrade si Sud/Ouest mentionné
- **Sombre** → **Moyen** (si Sud/Ouest)
- **Moyen** → **Lumineux** (si Sud/Ouest)

#### Classification orientation
- **Lumineux** : Sud, Sud-Ouest, Sud-Est
- **Moyen** : Est, Ouest
- **Sombre** : Nord, Nord-Ouest, Nord-Est

#### Classification luminosité image
- **Lumineux** : brightness ≥ 0.70
- **Moyen** : 0.40 ≤ brightness < 0.70
- **Sombre** : brightness < 0.40

### Output attendu
```json
{
  "main_value": "Lumineux" | "Luminosité moyenne" | "Sombre",
  "confidence": 50-70,  // 50% si pas d'étage, 70% si étage disponible
  "indices": "Exposition Indice:\n[étage] · [vis-à-vis] · [exposition mentionnée] · [luminosité image]"
}
```

### Format indices
- Ordre : Étage → Vis-à-vis → Exposition mentionnée → Luminosité image
- Exemple : `"Exposition Indice:\n3e étage · Vis-à-vis 15m · Sud mentionné · Luminosité 0.75"`

### Scoring (scoring_config.json)
- **Tier 1** (20 pts) : Lumineux (Sud, Sud-Ouest, vue dégagée, pas de vis-à-vis)
- **Tier 2** (10 pts) : Luminosité moyenne (Ouest, Est, vue semi-dégagée)
- **Tier 3** (0 pts) : Sombre (Nord, Nord-Est, vis-à-vis, pas dégagé)
- **Malus** : -3 pts pour vis-à-vis, -2 pts pour Nord, -2 pts pour RDC

---

## 4️⃣ CUISINE

### Source de données
- **Priorité** : `scores_detaille.cuisine.details.photo_validation.photo_result` (validation croisée texte + photos)
- **Fallback** : `style_analysis.cuisine` (analyse images uniquement)
- **Tier** : `scores_detaille.cuisine.tier` (résultat final après validation)

### Règles d'analyse

#### Détection cuisine ouverte
- **Cuisine ouverte** : Directement connectée au salon/séjour SANS mur ni porte
- **Cuisine fermée** : Mur, porte ou séparation claire entre cuisine et salon
- **Non spécifié** : Si tier2 (non analysée, note moyenne par défaut)

#### Validation croisée
- Analyse texte + analyse photos
- En cas de conflit, le tier représente le résultat final
- `detected_photos` : Liste des numéros d'images où la cuisine a été détectée

### Output attendu
```json
{
  "main_value": "Ouverte" | "Fermée" | "Non spécifié",
  "confidence": 90,  // Pourcentage (0-100)
  "indices": "Cuisine Indice:\nCuisine ouverte détectée image 1, image 3 · bar détecté"
}
```

### Format indices
- Si détecté par photos : `"Cuisine [ouverte/fermée] détectée image X, image Y"`
- Si détails supplémentaires : `"bar détecté"`, `"comptoir détecté"`
- Si non spécifié : `"Cuisine Indice:\nNon spécifié"`

### Scoring (scoring_config.json)
- **Tier 1** (20 pts) : Cuisine ouverte ou semi-ouverte sur salon
- **Tier 2** (10 pts) : Cuisine non trouvée dans les photos (score neutre)
- **Tier 3** (0 pts) : Cuisine fermée sans possibilité d'ouverture

---

## 5️⃣ HAUTEUR PLAFOND

### Source de données
- **Analyse IA images** : `analyses.hauteur_plafond` (via Gemini 2.5 Pro)
- **Estimation** : Basée sur éléments de référence (portes, fenêtres, etc.)

### Règles d'analyse
- **Modèle** : Gemini 2.5 Pro (meilleure précision)
- **Méthode** : Estimation visuelle basée sur éléments de référence
- **Éléments utilisés** : Portes, fenêtres, meubles standards

### Output attendu
```json
{
  "hauteur_estimee": 2.8,  // En mètres (nombre décimal)
  "confiance": 85,  // Pourcentage (0-100)
  "elements_reference": ["porte standard", "fenêtre", "meubles"]
}
```

### Format affichage
- Format : `"[hauteur] m"` (ex: "2.8 m")
- Si non disponible : `"Non spécifié"`

### Note
- Ce critère n'est pas directement utilisé dans le scoring final
- Peut être utilisé comme indice dans le style ou la luminosité

---

## 6️⃣ PIÈCE DE VIE

### Source de données
- **Analyse IA images** : `analyses.piece_de_vie` (via Gemini 2.5 Flash)
- **Surface totale** : `apartment.surface` (pour calcul du pourcentage)

### Règles d'analyse

#### Classification taille
- **petite** : Surface estimée < 20 m²
- **moyenne** : 20-35 m²
- **grande** : 35-50 m²
- **tres_grande** : > 50 m²

#### Calcul pourcentage
- Si `surface_totale_m2` fournie :
  - `pourcentage_surface_totale = (surface_estimee_m2 / surface_totale_m2) * 100`
- Arrondi à 1 décimale

### Output attendu
```json
{
  "taille_estimee": "grande",
  "surface_estimee_m2": 42.5,
  "confiance": 80,
  "elements_visibles": ["canapé", "table", "fenêtre"],
  "pourcentage_surface_totale": 88.5  // Si surface totale fournie
}
```

### Format affichage
- Format : `"[surface] m² ([pourcentage]% de la surface totale)"`
- Exemple : `"42.5 m² (88.5% de la surface totale)"`
- Si non disponible : `"Non spécifié"`

### Note
- Ce critère n'est pas directement utilisé dans le scoring final
- Peut être utilisé comme indice de qualité de vie

---

## 7️⃣ PRIX

### Source de données
- **Prix** : `apartment.prix` (chaîne de caractères)
- **Surface** : `apartment.surface` (chaîne de caractères)
- **Prix/m²** : Calculé ou `apartment.prix_m2`
- **Tier** : `scores_detaille.prix.tier`

### Règles d'analyse

#### Calcul prix/m²
- Extraction du prix : Regex `([\d\s]+)` depuis `prix`
- Extraction de la surface : Regex `(\d+)` depuis `surface`
- Calcul : `prix_m2 = prix_num // surface_num`
- Formatage : Séparateur de milliers avec espace (ex: "11 500")

#### Classification par tier
- **Tier 1** (20 pts) : ≤ 9 499 €/m² (Excellent rapport qualité/prix)
- **Tier 2** (10 pts) : 9 500 - 11 000 €/m² (Bon rapport qualité/prix)
- **Tier 3** (0 pts) : ≥ 11 001 €/m² (Prix élevé)

### Output attendu
```json
{
  "main_value": "11 500 / m² · <span class=\"tier-label moyen\">Moyen</span>",
  "confidence": null,  // Données factuelles
  "indices": null
}
```

### Format affichage
- Format : `"[prix] / m² · [tier-label]"`
- Tier labels :
  - Tier 1 : `"Good"` (classe `good`)
  - Tier 2 : `"Moyen"` (classe `moyen`)
  - Tier 3 : `"Bad"` (classe `bad`)
- Format HTML : `<span class="tier-label [classe]">[label]</span>`

### Scoring (scoring_config.json)
- **Tier 1** (20 pts) : Moins de 9.5k€/m²
- **Tier 2** (10 pts) : 9.5-11k€/m²
- **Tier 3** (0 pts) : Plus de 11k€/m²

---

## 8️⃣ BAIGNOIRE

### Source de données
- **Priorité** : `scores_detaille.baignoire.details.photo_validation.photo_result` (validation croisée texte + photos)
- **Fallback** : `apartment.baignoire` ou `apartment.baignoire_data`
- **Tier** : `scores_detaille.baignoire.tier` (résultat final après validation)

### Règles d'analyse

#### Détection baignoire
- **Baignoire présente** : Détectée dans les photos ou mentionnée dans le texte
- **Douche seulement** : Si douche détectée mais pas de baignoire
- **Non spécifié** : Si tier2 (non analysée) OU si photos analysées mais rien détecté

#### Validation croisée
- Analyse texte + analyse photos
- **Priorité aux photos** : Si photos ont analysé, utiliser leur résultat même en cas de conflit
- `detected_photos` : Liste des numéros d'images où la baignoire/douche a été détectée

### Output attendu
```json
{
  "main_value": "Oui" | "Non" | "Non spécifié",
  "confidence": 90,  // Pourcentage (0-100)
  "indices": "Baignoire Indice:\nBaignoire détectée image 1, image 3"
}
```

### Format indices
- Si baignoire détectée : `"Baignoire détectée image X, image Y"`
- Si douche détectée : `"Douche détectée image X, image Y"`
- Si non spécifié : `"Baignoire Indice:\nNon spécifié"`

### Scoring (scoring_config.json)
- **Tier 1** (10 pts) : Baignoire présente
- **Tier 2** (5 pts) : Cuisine/SDB non trouvée (score neutre)
- **Tier 3** (0 pts) : Pas de baignoire (seulement douche)

---

## 📊 Récapitulatif des Sources de Données

### Analyse IA Images (Gemini)
- **Style** : Gemini 2.5 Flash (3 premières photos)
- **Cuisine** : Gemini 2.5 Flash (toutes les photos jusqu'à détection)
- **Baignoire** : Gemini 2.5 Flash (toutes les photos jusqu'à détection)
- **Hauteur plafond** : Gemini 2.5 Pro (1ère photo)
- **Pièce de vie** : Gemini 2.5 Flash (5 premières photos)
- **Vis-à-vis** : Gemini 2.5 Flash (5 premières photos avec fenêtre)
- **Luminosité image** : Calcul depuis photos

### Analyse Texte (IA)
- **Style** : Détection depuis description/caractéristiques
- **Cuisine** : Détection depuis description/caractéristiques
- **Baignoire** : Détection depuis description/caractéristiques
- **Localisation** : Extraction métro/quartier depuis texte
- **Exposition** : Extraction orientation depuis texte

### Données Factuelles
- **Prix** : Depuis annonce (prix, surface)
- **Localisation** : Depuis map_info (géocodage)
- **Étage** : Depuis annonce ou API

---

## 🔄 Validation Croisée

### Critères avec validation croisée texte + photos
1. **Cuisine** : `scores_detaille.cuisine.details.photo_validation`
2. **Baignoire** : `scores_detaille.baignoire.details.photo_validation`

### Statuts de validation
- **Pas de conflit** : Texte et photos concordent → utiliser `photo_result`
- **Conflit** : Texte et photos divergent → utiliser `tier` comme résultat final
- **Tier2** : Non analysée → retourner "Non spécifié"

---

## 📝 Format Général des Outputs

Tous les critères suivent le même format de base :

```json
{
  "main_value": "Valeur principale affichée",
  "confidence": 70,  // null pour données factuelles
  "indices": "Critère Indice:\nDétails séparés par ·"
}
```

### Règles de formatage
- **main_value** : Valeur principale, toujours présente
- **confidence** : Pourcentage 0-100, ou `null` pour données factuelles
- **indices** : Format `"[Critère] Indice:\n[liste séparée par ·]"` ou `null`

---

## 🎯 Priorités d'Extraction

Pour chaque critère, les sources sont consultées dans cet ordre :

1. **scores_detaille.[critere]** (résultat final après validation croisée)
2. **style_analysis.[critere]** (analyse images uniquement)
3. **apartment.[critere]** (données brutes)
4. **Fallback** : Calcul depuis autres sources ou valeurs par défaut

---

## ✅ Checklist de Validation

Pour chaque critère, vérifier :
- [ ] `main_value` est présent et non vide
- [ ] `confidence` est un nombre 0-100 ou `null`
- [ ] `indices` suit le format `"[Critère] Indice:\n..."` ou est `null`
- [ ] Les valeurs correspondent aux règles de classification
- [ ] Les tiers correspondent à `scoring_config.json`

---

*Document généré le : 2025-01-XX*
*Version : 1.0*

