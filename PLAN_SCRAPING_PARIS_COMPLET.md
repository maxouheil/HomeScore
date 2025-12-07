# 🏙️ Plan Complet : Scraping Jinka Paris + Site avec Sélection de Critères

## 📋 Vue d'ensemble

**Objectif** : Créer une base de données complète de tous les appartements Jinka à Paris, appliquer le système de scoring existant, et développer un site web permettant aux utilisateurs de sélectionner 3 critères principaux et 2 critères secondaires pour filtrer et trier les appartements.

---

## 🎯 Phase 1 : Scraping Complet de Jinka Paris

### 1.1 Stratégie de Scraping

#### Option A : Via API (RECOMMANDÉ)
- **Avantages** : Plus rapide, plus stable, données structurées
- **Méthode** : Utiliser `jinka_api_client.py` existant
- **Endpoints** :
  - `/apiv2/alert/{token}/dashboard` - Liste paginée des appartements
  - `/apiv2/alert/{token}/ad/{id}` - Détails complets d'un appartement

#### Option B : Scraping HTML (FALLBACK)
- **Quand** : Si l'API ne permet pas de filtrer par ville/Paris
- **Méthode** : Utiliser `scrape_jinka.py` existant avec Playwright

### 1.2 Filtrage Paris

**Problème** : L'API actuelle récupère les appartements d'une alerte spécifique, pas tous les appartements de Paris.

**Solutions** :

1. **Créer plusieurs alertes Jinka** couvrant tous les arrondissements de Paris
   - Alerte 1 : Paris 1e-4e
   - Alerte 2 : Paris 5e-8e
   - Alerte 3 : Paris 9e-12e
   - Alerte 4 : Paris 13e-16e
   - Alerte 5 : Paris 17e-20e
   - Ou créer une alerte globale "Paris" si possible

2. **Filtrer après récupération** :
   - Récupérer tous les appartements de toutes les alertes
   - Filtrer par `postal_code` commençant par `75` (75001-75020)
   - Filtrer par `city` contenant "Paris"

### 1.3 Script de Scraping Complet

**Fichier** : `scrape_all_paris.py`

```python
# Fonctionnalités :
1. Connexion à Jinka via API
2. Récupération de toutes les alertes disponibles
3. Pour chaque alerte :
   - Récupérer toutes les pages (pagination)
   - Filtrer les appartements Paris (postal_code 75xxx)
   - Récupérer les détails complets de chaque appartement
4. Téléchargement des photos (max 10 par appartement)
5. Sauvegarde dans `data/paris_apartments.json`
6. Gestion des doublons (par ID)
7. Rate limiting et retry automatique
```

**Estimation** :
- ~10,000-50,000 appartements à Paris sur Jinka
- Temps estimé : 2-4 heures avec rate limiting
- Stockage : ~500MB-2GB de photos

### 1.4 Structure de Données

**Format** : Identique à `scraped_apartments.json` existant

```json
{
  "id": "90931157",
  "url": "https://www.jinka.fr/alert_result?token=...&ad=90931157",
  "titre": "Paris 19e - 70 m² - 3 pièces - 2 chambres",
  "prix": "775 000 €",
  "prix_m2": "11071 € / m²",
  "surface": "70 m²",
  "pieces": "3 pièces",
  "localisation": "Metro Ménilmontant · 35 Rue Mélingue",
  "coordinates": {"latitude": 48.87, "longitude": 2.38},
  "map_info": {
    "metros": ["Ménilmontant"],
    "quartier": "Belleville"
  },
  "photos": [...],
  "description": "...",
  "caracteristiques": "...",
  "etage": "4e étage",
  "agence": "...",
  "_api_data": {...}
}
```

---

## 🤖 Phase 2 : Application du Système de Scoring

### 2.1 Scoring Automatique

**Fichier** : `score_all_paris_apartments.py`

**Processus** :
1. Charger `data/paris_apartments.json`
2. Pour chaque appartement :
   - Analyser les photos (style, cuisine, luminosité) - **si pas déjà fait**
   - Calculer le score selon `scoring_config.json`
   - Appliquer bonus/malus
3. Sauvegarder dans `data/scores/paris_apartments_scores.json`

