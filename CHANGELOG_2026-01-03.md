# Changelog - 3 Janvier 2026

## 📊 Résumé
- **24 fichiers modifiés**
- **+2616 insertions, -1132 suppressions**
- Améliorations majeures du frontend (ApartmentCard), backend API, et critères d'analyse

## 🎨 Frontend

### ApartmentCard.jsx
- **Refactorisation majeure** : Amélioration de l'extraction et du formatage des données
- **Gestion améliorée des scores d'alerte** : Support du système de scoring sur 5 points pour les alertes
- **Extraction intelligente du quartier** : Priorité sur `map_info.quartier`, puis `scores_detaille.localisation.justification`, puis `exposition.details.photo_details.quartier`
- **Détection automatique des photos** : Support multi-sources pour les photos détectées (cuisine, baignoire)
- **Formatage du titre** : Format "750k · Belleville" avec priorité métro puis quartier
- **Gestion des scores** : Distinction claire entre `alert_score` (sur 5) et `megaScore` (sur 90)

### ApartmentCard.css
- Améliorations du style et de la mise en page

### Carousel.jsx & Carousel.css
- Améliorations de l'affichage du carousel de photos

### AlertResults.jsx
- Améliorations de l'affichage des résultats d'alertes

### App.jsx
- Refactorisation et améliorations de la logique principale

## 🔧 Backend

### backend/api/apartments.py
- **Enrichissement des données** : Fonction `enrich_apartment_with_indices()` améliorée
- **Support multi-sources pour les critères** : 
  - Baignoire : Support de `scores_detaille`, `style_analysis`, `formatted_data`, `baignoire_data`
  - Style : Création systématique de `formatted_data.style` même sans `scores_detaille`
  - Exposition : Support de `scores_detaille.ensoleillement`, `exposition` (scraping), `etage_num` (API), `visavis_distance`
- **Gestion d'erreurs améliorée** : Fallbacks robustes et cache en cas d'erreur
- **Logging détaillé** : Ajout de logs pour le debugging

### backend/main.py
- Améliorations de la configuration et des routes

### backend/watch_service.py
- Améliorations du service de watch pour les mises à jour en temps réel

## 📋 Critères d'analyse

### criteria/baignoire.py
- Améliorations de la détection et du formatage

### criteria/cuisine.py
- Améliorations mineures

### criteria/exposition.py
- Améliorations de l'analyse d'exposition (45 lignes modifiées)

### criteria/style.py
- **Refactorisation majeure** : 110 lignes modifiées
- Amélioration de la détection du style architectural

### criteria/__init__.py
- Ajout de nouveaux exports

## 🧪 Scripts et outils

### analyze_apartment_unified.py
- **Refactorisation importante** : 293 lignes modifiées
- Améliorations de l'analyse unifiée des appartements

### test_my_alert_api.py
- **Ajouts majeurs** : +291 lignes
- Nouveaux tests pour l'API d'alertes

### scoring.py
- Améliorations du système de scoring (49 lignes modifiées)

### scoring_optimized.py
- Optimisations mineures

### batch_analyze_paris.py
- Améliorations mineures

### generate_html.py & generate_scorecard_html.py
- Améliorations de la génération HTML

### dev.py
- Améliorations du script de développement

### start_backend.py
- Améliorations du démarrage du backend

## 📝 Documentation

### README.md
- Mise à jour de la documentation (9 lignes ajoutées)

## 🔄 Statistiques

- **Total** : 24 fichiers modifiés
- **Insertions** : +2616 lignes
- **Suppressions** : -1132 lignes
- **Net** : +1484 lignes

## 🎯 Points clés

1. **Frontend** : Refactorisation majeure de `ApartmentCard` pour une meilleure gestion des données et des scores
2. **Backend** : Enrichissement amélioré avec support multi-sources pour tous les critères
3. **Critères** : Améliorations significatives de `style.py` et `exposition.py`
4. **Tests** : Ajout de nombreux tests pour l'API d'alertes
5. **Analyse** : Refactorisation importante de `analyze_apartment_unified.py`

## 📌 Fichiers non suivis (nouveaux)

De nombreux nouveaux fichiers ont été créés aujourd'hui (non trackés par git) :
- Documentation Gemini, Jinka, critères
- Scripts d'analyse et de test
- Composants frontend supplémentaires (AlertSidebar, CriteriaAnalysis, etc.)
- Scripts de scraping et d'analyse

---

*Généré automatiquement le 2026-01-03*
