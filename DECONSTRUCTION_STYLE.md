# 🎨 Déconstruction du Barème Style - HomeScore

## 📊 Vue d'ensemble

Le critère **STYLE** représente **20 points** sur 100 dans le système de scoring HomeScore. Il évalue le style architectural de l'appartement selon 3 catégories principales : **Ancien**, **Atypique**, ou **Neuf**.

---

## 🎯 Les 3 Tiers du Barème Style

### **TIER 1 - ANCIEN (20 points)**
- **Styles détectés** : `Haussmannien`
- **Score** : 20/20 points
- **Indices visuels** :
  - Moulures
  - Cheminée
  - Parquet
  - Hauteur sous plafond importante
  - Balcon en fer forgé
  - Éléments architecturaux caractéristiques

### **TIER 2 - ATYPIQUE (10 points)**
- **Styles détectés** : `Loft`, `Atypique`, `Unique`, `Original`
- **Score** : 10/20 points
- **Indices textuels** :
  - Mots-clés directs : `loft`, `atypique`, `unique`, `original`
  - Concepts atypiques : `ancien entrepôt`, `ancien atelier`, `ancien hangar`, `ancien garage`
  - Mots-clés de rénovation : `réhabilité`, `transformé`, `reconverti`
  - Caractéristiques : `volume généreux`, `hauteur sous plafond importante`, `poutres apparentes`, `béton brut`
- **Indices visuels** :
  - Espaces ouverts
  - Volumes généreux
  - Caractère unique
  - Style industriel

### **TIER 3 - NEUF (0 points)**
- **Styles détectés** : `Moderne`, `Contemporain`, `Récent`, `Années 20-70`
- **Score** : 0/20 points
- **Indices visuels** :
  - Terrasse métal
  - Vue moderne
  - Sol moderne (carrelage)
  - Fenêtre moderne
  - Hauteur plafond réduite
  - Lignes épurées
  - Design minimaliste

---

## 🔄 Processus de Détection du Style (NOUVEAU SYSTÈME)

Le système utilise une **priorité stricte** : Analyse textuelle d'abord, puis analyse visuelle si nécessaire.

### **1. PRIORITÉ 1 : Analyse Textuelle avec OpenAI**

Le système commence par analyser le texte (description, caractéristiques, titre) avec OpenAI GPT pour détecter :
- **Mention explicite du style** : "haussmannien", "loft", "ancien entrepôt", etc.
- **Caractéristiques architecturales** : indices correspondants au style

**Si mention explicite + caractéristiques détectées** → **Confiance 100%** → Retour immédiat, pas d'analyse visuelle nécessaire.

**Si pas de mention explicite ou pas de caractéristiques** → Passage à l'analyse visuelle.

**Structure attendue** :
```json
{
  "style_analysis": {
    "style": {
      "type": "haussmannien|moderne|loft|atypique|autre",
      "confidence": 0.0-1.0,
      "justification": "description détaillée",
      "details": "éléments observés",
      "score": 20|10|0
    }
  }
}
```

### **2. PRIORITÉ 2 : Analyse Visuelle sur Top 5 Photos**

Si pas de mention explicite + caractéristiques dans le texte, le système analyse les **5 premières photos** avec **OpenAI Vision API**.

#### **A. Analyse Textuelle** (`analyze_text()`)
- Utilise `TextAIAnalyzer` (OpenAI GPT) pour analyser :
  - `description`
  - `caracteristiques`
  - `titre`
- Détecte les mentions explicites du style et les indices architecturaux
- **Si mention explicite + caractéristiques** → Retourne confiance 1.0 (100%) et arrête
- **Sinon** → Continue avec analyse visuelle

#### **B. Analyse Visuelle** (`analyze_single_photo()`)
- Utilise **OpenAI Vision API** pour analyser les **5 premières photos**
- **Nouveau prompt** : Détection d'indices précis avec confiance individuelle :

```
INDICES À DÉTECTER (avec confiance 0.0-1.0 pour chaque) :

1. CHEMINÉE : Cheminée visible (ancienne ou décorative)
2. PARQUET POINTE DE HONGRIE : Parquet avec motif pointe de Hongrie (chevrons)
3. MOULURES : Moulures au plafond ou sur les murs, corniches, rosaces
4. CHAUFFAGE : Radiateurs anciens en fonte
5. BALCON FER FORGÉ : Balcon avec garde-corps en fer forgé (style haussmannien)
```

