# Guide : Reverse Engineer l'API Privée LeBonCoin

Ce guide explique comment utiliser les scripts créés pour reverse engineer l'API privée de LeBonCoin.

## 🚀 Démarrage Rapide

### Étape 1 : Lancer l'exploration

Exécutez le script d'exploration qui va capturer toutes les requêtes réseau :

```bash
python explore_leboncoin_api.py
```

**Ce que fait le script :**
1. ✅ Ouvre un navigateur Chrome (visible pour debug)
2. ✅ Navigue sur la page d'accueil LeBonCoin
3. ✅ Effectue une recherche d'annonces immobilières
4. ✅ Ouvre les détails d'une annonce
5. ✅ Explore la page de connexion
6. ✅ Capture **TOUTES** les requêtes réseau avec détails complets
7. ✅ Sauvegarde les résultats dans `data/api_exploration/leboncoin/`

**Durée estimée :** 2-5 minutes

**Résultats sauvegardés :**
- `summary_YYYYMMDD_HHMMSS.json` - Résumé de l'exploration
- `requests_YYYYMMDD_HHMMSS.json` - Toutes les requêtes capturées
- `responses_YYYYMMDD_HHMMSS.json` - Toutes les réponses capturées
- `endpoints_YYYYMMDD_HHMMSS.json` - Endpoints API identifiés
- `cookies_YYYYMMDD_HHMMSS.json` - Cookies de session
- `tokens_YYYYMMDD_HHMMSS.json` - Tokens d'authentification
- `report_YYYYMMDD_HHMMSS.txt` - Rapport textuel

---

### Étape 2 : Analyser les résultats

Une fois l'exploration terminée, analysez les résultats :

```bash
# Voir les endpoints identifiés
cat data/api_exploration/leboncoin/endpoints_*.json | jq '.[] | {url, status, has_json}'

# Voir les cookies importants
cat data/api_exploration/leboncoin/cookies_*.json | jq '.[] | select(.name | contains("session") or contains("token"))'

# Voir les tokens d'authentification
cat data/api_exploration/leboncoin/tokens_*.json
```

---

## 📋 Workflow Complet

### Phase 1 : Exploration Initiale

```bash
# 1. Lancer l'exploration
python explore_leboncoin_api.py

# 2. Examiner les fichiers générés
ls -lh data/api_exploration/leboncoin/
```

### Phase 2 : Analyse Manuelle

Ouvrez les fichiers JSON générés pour une analyse plus approfondie :

```bash
# Voir les endpoints identifiés
cat data/api_exploration/leboncoin/endpoints_*.json | jq '.[] | {url, status, has_json}'

# Voir les cookies importants
cat data/api_exploration/leboncoin/cookies_*.json | jq '.[] | select(.name | contains("session") or contains("token"))'

# Voir les tokens d'authentification
cat data/api_exploration/leboncoin/tokens_*.json
```

### Phase 3 : Adapter le Client API

Une fois les endpoints identifiés, adaptez `leboncoin_api_client.py` :

1. Mettre à jour `BASE_URL` et `API_BASE_URL` avec les vraies URLs
2. Adapter les méthodes `search_properties()`, `get_property_details()`, etc.
3. Mettre à jour les endpoints dans chaque méthode
4. Adapter la structure des données selon les réponses réelles

### Phase 4 : Tests

Testez le client API :

```bash
python leboncoin_api_client.py
```

---

## 🔍 Ce Qu'il Faut Chercher

### 1. Endpoints API Principaux

Cherchez dans `endpoints_*.json` :

- **Recherche :**
  - `/api/search`
  - `/api/ads`
  - `/api/listing`

- **Détails :**
  - `/api/ads/{id}`
  - `/api/listing/{id}`

- **Photos :**
  - `/api/ads/{id}/images`
  - `/api/images/...`

### 2. Mécanisme d'Authentification

