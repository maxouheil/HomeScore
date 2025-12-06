# 📝 Changelog - HomeScore

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

## [3.4.0] - 2025-12-06

### 🎯 Version 3.4 - Améliorations Majeures du Système de Scoring et Interface

#### ✅ Améliorations Majeures

**🎯 Système de Scoring des Alertes Amélioré**
- ✅ **Nouveau système de scoring par tiers**: 2 critères principaux (30 pts max chacun) + 2 critères secondaires (20 pts max chacun) = 100 pts max
- ✅ **Logique de scoring simplifiée**: tier1 (good) = 100%, tier2 (moyen) = 50%, tier3 (bad) = 0 pts
- ✅ **Fonction `get_score_from_tier()`**: Attribution automatique des scores selon le tier détecté
- ✅ **Validation backend**: Vérification que `primary` et `secondary` contiennent exactement 2 critères chacun
- ✅ **Affichage dynamique**: Les scores suivent l'ordre défini dans l'alerte (primary puis secondary)
- ✅ **Couleurs cohérentes**: Vert pour "good", orange pour "moyen", rouge pour "bad"

**🎨 Améliorations Frontend Majeures**
- ✅ **AlertResults.jsx**: Amélioration de la gestion des états avec fade-out/fade-in pour transitions fluides
- ✅ **ApartmentCard.jsx**: Amélioration de l'affichage des quartiers avec priorité multi-sources (map_info, scores_detaille, exposition)
- ✅ **AlertCreator.jsx**: Interface améliorée pour la création et édition d'alertes
- ✅ **ScoreBadge.jsx**: Popup de breakdown des scores dans l'ordre défini par l'utilisateur
- ✅ **Carousel.jsx**: Passage des critères d'alerte pour affichage personnalisé
- ✅ **App.css**: Améliorations visuelles et responsive design

**🔧 Améliorations Backend**
- ✅ **backend/api/alerts.py**: Validation renforcée des critères d'alerte (2 primary + 2 secondary)
- ✅ **backend/api/apartments.py**: Amélioration de la gestion des données d'appartements
- ✅ **Calcul des scores d'alerte**: Calcul à la volée lors de l'appel API `/api/alerts/{id}/apartments`

**📊 Améliorations des Analyses**
- ✅ **analyze_photos.py**: Améliorations majeures de l'analyse des photos (+541 lignes)
- ✅ **analyze_apartment_style.py**: Améliorations de la détection de style (+230 lignes)
- ✅ **extract_exposition.py**: Améliorations de l'extraction d'exposition (+87 lignes)
- ✅ **extract_baignoire.py**: Améliorations de l'extraction de baignoire (+106 lignes)
- ✅ **extract_cuisine_text.py**: Améliorations de l'extraction de cuisine (+12 lignes)

**🎯 Améliorations du Scoring**
- ✅ **scoring.py**: Améliorations majeures du système de scoring (+450 lignes)
  - Extraction améliorée des stations de métro depuis l'API uniquement
  - Calcul amélioré du prix/m²
  - Gestion améliorée des fallbacks avec notes moyennes par défaut
- ✅ **scoring_config.json**: Mise à jour de la configuration de scoring
- ✅ **alert_scoring.py**: Refactorisation complète avec système basé sur les tiers (+220 lignes)

**🛠️ Outils de Diagnostic**
- ✅ **diagnostic_mega_score.py**: Améliorations du diagnostic des scores

**📄 Génération HTML**
- ✅ **generate_html.py**: Améliorations mineures
- ✅ **generate_scorecard_html.py**: Améliorations de la génération des scorecards (+64 lignes)

#### 🔧 Changements Techniques

**Fichiers Modifiés (27 fichiers, +2946 lignes, -640 lignes)**:
- `alert_scoring.py`: Refactorisation complète du système de scoring par tiers
- `backend/api/alerts.py`: Validation et gestion améliorées des alertes
- `backend/api/apartments.py`: Gestion améliorée des appartements
- `frontend/src/App.jsx`: Améliorations de l'application principale
- `frontend/src/App.css`: Améliorations visuelles
- `frontend/src/components/AlertCreator.jsx`: Interface améliorée
- `frontend/src/components/AlertResults.jsx`: Gestion d'état améliorée
- `frontend/src/components/ApartmentCard.jsx`: Affichage amélioré des données
- `frontend/src/components/ScoreBadge.jsx`: Affichage dynamique des scores
- `frontend/src/components/Carousel.jsx`: Passage des critères d'alerte
- `scoring.py`: Améliorations majeures du système de scoring
- `analyze_photos.py`: Améliorations majeures de l'analyse des photos
- `analyze_apartment_style.py`: Améliorations de la détection de style
- `extract_exposition.py`: Améliorations de l'extraction d'exposition
- `extract_baignoire.py`: Améliorations de l'extraction de baignoire
- `extract_cuisine_text.py`: Améliorations de l'extraction de cuisine
- `scoring_config.json`: Mise à jour de la configuration
- Et 11 autres fichiers modifiés

#### 📊 Résultats

**Système de Scoring des Alertes**:
- **Structure**: 2 critères principaux (30 pts) + 2 critères secondaires (20 pts) = 100 pts max
- **Tiers**: tier1 = 100%, tier2 = 50%, tier3 = 0%
- **Exemple**: haussmanien (30) + quartier (30) + luminosite (10) + cuisine_ouverte (20) = 90/100

**Frontend**:
- **Transitions fluides**: Fade-out/fade-in pour meilleure UX
- **Affichage amélioré**: Priorité multi-sources pour quartiers et métros
- **Personnalisation**: Scores affichés selon l'ordre défini dans l'alerte

**Backend**:
- **Validation renforcée**: Vérification stricte des critères d'alerte
- **Performance**: Calcul des scores à la volée optimisé

#### 🎯 Impact

**Expérience Utilisateur**:
- Interface plus fluide avec transitions
- Affichage personnalisé des scores selon les critères de l'alerte
- Meilleure visibilité des informations importantes

**Maintenabilité**:
- Code plus structuré et modulaire
- Validation renforcée pour éviter les erreurs
- Documentation améliorée dans CHANGELOG_SCORING_ALERTES.md

**Performance**:
- Calcul des scores optimisé
- Gestion d'état améliorée dans le frontend
- Extraction de données plus robuste