**Critères de Scoring** (déjà définis dans `scoring_config.json`) :
- **Localisation** (20 pts)
- **Prix** (20 pts)
- **Style** (20 pts)
- **Ensoleillement** (20 pts)
- **Surface** (5 pts)
- **Cuisine** (10 pts)
- **Étage** (5 pts)
- **Vue** (5 pts)
- **Baignoire** (10 pts)

**Total** : 105 points max (avec bonus Place de la Réunion)

### 2.2 Analyse IA des Photos

**Si pas déjà fait** :
- Utiliser `analyze_apartment_style.py` pour chaque appartement
- Détecter : style haussmannien, cuisine ouverte, luminosité
- Coût estimé : ~0.01-0.02€ par appartement (OpenAI Vision API)
- Pour 10,000 appartements : ~100-200€

**Optimisation** :
- Analyser seulement les appartements sans données d'analyse
- Mettre en cache les résultats
- Traitement par batch (100-200 à la fois)

---

## 🌐 Phase 3 : Site Web avec Sélection de Critères

### 3.1 Architecture Frontend

**Stack** :
- **React** + **Vite** (déjà en place)
- **TypeScript** (optionnel, pour meilleure robustesse)
- **Tailwind CSS** ou **Material-UI** pour le design
- **React Query** ou **SWR** pour la gestion des données

### 3.2 Fonctionnalités Principales

#### 3.2.1 Page d'Accueil - Sélection des Critères

**Interface** :
```
┌─────────────────────────────────────────────────┐
│  🏠 HomeScore Paris - Trouvez votre appartement │
├─────────────────────────────────────────────────┤
│                                                  │
│  CRITÈRES PRINCIPAUX (sélectionner 3) :        │
│  ☐ Localisation (20 pts)                        │
│  ☐ Prix (20 pts)                                 │
│  ☐ Style (20 pts)                               │
│  ☐ Ensoleillement (20 pts)                      │
│  ☐ Surface (5 pts)                               │
│  ☐ Cuisine (10 pts)                              │
│  ☐ Étage (5 pts)                                 │
│  ☐ Vue (5 pts)                                   │
│  ☐ Baignoire (10 pts)                            │
│                                                  │
│  CRITÈRES SECONDAIRES (sélectionner 2) :        │
│  ☐ Localisation                                  │
│  ☐ Prix                                          │
│  ☐ Style                                         │
│  ☐ Ensoleillement                               │
│  ☐ Surface                                       │
│  ☐ Cuisine                                       │
│  ☐ Étage                                         │
│  ☐ Vue                                           │
│  ☐ Baignoire                                     │
│                                                  │
│  [Rechercher]                                    │
└─────────────────────────────────────────────────┘
```

**Logique** :
- L'utilisateur sélectionne exactement 3 critères principaux
- L'utilisateur sélectionne exactement 2 critères secondaires
- Les critères principaux ne peuvent pas être sélectionnés comme secondaires
- Validation avant de permettre la recherche

#### 3.2.2 Page de Résultats

**Affichage** :
- Grille d'appartements (cards)
- Tri par :
  - Score total (par défaut)
  - Score des critères principaux uniquement
  - Score des critères secondaires uniquement
  - Prix croissant/décroissant
  - Surface croissante/décroissante
- Filtres additionnels :
  - Prix min/max
  - Surface min/max
  - Arrondissement
  - Score minimum

**Card Appartement** :
```
┌─────────────────────────────────────┐
│ [Photo principale]                  │
│                                     │
├─────────────────────────────────────┤
│ Paris 19e - 70 m² - 3 pièces       │
│ 775 000 € (11 071 €/m²)            │
│ Metro Ménilmontant                  │
│                                     │
│ Score Total: 85/105 ⭐⭐⭐⭐        │
│                                     │
│ Critères Principaux:               │
│ • Localisation: 20/20 ✅           │
│ • Prix: 12/20 ⚠️                   │
│ • Style: 20/20 ✅                  │
│                                     │
│ Critères Secondaires:              │
│ • Surface: 3/5                      │
│ • Cuisine: 10/10 ✅                 │
└─────────────────────────────────────┘
```

#### 3.2.3 Page Détail Appartement

