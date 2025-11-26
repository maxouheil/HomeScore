# Analyse de l'API SeLoger - Résultats de l'Exploration

**Date**: 2025-11-19  
**Script utilisé**: `explore_seloger_api.py`

## Résultats de l'Exploration

### Endpoints Découverts

#### 1. `/api/apps/home/news`
- **URL**: `https://www.seloger.com/api/apps/home/news`
- **Méthode**: `GET`
- **Status**: 200
- **Type**: JSON (mais non capturé dans la réponse)
- **Usage**: Actualités/News de la page d'accueil
- **Note**: ❌ Pas pour les annonces immobilières

### Observations

1. **Architecture SSR (Server-Side Rendering)**
   - Les données d'annonces semblent être dans le HTML initial
   - Pas de requêtes AJAX/GraphQL détectées pour charger les annonces
   - Le site utilise probablement du rendu côté serveur

2. **Protection Anti-Bot**
   - CAPTCHA détecté sur la page de recherche (`geo.captcha-delivery.com`)
   - Cela peut bloquer le chargement des données dynamiques
   - Les requêtes API peuvent être conditionnées à la résolution du CAPTCHA

3. **Requêtes POST**
   - Une requête POST vers `dd.seloger.com/js/` avec un body encodé
   - Probablement pour le tracking/analytics
   - Pas de données d'annonces

### Statistiques

- **Total requêtes capturées**: 94
- **Requêtes API identifiées**: 58 (mais beaucoup sont des assets/third-party)
- **Endpoints SeLoger réels**: 1 (`/api/apps/home/news`)
- **Réponses JSON**: 0 (aucune réponse JSON capturée)
- **Cookies capturés**: 4
- **Tokens d'authentification**: 0

## Conclusion

SeLoger ne semble **pas exposer d'API publique** pour récupérer les annonces immobilières. Les données sont probablement :

1. **Dans le HTML initial** (SSR) - nécessite du scraping HTML
2. **Chargées via JavaScript** après résolution du CAPTCHA
3. **Protégées par des mécanismes anti-bot** avancés

## Recommandations

### Option 1 : Scraping HTML (Recommandé)
- Parser le HTML de la page de recherche
- Extraire les données depuis les balises HTML
- Plus robuste mais plus fragile aux changements de structure

### Option 2 : Améliorer l'Exploration
- Attendre la résolution du CAPTCHA
- Interagir avec la page (cliquer sur filtres, scroll)
- Chercher des requêtes GraphQL ou WebSocket
- Attendre plus longtemps que le JavaScript charge

### Option 3 : Utiliser le Fallback HTML
- Les scrapers créés (`scrape_seloger.py`) supportent déjà le fallback HTML
- Implémenter le scraping HTML dans `_search_via_html()`

## Prochaines Étapes

1. ✅ Exploration initiale complétée
2. ⏳ Implémenter le scraping HTML dans `scrape_seloger.py`
3. ⏳ Tester le scraping HTML sur une vraie recherche
4. ⏳ Adapter le client API si des endpoints sont découverts plus tard

## Fichiers Générés

- `data/api_exploration/seloger/summary_20251119_143812.json`
- `data/api_exploration/seloger/endpoints_20251119_143812.json`
- `data/api_exploration/seloger/responses_20251119_143812.json`
- `data/api_exploration/seloger/requests_20251119_143812.json`
- `data/api_exploration/seloger/cookies_20251119_143812.json`
- `data/api_exploration/seloger/tokens_20251119_143812.json`
- `data/api_exploration/seloger/report_20251119_143812.txt`

## Notes Techniques

- Le site utilise CloudFront (CDN AWS)
- Protection DataDome/Fraud0 détectée
- UserCentrics pour la gestion des cookies
- Architecture micro-frontends (remoteEntry.js)



