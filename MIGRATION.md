# 🔄 Guide de Migration vers la Nouvelle Structure

## Vue d'ensemble

La nouvelle architecture simplifie le codebase en centralisant les données et en séparant clairement les responsabilités.

## Changements Principaux

### Ancienne Structure
- `data/scores/all_apartments_scores.json` → Scores
- `data/scraped_apartments.json` → Données scrapées
- Fusion manuelle nécessaire

### Nouvelle Structure
- `data/scores.json` → Scores + données fusionnées
- `data/scraped_apartments.json` → Données scrapées (inchangé)
- Fusion automatique dans `homescore.py`

## Étapes de Migration

### Option 1: Migration Automatique (Recommandée)

```bash
# Lancer le script de migration
python migrate_to_new_structure.py
```

Le script va :
1. Charger `data/scores/all_apartments_scores.json`
2. Charger `data/scraped_apartments.json`
3. Fusionner les données
4. Créer `data/scores.json` (nouveau format)

### Option 2: Migration Manuelle

Si vous préférez migrer manuellement :

```bash
# 1. S'assurer que scraped_apartments.json est à jour
# (déjà fait normalement)

# 2. Calculer les scores avec la nouvelle structure
python homescore.py
```

Cela va automatiquement :
- Charger `data/scraped_apartments.json`
- Calculer les scores avec `scoring.py`
- Sauvegarder dans `data/scores.json`
- Générer `output/homepage.html`

### Option 3: Re-scraping Complet

Si vous voulez repartir de zéro :

```bash
# 1. Scraper avec la nouvelle structure
python scrape.py <alert_url>

# 2. Calculer scores et générer HTML
python homescore.py
```

## Vérification Post-Migration

Après la migration, vérifiez :

```bash
# Vérifier que scores.json existe
ls -lh data/scores.json

# Vérifier le contenu
python -c "import json; data = json.load(open('data/scores.json')); print(f'{len(data)} appartements')"

# Générer le HTML
python homescore.py
```

## Structure des Fichiers Après Migration

```
data/
├── scraped_apartments.json    ← Données scrapées + analyses IA
└── scores.json                ← Scores calculés (nouveau format)
```

## Fichiers Conservés (Compatibilité)

Les anciens fichiers sont conservés pour compatibilité :
- `data/scores/all_apartments_scores.json` → Peut être supprimé après migration
- `data/scores/apartment_*_score.json` → Peuvent être supprimés après migration

## Migration des Scripts Existants

Si vous avez des scripts qui utilisent l'ancienne structure :

### Ancien Code
```python
# Charger depuis all_apartments_scores.json
with open('data/scores/all_apartments_scores.json') as f:
    scored = json.load(f)
```

### Nouveau Code
```python
# Charger depuis scores.json
with open('data/scores.json') as f:
    scored = json.load(f)
```

Ou utiliser `homescore.py` :
```python
from scoring import score_all_apartments
from generate_html import generate_html

# Charger et scorer
apartments = load_scraped_apartments()
scores = score_all_apartments(apartments)

# Générer HTML
html = generate_html(scores)
```

## Questions Fréquentes

### Q: Dois-je supprimer les anciens fichiers?
**R:** Non, vous pouvez les garder comme backup. Ils ne seront plus utilisés par la nouvelle architecture.

### Q: Mes anciens scores seront-ils perdus?
**R:** Non, ils seront migrés vers `data/scores.json`. Si vous préférez recalculer, utilisez `homescore.py`.

### Q: Puis-je utiliser les deux structures en parallèle?
**R:** Oui, mais ce n'est pas recommandé. La nouvelle structure est plus simple et efficace.

### Q: Que faire si la migration échoue?
**R:** Vérifiez que :
- `data/scores/all_apartments_scores.json` existe
- `data/scraped_apartments.json` existe
- Vous avez les permissions d'écriture dans `data/`

## Support

En cas de problème :
1. Vérifiez les logs du script de migration
2. Assurez-vous que tous les fichiers nécessaires existent
3. Essayez la migration manuelle (Option 2)

---

**Dernière mise à jour** : 2025-01-31

