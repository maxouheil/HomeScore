# 💰 Récapitulatif des Coûts en Tokens (API OpenAI)

## 🎯 Vue d'ensemble

Pour **chaque appartement** analysé, le système fait de nombreux appels API OpenAI, particulièrement coûteux pour l'analyse d'images.

---

## 📊 Détail des Appels API par Appartement

### 1. **Analyse de Style** (`analyze_apartment_style.py`)
- **Analyse texte** : 1 appel GPT-4o-mini (~500 tokens)
- **Analyse photos** : Jusqu'à **3 appels GPT-4o-mini** (1 par photo)
  - Chaque photo = ~800 tokens (image encodée en base64 + prompt)
- **Total style** : ~2900 tokens par appartement

### 2. **Analyse d'Exposition** (`extract_exposition.py` + `analyze_photos.py`)
- **Analyse texte** : 1 appel GPT-4o-mini (~500 tokens)
- **Analyse photos** : Jusqu'à **3 appels GPT-4o** ⚠️ (1 par photo)
  - Chaque photo = ~800 tokens (image base64 + prompt)
  - **GPT-4o est TRÈS CHER** pour les images !
- **Total exposition** : ~2900 tokens par appartement, mais avec modèle cher

### 3. **Analyse Baignoire** (`extract_baignoire.py`)
- **Analyse texte** : 1 appel GPT-4o-mini (~500 tokens)
- **Analyse photos** : Jusqu'à **3 appels GPT-4o** ⚠️ (1 par photo)
  - Chaque photo = ~300 tokens (image base64 + prompt)
- **Total baignoire** : ~1400 tokens par appartement, mais avec modèle cher

### 4. **Analyse Cuisine** (`extract_cuisine_text.py` + `analyze_photos.py`)
- **Analyse texte** : 1 appel GPT-4o-mini (~500 tokens)
- **Analyse photos** : Jusqu'à **3 appels GPT-4o-mini** (1 par photo)
  - Chaque photo = ~300 tokens (image base64 + prompt)
- **Total cuisine** : ~1400 tokens par appartement

### 5. **Scoring Final** (`score_appartement.py`, `score_batch_simple.py`)
- **Si utilisé** : 1 appel GPT-4o (~3000 tokens)
  - Prompt complet avec toutes les données de l'appartement
- **Note** : Le scoring actuel utilise des règles (`scoring.py`), pas OpenAI

---

## 💸 Coûts Estimés

### Par Appartement (avec photos)
- **Appels texte** : ~4-5 appels GPT-4o-mini = ~2000 tokens
- **Appels photo** : ~9-12 appels (mix GPT-4o et GPT-4o-mini) = ~5000-8000 tokens

**Total par appartement** : ~7000-10000 tokens

### Coûts OpenAI (prix approximatifs)
- **GPT-4o-mini** : ~$0.15 / 1M tokens (input), ~$0.60 / 1M tokens (output)
- **GPT-4o** : ~$2.50 / 1M tokens (input), ~$10 / 1M tokens (output)
- **GPT-4o Vision** : Plus cher encore (~$5-10 / 1M tokens input avec images)

### Exemple : Batch de 40 Appartements
- **Tokens texte** : 40 × 2000 = 80,000 tokens (~$0.01)
- **Tokens photo** : 40 × 6000 = 240,000 tokens (~$1.20-2.40 avec GPT-4o)
- **Total** : ~$1.20-2.40 pour 40 appartements

⚠️ **Le coût réel peut être plus élevé** car :
- Les images en base64 sont très volumineuses
- GPT-4o Vision coûte plus cher que GPT-4o standard
- Plusieurs photos peuvent être analysées par critère

---

## 🔍 Où sont les Appels API ?

### Fichiers Principaux

1. **`analyze_text_ai.py`** (ligne 229-305)
   - `_call_ai()` : Appel générique GPT-4o-mini
   - Utilisé pour : exposition, baignoire, cuisine, style (texte)

2. **`analyze_photos.py`** (lignes 59-157, 342-490, 492-652)
   - `_analyze_single_photo()` : GPT-4o pour exposition (ligne 78)
   - `_analyze_single_photo_baignoire()` : GPT-4o-mini pour baignoire (ligne 391)
   - `_analyze_single_photo_cuisine()` : GPT-4o-mini pour cuisine (ligne 539)

3. **`analyze_apartment_style.py`** (lignes 302-411)
   - `analyze_single_photo()` : GPT-4o-mini pour style (ligne 316)
   - `analyze_text()` : Appelle `TextAIAnalyzer` pour texte

4. **`extract_baignoire.py`** (lignes 210-320)
   - `_analyze_single_photo_baignoire()` : GPT-4o pour baignoire (ligne 236)

5. **`extract_exposition.py`** (ligne 125)
   - Appelle `text_ai_analyzer.analyze_exposition()` puis `photo_analyzer`

