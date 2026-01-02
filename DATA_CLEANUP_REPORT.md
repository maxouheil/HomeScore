# 🧹 RAPPORT DE NETTOYAGE DES DONNÉES

**Date:** 2026-01-03  
**Objectif:** Clarifier l'utilisation des données et éliminer les doublons/confusions

---

## 📊 ÉTAT ACTUEL DES DONNÉES

### ✅ Fichiers Principaux

| Fichier | Taille | Appartements | Statut | Utilisation |
|---------|--------|--------------|--------|-------------|
| `data/all_apartments.json` | 12.42 MB | 1463 | ✅ **PRINCIPAL** | **Backend API** (`backend/api/apartments.py`) |
| `data/scraped_apartments.json` | 7.31 MB | 1463 | ⚠️ Doublon | Scripts de scoring/analyse (ancien format) |
| `data/paris_apartments.json` | 9.15 MB | 1493 | ❓ Snapshot | Snapshot spécifique Paris (109 appartements uniques) |
| `data/jinka_apartments.json` | 0.49 MB | 47 | ✅ Spécifique | Données Jinka (tous dans all_apartments.json) |
| `data/scores/all_apartments_scores.json` | 13 MB | ? | ❓ Ancien format | Utilisé par plusieurs scripts de scoring |

### 📡 Fichiers API

| Fichier | Taille | Appartements | Statut |
|---------|--------|--------------|--------|
| `data/scraped_apartments_api_20251114_163718.json` | 0.22 MB | 42 | 📦 Archivé |

### 📁 Fichiers Individuels (Ancien Format)

| Répertoire | Fichiers | Statut |
|------------|----------|--------|
| `data/appartements/*.json` | 57 fichiers | 📦 **ARCHIVÉ** |

---

## 🔍 ANALYSE DES DOUBLONS

### Comparaison avec `all_apartments.json` (1463 appartements)

#### `scraped_apartments.json`
- ✅ **100% identique** (1463/1463)
- ⚠️ **DOUBLON COMPLET** - peut être supprimé si `all_apartments.json` est à jour

#### `paris_apartments.json`
- 📊 **1384 appartements en commun** (94.6%)
- ➕ **109 appartements uniques** dans paris_apartments.json
- ➖ **79 appartements manquants** par rapport à all_apartments.json
- ❓ **Snapshot spécifique** - peut contenir des données historiques

#### `jinka_apartments.json`
- ✅ **47 appartements** (tous présents dans all_apartments.json)
- ✅ **Sous-ensemble** de all_apartments.json
- 💡 Peut être conservé comme référence spécifique Jinka

---

## 🎯 RECOMMANDATIONS

### ✅ À CONSERVER

1. **`data/all_apartments.json`** ⭐ **SOURCE DE VÉRITÉ**
   - Utilisé par le backend (`backend/api/apartments.py`)
   - Contient 1463 appartements complets
   - **C'est le fichier principal à utiliser**

2. **`data/jinka_apartments.json`**
   - Données spécifiques Jinka (47 appartements)
   - Peut servir de référence pour les appartements Jinka
   - Tous présents dans all_apartments.json

### ❓ À VÉRIFIER/ARCHIVER

1. **`data/scraped_apartments.json`**
   - **DOUBLON COMPLET** avec all_apartments.json
   - Utilisé par certains scripts de scoring/analyse
   - **Action:** Migrer les scripts vers `all_apartments.json`, puis archiver

2. **`data/paris_apartments.json`**
   - Snapshot spécifique Paris (1493 appartements)
   - Contient 109 appartements non présents dans all_apartments.json
   - **Action:** Vérifier si ces 109 appartements doivent être intégrés dans all_apartments.json, puis archiver

### 🗑️ À SUPPRIMER/ARCHIVER

1. **`data/appartements/*.json`** (57 fichiers)
   - ✅ **DÉJÀ ARCHIVÉ** dans `data/archive/data_cleanup/appartements_individual_*`
   - Ancien format (fichiers individuels)
   - Peut être supprimé si all_apartments.json est à jour

