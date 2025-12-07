<!-- 2773efca-a8ac-493b-863f-a6e9d039d644 7280f78e-7224-4202-b74f-ddf22af5c977 -->
# HomeScore - Scoring d'appartements Jinka

## Architecture (inspirée de CandidaturesPlum)

### 1. Configuration et structure

- Créer `scoring_config.json` avec les 8 critères de notation :
  - Localisation (20 pts) : quartiers préférés, proximité transports
  - Style haussmannien (20 pts) : moulures, cheminée, parquet, hauteur sous plafond
  - Prix (20 pts) : budget cible avec fourchette acceptable
  - Ensoleillement (10 pts) : exposition (Sud > Est/Ouest > Nord), luminosité
  - Cuisine ouverte (10 pts) : ouverte/fermée/semi-ouverte
  - Étage (10 pts) : préférence étage (éviter RDC/dernier)
  - Vue (5 pts) : dégagée, sur cour, rue calme
  - Surface (5 pts) : m² min/max idéal

### 2. Analyse des méthodes de récupération des données

Avant le scraping, explorer les options pour récupérer les données efficacement :

**Option A - API Backend (MEILLEURE si disponible)** :
- Explorer les requêtes réseau (DevTools > Network > XHR/Fetch)
- Chercher des endpoints API internes (ex: `/api/alerts`, `/api/properties`)
- Avantages : Plus rapide, plus stable, données structurées JSON
- Tester avec un script d'exploration `explore_jinka_api.py`

**Option B - Scraping HTML (FALLBACK)** :
- Si pas d'API accessible, scraper le HTML avec Playwright
- Avantages : Fonctionne toujours, accès à toutes les données visibles
- Inconvénients : Plus lent, fragile aux changements CSS

**Décision** : Tester d'abord l'API backend, puis fallback sur scraping HTML si nécessaire

### 3. Scraping Jinka

Créer `scrape_jinka.py` avec Playwright :

- **Authentification Google** : Connexion automatique via `souheil.medaghri@gmail.com` (stocké dans `.env`)
- Navigation sur Jinka avec votre alerte active
- **Structure détectée** :
  - Grille d'annonces avec cartes cliquables
  - Sélecteur cartes : `a.sc-bdVaJa.csp.sc-dVhcbM.gnRFeF`
  - URL format : `/alert_result?token=...&ad=...` (extraire l'ID annonce)
  - URL type : `https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1`
- **Extraction par annonce** :
  - Cliquer sur chaque carte pour accéder aux détails
  - **Prix** : Sélecteur `.hmmXKG` (ex: "775 000 €")
  - **Prix/m²** : Sous le prix principal (ex: "11071 €/m²")
  - **Localisation** : "Paris 19e (75019)"
  - **Surface** : "70 m²"
  - **Pièces** : "3 pièces - 2 chambres"
  - **Date** : "Appartement, le 29 oct. à 16:28, par une agence"
  - **Transports** : Stations proches (Pyrénées 11, Jourdain 11, etc.)
  - **Localisation précise** : Carte interactive avec quartiers
    - Quartiers : "Buttes Chaumont", "Place des Fêtes", "Pyrénées", "Belleville"
    - Rues : "Avenue des Marnes", "Boulevard de la Villette", "Rue de Belleville", etc.
    - Proximité : "à seulement 350 m des Buttes-Chaumont"
    - Sélecteur carte : `.leaflet-container` (Leaflet/OpenStreetMap)
  - **Description** : Sélecteur `.fz-16.sc-bxivhb.fcnykg` (bloc descriptif détaillé)
    - Surface : "69,96 m²" (détection automatique)
    - Étage : "4e étage" (détection automatique)
    - Cuisine : "cuisine américaine ouverte" (détection automatique)
    - Chambres : "deux chambres, dont l'une de plus de 15 m²"
    - Luminosité : "lumineux et spacieux"
    - Style : "immeuble entièrement restauré" (détection haussmannien)
    - Détection mots-clés : "haussmannien", "moulures", "parquet", "cheminée", "restauré"
  - **Photos** : URLs des images (grande + miniatures)
  - **Caractéristiques** : nb pièces, étage, exposition, type cuisine
  - **Statut** : "NON VUE" pour détecter les nouvelles annonces
- Sauvegarde dans `data/appartements/{id}.json`
- Gestion pagination pour scraper toutes les offres de l'alerte

### 3. Scoring avec OpenAI

Créer `score_appartement.py` :

- Prompt système adapté de `scoring_prompt.txt` (CandidaturesPlum)
- Analyse intelligente de chaque critère avec GPT-4o
- Détection automatique :
  - Quartier et scoring localisation selon vos préférences
  - Éléments haussmanniens dans description/photos
  - Rapport qualité/prix
  - Orientation et luminosité mentionnées
  - Configuration cuisine (parsing description)
- Output JSON avec scores par axe + justifications

### 4. Automatisation quotidienne

Créer `run_daily_scrape.py` :

- Script orchestrateur : scraping → scoring → rapport
- Détection nouveaux appartements (comparaison avec scrapes précédents)
- Envoi notification si score > seuil (ex: 75/100)
- Logs d'exécution

### 5. Génération rapport HTML

Créer `generate_html_report.py` :

- Template style CandidaturesPlum avec cartes visuelles
- Tri par score décroissant
- Affichage : photo principale, score global, décomposition par critère
- Liens directs vers annonces Jinka
- Indicateurs visuels (🟢/🟡/🔴 par critère)
- Export `rapport_appartements.html`

### 6. Prompt de scoring

Créer `scoring_prompt.txt` avec :

- Contexte : "Tu es expert immobilier parisien spécialisé dans l'analyse d'appartements haussmanniens"
- Grille détaillée des 8 axes avec signaux positifs/négatifs
- Format de sortie structuré (score + justification par axe)
- Exemples de bon/moyen/mauvais pour chaque critère

## Fichiers clés

- `scrape_jinka.py` - Extraction des annonces
- `score_appartement.py` - Scoring OpenAI
- `scoring_config.json` - Critères et pondération
- `scoring_prompt.txt` - Prompt d'évaluation
- `generate_html_report.py` - Rapport visuel
- `run_daily_scrape.py` - Orchestrateur automatique
- `.env` - Identifiants Google (souheil.medaghri@gmail.com)
- `requirements.txt` - playwright, openai, beautifulsoup4, python-dotenv
- `README.md` - Documentation d'usage

## Utilisation

```bash
# Premier lancement manuel
python scrape_jinka.py  # URL de votre alerte en paramètre
python score_appartement.py
python generate_html_report.py

# Automatisation (cron daily)
python run_daily_scrape.py
```

### To-dos

- [ ] Créer l'arborescence du projet et les fichiers de configuration (scoring_config.json, requirements.txt, README.md, .env)
- [ ] Développer le scraper Jinka avec Playwright pour extraire les données des appartements (avec auth Google)
- [ ] Rédiger le prompt de scoring détaillé adapté aux critères immobiliers
- [ ] Implémenter le module de scoring avec OpenAI (score_appartement.py)
- [ ] Créer le générateur de rapport HTML avec design inspiré de CandidaturesPlum
- [ ] Développer le script d'automatisation quotidienne avec détection de nouveautés