**Contenu** :
- Carrousel de photos
- Toutes les informations de l'appartement
- Détail du scoring par critère
- Carte interactive (localisation)
- Lien vers l'annonce Jinka originale

### 3.3 Backend API

**Endpoints à créer** :

```python
# backend/api/paris_apartments.py

GET /api/paris-apartments
  - Query params: 
    - primary_criteria: ["localisation", "prix", "style"]
    - secondary_criteria: ["surface", "cuisine"]
    - min_score: int
    - max_price: int
    - min_surface: int
    - arrondissement: int (1-20)
    - sort_by: "total_score" | "primary_score" | "secondary_score" | "price" | "surface"
    - order: "asc" | "desc"
    - page: int
    - limit: int (default: 20)
  - Response: Liste paginée d'appartements avec scores calculés

GET /api/paris-apartments/{id}
  - Response: Détails complets d'un appartement

GET /api/paris-apartments/stats
  - Response: Statistiques globales (nombre total, prix moyen, etc.)

GET /api/criteria/available
  - Response: Liste des critères disponibles avec leurs poids
```

### 3.4 Calcul du Score Personnalisé

**Logique** :
- **Score Principal** = Somme des scores des 3 critères principaux (max 60 pts)
- **Score Secondaire** = Somme des scores des 2 critères secondaires (max 15 pts)
- **Score Total** = Score Principal + Score Secondaire (max 75 pts)

**Exemple** :
- Critères principaux : Localisation (20), Prix (12), Style (20) = 52/60
- Critères secondaires : Surface (3), Cuisine (10) = 13/15
- **Score Total** = 65/75

**Tri** :
- Par défaut : Score Total décroissant
- Option : Score Principal uniquement
- Option : Score Secondaire uniquement

---

## 📊 Phase 4 : Base de Données

### 4.1 Structure de Stockage

**Option A : JSON Files (ACTUEL)**
- `data/paris_apartments.json` - Tous les appartements
- `data/scores/paris_apartments_scores.json` - Scores complets
- **Avantages** : Simple, pas de DB à gérer
- **Inconvénients** : Lent pour grandes quantités, pas de requêtes complexes

**Option B : SQLite (RECOMMANDÉ pour MVP)**
- Base de données locale SQLite
- Tables :
  - `apartments` : Données de base
  - `scores` : Scores par critère
  - `photos` : Métadonnées des photos
- **Avantages** : Requêtes rapides, filtrage efficace
- **Inconvénients** : Migration nécessaire

**Option C : PostgreSQL (PRODUCTION)**
- Base de données PostgreSQL
- **Avantages** : Scalable, requêtes complexes, indexation
- **Inconvénients** : Infrastructure nécessaire

### 4.2 Migration vers SQLite

**Script** : `migrate_to_sqlite.py`

```python
# Fonctionnalités :
1. Créer la base SQLite
2. Créer les tables
3. Importer les données JSON existantes
4. Créer les index pour performance
5. Migration réversible
```

---

## 🔄 Phase 5 : Mise à Jour Continue

### 5.1 Scraping Quotidien

**Script** : `update_paris_database.py`

