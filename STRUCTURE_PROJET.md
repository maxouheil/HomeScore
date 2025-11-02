# 📁 Structure du Projet HomeScore - Architecture Simplifiée

## 🎯 Architecture Minimale

**Principe fondamental**: Architecture simplifiée avec séparation claire des responsabilités.

### Fichiers Python Principaux

1. **`homescore.py`** ⭐ **ORCHESTRATEUR CENTRAL**
   - Point d'entrée principal
   - Charge `data/scraped_apartments.json`
   - Calcule les scores via `scoring.py`
   - Génère HTML via `generate_html.py`
   - Sauvegarde dans `data/scores.json`

2. **`scrape.py`** ⭐ **SCRAPING + ANALYSE IA**
   - Scraping depuis Jinka (utilise `scrape_jinka.py`)
   - Analyse IA des images (utilise `analyze_apartment_style.py`)
   - Sauvegarde dans `data/scraped_apartments.json`

3. **`scoring.py`** ⭐ **CALCUL DES SCORES**
   - Calcul depuis règles simples (pas d'IA)
   - Utilise `scoring_config.json` pour les règles
   - Génère `data/scores.json`

4. **`generate_html.py`** ⭐ **GÉNÉRATION HTML**
   - UN SEUL générateur HTML
   - Utilise les modules `criteria/*.py` pour le formatage
   - Génère `output/homepage.html`

### Module `criteria/` - Formatage par Critère

Un fichier par critère pour le formatage de l'affichage :

- **`criteria/localisation.py`**: Formatage "Metro · Quartier"
- **`criteria/prix.py`**: Formatage "X / m² · Good/Moyen/Bad"
- **`criteria/style.py`**: Formatage "Style (X% confiance) + indices"
- **`criteria/exposition.py`**: Formatage "Lumineux/Moyen/Sombre (X% confiance) + indices"
- **`criteria/cuisine.py`**: Formatage "Ouverte/Semi/Fermée (X% confiance) + indices"
- **`criteria/baignoire.py`**: Formatage "Oui/Non (X% confiance) + indices"

## 💾 Sources de Données Uniques

### **Données Scrapées** : `data/scraped_apartments.json`
- **Contenu**: Données scrapées + analyses IA (style, cuisine, luminosité, exposition)
- **Généré par**: `scrape.py`
- **Structure**: List de dicts avec toutes les données d'appartement

### **Scores** : `data/scores.json`
- **Contenu**: Scores calculés depuis règles simples
- **Généré par**: `scoring.py`
- **Structure**: List de dicts avec scores détaillés par critère

### **HTML Généré** : `output/homepage.html`
- **Contenu**: Rapport HTML unique avec tous les appartements
- **Généré par**: `generate_html.py`
- **Format**: HTML avec CSS intégré, carousel pour photos

## 🔄 Flux de Données

```
1. SCRAPING + ANALYSE IA
   scrape.py
   ├─ scrape_jinka.py → scraping depuis Jinka
   ├─ analyze_apartment_style.py → analyse IA images (style, cuisine, luminosité)
   └─ extract_exposition.py → analyse exposition
   ↓
   data/scraped_apartments.json (source unique)

2. CALCUL DES SCORES
   scoring.py
   ├─ Charge scoring_config.json (règles)
   ├─ Calcule depuis données structurées (pas d'IA)
   └─ Génère scores détaillés par critère
   ↓
   data/scores.json (source unique)

3. GÉNÉRATION HTML
   generate_html.py
   ├─ Charge data/scores.json
   ├─ Utilise criteria/*.py pour formatage
   └─ Génère output/homepage.html
```

## 📋 Traçabilité par Critère

### 1. LOCALISATION
- **Scrap**: `scrape_jinka.py` → `localisation`, `map_info`, `transports`
- **Calcul**: `scoring.py` → règles depuis `scoring_config.json`
- **Formatage**: `criteria/localisation.py` → "Metro · Quartier"

### 2. PRIX
- **Scrap**: `scrape_jinka.py` → `prix`, `prix_m2`, `surface`
- **Calcul**: `scoring.py` → seuils prix/m² depuis config
- **Formatage**: `criteria/prix.py` → "X / m² · Good/Moyen/Bad"

### 3. STYLE
- **Scrap**: `scrape.py` → appelle `analyze_apartment_style.py` → `style_analysis.style`
- **IA Images**: Analyse 3 photos avec OpenAI Vision
- **Calcul**: `scoring.py` → depuis `style_analysis.style.type`
- **Formatage**: `criteria/style.py` → "Style (X% confiance) + indices"

### 4. EXPOSITION
- **Scrap**: `scrape.py` → `analyze_apartment_style.py` → `style_analysis.luminosite`
- **IA Images**: Analyse photos avec OpenAI Vision
- **Calcul**: `scoring.py` → depuis `style_analysis.luminosite` + `exposition`
- **Formatage**: `criteria/exposition.py` → "Lumineux (X% confiance) + indices"

### 5. CUISINE OUVERTE
- **Scrap**: `scrape.py` → `analyze_apartment_style.py` → `style_analysis.cuisine`
- **IA Images**: Analyse photos avec OpenAI Vision
- **Calcul**: `scoring.py` → depuis `style_analysis.cuisine.ouverte`
- **Formatage**: `criteria/cuisine.py` → "Ouverte/Semi/Fermée (X% confiance) + indices"

### 6. BAIGNOIRE
- **Scrap**: Pas de scrap direct
- **IA Images**: `extract_baignoire.py` → appelé à la volée (texte + images si nécessaire)
- **Calcul**: Pas de scoring dédié (score calculé dans extract_baignoire si nécessaire)
- **Formatage**: `criteria/baignoire.py` → "Oui/Non (X% confiance) + indices"

## 🎨 Format d'Affichage

Chaque critère affiche :
- **Valeur principale**: Formatée selon le type de critère
- **Confiance**: Pourcentage (quand disponible depuis analyse IA)
- **Indices**: Détails supplémentaires (quand disponibles)

Exemples :
- **LOCALISATION**: "Metro Ménilmontant · Belleville"
- **PRIX**: "11,500 / m² · Moyen"
- **STYLE**: "Haussmannien (85% confiance)" + "Indices: Moulures · cheminée · parquet"
- **EXPOSITION**: "Lumineux (90% confiance)" + "3e étage · pas de vis à vis"
- **CUISINE OUVERTE**: "Ouverte (95% confiance)" + "Analyse photo : Cuisine ouverte détectée"
- **BAIGNOIRE**: "Oui (80% confiance)" + "Analyse photo : Baignoire détectée"

## 📁 Fichiers Supprimés (Nettoyage)

### Anciens Générateurs HTML
- ❌ `generate_scorecard_html_old.py` (supprimé)
- ❌ `generate_scorecard_html_new.py` (supprimé)
- ❌ `generate_fitscore_style_html.py` (supprimé)

### Fichiers de Test/Backup
- ❌ `data/scraped_3_apartments.json` (supprimé)
- ❌ `data/batch_scraped_apartments.json` (supprimé)
- ✅ `data/scraped_apartments.json.backup_*` (déplacés dans `data/backups/`)

## 🔧 Fichiers Utilitaires (Conservés)

- **`scrape_jinka.py`**: Scraper Jinka (utilisé par `scrape.py`)
- **`analyze_apartment_style.py`**: Analyse IA images (utilisé par `scrape.py`)
- **`extract_baignoire.py`**: Détection baignoire (utilisé par `criteria/baignoire.py`)
- **`extract_exposition.py`**: Extraction exposition (utilisé par `scrape_jinka.py`)

## 🚀 Utilisation

### Workflow Complet
```bash
# 1. Scraper et analyser avec IA
python scrape.py <alert_url>

# 2. Calculer scores et générer HTML
python homescore.py
```

### Étapes Individuelles
```bash
# Scraping uniquement
python scrape.py <alert_url>

# Scoring uniquement (si données déjà scrapées)
python -c "from scoring import score_all_apartments, load_scraped_apartments; import json; apartments = load_scraped_apartments(); scores = score_all_apartments(apartments); json.dump(scores, open('data/scores.json', 'w'), indent=2)"

# Génération HTML uniquement (si scores déjà calculés)
python generate_html.py
```

## 📝 Notes Importantes

### IA Utilisée UNIQUEMENT pour :
- Analyse d'images (OpenAI Vision) → détecte indices + confiance
- Style: "haussmannien", "70s", "moderne" + indices
- Cuisine: ouverte/semi/fermée + indices
- Luminosité: excellente/bonne/moyenne + indices
- Baignoire: oui/non + indices (si nécessaire)

### Scoring Final (PAS d'IA) :
- Règles simples depuis `scoring_config.json`
- Calcul depuis données structurées
- Pas de prompt OpenAI pour scoring final

---

**Dernière mise à jour** : 2025-01-31 (Architecture simplifiée)