6. **`extract_cuisine_text.py`** (ligne 20)
   - Appelle `text_ai_analyzer.analyze_cuisine_ouverte()` puis `photo_analyzer`

---

## ⚠️ Problèmes Identifiés

### 1. **Multiples Analyses de la Même Photo**
- Une même photo peut être analysée plusieurs fois pour différents critères :
  - Exposition (GPT-4o)
  - Baignoire (GPT-4o)
  - Cuisine (GPT-4o-mini)
  - Style (GPT-4o-mini)
- **Solution** : Mettre en cache les résultats d'analyse photo

### 2. **Utilisation de GPT-4o au lieu de GPT-4o-mini**
- **Exposition** : Utilise GPT-4o (ligne 78 de `analyze_photos.py`)
- **Baignoire** : Utilise GPT-4o (ligne 236 de `extract_baignoire.py`)
- **Coût** : GPT-4o coûte ~10-20x plus cher que GPT-4o-mini
- **Solution** : Passer à GPT-4o-mini pour toutes les analyses photo

### 3. **Pas de Cache**
- Chaque exécution ré-analyse toutes les photos
- **Solution** : Mettre en cache les résultats par URL de photo

### 4. **Trop de Photos Analysées**
- **3 photos par critère** = jusqu'à 12 analyses photo par appartement
- **Solution** : Réduire à 1-2 photos maximum, ou analyser une seule fois

### 5. **Images Base64 Volumineuses**
- Chaque image encodée en base64 = ~50-200KB de tokens
- **Solution** : Compresser/réduire la taille des images avant encodage

---

## 💡 Recommandations pour Réduire les Coûts

### Priorité 1 : Urgent ⚠️
1. **Remplacer GPT-4o par GPT-4o-mini** pour toutes les analyses photo
   - `analyze_photos.py` ligne 78 : `'model': 'gpt-4o'` → `'model': 'gpt-4o-mini'`
   - `extract_baignoire.py` ligne 236 : `'model': 'gpt-4o'` → `'model': 'gpt-4o-mini'`
   - **Économie** : ~90% de réduction sur les coûts photo

2. **Réduire le nombre de photos analysées**
   - De 3 à 1 photo par critère (ou analyser 1 photo pour tous les critères)
   - **Économie** : ~66% de réduction

### Priorité 2 : Important
3. **Mettre en cache les résultats d'analyse**
   - Cache par URL de photo + critère
   - **Économie** : 100% sur les re-analyses

4. **Analyser une photo une seule fois pour tous les critères**
   - Au lieu de 4 analyses séparées, faire 1 analyse complète
   - **Économie** : ~75% de réduction

### Priorité 3 : Optimisation
5. **Compresser les images avant encodage**
   - Réduire la résolution (ex: 512x512 max)
   - **Économie** : ~50% de tokens par image

6. **Utiliser des modèles plus petits**
   - Pour certaines analyses simples, utiliser GPT-3.5-turbo si disponible

---

## 📈 Estimation des Économies

### Avant Optimisation (exemple : 40 appartements)
- Coût actuel : ~$2-5 par batch

### Après Optimisation
1. GPT-4o → GPT-4o-mini : **-90%** sur les coûts photo
2. 3 photos → 1 photo : **-66%** sur le nombre d'appels
3. Cache : **-100%** sur les re-analyses
4. Compression images : **-50%** sur les tokens par image

**Coût estimé après optimisation** : ~$0.10-0.20 par batch de 40 appartements

**Économie totale** : ~90-95% de réduction des coûts ! 🎉

---

## 🔧 Actions Immédiates Recommandées

1. ✅ **Changer GPT-4o → GPT-4o-mini** dans :
   - `analyze_photos.py` ligne 78
   - `extract_baignoire.py` ligne 236

2. ✅ **Réduire à 1 photo** au lieu de 3 dans :
   - `analyze_photos.py` ligne 37
   - `analyze_apartment_style.py` ligne 47
   - `extract_baignoire.py` ligne 183

3. ✅ **Implémenter un cache simple** :
   - Fichier JSON avec hash de l'URL photo + critère → résultat

4. ✅ **Analyser une photo une seule fois** :
   - Créer une fonction `analyze_photo_complete()` qui retourne tous les critères

---

## 📝 Notes Techniques

### Modèles Utilisés Actuellement
- **GPT-4o-mini** : Text analysis (exposition, baignoire, cuisine, style)
- **GPT-4o** : Photo analysis (exposition, baignoire) ⚠️ CHER
- **GPT-4o-mini** : Photo analysis (cuisine, style)

### Taille des Prompts
- **Texte** : ~500-1000 tokens par appel
- **Photo** : ~300-800 tokens par appel (sans compter l'image base64)
- **Image base64** : ~50-200KB = ~37,000-150,000 tokens par image

### Fréquence des Appels
- **Par appartement** : ~13-16 appels API
- **Par batch (40 appartements)** : ~520-640 appels API
- **Avec cache** : Réduit drastiquement sur les re-analyses

