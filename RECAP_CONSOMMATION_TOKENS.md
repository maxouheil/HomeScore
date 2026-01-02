# 📊 Récapitulatif de la consommation de tokens - 7 décembre 2025

## 🔍 Problèmes identifiés

### 1. **Scoring avec critère "calme" - Activité massive le 7 décembre**

**Observation :**
- **273 fichiers de cache créés** le 7 décembre dans `data/cache/calme/`
- Pic d'activité entre **14:30-14:32** (40+ fichiers créés en quelques minutes)
- Activité continue toute la journée (12:00-14:32)

**Script responsable :**
- `score_all_with_calme.py` - Script qui score tous les appartements avec le nouveau critère "calme"

**Problème :**
Le critère "calme" utilise **Overpass API** (gratuit) et **Nominatim** (gratuit), donc **PAS de consommation de tokens OpenAI**. Cependant, le scoring peut déclencher d'autres analyses qui consomment des tokens.

---

### 2. **Appels OpenAI non optimisés dans `score_style()`**

**Fichier :** `scoring.py` (lignes 327-384)

**Problème identifié :**
```python
# Ligne 327-384 dans scoring.py
# Si pas de style_analysis, essayer de le générer UNIQUEMENT si les photos sont déjà en cache
try:
    from analyze_apartment_style import ApartmentStyleAnalyzer
    from cache_api import get_cache
    
    cache = get_cache()
    photos = apartment.get('photos', [])
    
    # Vérifier si au moins une photo est déjà en cache
    photos_in_cache = False
    if photos:
        # Vérifier si la première photo a une analyse en cache
        first_photo_url = photos[0] if isinstance(photos[0], str) else photos[0].get('url', '')
        if first_photo_url:
            cached_style = cache.get('style_photo', first_photo_url)
            if cached_style:
                photos_in_cache = True
    
    # Seulement analyser si les photos sont déjà en cache (pour éviter les appels API)
    if photos_in_cache or style_analysis:
        style_analyzer = ApartmentStyleAnalyzer()
        style_analysis = style_analyzer.analyze_apartment_photos_from_data(apartment)
```

**⚠️ PROBLÈME CRITIQUE :**
La condition `if photos_in_cache or style_analysis:` est **LOGIQUEMENT INCORRECTE** :
- Si `style_analysis` existe déjà, pourquoi ré-analyser ?
- Si `photos_in_cache` est True mais qu'il n'y a pas de `style_analysis`, cela déclenche une nouvelle analyse OpenAI

**Impact :**
- Si `score_all_with_calme.py` est exécuté sur **tous les appartements** sans `style_analysis`, cela peut déclencher des centaines d'appels OpenAI Vision API
- Chaque appel analyse plusieurs photos (3-5 photos par appartement)
- Coût estimé : ~$0.01-0.02 par appartement avec photos

---

### 3. **Analyse de style déclenchée automatiquement**

**Fichier :** `analyze_apartment_style.py`

**Problème :**
- `ApartmentStyleAnalyzer.analyze_apartment_photos_from_data()` peut faire des appels OpenAI Vision API
- Utilise `gpt-4o-mini` (économique mais coûte quand même)
- Analyse plusieurs photos par appartement

**Scénario probable :**
1. `score_all_with_calme.py` est exécuté sur **tous les appartements**
2. Pour chaque appartement, `score_apartment()` est appelé
3. `score_style()` vérifie si `style_analysis` existe
4. Si pas de `style_analysis` mais photos en cache → **NOUVEL APPEL OPENAI**
5. Résultat : **273 appartements × ~$0.01-0.02 = $2.73-$5.46** (mais peut être plus si plusieurs photos analysées)

---

### 4. **Autres analyses déclenchées lors du scoring**

**Fichiers concernés :**
- `score_cuisine()` - Peut appeler `extract_cuisine_text.py` → OpenAI Vision
- `score_baignoire()` - Peut appeler `extract_baignoire.py` → OpenAI Vision
- `score_large_piece_vie()` - Peut appeler `analyze_photos.py` → OpenAI Vision
- `score_hauteur_plafond()` - Peut appeler `analyze_photos.py` → OpenAI Vision

