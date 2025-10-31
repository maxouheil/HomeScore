# 📁 Structure du Projet HomeScore - Clarification

## 🎯 **Fichiers HTML Générés**

### **Fichiers de Génération HTML Principaux :**

1. **`generate_scorecard_html.py`** ⭐ **PRINCIPAL (actuellement ouvert)**
   - **Fichier généré** : `output/scorecard_rapport.html`
   - **Style** : Design scorecard moderne avec grille responsive
   - **Fonctionnalités** :
     - Fusionne `data/scores/all_apartments_scores.json` + `data/scraped_apartments.json`
     - Intègre `style_analysis` depuis les données scrapées
     - Affiche photos depuis `data/photos/{id}/`
     - Nettoyage automatique des quartiers (supprime scores de probabilité)

2. **`generate_fitscore_style_html.py`**
   - **Fichier généré** : `output/scorecard_fitscore_style.html`
   - **Style** : Design inspiré de Fitscore avec police Blacklist
   - **Utilisation** : Alternative au design principal

3. **`generate_html_report.py`**
   - **Fichier généré** : `output/rapport_appartements.html`
   - **Style** : Rapport simplifié
   - **Utilisation** : Utilisé par `score_batch_apartments.py` et `run_daily_scrape.py`

### **Fichiers HTML Actuels :**
- `output/scorecard_rapport.html` ← **PRINCIPAL** (généré par `generate_scorecard_html.py`)
- `output/scorecard_fitscore_style.html` (généré par `generate_fitscore_style_html.py`)
- `output/scorecard_maquette.html` (maquette/test)
- `test_placeholder.html` (test)

---

## 💾 **Stockage des Données**

### **📊 Scores (scoring)**
- **Fichier principal** : `data/scores/all_apartments_scores.json`
  - Contient tous les scores détaillés par appartement
  - Structure : `[{id, score_total, scores_detaille, ...}, ...]`
- **Fichiers individuels** : `data/scores/apartment_{id}_score.json`
  - Scores détaillés par appartement

### **🏠 Données Scrapées**
- **Fichier principal** : `data/scraped_apartments.json`
  - Contient toutes les données scrapées depuis Jinka
  - Inclut : prix, surface, localisation, caractéristiques, photos URLs, **style_analysis**
- **Fichiers individuels** : `data/appartements/{id}.json`
  - Données complètes par appartement (18 appartements actuellement)

### **📸 Photos**
- **Répertoire** : `data/photos/{apartment_id}/`
  - Format : `photo_1_{timestamp}.jpg`, `photo_2_{timestamp}.jpg`, etc.
  - Max 4 photos par appartement généralement
- **Métadonnées** : `data/photos_metadata/{id}.json`
  - Informations sur les photos téléchargées

### **🎨 Analyse de Style**
- **Fichier** : `data/apartment_style_analysis.json`
- **Intégration** : Fusionné dans `scraped_apartments.json` sous la clé `style_analysis`
- **Utilisation** : Utilisé par `generate_scorecard_html.py` pour afficher le style

### **🗺️ Screenshots de Cartes**
- **Répertoire** : `data/screenshots/`
  - 153 fichiers PNG de screenshots de cartes Google Maps
  - Utilisés pour détecter les quartiers

---

## 📝 **Fichiers Markdown de Documentation**

### **Markdown Principal à Mettre à Jour :**
- **`RESUME_SCORING_AFFINE.md`** ⭐ **PRINCIPAL** (actuellement ouvert)
  - Documente le système de scoring affiné
  - Critères de scoring (8 axes)
  - Système de tiers (GOOD/MOYEN/BAD)
  - À mettre à jour avec toutes les évolutions récentes

### **Autres Markdowns de Documentation :**
- `RESUME_DETECTION_STYLE.md` - Documentation sur la détection de style
- `CHANGELOG_EXPOSITION.md` - Changelog de la logique d'exposition
- `CHANGELOG.md` - Changelog général du projet
- `README.md` - Documentation principale du projet
- `DESIGN_SCORECARD.md` - Design du scorecard

### **Markdowns de Diagnostic :**
- `DIAGNOSTIC_EXPOSITION.md`
- `DIAGNOSTIC_CUISINE_OUVERTE.md`
- `FALLBACK_CUISINE_OUVERTE.md`
- `RESULTATS_FALLBACK_CUISINE.md`

---

## 🔄 **Flux de Données**

```
1. SCRAPING
   scrape_jinka.py
   ↓
   data/scraped_apartments.json (avec style_analysis)

2. SCORING
   score_batch_simple.py
   ↓
   data/scores/all_apartments_scores.json

3. GÉNÉRATION HTML
   generate_scorecard_html.py
   ├─ Charge: data/scores/all_apartments_scores.json
   ├─ Fusionne: data/scraped_apartments.json (pour style_analysis)
   ├─ Utilise: data/photos/{id}/ (pour afficher photos)
   └─ Génère: output/scorecard_rapport.html
```

---

## ⚠️ **Fichiers à NE PAS Modifier Accidentellement**

### **Backups de données :**
- `data/scraped_apartments.json.backup_*` (backups automatiques)
- Ne pas supprimer ou modifier ces fichiers

### **Fichiers de configuration :**
- `scoring_config.json` - Configuration du scoring
- `scoring_prompt.txt` - Prompt OpenAI pour le scoring
- `config.json` - Configuration générale

### **Fichiers de test/old :**
- `generate_scorecard_html_old.py` - Version ancienne (backup)
- `generate_scorecard_html_new.py` - Version test (à vérifier)

---

## 📋 **Résumé - Sur Quoi Travailler**

### ✅ **Fichier HTML Principal :**
- **Script** : `generate_scorecard_html.py` (actuellement ouvert)
- **Output** : `output/scorecard_rapport.html`
- **Données sources** :
  - `data/scores/all_apartments_scores.json` (scores)
  - `data/scraped_apartments.json` (données scrapées + style_analysis)
  - `data/photos/{id}/` (photos)

### ✅ **Markdown à Mettre à Jour :**
- **`RESUME_SCORING_AFFINE.md`** ⭐ (actuellement ouvert)
- Mettre à jour avec toutes les évolutions récentes :
  - Améliorations exposition (bonus étage >=4, fallback photos)
  - Améliorations style (détection via photos + texte)
  - Améliorations HTML (fusion données, nettoyage quartiers)
  - Nouveaux critères de scoring

### ✅ **Données Principales :**
- **Scores** : `data/scores/all_apartments_scores.json`
- **Scraped** : `data/scraped_apartments.json`
- **Photos** : `data/photos/{id}/`

---

**Dernière mise à jour** : 2025-01-31

