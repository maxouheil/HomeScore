# 📋 Plan de Migration : HTML Scraping → API

## 🎯 Objectif

Migrer progressivement le système pour utiliser les données de l'API Jinka au lieu du scraping HTML, améliorant ainsi la performance, la stabilité et la qualité des données.

---

## 📊 État Actuel

### Données HTML (anciennes)
- **Source** : `scrape_jinka.py` (scraping HTML avec Playwright)
- **Format** : `data/scraped_apartments.json` ou `data/appartements/*.json`
- **Problèmes** :
  - Lent (plusieurs minutes pour 42 appartements)
  - Fragile (dépendant du HTML/CSS)
  - Consomme beaucoup de ressources (navigateur)
  - Données parfois incomplètes

### Données API (nouvelles)
- **Source** : `scrape_jinka_api.py` (API Jinka)
- **Format** : `data/scraped_apartments_api_*.json`
- **Avantages** :
  - Rapide (~5 secondes pour 42 appartements)
  - Stable (données structurées)
  - Moins de ressources
  - Données complètes et fiables

---

## 🔄 Plan de Migration en 4 Phases

### Phase 1 : Compatibilité et Unification ✅ (Priorité Haute)

**Objectif** : S'assurer que les données API sont compatibles avec le format existant

**Actions** :
- [x] ✅ Créer `api_data_adapter.py` pour convertir API → format scraping
- [x] ✅ Tester la compatibilité avec le scoring existant
- [ ] Créer une fonction `load_apartments()` unifiée qui charge depuis API ou HTML
- [ ] Créer un script de migration `migrate_to_api_format.py` pour convertir les anciennes données

**Fichiers à créer/modifier** :
- `data_loader.py` (nouveau) - Chargeur unifié de données
- `migrate_to_api_format.py` (nouveau) - Migration des anciennes données

**Durée estimée** : 1-2 heures

---

### Phase 2 : Migration du Scraping Principal ✅ (Priorité Haute)

**Objectif** : Remplacer le scraping HTML par l'API dans les scripts principaux

**Actions** :
- [x] ✅ Créer `scrape_jinka_api.py` avec interface compatible
- [x] ✅ Tester avec l'alerte RP (42 appartements)
- [ ] Modifier `run_daily_scrape.py` pour utiliser l'API par défaut
- [ ] Modifier `scrape.py` pour utiliser l'API
- [ ] Modifier `batch_scraper.py` pour utiliser l'API
- [ ] Conserver le scraping HTML comme fallback optionnel

**Fichiers à modifier** :
- `run_daily_scrape.py` - Utiliser `JinkaAPIScraper` au lieu de `JinkaScraper`
- `scrape.py` - Ajouter option `--use-api` (défaut: True)
- `batch_scraper.py` - Utiliser l'API par défaut

**Durée estimée** : 2-3 heures

---

### Phase 3 : Migration des Scripts de Traitement (Priorité Moyenne)

**Objectif** : Adapter les scripts qui consomment les données pour utiliser le nouveau format

**Scripts à migrer** :
- [ ] `scoring.py` - Vérifier compatibilité avec données API
- [ ] `score_appartement.py` - Adapter si nécessaire
- [ ] `generate_html_report.py` - Utiliser nouvelles données
- [ ] `generate_scorecard_html.py` - Adapter le format
- [ ] `analyze_apartment_style.py` - Utiliser photos API
- [ ] `analyze_photos_unified.py` - Adapter pour photos API
- [ ] `extract_exposition.py` - Vérifier compatibilité

**Fichiers à modifier** :
- Tous les scripts qui chargent `scraped_apartments.json`
- Utiliser `data_loader.py` unifié

**Durée estimée** : 3-4 heures

---

### Phase 4 : Optimisation et Nettoyage (Priorité Basse)

**Objectif** : Nettoyer le code et optimiser l'utilisation de l'API

**Actions** :
- [ ] Supprimer le code HTML scraping non utilisé (garder comme fallback)
- [ ] Optimiser le cache API
- [ ] Améliorer la gestion d'erreurs API
- [ ] Documenter la nouvelle architecture
- [ ] Créer des tests de régression