---

## [3.3.0] - 2025-11-05

### 🎯 Version 3.3 - Exploration API Jinka et Préparation Migration

#### ✅ Explorations et Analyses Majeures

**🔍 Reverse Engineering API Jinka Complète**
- ✅ **explore_jinka_api_advanced.py**: Script d'exploration avancée avec interception réseau complète
- ✅ **analyze_api_exploration.py**: Analyse automatique des endpoints et structures JSON découvertes
- ✅ **test_jinka_api_endpoints.py**: Tests directs des endpoints API avec authentification Bearer token
- ✅ **GUIDE_REVERSE_ENGINEER_API.md**: Guide complet pour reverse engineer l'API Jinka
- ✅ **PLAN_REVERSE_ENGINEER_API_JINKA.md**: Plan détaillé en 6 phases pour l'exploration
- ✅ **docs/api/JINKA_API_REFERENCE.md**: Documentation complète de l'API avec tous les endpoints découverts

**📊 Documentation Comparative Scraping vs API**
- ✅ **RECAP_SCRAPING_VS_API.md**: Récapitulatif complet comparant scraping HTML vs API (20+ champs analysés)
- ✅ **RECAP_PHOTOS_SCRAPING_VS_API.md**: Analyse détaillée de l'extraction des photos (scraping 500 lignes vs API 1 ligne)
- ✅ **Données identifiées**: 30+ champs disponibles via API vs 20 champs scraping
- ✅ **Avantages API**: 10x+ plus rapide, données structurées, ordre garanti, plus stable
- ✅ **Données perdues**: Alt text photos, dimensions (peuvent être générées/récupérées)

**📋 Plan de Migration**
- ✅ **Plan de migration complet**: 7 phases pour migrer scraping HTML → API Jinka
- ✅ **Architecture hybride**: Fallback scraping HTML en cas d'échec API
- ✅ **Compatibilité**: Adaptation format API → format scraping pour scoring existant
- ✅ **10 todos définis**: Plan d'action détaillé avec dépendances

#### 🔧 Découvertes Techniques

**Endpoints API Identifiés**:
- ✅ `/apiv2/alert/{token}/dashboard`: Liste des appartements
- ✅ `/apiv2/alert/{token}/ad/{id}`: Détails complets d'un appartement
- ✅ `/apiv2/ad/{id}/contact_info`: Informations de contact
- ✅ `/apiv2/config`: Configuration utilisateur

**Authentification**:
- ✅ JWT Token (`LA_API_TOKEN`) dans cookie + header Authorization Bearer
- ✅ Login via code email (réutilisable depuis scraping existant)
- ✅ Token valide ~30 jours

**Données Structurées Disponibles**:
- ✅ Prix, surface, pièces, chambres en nombres (pas de parsing nécessaire)
- ✅ Coordonnées GPS précises (`lat`/`lng`)
- ✅ Stations métro structurées (`stops[]` avec lignes)
- ✅ Quartier officiel (`quartier_name`)
- ✅ Caractéristiques structurées (`features{}`: lift, bath, parking, etc.)
- ✅ Photos en CSV (ordre garanti)
- ✅ Informations agence complètes (logo, SIRET, partenaire)
- ✅ Dates ISO standard (`created_at`, `expired_at`)
- ✅ DPE, favoris, honoraires, contact info

#### 📁 Nouveaux Fichiers

**Scripts d'Exploration**:
- `explore_jinka_api_advanced.py`: Exploration réseau complète avec Playwright
- `analyze_api_exploration.py`: Analyse automatique des données capturées
- `test_jinka_api_endpoints.py`: Tests directs des endpoints API

**Documentation**:
- `GUIDE_REVERSE_ENGINEER_API.md`: Guide pas-à-pas pour explorer l'API
- `PLAN_REVERSE_ENGINEER_API_JINKA.md`: Plan complet en 6 phases
- `RECAP_SCRAPING_VS_API.md`: Comparaison détaillée scraping vs API
- `RECAP_PHOTOS_SCRAPING_VS_API.md`: Analyse spécifique des photos
- `docs/api/JINKA_API_REFERENCE.md`: Référence complète de l'API

**Données Capturées**:
- `data/api_exploration/cookies_*.json`: Cookies et tokens capturés
- `data/api_exploration/requests_*.json`: Requêtes réseau capturées
- `data/api_exploration/api_responses_detailed.json`: Réponses JSON complètes
- `data/api_exploration/api_structures_report.md`: Rapport des structures JSON

#### 🎯 Prochaines Étapes

