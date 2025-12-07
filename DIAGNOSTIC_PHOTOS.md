# 🔍 Diagnostic: Pourquoi certains appartements n'ont pas d'images

## ⚠️ IMPORTANT: Fichier HTML unique

**🚨 ON TRAVAILLE UNIQUEMENT SUR `output/homepage.html`**

- **Fichier généré par:** `generate_scorecard_html.py`
- **NE JAMAIS créer d'autres fichiers HTML** (pas de `scorecard_fitscore_style.html`, etc.)
- **Toujours modifier:** `generate_scorecard_html.py` puis régénérer `homepage.html`
- **Voir:** `REGLE_HTML_UNIQUE.md` pour les règles complètes

## 📊 Résumé du diagnostic

**Date:** 2025-01-31  
**Total appartements analysés:** 17  
**Fichier HTML:** `output/homepage.html` (UNIQUEMENT)

### ✅ BONNE NOUVELLE
- **Tous les appartements (17/17) ont des photos détectées** par `get_all_apartment_photos()`
- **Tous les fichiers photo existent** dans `data/photos/{id}/`
- **Tous les appartements ont des photos dans le HTML généré**

### ⚠️ PROBLÈMES IDENTIFIÉS

#### 1. Limitation du nombre de photos téléchargées
- **Problème:** Le système télécharge seulement **4 photos maximum** par appartement (limite dans `scrape_jinka.py`)
- **Impact:** Les appartements ont souvent **7-10 photos dans le JSON** mais seulement **2-4 téléchargées**
- **Exemple:** 
  - Appartement `90129925`: 10 photos dans JSON → seulement 4 téléchargées
  - Appartement `88404156`: 10 photos dans JSON → seulement 2 téléchargées

#### 2. Photos dans JSON mais non téléchargées
- **Total photos dans JSON:** 155
- **Total photos téléchargées:** 66
- **Différence:** 89 photos disponibles dans le JSON mais non téléchargées localement

#### 3. Dossier `photos_v2` non utilisé
- **Problème:** Le code cherche d'abord dans `photos_v2/` mais aucun appartement n'a de photos dans ce dossier
- **Impact:** Tous les appartements utilisent le fallback vers `photos/` (ancien système)
- **Solution:** Soit utiliser `photos_v2/`, soit retirer cette vérification

## 🔍 Causes possibles si vous voyez des appartements sans images

### 1. **PROBLÈME CRITIQUE IDENTIFIÉ: Carousel non initialisé**
- **Symptôme:** Les images ont `display: none` dans la console développeur
- **Cause:** Le carousel n'appelait pas `updateCarousel()` après l'initialisation
- **Impact:** Les slides n'étaient pas positionnées correctement au chargement
- **✅ CORRIGÉ:** Ajout de `updateCarousel()` dans `initCarousel()`

### 2. Images avec erreur de chargement
- **Symptôme:** Les images se cachent avec `display: none` si elles ne peuvent pas se charger
- **Cause:** `onerror="this.style.display='none'"` cache l'image en cas d'erreur
- **✅ AMÉLIORÉ:** Changé pour cacher seulement la slide parente et logger l'erreur dans la console

### 3. HTML non régénéré
- **Symptôme:** Les photos existent mais ne sont pas visibles dans le HTML
- **Solution:** Régénérer le HTML avec `python3 generate_scorecard_html.py` (génère `output/homepage.html`)

### 4. Chemins relatifs incorrects
- **Symptôme:** Les photos ne se chargent pas dans le navigateur
- **Vérification:** Les chemins sont `../data/photos/{id}/photo_X.jpg`
- **Solution:** S'assurer que le HTML est ouvert depuis le dossier `output/`

### 5. Filtrage trop strict
- **Symptôme:** Certaines photos sont exclues par les patterns de filtrage
- **Patterns exclus:** `logo`, `placeholder`, `icon`, `AppStore.png`, etc.
- **Solution:** Vérifier si des photos valides sont exclues par erreur

### 6. Photos non téléchargées pour de nouveaux appartements
- **Symptôme:** Nouveaux appartements ajoutés sans photos téléchargées
- **Solution:** Exécuter `python3 batch_download_all_photos.py` ou `python3 download_apartment_photos.py`

## 🛠️ Solutions recommandées

### Solution 1: Télécharger toutes les photos disponibles
```bash
# Télécharger toutes les photos depuis le JSON
python3 batch_download_all_photos.py
```

### Solution 2: Augmenter la limite de photos téléchargées
Modifier `scrape_jinka.py` ligne 1271:
```python
# Actuel: limite à 4 photos
if len(valid_photos) >= 4:
    break

# Modifier pour télécharger jusqu'à 8 photos
if len(valid_photos) >= 8:
    break
```

### Solution 3: Utiliser le fallback vers les URLs distantes
Le code dans `get_all_apartment_photos()` utilise déjà un fallback vers les URLs distantes si aucune photo locale n'est trouvée. Vérifier que ce fallback fonctionne correctement.

### Solution 4: Vérifier les chemins dans le HTML
S'assurer que les chemins relatifs sont corrects par rapport à l'emplacement du fichier HTML.

## 📋 Checklist de vérification

- [ ] Régénérer le HTML: `python3 generate_fitscore_style_html.py`
- [ ] Vérifier que le HTML est ouvert depuis `output/`
- [ ] Vérifier les photos dans `data/photos/{id}/`
- [ ] Vérifier les logs de téléchargement pour erreurs
- [ ] Tester le téléchargement pour un appartement spécifique

## 🔧 Script de diagnostic

Un script de diagnostic complet est disponible:
```bash
python3 diagnostic_photos.py
```

Ce script vérifie:
- Photos dans JSON vs photos téléchargées
- Détection par `get_all_apartment_photos()`
- Existence des fichiers
- Chemins dans le HTML (`output/homepage.html` uniquement)

## 📝 Notes

- Le système limite volontairement à 4 photos pour économiser l'espace disque
- Les photos non téléchargées sont toujours disponibles via les URLs distantes dans le JSON
- Le fallback vers les URLs distantes devrait fonctionner si les photos locales ne sont pas trouvées

