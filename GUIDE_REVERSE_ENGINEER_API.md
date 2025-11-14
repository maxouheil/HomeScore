# Guide : Reverse Engineer l'API Privée Jinka

Ce guide explique comment utiliser les scripts créés pour reverse engineer l'API privée de Jinka.

## 🚀 Démarrage Rapide

### Étape 1 : Lancer l'exploration

Exécutez le script d'exploration avancé qui va capturer toutes les requêtes réseau :

```bash
python explore_jinka_api_advanced.py
```

**Ce que fait le script :**
1. ✅ Ouvre un navigateur Chrome (visible pour debug)
2. ✅ Se connecte à Jinka via email/code
3. ✅ Navigue sur le dashboard
4. ✅ Explore une page d'alerte
5. ✅ Ouvre les détails d'un appartement
6. ✅ Capture **TOUTES** les requêtes réseau avec détails complets
7. ✅ Sauvegarde les résultats dans `data/api_exploration/`

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
python analyze_api_exploration.py
```

**Ce que fait le script :**
1. ✅ Charge automatiquement la dernière exploration
2. ✅ Identifie les patterns d'endpoints
3. ✅ Analyse le mécanisme d'authentification
4. ✅ Analyse les structures de données JSON
5. ✅ Génère une documentation API basique

**Résultats :**
- Analyse détaillée dans la console
- `api_documentation_YYYYMMDD_HHMMSS.md` - Documentation générée

---

## 📋 Workflow Complet

### Phase 1 : Exploration Initiale

```bash
# 1. Lancer l'exploration
python explore_jinka_api_advanced.py

# 2. Analyser les résultats
python analyze_api_exploration.py

# 3. Examiner les fichiers générés
ls -lh data/api_exploration/
```

### Phase 2 : Analyse Manuelle (Optionnel)

Ouvrez les fichiers JSON générés pour une analyse plus approfondie :

```bash
# Voir les endpoints identifiés
cat data/api_exploration/endpoints_*.json | jq '.[] | {url, status, has_json}'

# Voir les cookies importants
cat data/api_exploration/cookies_*.json | jq '.[] | select(.name | contains("session") or contains("token"))'

# Voir les tokens d'authentification
cat data/api_exploration/tokens_*.json
```

### Phase 3 : Tests avec curl/Postman

Utilisez les endpoints identifiés pour tester directement :

```bash
# Exemple avec curl (à adapter selon les endpoints trouvés)
curl -X GET "https://api.jinka.fr/v2/alerts/..." \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Cookie: session=YOUR_SESSION"
```

---

## 🔍 Ce Qu'il Faut Chercher

### 1. Endpoints API Principaux

Cherchez dans `endpoints_*.json` :

- **Authentification :**
  - `/api/auth/login`
  - `/api/auth/google`
  - `/api/auth/refresh`

- **Alertes :**
  - `/api/v2/alerts`
  - `/api/alerts/{id}/properties`

- **Appartements :**
  - `/api/properties/{ad_id}`
  - `/api/properties/{ad_id}/photos`

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

Pour voir plus de détails pendant l'exploration, modifiez `explore_jinka_api_advanced.py` :

```python
# Ligne 52 : Changer headless=False pour voir le navigateur
self.browser = await self.playwright.chromium.launch(headless=False)

# Ajouter plus de logs
print(f"🔍 Requête: {request.url}")
```

### Filtrage des Requêtes

Pour ne capturer que certaines requêtes, modifiez la fonction `_handle_request` :

```python
# Exemple : capturer uniquement les requêtes vers api.jinka.fr
if 'api.jinka.fr' not in url:
    return  # Ignorer cette requête
```

### Export HAR

Pour exporter au format HAR (compatible avec DevTools), ajoutez :

```python
# À la fin de explore_authentication()
har = await self.page.context.har()
with open('data/api_exploration/network.har', 'w') as f:
    json.dump(har, f)
```

---

## 📊 Analyse des Résultats

### Patterns d'URLs à Identifier

1. **Base URL de l'API :**
   - `https://api.jinka.fr`
   - `https://www.jinka.fr/api`
   - `https://api.jinka.fr/v2`

2. **Structure des endpoints :**
   - RESTful : `/api/v2/alerts/{id}`
   - GraphQL : `/graphql`
   - RPC : `/api/rpc`

3. **Paramètres de requête :**
   - Pagination : `?page=1&limit=20`
   - Filtres : `?filter=...&sort=...`
   - Tokens : `?token=...`

### Structures JSON à Documenter

Pour chaque endpoint, documentez :

```json
{
  "endpoint": "GET /api/v2/alerts/{id}/properties",
  "request": {
    "headers": {
      "Authorization": "Bearer ...",
      "Cookie": "session=..."
    },
    "params": {
      "page": 1,
      "limit": 20
    }
  },
  "response": {
    "status": 200,
    "body": {
      "properties": [...],
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
- Respectez les Terms of Service de Jinka

---

## 🎯 Prochaines Étapes

Après avoir exploré l'API :

1. **Créer le client API** (`jinka_api_client.py`)
   - Utiliser les endpoints identifiés
   - Implémenter l'authentification
   - Gérer les erreurs et retry

2. **Migrer le scraper**
   - Remplacer le scraping HTML par des appels API
   - Conserver le scraping comme fallback

3. **Documenter l'API**
   - Créer `docs/api/jinka_api_reference.md`
   - Documenter tous les endpoints
   - Ajouter des exemples d'utilisation

---

## 📚 Ressources

- [Plan complet](PLAN_REVERSE_ENGINEER_API_JINKA.md)
- [Playwright Network API](https://playwright.dev/python/docs/network)
- [Reverse Engineering APIs](https://www.apisec.ai/blog/api-reverse-engineering)

---

**Besoin d'aide ?** Consultez les fichiers générés dans `data/api_exploration/` pour plus de détails.