**Durée estimée** : 2-3 heures

---

## 🛠️ Implémentation Détaillée

### Étape 1 : Créer le chargeur de données unifié

**Fichier** : `data_loader.py`

```python
"""
Chargeur unifié de données d'appartements
Supporte à la fois le format API et HTML
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional

def load_apartments(prefer_api: bool = True) -> List[Dict]:
    """
    Charge les appartements depuis API ou HTML
    
    Args:
        prefer_api: Préférer les données API si disponibles
    
    Returns:
        Liste des appartements
    """
    # Chercher les fichiers API récents
    if prefer_api:
        api_files = sorted(
            Path('data').glob('scraped_apartments_api_*.json'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        if api_files:
            with open(api_files[0], 'r', encoding='utf-8') as f:
                return json.load(f)
    
    # Fallback sur HTML
    html_file = Path('data/scraped_apartments.json')
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return []
```

### Étape 2 : Modifier `run_daily_scrape.py`

**Changements** :
```python
# Avant
from scrape_jinka import JinkaScraper
scraper = JinkaScraper()

# Après
from scrape_jinka_api import JinkaAPIScraper
scraper = JinkaAPIScraper()  # Plus rapide et stable
```

### Étape 3 : Créer un script de migration

**Fichier** : `migrate_to_api_format.py`

```python
"""
Migre les anciennes données HTML vers le format API
"""

import json
from pathlib import Path
from api_data_adapter import adapt_api_to_scraped_format

def migrate_old_data():
    """Convertit les anciennes données si nécessaire"""
    # Logique de migration si besoin
    pass
```

---

## 📝 Checklist de Migration

### Phase 1 : Compatibilité
- [ ] Créer `data_loader.py`
- [ ] Tester compatibilité scoring avec données API
- [ ] Créer script de migration

### Phase 2 : Scraping Principal
- [ ] Modifier `run_daily_scrape.py`
- [ ] Modifier `scrape.py`
- [ ] Modifier `batch_scraper.py`
- [ ] Tester le workflow complet

### Phase 3 : Scripts de Traitement
- [ ] Adapter `scoring.py`
- [ ] Adapter `generate_html_report.py`
- [ ] Adapter scripts d'analyse
- [ ] Tester tous les scripts

### Phase 4 : Nettoyage
- [ ] Supprimer code obsolète
- [ ] Documenter changements
- [ ] Créer tests

---

## ⚠️ Points d'Attention

### Compatibilité
- Les données API sont déjà compatibles grâce à `api_data_adapter.py`
- Tous les champs nécessaires sont présents
- Format identique au scraping HTML

### Fallback
- Garder le scraping HTML comme option de secours
- Ajouter un flag `--use-html` pour forcer HTML si besoin
- Gérer les erreurs API gracieusement

### Performance
- L'API est 10x plus rapide
- Réduire les délais dans les scripts batch
- Optimiser le cache API

---

## 🎯 Résultats Attendus

Après migration complète :
- ✅ **Performance** : 10x plus rapide (5s vs 50s+)
- ✅ **Stabilité** : Moins de breaking changes
- ✅ **Qualité** : Données plus complètes et fiables
- ✅ **Maintenance** : Code plus simple et maintenable

---

## 📅 Timeline Suggérée

- **Semaine 1** : Phase 1 + Phase 2 (compatibilité + scraping principal)
- **Semaine 2** : Phase 3 (scripts de traitement)
- **Semaine 3** : Phase 4 (optimisation et nettoyage)

**Total estimé** : 8-12 heures de travail

---

## 🚀 Démarrage Rapide

Pour commencer la migration immédiatement :

```bash
# 1. Tester le scraper API
python scrape_with_api.py

# 2. Vérifier les données
python show_apartment_data.py

# 3. Tester le scoring avec les nouvelles données
# (à adapter selon votre workflow)
```

---

**Dernière mise à jour** : 2025-11-14
**Statut** : Phase 1 et 2 complétées ✅