2. **`data/scraped_apartments_api_*.json`**
   - Anciens fichiers API (1 fichier restant)
   - Peut être archivé si les données sont dans all_apartments.json

---

## 📋 PLAN D'ACTION

### Phase 1: Migration des Scripts ✅

**Objectif:** Faire migrer tous les scripts vers `all_apartments.json`

#### Scripts à migrer:
- `score_all_with_calme.py` → Utilise `scraped_apartments.json`
- `score_all_with_calme_optimized.py` → Utilise `scraped_apartments.json`
- `check_all_apartments_data.py` → Utilise `scraped_apartments.json`
- `generate_scorecard_html.py` → Utilise `scraped_apartments.json`
- Autres scripts de scoring/analyse

**Action:** Modifier ces scripts pour utiliser `data/all_apartments.json` au lieu de `scraped_apartments.json`

### Phase 2: Intégration des Données Manquantes ⚠️

**Objectif:** Vérifier et intégrer les 109 appartements uniques de `paris_apartments.json`

**Action:** 
1. Identifier les 109 appartements uniques dans `paris_apartments.json`
2. Vérifier s'ils doivent être ajoutés à `all_apartments.json`
3. Si oui, les intégrer
4. Si non, archiver `paris_apartments.json`

### Phase 3: Nettoyage Final 🧹

**Objectif:** Supprimer/archiver les fichiers obsolètes

**Actions:**
1. ✅ Archiver `data/appartements/*.json` (DÉJÀ FAIT)
2. Archiver `data/scraped_apartments.json` (après migration des scripts)
3. Archiver `data/paris_apartments.json` (après intégration des données)
4. Archiver `data/scraped_apartments_api_*.json` (anciens fichiers API)

---

## 🏗️ STRUCTURE RECOMMANDÉE

### Fichiers Actifs

```
data/
├── all_apartments.json          ⭐ SOURCE DE VÉRITÉ (backend + scripts)
├── jinka_apartments.json        ✅ Référence spécifique Jinka
└── scores/
    └── all_apartments_scores.json  (si utilisé séparément)
```

### Fichiers Archivés

```
data/archive/
├── data_cleanup/
│   ├── appartements_individual_*/  ✅ Déjà archivé
│   ├── scraped_apartments.json     (après migration)
│   ├── paris_apartments.json       (après intégration)
│   └── scraped_apartments_api_*.json
```

---

## 🔧 UTILISATION RECOMMANDÉE

### Pour le Backend
```python
# backend/api/apartments.py
apartments_file = 'data/all_apartments.json'  # ✅ DÉJÀ UTILISÉ
```

### Pour les Scripts
```python
# TOUS LES SCRIPTS DEVRAIENT UTILISER:
from backend.api.apartments import load_apartments_data

apartments = load_apartments_data(enrich=False)  # ✅ Utilise all_apartments.json
```

### Alternative (si besoin de charger directement)
```python
import json
from pathlib import Path

apartments_file = Path('data/all_apartments.json')
with open(apartments_file, 'r', encoding='utf-8') as f:
    apartments = json.load(f)
```

---

## 📊 STATISTIQUES FINALES

- **Fichiers principaux:** 4
- **Fichiers API:** 1 (à archiver)
- **Fichiers individuels:** 57 (✅ archivés)
- **Doublons identifiés:** 1463 appartements
- **Source de vérité:** `data/all_apartments.json` (1463 appartements)

---

## ✅ ACTIONS EFFECTUÉES

1. ✅ Archivage de 57 fichiers individuels dans `data/appartements/`
2. ✅ Analyse complète des doublons
3. ✅ Identification des fichiers utilisés/non utilisés
4. ✅ Création du rapport de nettoyage

## 🔜 PROCHAINES ÉTAPES

1. Migrer les scripts vers `all_apartments.json`
2. Intégrer les 109 appartements uniques de `paris_apartments.json` (si nécessaire)
3. Archiver les fichiers obsolètes
4. Mettre à jour la documentation

---

**Scripts créés:**
- `analyze_data_cleanup.py` - Analyse des données
- `cleanup_data.py` - Nettoyage et archivage

**Rapports générés:**
- `data/cleanup_report_*.json` - Rapport détaillé