Chaque indice retourne :
- `present`: true/false
- `confiance`: 0.0-1.0 (selon visibilité claire)
- `description`: description de ce qui est observé

#### **C. Agrégation des Indices** (`aggregate_analyses()`)
- Agrège les indices de toutes les photos analysées
- Calcule la confiance moyenne par indice
- **Si ≥ 2 indices haussmanniens détectés** → Force style "haussmannien"
- Construit les détails avec liste des indices et leurs confiances

### **3. Fallback : Analyse Texte Seule**

Si l'analyse visuelle échoue aussi, le système utilise une **analyse texte simple** avec des mots-clés (code legacy dans `scoring.py`) :

```python
# Mots-clés directs pour "Atypique"
atypique_direct = ['loft', 'atypique', 'unique', 'original', ...]

# Concepts atypiques
atypique_concepts = [
    'ancien entrepôt', 'ancien atelier', 'ancien hangar',
    'entrepôt rénové', 'atelier rénové', 'hangar rénové',
    'réhabilité', 'transformé', 'reconverti',
    'volume généreux', 'hauteur sous plafond importante',
    'caractère industriel', 'poutres apparentes', 'béton brut',
    'espaces ouverts', 'grands volumes'
]

# Détection Haussmannien
is_haussmannien = 'haussmann' in text_combined

# Détection Atypique
is_atypique = any(keyword in text_combined for keyword in atypique_direct) or \
              any(concept in text_combined for concept in atypique_concepts)
```

---

## 📝 Fonction `score_style()` dans `scoring.py`

### **Algorithme de Scoring**

```python
def score_style(apartment, config):
    """
    1. Cherche style_analysis['style']['type']
    2. Si trouvé → classifie selon les tiers :
       - tier1_styles → 20 pts
       - 'atypique' ou 'loft' → 10 pts
       - sinon → 0 pts
    3. Si pas de style_analysis → génère avec ApartmentStyleAnalyzer
    4. Si génération échoue → fallback analyse texte seule
    """
```

### **Logique de Classification**

1. **Normalisation** : `style_type.lower()`
2. **Vérification Tier 1** : `'haussmann' in style_type` → **20 pts**
3. **Vérification Tier 2** : `'atypique' in style_type or 'loft' in style_type` → **10 pts**
4. **Par défaut** : **0 pts** (Tier 3 - Neuf)

---

## 🎨 Formatage pour l'Affichage (`criteria/style.py`)

La fonction `format_style()` transforme les données brutes en format d'affichage :

### **Transformation des Styles**

```python
# style_type → style_name pour affichage
if 'haussmann' in style_type_lower:
    style_name = "Ancien"
elif 'loft' in style_type_lower or 'atypique' in style_type_lower:
    style_name = "Atypique"
else:
    style_name = "Neuf"
```

### **Extraction des Indices**

1. **Pour Ancien** : cherche `['moulures', 'cheminée', 'parquet', 'hauteur sous plafond', ...]`
2. **Pour Atypique** : cherche `['loft', 'atypique', 'unique', 'original', 'espace ouvert', ...]`
3. **Pour Neuf** : cherche `['terrasse métal', 'vue', 'sol moderne', 'fenêtre moderne', ...]`

### **Fallback sur `scores_detaille`**

Si `style_analysis` n'existe pas, cherche dans `scores_detaille.style.justification` :
- Si contient `'haussmann'` ou `'moulures'` → `style_type = 'haussmannien'`
- Si contient `'70'` ou `'seventies'` ou `'moderne'` → `style_type = 'moderne'`

---

## 📂 Fichiers Clés

### **Configuration**
- `scoring_config.json` : Définition des tiers et scores
  ```json
  "style": {
    "poids": 20,
    "tiers": {
      "tier1": {"score": 20, "styles": ["Haussmannien"]},
      "tier2": {"score": 10, "styles": ["Loft", "Atypique", "Unique", "Original"]},
      "tier3": {"score": 0, "styles": ["Moderne", "Contemporain", "Récent", ...]}
    }
  }
  ```

