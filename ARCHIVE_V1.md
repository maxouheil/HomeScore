# 📦 Archive - HomeScore v1 (HTML Scraping)

## Statut : ARCHIVÉE

La version v1 utilisant le scraping HTML a été archivée au profit de la **v2 API** qui est plus rapide, stable et fiable.

## Fichiers Archivés

### Scripts Principaux
- `homescore.py` → Utiliser `homescore_v2.py` à la place
- `scrape_jinka.py` → Utiliser `scrape_jinka_api.py` à la place
- `run_daily_scrape.py` → À migrer vers v2

### Données
- `data/scraped_apartments.json` → Format HTML (ancien)
- `data/scores/` → Scores v1 (conservés)

## Nouvelle Structure v2

### Scripts
- `homescore_v2.py` - Orchestrateur principal v2
- `scrape_jinka_api.py` - Scraper API
- `scrape_with_api.py` - Script de scraping avec API
- `data_loader.py` - Chargeur unifié de données

### Données
- `data/scraped_apartments_api_*.json` - Données API
- `data/scraped_apartments_v2.json` - Format unifié v2
- `data/scores_v2/` - Scores v2

## Migration

Pour migrer vers v2 :
1. Utiliser `scrape_with_api.py` pour scraper
2. Utiliser `homescore_v2.py` pour scorer et générer HTML
3. Les données v1 restent disponibles mais ne sont plus utilisées

## Avantages v2

- ✅ **10x plus rapide** (5s vs 50s+)
- ✅ **Plus stable** (pas de dépendance HTML/CSS)
- ✅ **Données plus complètes** (API structurée)
- ✅ **Moins de ressources** (pas de navigateur)

---

**Date d'archivage** : 2025-11-14
**Version de remplacement** : HomeScore v2 (API)