**Problème :**
Chaque critère peut déclencher des appels OpenAI indépendamment, même si les données sont déjà en cache.

---

## 💰 Estimation des coûts

### Scénario probable (7 décembre) :
- **273 appartements** traités avec `score_all_with_calme.py`
- Chaque appartement peut déclencher :
  - 1 appel OpenAI Vision pour `style_analysis` (si pas présent)
  - 1 appel pour `cuisine` (si pas analysé)
  - 1 appel pour `baignoire` (si pas analysé)
  - 1 appel pour `large_piece_vie` (si pas analysé)
  - 1 appel pour `hauteur_plafond` (si pas analysé)

**Coût par appartement :**
- Si 1-2 analyses déclenchées : ~$0.01-0.02
- Si toutes les analyses déclenchées : ~$0.05-0.10

**Total estimé :**
- Minimum : 273 × $0.01 = **$2.73**
- Maximum : 273 × $0.10 = **$27.30**
- Probable : 273 × $0.02-0.05 = **$5.46-$13.65**

**Note :** Le coût réel de $50 suggère que :
- Soit plus d'appartements ont été traités
- Soit plusieurs analyses ont été déclenchées par appartement
- Soit des scripts supplémentaires ont été exécutés

---

## 🔧 Solutions recommandées

### 1. **Corriger la logique dans `score_style()`**

**Problème actuel :**
```python
if photos_in_cache or style_analysis:
    # Analyse même si style_analysis existe déjà !
```

**Solution :**
```python
# Ne PAS analyser si style_analysis existe déjà
if style_analysis:
    # Utiliser les données existantes
    return style_analysis
    
# Seulement analyser si photos en cache ET pas de style_analysis
if photos_in_cache and not style_analysis:
    style_analyzer = ApartmentStyleAnalyzer()
    style_analysis = style_analyzer.analyze_apartment_photos_from_data(apartment)
```

### 2. **Vérifier le cache AVANT d'appeler les fonctions de scoring**

Dans `score_all_with_calme.py`, ajouter des vérifications de cache avant de scorer :
```python
# Vérifier si l'appartement a déjà tous les scores nécessaires
if apartment.get('scores_detaille', {}).get('style'):
    # Skip l'analyse de style
    pass
```

### 3. **Ajouter des logs de consommation**

Ajouter des logs pour tracker les appels OpenAI :
```python
import logging
logger = logging.getLogger('openai_calls')
logger.info(f"Appel OpenAI Vision pour {apartment_id}: {model}, {num_photos} photos")
```

### 4. **Utiliser le cache de manière plus agressive**

Vérifier le cache AVANT chaque appel API, pas seulement après.

### 5. **Limiter les analyses lors du scoring**

Ajouter un flag pour désactiver les analyses IA lors du scoring :
```python
score_apartment(apartment, config, skip_ai_analysis=True)
```

---

## 📋 Actions immédiates

1. ✅ **Vérifier les logs** pour identifier quels scripts ont été exécutés le 7 décembre
2. ✅ **Corriger la logique dans `score_style()`** pour éviter les ré-analyses
3. ✅ **Ajouter des vérifications de cache** dans tous les critères de scoring
4. ✅ **Monitorer les appels OpenAI** avec des logs détaillés
5. ✅ **Limiter les analyses** lors du scoring en batch

---

## 🔍 Scripts à vérifier

- `score_all_with_calme.py` - Exécuté le 7 décembre ?
- `analyze_all_apartments_style.py` - Exécuté le 7 décembre ?
- `rescore_all_apartments.py` - Exécuté le 7 décembre ?
- `batch_scrape_known_urls.py` - Exécuté le 7 décembre ?

---

## 📊 Statistiques du 7 décembre

- **273 fichiers de cache** créés dans `data/cache/calme/`
- **Pic d'activité** : 14:30-14:32 (40+ fichiers)
- **Activité continue** : 12:00-14:32
- **Coût estimé** : $5-27 selon le nombre d'analyses déclenchées

---

**Date de création :** 7 décembre 2025
**Auteur :** Analyse automatique