### **Scoring**
- `scoring.py` : Fonction `score_style()` - logique principale
- `criteria/style.py` : Fonction `format_style()` - formatage pour affichage

### **Analyse**
- `analyze_apartment_style.py` : Classe `ApartmentStyleAnalyzer`
  - `analyze_text()` : Analyse textuelle IA
  - `analyze_single_photo()` : Analyse visuelle OpenAI Vision
  - `combine_text_and_photo_analysis()` : Validation croisée
  - `calculate_style_score()` : Calcul du score final

### **Affichage**
- `generate_scorecard_html.py` : Fonction `format_style_criterion()` - génération HTML

---

## 🔍 Exemples Concrets

### **Exemple 1 : Appartement Haussmannien**
```json
{
  "style_analysis": {
    "style": {
      "type": "haussmannien",
      "confidence": 0.85,
      "details": "Moulures · cheminée · parquet",
      "score": 20
    }
  }
}
```
**Résultat** : **20/20 points** (Tier 1 - Ancien)

### **Exemple 2 : Loft Atypique**
```json
{
  "description": "Magnifique loft atypique rénové, ancien entrepôt transformé avec poutres apparentes"
}
```
**Détection** : Mots-clés `loft`, `atypique`, `ancien entrepôt`, `transformé` → **10/20 points** (Tier 2 - Atypique)

### **Exemple 3 : Appartement Moderne**
```json
{
  "style_analysis": {
    "style": {
      "type": "moderne",
      "confidence": 0.90,
      "details": "Terrasse métal · sol moderne · fenêtre moderne",
      "score": 0
    }
  }
}
```
**Résultat** : **0/20 points** (Tier 3 - Neuf)

---

## ⚠️ Points d'Attention

1. **Priorité des Sources** :
   - `style_analysis` (texte + photos) > `scores_detaille.style` (texte seul) > fallback texte simple

2. **Confiance** :
   - La confiance est ajustée lors de la validation croisée
   - Si texte et photos sont cohérents → confiance augmentée
   - Si conflit → confiance diminuée

3. **Cache** :
   - Les analyses de photos sont mises en cache (`cache_api.py`)
   - Clé de cache : `style_photo:{photo_path}`

4. **Performance** :
   - Seulement les **3 premières photos** sont analysées pour économiser les tokens OpenAI
   - Les analyses sont mises en cache pour éviter les appels répétés

5. **Fallback Systématique** :
   - Si aucune détection, le système retourne toujours un résultat :
   - Tier 3 (0 pts) par défaut avec justification "Style neuf (par défaut)"

---

## 🎯 Résumé du Flux Complet

```
┌─────────────────────────────────────────────────────────────┐
│                    APPARTEMENT DATA                         │
│  - description, caracteristiques, titre                      │
│  - photos (URLs)                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  style_analysis existe?│
         └───────┬───────────────┘
                 │
        ┌────────┴────────┐
        │ OUI             │ NON
        ▼                 ▼
┌───────────────┐  ┌──────────────────────────┐
│ Utiliser      │  │ ApartmentStyleAnalyzer  │
│ style_analysis│  │  1. analyze_text()       │
│               │  │  2. analyze_photos()     │
└───────┬───────┘  │  3. combine()            │
        │          └──────────┬───────────────┘
        │                    │
        └──────────┬─────────┘
                   ▼
         ┌─────────────────────┐
         │ Classification Tier │
         │  Haussmannien → 20  │
         │  Atypique → 10      │
         │  Neuf → 0           │
         └──────────┬──────────┘
                    ▼
         ┌─────────────────────┐
         │ Formatage Affichage │
         │  - style_name       │
         │  - confidence       │
         │  - indices          │
         └─────────────────────┘
```

---

## 📚 Références

- Configuration : `scoring_config.json` lignes 54-73
- Scoring : `scoring.py` lignes 191-329
- Formatage : `criteria/style.py` lignes 7-105
- Analyse : `analyze_apartment_style.py` lignes 18-556
- Affichage : `generate_scorecard_html.py` lignes 473-551