**Processus** :
1. Récupérer les nouvelles annonces (depuis les alertes)
2. Comparer avec la base existante (par ID)
3. Ajouter les nouveaux appartements
4. Marquer les appartements expirés (si `expired_at` dans l'API)
5. Recalculer les scores si nécessaire
6. Notifier les nouveaux appartements intéressants (optionnel)

**Fréquence** : 1 fois par jour (cron job)

### 5.2 Cache et Performance

- **Cache Redis** (optionnel) : Pour les requêtes fréquentes
- **CDN** : Pour servir les photos
- **Pagination** : Limiter à 20-50 résultats par page
- **Lazy Loading** : Charger les photos à la demande

---

## 📁 Structure de Fichiers Proposée

```
HomeScore/
├── scripts/
│   ├── scrape_all_paris.py          # Scraping complet Paris
│   ├── score_all_paris_apartments.py # Scoring de tous les appartements
│   ├── update_paris_database.py      # Mise à jour quotidienne
│   └── migrate_to_sqlite.py          # Migration vers SQLite
│
├── backend/
│   ├── api/
│   │   └── paris_apartments.py       # Nouveaux endpoints API
│   └── database/
│       └── models.py                 # Modèles SQLite/PostgreSQL
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── HomePage.jsx          # Sélection des critères
│       │   ├── ResultsPage.jsx       # Page de résultats
│       │   └── ApartmentDetail.jsx   # Détail appartement
│       └── components/
│           ├── CriteriaSelector.jsx  # Sélecteur de critères
│           ├── ApartmentCard.jsx     # Card appartement
│           └── ScoreDisplay.jsx      # Affichage des scores
│
└── data/
    ├── paris_apartments.json         # Tous les appartements Paris
    ├── paris_apartments.db           # SQLite (si migration)
    └── scores/
        └── paris_apartments_scores.json
```

---

## ⏱️ Planning d'Implémentation

### Semaine 1 : Scraping
- [ ] Jour 1-2 : Créer `scrape_all_paris.py`
- [ ] Jour 3-4 : Tester le scraping sur quelques alertes
- [ ] Jour 5 : Scraping complet de toutes les alertes Paris
- [ ] Jour 6-7 : Téléchargement des photos et nettoyage des données

### Semaine 2 : Scoring
- [ ] Jour 1-2 : Créer `score_all_paris_apartments.py`
- [ ] Jour 3-4 : Analyse IA des photos (si nécessaire)
- [ ] Jour 5-6 : Calcul des scores pour tous les appartements
- [ ] Jour 7 : Validation et correction des scores

### Semaine 3 : Backend API
- [ ] Jour 1-2 : Créer les endpoints API pour Paris
- [ ] Jour 3-4 : Implémenter le calcul de score personnalisé
- [ ] Jour 5-6 : Tests et optimisation
- [ ] Jour 7 : Migration vers SQLite (optionnel)

### Semaine 4 : Frontend
- [ ] Jour 1-2 : Page de sélection des critères
- [ ] Jour 3-4 : Page de résultats avec tri et filtres
- [ ] Jour 5-6 : Page détail appartement
- [ ] Jour 7 : Tests et polish UI/UX

### Semaine 5 : Finalisation
- [ ] Jour 1-2 : Tests end-to-end
- [ ] Jour 3-4 : Optimisation performance
- [ ] Jour 5-6 : Documentation
- [ ] Jour 7 : Déploiement

---

## 🚀 Commandes d'Exécution

### Scraping Complet
```bash
python scripts/scrape_all_paris.py
```

### Scoring Complet
```bash
python scripts/score_all_paris_apartments.py
```

### Mise à Jour Quotidienne
```bash
python scripts/update_paris_database.py
```

### Démarrage du Serveur
```bash
# Backend
python backend/main.py

# Frontend
cd frontend && npm run dev
```

---

## 📝 Notes Importantes

1. **Rate Limiting** : Respecter les limites de l'API Jinka (déjà géré dans `jinka_api_client.py`)

2. **Coûts** :
   - OpenAI Vision API : ~100-200€ pour 10,000 appartements
   - Stockage photos : ~500MB-2GB
   - Hébergement : Selon le choix (Vercel, Railway, etc.)

3. **Légalité** :
   - Vérifier les conditions d'utilisation de Jinka
   - Ne pas surcharger les serveurs
   - Respecter le robots.txt

4. **Performance** :
   - Indexer la base de données sur `id`, `postal_code`, `score_total`
   - Utiliser la pagination pour les grandes listes
   - Mettre en cache les requêtes fréquentes

5. **Évolutivité** :
   - Prévoir l'ajout d'autres villes (Lyon, Marseille, etc.)
   - Permettre la personnalisation des critères par utilisateur
   - Ajouter des notifications pour nouveaux appartements

---

## ✅ Checklist de Validation

- [ ] Tous les appartements Paris récupérés
- [ ] Photos téléchargées pour tous les appartements
- [ ] Scores calculés pour tous les appartements
- [ ] API fonctionnelle avec filtres et tri
- [ ] Frontend avec sélection de critères
- [ ] Page de résultats avec tri personnalisé
- [ ] Page détail complète
- [ ] Tests end-to-end passés
- [ ] Performance acceptable (<2s pour résultats)
- [ ] Documentation complète

---

**Date de création** : 2025-01-XX
**Auteur** : HomeScore Team
**Version** : 1.0



