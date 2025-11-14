# 🚀 Optimisation : Analyse Unifiée des Photos

## 📋 Problème Initial

Lors du scoring d'un appartement, plusieurs critères nécessitent l'analyse des photos :
- **Style** (haussmannien, atypique, moderne)
- **Cuisine** (ouverte/fermée)
- **Luminosité** (très lumineux, lumineux, moyen, faible)
- **Baignoire** (présente/absente)

### ❌ Avant l'optimisation

Chaque critère analysait les photos **séparément** avec des appels API Vision distincts :

```
Appartement avec 5 photos :
├── score_style() → analyse 5 photos pour style
├── score_cuisine() → analyse 5 photos pour cuisine
├── score_baignoire() → analyse 5 photos pour baignoire
└── score_ensoleillement() → analyse 3 photos pour luminosité

Total : ~18 appels API Vision par appartement
Temps : ~2-3 minutes par appartement
```

**Problèmes :**
- 🔴 Analyse répétée des mêmes photos
- 🔴 Coûts API élevés (multiples appels)
- 🔴 Temps de traitement long
- 🔴 Cache non optimisé (chaque critère a son propre cache)

## ✅ Solution : Analyse Unifiée

### Concept

**Une seule analyse par photo** qui extrait **TOUTES les informations** nécessaires en un seul appel API :

```
Appartement avec 5 photos :
└── analyze_photo_unified() → analyse chaque photo UNE FOIS pour extraire :
    ├── Style
    ├── Cuisine
    ├── Luminosité
    └── Baignoire

Total : 5 appels API Vision par appartement (au lieu de 18)
Temps : ~30-40 secondes par appartement
```

### Architecture

```
┌─────────────────────────────────────────┐
│  UnifiedPhotoAnalyzer                   │
│                                         │
│  analyze_photo_unified(photo_url)      │
│    ↓                                    │
│  Un seul appel OpenAI Vision            │
│  avec prompt unifié qui demande :      │
│    - Style                             │
│    - Cuisine                           │
│    - Luminosité                        │
│    - Baignoire                         │
│    ↓                                    │
│  Retourne JSON avec TOUT               │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Scoring Optimisé                       │
│                                         │
│  - Réutilise les résultats              │
│  - Pas de réanalyse                    │
│  - Cache optimisé                      │
└─────────────────────────────────────────┘
```

## 🔧 Implémentation

### Fichiers créés/modifiés

1. **`analyze_photos_unified.py`** (nouveau)
   - `UnifiedPhotoAnalyzer` : Classe principale
   - `analyze_photo_unified()` : Analyse une photo pour tout extraire
   - `analyze_all_photos_unified()` : Analyse toutes les photos et agrège

2. **`scoring_optimized.py`** (modifié)
   - `analyze_photos_once()` : Analyse toutes les photos une seule fois
   - Réutilise les résultats pour tous les critères
   - `score_style_optimized()` : Utilise le cache
   - `score_cuisine_optimized()` : Utilise le cache
   - `score_baignoire_optimized()` : Utilise le cache

3. **`add_new_apartments_to_db.py`** (modifié)
   - Utilise `scoring_optimized` au lieu de `scoring`

### Prompt unifié OpenAI Vision

Le prompt demande **TOUT en une seule fois** :

```json
{
  "style": {
    "type": "haussmannien|atypique|moderne|autre",
    "confidence": 0.0-1.0,
    "indices": ["moulures", "parquet", ...]
  },
  "cuisine": {
    "ouverte": true|false,
    "confidence": 0.0-1.0,
    "indices": "description"
  },
  "luminosite": {
    "type": "tres_lumineux|lumineux|moyen|faible",
    "score": 0-10,
    "confidence": 0.0-1.0
  },
  "baignoire": {
    "presente": true|false,
    "confidence": 0.0-1.0,
    "is_bathroom": true|false
  }
}
```

## 📊 Gains de Performance

### Métriques

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| **Appels API par appartement** | ~18 | ~5 | **-72%** |
| **Temps par appartement** | 2-3 min | 30-40 sec | **-75%** |
| **Coût API (tokens)** | ~180k | ~50k | **-72%** |
| **Photos analysées** | 18 fois | 5 fois | **-72%** |

### Exemple concret

**Avant :**
- 17 nouveaux appartements × 18 appels = **306 appels API**
- Temps estimé : **34-51 minutes**

**Après :**
- 17 nouveaux appartements × 5 appels = **85 appels API**
- Temps estimé : **8-11 minutes**

**Gain total : ~75% plus rapide** ⚡

## 🎯 Utilisation

### Pour scorer les nouveaux appartements

Le script `add_new_apartments_to_db.py` utilise automatiquement la version optimisée :

```bash
python add_new_apartments_to_db.py
```

### Utilisation programmatique

```python
from scoring_optimized import score_apartment_optimized
from scoring import load_scoring_config

# Charger la config
config = load_scoring_config()

# Scorer un appartement (analyse unifiée automatique)
score_result = score_apartment_optimized(apartment_data, config)
```

### Utilisation directe de l'analyseur unifié

```python
from analyze_photos_unified import UnifiedPhotoAnalyzer

analyzer = UnifiedPhotoAnalyzer()

# Analyser toutes les photos d'un appartement
photos_urls = ["url1", "url2", "url3", ...]
result = analyzer.analyze_all_photos_unified(photos_urls, apartment_id="12345")

# Résultat contient :
# - result['style'] : {'type': 'haussmannien', 'confidence': 0.9}
# - result['cuisine'] : {'ouverte': True, 'confidence': 0.85}
# - result['luminosite'] : {'type': 'lumineux', 'score': 7}
# - result['baignoire'] : {'presente': True, 'confidence': 0.8}
```

