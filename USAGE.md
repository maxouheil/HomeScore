# 📖 Guide d'Utilisation - HomeScore Nouvelle Structure

## 🚀 Démarrage Rapide

### Mode Développement (Nouveau - Recommandé)

Pour une expérience de développement moderne avec hot reload :

```bash
# Lance le backend + frontend avec hot reload
python dev.py
```

**Fonctionnalités :**
- ✅ Interface React moderne avec hot reload
- ✅ Mises à jour automatiques via WebSocket
- ✅ Tri automatique par score décroissant
- ✅ Formatage intelligent des données

### Workflow Complet (Traditionnel)

```bash
# 1. Scraper les appartements et analyser avec IA
python scrape.py <URL_ALERTE_JINKA>

# 2. Calculer les scores et générer le HTML
python homescore.py
```

C'est tout ! Le fichier `output/homepage.html` sera généré automatiquement.

## 📋 Étapes Détaillées

### Étape 1: Scraping + Analyse IA

```bash
python scrape.py https://www.jinka.fr/alert/...
```

**Ce que fait cette commande :**
- Se connecte à Jinka
- Scrape les appartements de l'alerte
- Analyse les photos avec OpenAI Vision (style, cuisine, luminosité)
- Extrait l'exposition
- Sauvegarde dans `data/scraped_apartments.json`

**Durée :** ~2-3 minutes par appartement

### Étape 2: Scoring + Génération HTML

```bash
python homescore.py
```

**Ce que fait cette commande :**
- Charge `data/scraped_apartments.json`
- Calcule les scores avec règles simples (pas d'IA)
- Sauvegarde dans `data/scores.json`
- Génère `output/homepage.html`

**Durée :** ~5-10 secondes

## 🔧 Utilisation Avancée

### Scraping Seulement

Si vous voulez juste scraper sans analyser :

```bash
python scrape.py <URL_ALERTE>
# Les données seront dans data/scraped_apartments.json
```

### Scoring Seulement

Si vous avez déjà scrapé et voulez juste recalculer les scores :

```python
from scoring import score_all_apartments, load_scraped_apartments
import json

# Charger les données scrapées
apartments = load_scraped_apartments()

# Calculer les scores
scores = score_all_apartments(apartments)

# Sauvegarder
with open('data/scores.json', 'w') as f:
    json.dump(scores, f, indent=2)
```

### Génération HTML Seulement

Si vous avez déjà les scores :

```bash
python generate_html.py
```

Ou en Python :

```python
from generate_html import generate_html, load_scored_apartments

# Charger les scores
apartments = load_scored_apartments()

# Générer HTML
html = generate_html(apartments)

# Sauvegarder
with open('output/homepage.html', 'w') as f:
    f.write(html)
```

## 📁 Structure des Fichiers

### Fichiers de Données

- **`data/scraped_apartments.json`** : Données scrapées + analyses IA
- **`data/scores.json`** : Scores calculés

### Fichiers Générés

- **`output/homepage.html`** : Rapport HTML unique

### Fichiers de Configuration

- **`scoring_config.json`** : Règles de scoring
- **`.env`** : Clés API (OpenAI, Jinka)

## 🎯 Personnalisation

### Modifier les Règles de Scoring

Éditez `scoring_config.json` :

```json
{
  "axes": {
    "prix": {
      "tiers": {
        "tier1": {
          "prix_m2_max": 9499  // Modifier ici (< 9500)
        }
      }
    }
  }
}
```

Puis relancez :
```bash
python homescore.py
```

### Modifier le Format d'Affichage

Éditez les fichiers dans `criteria/` :

- `criteria/localisation.py` → Format "Metro · Quartier"
- `criteria/prix.py` → Format "X / m² · Good/Moyen/Bad"
- `criteria/style.py` → Format "Style (X% confiance)"
- etc.

## 🔍 Vérification

### Vérifier les Données Scrapées

```bash
python -c "import json; data = json.load(open('data/scraped_apartments.json')); print(f'{len(data)} appartements'); print(data[0].keys() if data else 'Vide')"
```

### Vérifier les Scores

```bash
python -c "import json; data = json.load(open('data/scores.json')); print(f'{len(data)} appartements'); print(f'Score moyen: {sum(a.get(\"score_total\", 0) for a in data) / len(data):.1f}' if data else 'Vide')"
```

### Vérifier le HTML

```bash
open output/homepage.html  # Sur macOS
# ou
xdg-open output/homepage.html  # Sur Linux
```

## 🐛 Dépannage

### Erreur : "Fichier data/scraped_apartments.json non trouvé"

**Solution :** Lancez d'abord le scraping :
```bash
python scrape.py <URL_ALERTE>
```

### Erreur : "OPENAI_API_KEY non définie"

**Solution :** Créez un fichier `.env` :
```env
OPENAI_API_KEY=votre_clé_ici
```

### Erreur : "Aucun appartement trouvé"

**Solution :** Vérifiez que `data/scraped_apartments.json` contient des données :
```bash
python -c "import json; print(len(json.load(open('data/scraped_apartments.json'))))"
```

### Les scores ne sont pas à jour

**Solution :** Recalculez les scores :
```bash
python homescore.py
```

## 📊 Exemples d'Utilisation

### Mise à Jour Quotidienne

```bash
# Script quotidien
#!/bin/bash
python scrape.py <URL_ALERTE> && python homescore.py
```

### Mise à Jour Incrémentale

Si vous avez déjà scrapé et voulez juste mettre à jour les scores :

```bash
python homescore.py
```

### Analyse d'un Appartement Spécifique

```python
from scoring import score_apartment, load_scoring_config
import json

# Charger un appartement
with open('data/scraped_apartments.json') as f:
    apartments = json.load(f)
    apartment = apartments[0]  # Premier appartement

# Scorer
config = load_scoring_config()
score = score_apartment(apartment, config)
print(f"Score: {score['score_total']}/100")
```

## 📞 Support

En cas de problème :
1. Vérifiez les logs dans la console
2. Vérifiez que les fichiers nécessaires existent
3. Consultez `MIGRATION.md` pour la migration
4. Consultez `STRUCTURE_PROJET.md` pour l'architecture

---

**Dernière mise à jour** : 2025-01-31