Dans `cookies_*.json` et `tokens_*.json`, cherchez :

- **Cookies de session :** `session`, `session_id`, `auth_token`
- **Headers d'authentification :** `Authorization: Bearer ...`
- **Tokens JWT :** Tokens longs encodés en base64

### 3. Structure des Données

Dans `responses_*.json`, examinez :

- **Format JSON :** Structure des objets
- **Pagination :** Comment sont paginées les listes
- **Filtres :** Paramètres de requête pour filtrer/trier

---

## 🛠️ Utilisation Avancée

### Mode Debug

Pour voir plus de détails pendant l'exploration, modifiez `explore_leboncoin_api.py` :

```python
# Ligne 32 : Changer headless=False pour voir le navigateur
self.browser = await self.playwright.chromium.launch(headless=False)

# Ajouter plus de logs
print(f"🔍 Requête: {request.url}")
```

### Filtrage des Requêtes

Pour ne capturer que certaines requêtes, modifiez la fonction `_handle_request` :

```python
# Exemple : capturer uniquement les requêtes vers api.leboncoin.fr
if 'api.leboncoin.fr' not in url:
    return  # Ignorer cette requête
```

---

## 📊 Analyse des Résultats

### Patterns d'URLs à Identifier

1. **Base URL de l'API :**
   - `https://api.leboncoin.fr`
   - `https://www.leboncoin.fr/api`
   - `https://ws.leboncoin.fr`

2. **Structure des endpoints :**
   - RESTful : `/api/v1/ads/{id}`
   - GraphQL : `/graphql`
   - WebSocket : `ws://ws.leboncoin.fr/...`

3. **Paramètres de requête :**
   - Pagination : `?page=1&limit=20`
   - Filtres : `?filter=...&sort=...`
   - Tokens : `?token=...`

### Structures JSON à Documenter

Pour chaque endpoint, documentez :

```json
{
  "endpoint": "GET /api/search",
  "request": {
    "headers": {
      "Authorization": "Bearer ...",
      "Cookie": "session=..."
    },
    "params": {
      "category": 9,
      "real_estate_type": 2,
      "locations": "Paris",
      "page": 1,
      "limit": 20
    }
  },
  "response": {
    "status": 200,
    "body": {
      "ads": [...],
      "pagination": {...}
    }
  }
}
```

---

## ⚠️ Points d'Attention

### Rate Limiting

L'API peut avoir des limites de taux. Si vous voyez des erreurs 429 :

- Ajoutez des délais entre les requêtes
- Réutilisez les sessions existantes
- Implémentez un système de retry avec backoff

### Authentification

Les tokens peuvent expirer rapidement :

- Documentez la durée de validité
- Identifiez le mécanisme de refresh
- Testez la réutilisation des cookies

### Sécurité

Respectez les bonnes pratiques :

- Ne partagez jamais les tokens/cookies
- Utilisez uniquement pour usage personnel
- Respectez les Terms of Service de LeBonCoin

---

## 🎯 Prochaines Étapes

Après avoir exploré l'API :

1. **Créer le client API** (`leboncoin_api_client.py`)
   - Utiliser les endpoints identifiés
   - Implémenter l'authentification
   - Gérer les erreurs et retry

2. **Migrer le scraper**
   - Remplacer le scraping HTML par des appels API
   - Conserver le scraping comme fallback

3. **Documenter l'API**
   - Créer `docs/api/leboncoin_api_reference.md`
   - Documenter tous les endpoints
   - Ajouter des exemples d'utilisation

---

## 📚 Ressources

- [Plan complet](../reverse-engineer-apis-seloger-leboncoin.plan.md)
- [Playwright Network API](https://playwright.dev/python/docs/network)
- [Reverse Engineering APIs](https://www.apisec.ai/blog/api-reverse-engineering)

---

**Besoin d'aide ?** Consultez les fichiers générés dans `data/api_exploration/leboncoin/` pour plus de détails.