## 🔍 Fonctionnement Détaillé

### 1. Analyse d'une photo

```python
def analyze_photo_unified(photo_url):
    """
    1. Télécharge la photo
    2. Encode en base64
    3. Appel OpenAI Vision avec prompt unifié
    4. Parse le JSON de réponse
    5. Cache le résultat
    6. Retourne toutes les infos
    """
```

### 2. Agrégation des résultats

Pour plusieurs photos, on agrège les résultats :

- **Style** : Mode (le plus fréquent) avec confiance moyenne
- **Cuisine** : Si au moins une photo montre cuisine ouverte → ouverte
- **Luminosité** : Mode des types + score moyen
- **Baignoire** : Si au moins une photo montre baignoire → présente

### 3. Réutilisation dans le scoring

```python
# Analyse UNE FOIS
photo_cache = analyze_photos_once(apartment)

# Réutilise pour tous les critères
score_style = score_style_optimized(apartment, config, photo_cache)
score_cuisine = score_cuisine_optimized(apartment, config, photo_cache)
score_baignoire = score_baignoire_optimized(apartment, config, photo_cache)
```

## 💾 Cache

Le système utilise un cache pour éviter de réanalyser les mêmes photos :

- **Clé de cache** : `{apartment_id}_unified_{photo_url}`
- **Stockage** : Via `cache_api.py`
- **Avantage** : Si une photo a déjà été analysée, réutilisation immédiate

## 🔄 Fallback

Si l'analyse unifiée échoue, le système utilise automatiquement la méthode ancienne :

```python
try:
    # Analyse unifiée
    unified_result = analyzer.analyze_all_photos_unified(...)
except:
    # Fallback sur méthode ancienne
    result = _fallback_analysis(...)
```

## 📈 Résultats

### Avant optimisation
```
🏠 Scoring 1/17: Appartement 85467731
   📸 Analyse photo cuisine 1/5...
   📸 Analyse photo cuisine 2/5...
   📸 Analyse photo style 1/5...
   📸 Analyse photo style 2/5...
   📸 Analyse photo baignoire 1/5...
   ⏱️ Temps: ~2-3 minutes
```

### Après optimisation
```
🏠 Scoring 1/17: Appartement 85467731
   📸 Analyse UNIFIÉE des photos (style + cuisine + luminosité + baignoire ensemble)...
      📸 Photo 1/5...
      📸 Photo 2/5...
      ✅ Style: haussmannien (90%)
      ✅ Cuisine: Ouverte (85%)
      ✅ Luminosité: lumineux
      ✅ Baignoire: Oui (80%)
      📊 5 photos analysées en UNE SEULE passe
   ⏱️ Temps: ~30-40 secondes
```

## 🎯 Critères Extraits

### Style
- **haussmannien** : moulures, parquet ancien, cheminée, hauts plafonds
- **atypique** : loft, conversion, original, unique
- **moderne** : contemporain, récent, années 60-70

### Cuisine
- **ouverte** : visible depuis salon, bar, séparation partielle
- **fermée** : séparée par mur, porte, espace clos

### Luminosité
- **tres_lumineux** : très clair, beaucoup de lumière naturelle
- **lumineux** : clair, bonne luminosité
- **moyen** : luminosité moyenne
- **faible** : sombre, peu de lumière

### Baignoire
- **presente** : baignoire visible dans la photo
- **absente** : pas de baignoire (seulement douche ou pas de salle de bain)

## ✅ Avantages

1. **Performance** : 75% plus rapide
2. **Coûts** : 72% moins d'appels API
3. **Simplicité** : Une seule fonction d'analyse
4. **Cache optimisé** : Une seule clé de cache par photo
5. **Maintenabilité** : Code plus simple et centralisé

## 🔧 Maintenance

### Ajouter un nouveau critère

Pour ajouter un nouveau critère à l'analyse unifiée :

1. Modifier le prompt dans `analyze_photo_unified()` pour inclure le nouveau critère
2. Ajouter l'extraction dans `analyze_all_photos_unified()`
3. Mettre à jour `analyze_photos_once()` pour utiliser le nouveau résultat
4. Créer `score_nouveau_critere_optimized()` qui utilise le cache

### Modifier le prompt

Le prompt est dans `analyze_photos_unified.py`, fonction `analyze_photo_unified()`.

## 📝 Notes Techniques

- **Modèle utilisé** : `gpt-4o-mini` (optimisé pour réduire les coûts)
- **Max photos analysées** : 5 (suffisant pour détecter tous les critères)
- **Format réponse** : JSON strict (parsing robuste avec nettoyage markdown)
- **Timeout** : 30 secondes par appel API
- **Cache** : Persistant via `cache_api.py`

## 🚀 Prochaines Optimisations Possibles

1. **Parallélisation** : Analyser plusieurs photos en parallèle (actuellement séquentiel)
2. **Batch API** : Utiliser les batch requests OpenAI si disponible
3. **Résultats partiels** : Si certaines photos échouent, continuer avec les autres
4. **Priorisation** : Analyser d'abord les photos les plus pertinentes (salon, cuisine)

## 📅 Date de création

2024-11-03 - Optimisation majeure de l'analyse des photos pour réduire les appels API de 72%






