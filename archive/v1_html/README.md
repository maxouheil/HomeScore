# HomeScore v1 - Version HTML Scraping

## 📋 Description

Cette version utilise le scraping HTML avec Playwright pour récupérer les données depuis Jinka.

## ⚠️ Statut

**ARCHIVÉE** - Remplacée par HomeScore v2 (API)

## 📁 Fichiers Principaux

- `homescore.py` - Orchestrateur principal v1
- `scrape_jinka.py` - Scraper HTML avec Playwright
- `data/scraped_apartments.json` - Données scrapées HTML
- `data/scores/` - Scores calculés v1

## 🔄 Migration vers v2

Pour utiliser la nouvelle version API :
```bash
python homescore_v2.py
```

## 📝 Notes

- La v1 reste disponible comme fallback
- Les données v1 sont conservées dans `data/`
- La v2 utilise `data/scores_v2/` pour éviter les conflits