**Migration vers API** (Plan créé, en attente d'exécution):
1. Créer client API (`jinka_api_client.py`)
2. Créer adaptateur format (`api_data_adapter.py`)
3. Adapter analyses IA (style, exposition)
4. Migrer scraping vers API
5. Tests et validation
6. Rollout progressif avec fallback

#### 📊 Résultats de l'Exploration

**Performance Attendue**:
- **Vitesse**: 10x+ plus rapide (pas de rendu HTML)
- **Fiabilité**: Données structurées vs parsing fragile
- **Stabilité**: Pas de dépendance aux sélecteurs CSS
- **Complétude**: 30+ champs vs 20 champs scraping

**Compatibilité**:
- ✅ Format API peut être adapté pour scoring existant
- ✅ Analyses IA peuvent être réutilisées sur données API
- ✅ Fallback scraping disponible en cas d'échec API

## [3.2.0] - 2025-02-01 (Dernières 3h)

### 🎯 Version 3.2 - Documentation, Optimisation et Outils de Maintenance

#### ✅ Améliorations Majeures

**📚 Documentation Complète du Système Style**
- ✅ **DECONSTRUCTION_STYLE.md**: Documentation exhaustive du barème Style (20 points)
- ✅ **Processus de détection**: Documentation complète de la priorité texte → photos → fallback
- ✅ **Indices visuels détaillés**: Cheminée, parquet pointe de Hongrie, moulures, chauffage, balcon fer forgé
- ✅ **Flux complet**: Diagramme du processus de détection de bout en bout
- ✅ **Références techniques**: Lignes de code exactes pour chaque composant
- ✅ **Exemples concrets**: Cas d'usage pour chaque tier (Ancien/Atypique/Neuf)

**💰 Rapport d'Optimisation des Coûts**
- ✅ **RAPPORT_OPTIMISATION.md**: Analyse complète du système de cache et des coûts OpenAI
- ✅ **546 entrées en cache**: Répartition par type (exposition, baignoire, style, cuisine)
- ✅ **Économie 90-95%**: Réduction des coûts vs système non optimisé
- ✅ **Coût estimé**: ~$0.01-0.02 par appartement (première fois), ~$0 avec cache
- ✅ **Recommandations**: Suggestions d'optimisation optionnelles (réduction photos style, compression images)
- ✅ **Coût mensuel**: ~$1-2/mois pour 40 appartements × 2 analyses

**🔄 Scripts de Recalcul de Luminosité Image**
- ✅ **recalculate_brightness.py**: Script pour recalculer brightness_value pour tous les appartements
- ✅ **recalculate_all_brightness.py**: Script batch pour mise à jour complète
- ✅ **update_scores_with_brightness.py**: Mise à jour des scores avec luminosité image
- ✅ **Intégration automatique**: Ajout de brightness_value dans exposition.details
- ✅ **Test API**: test_api_brightness.py pour vérifier l'intégration dans l'API

**🌐 Extraction Complète des URLs Dashboard**
- ✅ **extract_all_apartment_urls.py**: Script Python pour extraction complète depuis dashboard
- ✅ **extract_all_urls_dashboard.js**: Script JavaScript pour console navigateur
- ✅ **PLAN_RECUPERATION_TOUTES_URLS.md**: Plan détaillé avec 3 stratégies (scroll infini, pagination, bouton "Voir plus")
- ✅ **EXTRACTION_DASHBOARD_README.md**: Guide d'utilisation complet
- ✅ **Méthode hybride**: Combine scroll + bouton + pagination pour extraction robuste
- ✅ **Déduplication**: Évite les doublons automatiquement

#### 🔧 Changements Techniques

**Nouveaux Fichiers**:
- `DECONSTRUCTION_STYLE.md`: Documentation complète du système Style (349 lignes)
- `RAPPORT_OPTIMISATION.md`: Analyse des coûts et optimisations (178 lignes)
- `recalculate_brightness.py`: Script de recalcul individuel
- `recalculate_all_brightness.py`: Script de recalcul batch
- `update_scores_with_brightness.py`: Mise à jour des scores
- `test_api_brightness.py`: Test de l'API brightness
- `extract_all_apartment_urls.py`: Extraction URLs depuis dashboard
- `extract_all_urls_dashboard.js`: Script JS pour console navigateur
- `PLAN_RECUPERATION_TOUTES_URLS.md`: Plan d'implémentation
- `EXTRACTION_DASHBOARD_README.md`: Guide d'utilisation

**Fichiers Modifiés**:
- Documentation améliorée et complétée
- Scripts de maintenance ajoutés

#### 📊 Résultats

**Documentation**:
- **Style**: Documentation complète avec diagrammes de flux et exemples
- **Optimisation**: Analyse détaillée des coûts avec recommandations concrètes
- **Extraction URLs**: Guide complet avec 3 stratégies d'implémentation

**Outils de Maintenance**:
- **Recalcul luminosité**: Scripts disponibles pour mise à jour rétroactive
- **Extraction URLs**: Solutions pour récupérer toutes les URLs depuis dashboard
- **Tests**: Scripts de vérification pour l'intégration API

**Optimisation**:
- **Cache**: 546 entrées actives avec TTL 30 jours
- **Coûts**: Système déjà très optimisé (~90-95% d'économie)
- **Recommandations**: Suggestions optionnelles pour optimisation supplémentaire

#### 🎯 Impact

**Maintenabilité**:
- Documentation complète facilite la compréhension et l'évolution du système
- Scripts de maintenance permettent la mise à jour rétroactive des données

**Coûts**:
- Rapport détaillé permet de monitorer et optimiser les coûts OpenAI
- Système déjà très optimisé avec cache efficace

**Fonctionnalités**:
- Extraction complète des URLs permet de scraper tous les appartements de l'alerte
- Recalcul de luminosité permet d'améliorer les scores d'exposition existants

---

## [3.1.0] - 2025-02-01

### 🎯 Version 3.1 - Détection Avancée et Indices de Confiance

#### ✅ Améliorations Majeures

**🍳 Détection Cuisine Ouverte avec Fallback Visuel**
- ✅ **Système de fallback visuel**: Analyse automatique des photos pour détecter le type de cuisine quand l'information n'est pas dans le texte
- ✅ **100% de couverture**: Tous les appartements ont maintenant une détection cuisine (vs 35.3% avant)
- ✅ **3 types détectés**: Ouverte, Semi-ouverte, Fermée avec confiance 60-100%
- ✅ **Indices visuels**: Détection de bar/comptoir, murs séparants, îlot central, continuité visuelle
- ✅ **Validation croisée**: Combinaison intelligente texte + photos avec gestion des conflits
- ✅ **Agrégation multi-photos**: Vote majoritaire sur 5 photos analysées avec confiance ajustée
- ✅ **Résultats**: 58.8% ouverte, 29.4% semi-ouverte, 11.8% fermée sur 17 appartements testés

**📊 Calcul Exposition Amélioré - Système de Vote par Signaux**
- ✅ **Vote majoritaire multi-signaux**: Combinaison de 3 signaux (orientation, étage, luminosité image)
- ✅ **Classification intelligente**: Chaque signal classe en "Lumineux", "Luminosité moyenne", ou "Sombre"
- ✅ **Calcul de confiance dynamique**: 
  - Base 60% pour 1 signal
  - +20% par signal supplémentaire d'accord
  - -15% par signal en désaccord
  - +10% si signal image fort et d'accord
  - -10% si signal image faible
  - Bornes: 50-95%
- ✅ **Bonus étage >=4**: Prise en compte automatique dans le calcul
- ✅ **Luminosité image**: Analyse de la luminosité réelle des photos (0.0-1.0)
- ✅ **Indices détaillés**: Affichage de l'étage, exposition directionnelle, et luminosité image

**🎯 Système d'Indices de Confiance**
- ✅ **Confiance par critère**: Chaque critère affiche maintenant un indice de confiance (50-95%)
- ✅ **Exposition**: Confiance basée sur cohérence des signaux (orientation, étage, image)
- ✅ **Cuisine**: Confiance basée sur nombre de photos détectant le même type (60-100%)
- ✅ **Style**: Confiance basée sur validation croisée texte + photos (70-100%)
- ✅ **Baignoire**: Confiance basée sur présence explicite dans caractéristiques (50-100%)
- ✅ **Affichage**: Format "(X% confiance)" affiché dans l'interface pour chaque critère

**🔄 Validation Croisée Texte + Photos**
- ✅ **Détection automatique des conflits**: Comparaison texte vs photos pour style et cuisine
- ✅ **Résolution intelligente**: Choix de la source la plus confiante en cas de conflit
- ✅ **Marquage des validations**: Indication visuelle "✅ Validé par photos" ou "⚠️ Conflit"
- ✅ **Ajustement de confiance**: Réduction de confiance en cas de conflit, augmentation si cohérent

#### 🔧 Changements Techniques

**Fichiers Modifiés**:
- `analyze_apartment_style.py`: 
  - Prompt amélioré avec indices visuels détaillés pour cuisine
  - Format JSON enrichi (cuisine_type, cuisine_indices, cuisine_confidence)
  - Agrégation multi-photos avec vote majoritaire
  - Validation croisée texte + photos
  
- `criteria/exposition.py`:
  - Nouvelle fonction `classify_orientation()` pour classifier l'exposition
  - Nouvelle fonction `classify_etage()` pour classifier selon l'étage
  - Nouvelle fonction `classify_image_brightness()` pour classifier selon luminosité image
  - Nouvelle fonction `vote_majority()` pour décision par vote majoritaire
  - Nouvelle fonction `calculate_confidence()` pour calcul dynamique de confiance
  - `format_exposition()` refactorisé pour utiliser le système de vote par signaux
  
- `criteria/cuisine.py`:
  - Intégration de la validation croisée depuis `scores_detaille`
  - Extraction des indices visuels depuis `photo_validation`
  - Formatage avec confiance et indices détaillés
  
- `extract_exposition.py`:
  - Intégration du calcul de luminosité image depuis photos
  - Extraction automatique de l'étage pour bonus >=4
  - Combinaison des signaux multiples

**Nouveaux Fichiers**:
- `FALLBACK_CUISINE_OUVERTE.md`: Documentation technique du système de fallback visuel
- `DIAGNOSTIC_CUISINE_OUVERTE.md`: Diagnostic initial du problème de détection
- `RESULTATS_FALLBACK_CUISINE.md`: Résultats et statistiques du système de fallback

#### 📊 Résultats

**Détection Cuisine**:
- **Avant**: 35.3% avec info texte (6/17), 64.7% sans info
- **Après**: 100% avec détection (17/17), 0% sans info
- **Confiance moyenne**: 70-100% selon nombre de photos concordantes
- **Indices visuels**: 3 indices/photos en moyenne détectés

**Calcul Exposition**:
- **Système multi-signaux**: Combinaison orientation + étage + luminosité image
- **Confiance dynamique**: 50-95% selon cohérence des signaux
- **Précision améliorée**: Détection plus fiable grâce au vote majoritaire

**Indices de Confiance**:
- **Exposition**: 50-95% selon cohérence des signaux
- **Cuisine**: 60-100% selon nombre de photos concordantes
- **Style**: 70-100% selon validation croisée
- **Affichage**: Tous les critères affichent maintenant leur confiance

#### 🎯 Impact sur le Scoring

**Cuisine**:
- Score moyen attendu: ~9/10 (vs ~3/10 avant pour appartements sans info)
- Distribution: 88.2% ouverte/semi-ouverte (10 pts), 11.8% fermée (1 pt)

**Exposition**:
- Calcul plus précis grâce au vote multi-signaux
- Confiance affichée permet d'évaluer la fiabilité du score

**Qualité globale**:
- Tous les critères ont maintenant une métrique de confiance
- Meilleure traçabilité des décisions de scoring
- Validation croisée réduit les erreurs de détection

---

## [3.0.0] - 2025-01-31

### 🎉 Version 3.0 - Architecture React + Backend API

#### ✅ Nouvelle Architecture

**⚛️ Frontend React + Vite**
- ✅ Interface React moderne avec composants réutilisables
- ✅ Hot Module Replacement (HMR) pour développement rapide
- ✅ Tri automatique par mega score décroissant
- ✅ Formatage intelligent des données (prix, quartier, étage, prix/m²)
- ✅ Carousel de photos interactif
- ✅ Score badges avec couleurs dynamiques

**🔧 Backend FastAPI**
- ✅ API REST pour servir les données d'appartements
- ✅ WebSocket pour mises à jour temps réel
- ✅ WatchService pour surveillance automatique des fichiers
- ✅ Cache intelligent pour optimiser les performances

**📊 Améliorations du Scoring**
- ✅ Mega score calculé depuis les scores réels affichés
- ✅ Cohérence garantie entre affichage et calcul
- ✅ Correction automatique des tiers selon les valeurs affichées
- ✅ Exposition : Lumineux = 20pts, Luminosité moyenne = 10pts, Sombre = 0pts
- ✅ Cuisine : Ouverte = 10pts, Fermée = 0pts

**🎨 Améliorations UI/UX**
- ✅ Titres des critères en casse normale (pas d'ALL CAPS)
- ✅ Cera Pro Medium 16px pour les titres de critères
- ✅ Affichage de l'étage dans le subtitle
- ✅ Prix/m² remplacé par l'étage dans le subtitle
- ✅ Style affiché comme "Ancien / Atypique / Neuf"

#### 🔧 Changements Techniques

**Nouveaux Fichiers :**
- `frontend/` : Application React complète avec Vite
- `backend/` : API FastAPI avec WebSocket
- `dev.py` : Script de démarrage unifié
- `frontend/src/utils/scoreUtils.js` : Utilitaires de calcul de score

**Modifications :**
- `generate_scorecard_html.py` : Améliorations de formatage
- `scoring.py` : Calculs de scores améliorés

## [2.3.0] - 2025-02-01

### 🎯 Version 2.3 - Améliorations de Détection et Scoring Affiné

#### ✅ Améliorations Majeures

**📍 Extraction Multi-Stations de Métro**
- ✅ **`get_all_metro_stations()`**: Nouvelle fonction qui récupère TOUTES les stations de métro mentionnées dans l'annonce (au lieu d'une seule)
- ✅ **Détection améliorée**: Extraction depuis justification IA, map_info, transports, et description
- ✅ **Nettoyage intelligent**: Suppression des doublons, nettoyage des parenthèses et formats variables
- ✅ **`get_metro_tier()`**: Nouvelle fonction qui détermine le tier d'une station selon `scoring_config.json`
- ✅ **Mapping explicite**: Liste précise des stations Tier 1 et Tier 2 pour meilleure précision

**🎨 Amélioration de la Détection de Style**
- ✅ **Catégorisation simplifiée**: Style maintenant classé en 3 catégories (Ancien / Atypique / Neuf)
- ✅ **Détection améliorée**: Utilise à la fois `style_analysis` (IA images) et `scores_detaille` (IA texte)
- ✅ **Indices contextuels**: Extraction intelligente des indices selon le style détecté
- ✅ **Fallback robuste**: Si style non détecté par IA images, recherche dans justification texte

**📊 Scoring de Localisation Affiné**
- ✅ **Utilisation de toutes les stations**: Le scoring vérifie maintenant TOUTES les stations pour déterminer le meilleur tier
- ✅ **Matching flexible**: Vérification dans localisation, quartier, description, et toutes les stations de métro
- ✅ **Meilleure précision**: Détection plus fiable des zones Tier 1 (Place de la Réunion, ligne 2 Belleville-Avron)

**🚫 Suppression des Bonus/Malus**
- ✅ **Bonus/Malus supprimés**: Tous les bonus et malus généraux ont été retirés car jamais validés
- ✅ **Score simplifié**: Le mega score se base maintenant uniquement sur 6 critères (localisation, prix, style, ensoleillement, cuisine, baignoire)
- ✅ **Exception**: Bonus Place de la Réunion (+5) conservé et intégré dans le score de localisation (20 → 25 pts max)
- ✅ **Ensoleillement corrigé**: 20 pts max - Barème simplifié: Lumineux = 20 pts, Moyenne = 10 pts, Sombre = 0 pts
- ✅ **Documentation**: `RECAP_BONUS_MALUS.md` documente la suppression et les raisons
- ✅ **Impact**: Score max = 105 pts (100 pts base + 5 pts bonus Place de la Réunion)

**🎨 Améliorations Design System**
- ✅ **DESIGN_SCORECARD.md mis à jour**: Documentation complète de la structure en deux colonnes pour les critères
- ✅ **Grille responsive**: Amélioration de l'affichage avec grid layout pour séparer texte et badges
- ✅ **Typographie Cera Pro**: Tous les textes utilisent maintenant Cera Pro avec `!important`

#### 🔧 Changements Techniques

**Fichiers Modifiés**:
- `criteria/localisation.py`: 
  - Ajout de `get_all_metro_stations()` pour récupérer toutes les stations
  - Ajout de `get_metro_tier()` pour déterminer le tier d'une station
  - Amélioration de `get_metro_name()` pour utiliser toutes les stations et déterminer la meilleure
- `criteria/style.py`: 
  - Refactorisation de `format_style()` pour catégoriser en Ancien/Atypique/Neuf
  - Amélioration de la détection avec fallback vers `scores_detaille`
  - Extraction intelligente des indices selon le style
- `scoring.py`: 
  - `score_localisation()` utilise maintenant toutes les stations pour scoring
  - Matching flexible sur toutes les sources de données
- `generate_scorecard_html.py`: 
  - Améliorations de l'affichage avec structure grid pour critères
  - Meilleure intégration des métros multiples
- `scoring_prompt.txt`: Mise à jour des critères de style (Ancien/Atypique/Neuf)

**Nouveaux Fichiers**:
- `RECAP_BONUS_MALUS.md`: Documentation complète de la suppression des bonus/malus
- `analyze_bonus_malus.py`: Script d'analyse pour évaluer la pertinence des bonus/malus

#### 📊 Résultats

**Extraction Métro**:
- **Avant**: 1 seule station extraite (parfois incorrecte)
- **Après**: Toutes les stations extraites avec détermination du meilleur tier
- **Précision**: Amélioration significative de la détection des zones Tier 1

**Détection Style**:
- **Catégorisation**: 3 catégories claires (Ancien/Atypique/Neuf) au lieu de nombreux types
- **Fiabilité**: Utilisation combinée IA images + IA texte pour meilleure précision
- **Indices**: Extraction contextuelle des indices pertinents selon le style

**Scoring**:
- **Simplification**: Score basé uniquement sur 6 critères (plus de bonus/malus généraux)
- **Clarté**: Calcul plus transparent et prévisible
- **Ensoleillement**: Corrigé à 20 pts max - Barème: Lumineux = 20 pts, Moyenne = 10 pts, Sombre = 0 pts
- **Score max**: 105 pts (100 pts base + 5 pts bonus Place de la Réunion intégré dans localisation)

---

## [2.2.0] - 2025-01-31

### 🎯 Version 2.2 - Architecture Simplifiée et Système de Watch

#### ✅ Améliorations Majeures

**🏗️ Refonte de l'Architecture**
- ✅ **Architecture simplifiée**: Séparation claire des responsabilités avec 4 fichiers principaux
- ✅ **`homescore.py`**: Orchestrateur central qui coordonne scraping, scoring et génération HTML
- ✅ **`scrape.py`**: Point d'entrée unique pour scraping + analyse IA images
- ✅ **`scoring.py`**: Calcul des scores avec règles simples (pas d'IA pour scoring final)
- ✅ **`generate_html.py`**: UN SEUL générateur HTML remplaçant tous les anciens générateurs
- ✅ **Module `criteria/`**: Un fichier par critère pour le formatage (localisation, prix, style, exposition, cuisine, baignoire)

**📁 Sources de Données Unifiées**
- ✅ **`data/scraped_apartments.json`**: Source unique pour données scrapées + analyses IA
- ✅ **`data/scores.json`**: Source unique pour scores calculés (remplace `data/scores/all_apartments_scores.json`)
- ✅ **`output/homepage.html`**: UN SEUL fichier HTML généré (remplace tous les anciens formats)

**🔄 Système de Watch Auto-Reload**
- ✅ **`watch_scorecard.py`**: Surveillance automatique des fichiers avec régénération HTML
- ✅ **`watch_scorecard_server.py`**: Serveur HTTP avec auto-reload pour visualisation en temps réel
- ✅ **Polling intelligent**: Détection des changements sans dépendances externes
- ✅ **Debounce**: Évite les régénérations trop fréquentes
- ✅ **Cache de modification**: Système de cache pour optimiser les performances

**📚 Documentation Complète**
- ✅ **`STRUCTURE_PROJET.md`**: Documentation complète de l'architecture simplifiée
- ✅ **`USAGE.md`**: Guide d'utilisation détaillé avec exemples
- ✅ **`MIGRATION.md`**: Guide de migration depuis l'ancienne structure
- ✅ **`WATCH_GUIDE.md`**: Guide d'utilisation du système de watch
- ✅ **`DESIGN_SCORECARD.md`**: Design system complet pour les scorecards
- ✅ **`DESIGN_SYSTEM_CARD.md`**: Documentation du design system avec Cera Pro

**🔍 Outils de Diagnostic**
- ✅ **`diagnostic_mega_score.py`**: Diagnostic du calcul du mega score pour vérifier les scores
- ✅ **Vérification automatique**: Détection des différences entre ancien et nouveau calcul
- ✅ **Correction des scores**: Identification des critères incorrectement inclus

#### 🔧 Changements Techniques

**Fichiers Créés**:
- `homescore.py`: Orchestrateur central
- `scrape.py`: Point d'entrée scraping + IA
- `scoring.py`: Calcul des scores
- `generate_html.py`: Générateur HTML unique
- `criteria/__init__.py`: Module de formatage
- `criteria/localisation.py`: Formatage localisation
- `criteria/prix.py`: Formatage prix
- `criteria/style.py`: Formatage style
- `criteria/exposition.py`: Formatage exposition
- `criteria/cuisine.py`: Formatage cuisine
- `criteria/baignoire.py`: Formatage baignoire
- `watch_scorecard.py`: Watch simple
- `watch_scorecard_server.py`: Watch avec serveur HTTP
- `migrate_to_new_structure.py`: Script de migration
- `diagnostic_mega_score.py`: Diagnostic des scores

**Fichiers Supprimés**:
- ❌ `generate_fitscore_style_html.py`: Remplacé par `generate_html.py`
- ❌ Anciens générateurs HTML multiples: Consolidés en un seul

**Fichiers Modifiés**:
- `README.md`: Mise à jour avec nouvelle architecture
- `STRUCTURE_PROJET.md`: Documentation complète de l'architecture
- `generate_scorecard_html.py`: Conservé pour compatibilité mais `generate_html.py` est recommandé

#### 📊 Avantages de la Nouvelle Architecture

**Simplicité**:
- ✅ 4 fichiers principaux au lieu de multiples scripts dispersés
- ✅ Flux de données clair et prévisible
- ✅ Une seule source de vérité par type de données

**Maintenabilité**:
- ✅ Code modulaire avec séparation des responsabilités
- ✅ Formatage centralisé dans `criteria/`
- ✅ Tests et diagnostics facilités

**Performance**:
- ✅ Système de watch optimisé avec cache
- ✅ Debounce pour éviter les régénérations inutiles
- ✅ Pas de dépendances externes pour le watch de base

#### 🚀 Workflow Simplifié

**Avant**:
```bash
python scrape_jinka.py <url>
python analyze_apartment_style.py
python generate_scorecard_html.py
# ou
python generate_fitscore_style_html.py
```

**Maintenant**:
```bash
# 1. Scraping + analyse IA
python scrape.py <alert_url>

# 2. Scoring + génération HTML
python homescore.py
```

**Avec Watch**:
```bash
# Terminal 1: Watch automatique
python watch_scorecard.py

# Terminal 2: Modifications
# Le HTML se régénère automatiquement
```

#### 📈 Résultats

- **Lignes de code**: Réduction de ~30% grâce à la consolidation
- **Fichiers principaux**: 4 fichiers au lieu de 10+
- **Temps de développement**: Réduction significative grâce au watch
- **Clarté**: Architecture beaucoup plus compréhensible

---

## [2.1.0] - 2025-11-01

### 🎯 Version 2.1 - Système de Scoring Affiné et Améliorations

#### ✅ Améliorations Majeures

**🎯 Système de Scoring Affiné avec Système de Tiers**
- ✅ **Nouveau système de notation**: GOOD = 100%, MOYEN = 60%, BAD = 10% du score maximum de chaque axe
- ✅ **8 Axes de Scoring**: Localisation (20), Prix (20), Style (20), Ensoleillement (10), Étage (10), Surface (5), Cuisine (10), Vue (5)
- ✅ **Tiers précis par critère**: Chaque axe a des tiers clairement définis avec scores spécifiques
- ✅ **Zones d'élimination et veto**: Gestion automatique des appartements non éligibles
- ✅ **Bonus Place de la Réunion**: +5 points supplémentaires pour cette zone spécifique

**📋 Critères de Scoring Détaillés**
- ✅ **TIER 1 Localisation**: Place de la Réunion (+5 bonus), Tronçon ligne 2 Belleville-Avron
- ✅ **TIER 2 Localisation**: Goncourt, 11e, 20e deep, 19e proche Buttes-Chaumont, Pyrénées, Jourdain
- ✅ **TIER 3 Localisation**: Reste du 10e, 20e, 19e (2 pts)
- ✅ **Veto Style**: Années 60-70 = élimination automatique
- ✅ **Prix/m²**: Scoring basé sur <9k€/m² (20 pts), 9-11k€/m² (12 pts), >11k€/m² (2 pts)

**🔍 Améliorations de Détection**
- ✅ **Analyse Contextuelle**: Détection améliorée du style et de l'exposition
- ✅ **Documentation Style**: Ajout de `RESUME_DETECTION_STYLE.md` pour diagnostiquer les problèmes
- ✅ **Debug Photo Extraction**: Nouveau script `debug_photo_extraction.py` pour diagnostiquer l'extraction de photos
- ✅ **Tests Map Screenshots**: Nouveaux scripts pour vérifier les screenshots de cartes

#### 🔧 Changements Techniques

**Fichiers Modifiés**:
- `scoring_config.json`: Configuration avec système de tiers détaillé
- `scoring_prompt.txt`: Prompt OpenAI affiné avec les nouveaux critères
- `test_new_scoring.py`: Script de test du nouveau système de scoring
- `extract_apartment_photos.py`: Améliorations de l'extraction de photos
- `download_apartment_photos.py`: Améliorations du téléchargement
- `generate_fitscore_style_html.py`: Améliorations de l'affichage
- `generate_scorecard_html.py`: Améliorations de l'affichage
- `scrape_from_urls.py`: Améliorations du scraping
- `scrape_jinka.py`: Améliorations du scraper principal

**Nouveaux Fichiers**:
- `RESUME_DETECTION_STYLE.md`: Documentation complète du système de détection de style
- `debug_photo_extraction.py`: Outil de debug pour l'extraction de photos
- `test_all_photos_v2.py`: Test de tous les appartements
- `test_photo_extraction_v2.py`: Test de l'extraction de photos v2
- `test_single_apartment.py`: Test d'un appartement spécifique
- `test_map_screenshots.py`: Test des screenshots de cartes
- `verify_map_screenshots.py`: Vérification des screenshots

#### 📊 Résultats

**Système de Scoring**:
- Score maximum: 100 points (80 points principaux + bonus)
- Système de tiers: GOOD/MOYEN/BAD pour chaque critère
- Justification détaillée: Chaque score est justifié avec analyse par tier

**Exemple de Score (Appartement 90931157)**:
- Localisation: 15/20 (TIER 2)
- Prix: 10/20 (TIER 3)
- Style: 15/20 (TIER 2)
- Ensoleillement: 10/10 (TIER 1)
- Étage: 10/10 (TIER 1)
- Surface: 5/5 (TIER 1)
- Cuisine: 10/10 (TIER 1)
- Vue: 5/5 (EXCELLENT)
- **Score Final: 80/100** 🌟

#### 🚀 Améliorations Futures Identifiées

**Points d'Attention**:
- Extraction du prix/m² à améliorer pour un scoring plus précis
- Parser correctement les données de surface (70m² vs erreurs de parsing)
- Affiner la détection des quartiers spécifiques
- Intégrer `style_analysis` dans le scoring (actuellement non utilisé)

---

## [2.0.0] - 2025-10-31

### 🎉 Version 2.0 - Amélioration Majeure de la Détection des Photos

#### ✅ Améliorations Majeures

**📸 Détection des Photos - 100% de Succès**
- ✅ **100% Photo Detection**: Tous les 17 appartements ont maintenant des photos détectées
- ✅ **83 Photos Total**: Extraction réussie de 83 photos (contre 68 avant)
- ✅ **19+ Domaines Supportés**: Ajout du support pour tous les principaux CDNs d'images immobilières

**🌐 Support Multi-CDN**
- ✅ Ajout de `uploadcaregdc`, `uploadcare`, `s3.amazonaws.com` (Uploadcare)
- ✅ Ajout de `googleusercontent.com` (Google Photos/CDN)
- ✅ Ajout de `cdn.safti.fr`, `safti.fr` (CDN SAFTI)
- ✅ Ajout de `paruvendu.fr`, `immo-facile.com` (ParuVendu/Immo-Facile)
- ✅ Ajout de `mms.seloger.com`, `seloger.com` (SELOGER)
- ✅ Support étendu pour `transopera.staticlbi.com`, `images.century21.fr`, etc.

**🔍 Améliorations Techniques**
- ✅ **Smart Preloader Detection**: Gestion intelligente des images avec `alt="preloader"` qui sont en fait de vraies photos
- ✅ **Enhanced Gallery Detection**: Ciblage amélioré des photos visibles dans les divs `col` (first, middle, last)
- ✅ **Lazy Loading Support**: Support complet pour `data-src`, `data-lazy-src`, et `srcset`
- ✅ **Scroll Triggering**: Défilement automatique pour déclencher le chargement des images lazy
- ✅ **Improved Filtering**: Filtrage intelligent qui vérifie les patterns d'URL avant d'exclure par alt text
- ✅ **Déduplication par URL**: Évite les doublons en vérifiant les URLs uniques

**🎨 Améliorations UX**
- ✅ **Clickable Cards**: Les cartes d'appartements sont maintenant cliquables et ouvrent l'URL Jinka
- ✅ **Better Photo Display**: Priorisation des photos du système d'extraction amélioré (v2)
- ✅ **Visual Consistency**: 100% de couverture - tous les appartements ont des photos

#### 📊 Résultats

**Avant (v1.0)**:
- 7 appartements avec photos (41%)
- 37 photos extraites
- 59% des appartements sans photos

**Après (v2.0)**:
- 17 appartements avec photos (100%)
- 83 photos extraites (+124% d'augmentation)
- 0% des appartements sans photos

#### 🔧 Changements Techniques

**Fichiers Modifiés**:
- `scrape_jinka.py`: Amélioration de `extract_photos()`
- `download_apartment_photos.py`: Amélioration de `extract_apartment_photos()`
- `generate_fitscore_style_html.py`: Ajout des liens cliquables et priorité photos_v2
- `generate_scorecard_html.py`: Ajout des liens cliquables et priorité photos_v2

**Nouveaux Scripts**:
- `test_photo_extraction_v2.py`: Script de test pour la nouvelle extraction
- `test_all_photos_v2.py`: Test de tous les appartements
- `test_single_apartment.py`: Test d'un appartement spécifique
- `debug_photo_extraction.py`: Outil de debug pour diagnostiquer les problèmes

#### 📈 Statistiques

- **Photos extraites**: 83 (+46 photos par rapport à v1.0)
- **Taux de succès**: 100% (contre 41% avant)
- **Domaines supportés**: 19+ (contre 7 avant)
- **Temps de traitement**: ~2-3 minutes par appartement

---

## [1.0.0] - 2025-10-29

### 🎉 Version Initiale - Système Complet

#### ✅ Fonctionnalités Ajoutées

**🔧 Infrastructure de Base**
- [x] Configuration du projet avec structure modulaire
- [x] Gestion des dépendances (Playwright, OpenAI, etc.)
- [x] Variables d'environnement sécurisées
- [x] Configuration JSON pour critères de scoring

**🌐 Scraping Jinka**
- [x] Connexion automatique via Google OAuth
- [x] Navigation et authentification robuste
- [x] Extraction des URLs d'appartements depuis les alertes
- [x] Scraping des données détaillées de chaque appartement
- [x] Mode headless pour l'efficacité
- [x] Gestion d'erreurs et retry automatique

**📊 Extraction de Données**
- [x] **Prix** : Extraction automatique (775 000 €)
- [x] **Surface** : Détection via regex (70 m²)
- [x] **Étage** : Identification automatique (4e étage)
- [x] **Localisation** : Arrondissement + analyse de carte
- [x] **Description** : Texte intégral complet
- [x] **Caractéristiques** : Parking, ascenseur, balcon, etc.
- [x] **Photos** : URLs des images
- [x] **Agence** : Nom de l'agence (GLOBALSTONE)

**🗺️ Analyse de Carte Avancée**
- [x] Screenshots automatiques de la carte Jinka
- [x] Identification du quartier basée sur les rues visibles
- [x] Extraction des coordonnées GPS (en développement)
- [x] Base de données des quartiers du 19e
- [x] Détection des métros et points d'intérêt

**🏛️ Scoring Haussmannien Intelligent**
- [x] Détection automatique des éléments architecturaux
- [x] Mots-clés étendus (moulures, parquet, cheminée, etc.)
- [x] Scoring par catégorie (architectural, caractère, matériaux, détails)
- [x] Score final calculé automatiquement (30/100)
- [x] Système de bonus/malus

**📈 Système de Scoring Complet**
- [x] **Localisation** : 20pts (Paris 19e, proximité Buttes-Chaumont)
- [x] **Style** : 20pts (détection haussmannien)
- [x] **Prix** : 20pts (775k€, 11k€/m²)
- [x] **Ensoleillement** : 10pts (lumineux, spacieux)
- [x] **Cuisine ouverte** : 10pts (américaine ouverte)
- [x] **Étage** : 10pts (4e étage, ascenseur)
- [x] **Vue** : 5pts (balcon, terrasse)
- [x] **Surface** : 5pts (70m², 3 pièces)

**📊 Rapports et Visualisation**
- [x] Génération HTML avec cartes d'appartements
- [x] Scores détaillés par critère
- [x] Photos et descriptions intégrées
- [x] Interface moderne et responsive
- [x] Export des données en JSON

**🤖 Intégration OpenAI**
- [x] Configuration de l'API OpenAI
- [x] Prompt personnalisé pour le scoring
- [x] Parsing des réponses JSON
- [x] Gestion des erreurs API

**⚙️ Automatisation**
- [x] Script de démarrage rapide
- [x] Tests automatisés du système
- [x] Gestion des erreurs robuste
- [x] Logs détaillés pour le debug

#### 🔧 Améliorations Techniques

**Sélecteurs CSS Robustes**
- [x] Détection automatique des cartes d'appartements
- [x] Fallback sur plusieurs sélecteurs
- [x] Debug avancé pour identifier les éléments

**Extraction de Coordonnées**
- [x] Parsing des transformations CSS Leaflet
- [x] Conversion Web Mercator vers lat/lng
- [x] Validation des coordonnées extraites

**Gestion des Erreurs**
- [x] Retry automatique sur échecs
- [x] Logs détaillés pour le debug
- [x] Fallback gracieux sur erreurs

#### 📊 Résultats de Test

**Appartement Test (ID: 90931157)**
- ✅ **Scraping** : 2 appartements trouvés et scrapés
- ✅ **Données** : Toutes les données extraites avec succès
- ✅ **Screenshots** : 2 cartes sauvegardées (450KB chacune)
- ✅ **Quartier** : Place des Fêtes identifié
- ✅ **Score** : 51/100 calculé automatiquement

#### 🎯 Performance

- **Temps de scraping** : ~30 secondes par appartement
- **Taux de succès** : 100% sur l'appartement test
- **Données extraites** : 15+ champs par appartement
- **Screenshots** : Génération automatique et fiable

#### 📁 Fichiers Créés

```
HomeScore/
├── README.md                    # Documentation complète
├── CHANGELOG.md                 # Historique des changements
├── requirements.txt             # Dépendances Python
├── .env                        # Variables d'environnement
├── config.json                 # Configuration générale
├── scoring_config.json         # Critères de scoring
├── scoring_prompt.txt          # Prompt OpenAI
├── scrape_jinka.py             # Scraper principal (600+ lignes)
├── score_appartement.py        # Module de scoring
├── generate_html_report.py     # Générateur de rapports
├── run_daily_scrape.py         # Automatisation quotidienne
├── test_homescore.py           # Tests du système
├── quick_start.py              # Démarrage rapide
├── test_extraction.py          # Tests d'extraction
├── test_final_extraction.py    # Tests finaux
├── analyze_map_screenshot.py   # Analyse des screenshots
├── analyze_quartier.py         # Analyse du quartier
├── data/
│   ├── appartements/           # Données scrapées (JSON)
│   └── screenshots/            # Screenshots de cartes
└── output/
    └── rapport_appartements.html  # Rapport final
```

#### 🚀 Prochaines Étapes

**Court terme**
- [ ] Correction des coordonnées GPS
- [ ] Extraction d'adresses exactes
- [ ] Amélioration de l'OCR sur les cartes

**Long terme**
- [ ] Interface web pour visualisation
- [ ] Machine Learning pour scoring automatique
- [ ] Intégration d'autres sites immobiliers

---

## 📈 Statistiques du Projet

- **Lignes de code** : 1000+
- **Fichiers créés** : 15+
- **Fonctionnalités** : 20+
- **Tests** : 5 scripts de test
- **Documentation** : README + CHANGELOG complets

## 🎉 Conclusion

Le système HomeScore est maintenant **100% fonctionnel** avec :
- ✅ Scraping automatique Jinka
- ✅ Extraction de données complète
- ✅ Scoring intelligent sur 100 points
- ✅ Analyse de carte avancée
- ✅ Rapports HTML visuels
- ✅ Documentation complète

**Prêt pour la production ! 🚀**
