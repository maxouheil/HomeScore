# Guide : Extraction des URLs depuis les emails Jinka

## Vue d'ensemble

Ce système permet d'extraire automatiquement **toutes** les URLs d'appartements depuis tes emails d'alerte Jinka, avec gestion de l'historique et déduplication.

## Avantages

✅ **Robuste** : Pas de problème de 403 ou de détection de bot  
✅ **Complet** : Récupère toutes les URLs des emails d'alerte  
✅ **Historique** : Garde une trace de toutes les URLs déjà extraites  
✅ **Déduplication** : Évite les doublons même entre différentes sources  
✅ **Automatisable** : Peut être lancé en cron job  

## Configuration initiale

### 1. Créer un App Password Gmail

1. Va sur https://myaccount.google.com/apppasswords
2. Sélectionne "Mail" et "Autre (nom personnalisé)"
3. Donne un nom (ex: "HomeScore")
4. Gmail génère un mot de passe de 16 caractères
5. **Copie ce mot de passe** (tu ne pourras plus le voir après)

### 2. Configurer le fichier .env

Ajoute ces lignes dans ton fichier `.env` :

```bash
JINKA_EMAIL=ton_email@gmail.com
EMAIL_PASSWORD=xxxx_xxxx_xxxx_xxxx  # Le App Password de 16 caractères (sans espaces)
```

**Important** : Utilise l'App Password, pas ton mot de passe Gmail normal !

## Utilisation

### Étape 1 : Extraire les URLs depuis les emails

```bash
python extract_all_urls_from_email.py
```

Ce script va :
- Se connecter à ta boîte email via IMAP
- Chercher les emails de Jinka des **90 derniers jours**
- Extraire toutes les URLs d'appartements
- Comparer avec l'historique pour éviter les doublons
- Sauvegarder dans `data/all_apartment_urls_from_email.json`
- Mettre à jour l'historique dans `data/apartment_urls_history.json`

**Résultat** :
- `data/all_apartment_urls_from_email.json` : Toutes les URLs (historique + nouvelles)
- `data/new_apartment_urls_from_email.json` : Seulement les nouvelles URLs
- `data/apartment_urls_history.json` : Historique complet avec métadonnées

### Étape 2 : Fusionner toutes les sources (optionnel)

Si tu as des URLs depuis différentes sources (emails, dashboard, etc.) :

```bash
python merge_all_urls.py
```

Ce script fusionne :
- URLs depuis emails (`all_apartment_urls_from_email.json`)
- URLs depuis dashboard page 1 (`apartment_urls_page1.json`)
- URLs existantes dans les scores (`all_apartments_scores.json`)

**Résultat** : `data/all_apartment_urls_merged.json` avec toutes les URLs dédupliquées

### Étape 3 : Scraper les appartements

```bash
python scrape_from_urls.py
```

Le script `scrape_from_urls.py` utilise automatiquement :
1. `all_apartment_urls_merged.json` (si disponible)
2. `all_apartment_urls_from_email.json` (sinon)
3. `apartment_urls_page1.json` (sinon)
4. `all_apartments_scores.json` (sinon)

Ou spécifier un fichier :
```bash
python -c "from scrape_from_urls import scrape_from_urls; import asyncio; asyncio.run(scrape_from_urls('data/all_apartment_urls_from_email.json'))"
```

## Fichiers générés

| Fichier | Description |
|---------|-------------|
| `data/all_apartment_urls_from_email.json` | Toutes les URLs extraites des emails |
| `data/new_apartment_urls_from_email.json` | Nouvelles URLs (pas dans l'historique) |
| `data/apartment_urls_history.json` | Historique complet avec métadonnées |
| `data/all_apartment_urls_merged.json` | Fusion de toutes les sources |
| `data/apartment_urls_page1.json` | URLs depuis dashboard page 1 |

## Workflow recommandé

### Première utilisation

1. Configure `.env` avec `JINKA_EMAIL` et `EMAIL_PASSWORD`
2. Lance `python extract_all_urls_from_email.py`
3. Vérifie les résultats dans `data/all_apartment_urls_from_email.json`
4. Lance `python merge_all_urls.py` pour fusionner avec d'autres sources
5. Lance `python scrape_from_urls.py` pour scraper les appartements

### Utilisation régulière

```bash
# 1. Extraire les nouvelles URLs depuis les emails
python extract_all_urls_from_email.py

# 2. Fusionner avec d'autres sources (si nécessaire)
python merge_all_urls.py

# 3. Scraper les nouveaux appartements
python scrape_from_urls.py
```

### Automatisation (cron job)

Ajoute dans ton crontab pour lancer automatiquement tous les jours :

```bash
# Tous les jours à 8h du matin
0 8 * * * cd /path/to/HomeScore && python extract_all_urls_from_email.py >> logs/email_extraction.log 2>&1
```

## Dépannage

### Erreur "IMAP4.error: LOGIN failed"
- Vérifie que tu utilises bien un **App Password**, pas ton mot de passe normal
- Active l'accès IMAP dans les paramètres Gmail

### Aucune URL trouvée
- Vérifie que tu as bien reçu des emails d'alerte Jinka
- Augmente `days_back` dans le script (par défaut 90 jours)
- Vérifie les filtres d'expéditeur dans le code

### Erreur "BeautifulSoup not found"
- Installe BeautifulSoup4 : `pip install beautifulsoup4`
- Ou le script fonctionnera sans, mais avec moins de précision

## Structure des données

### Format des fichiers JSON

```json
[
  "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=75507606&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
  "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=75578302&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
  ...
]
```

### Format de l'historique

```json
{
  "urls": [...],
  "last_extraction": "2024-10-29T20:00:00",
  "total_count": 150
}
```

## Avantages vs scraping web

| Aspect | Emails ✅ | Scraping web |
|--------|-----------|--------------|
| Robustesse | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Détection bot | ❌ Non | ✅ Oui (403) |
| Format stable | ✅ Oui | ❌ Change souvent |
| Complet | ✅ Toutes les URLs | ⚠️ Limité par pagination |
| Automatisation | ✅ Facile | ⚠️ Compliqué |






