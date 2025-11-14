# Plan : Reverse Engineer l'API Privée Jinka

## 🎯 Objectif

Découvrir et documenter l'API privée de Jinka pour remplacer le scraping HTML par des appels API directs, améliorant ainsi la performance, la stabilité et la maintenabilité du système.

---

## 📋 Phase 1 : Exploration et Interception des Requêtes

### 1.1 Améliorer le script d'exploration existant

**Fichier : `explore_jinka_api.py` (à améliorer)**

**Objectifs :**
- Intercepter TOUTES les requêtes réseau (pas seulement celles avec certains mots-clés)
- Capturer les headers complets (Authorization, Cookies, Referer, etc.)
- Sauvegarder les réponses complètes (body, status, headers)
- Capturer les requêtes WebSocket si présentes
- Identifier les appels GraphQL si présents

**Métriques à capturer :**
```python
{
    'timestamp': '2024-01-01T12:00:00',
    'url': 'https://api.jinka.fr/v2/alerts/...',
    'method': 'GET/POST/PUT/DELETE',
    'headers': {...},
    'request_body': {...},
    'response_status': 200,
    'response_headers': {...},
    'response_body': {...},
    'response_time_ms': 150,
    'cookies': [...]
}
```

**Actions spécifiques :**
- [ ] Capturer toutes les requêtes réseau (pas de filtre par défaut)
- [ ] Sauvegarder les cookies de session
- [ ] Capturer les requêtes lors de la connexion
- [ ] Capturer les requêtes lors de la navigation dashboard
- [ ] Capturer les requêtes lors de l'affichage d'une annonce
- [ ] Capturer les requêtes lors du scroll infini
- [ ] Identifier les patterns d'URLs (endpoints)

---

### 1.2 Analyse manuelle avec DevTools

**Outils :**
- Chrome DevTools > Network tab
- Filtres : XHR, Fetch, WS (WebSocket), JS
- Export HAR (HTTP Archive)

**Workflow à documenter :**
1. **Connexion :**
   - Ouvrir DevTools > Network
   - Se connecter à Jinka (Google OAuth)
   - Identifier les endpoints d'authentification
   - Noter les tokens/cookies générés

2. **Dashboard :**
   - Naviguer vers le dashboard
   - Identifier les endpoints qui chargent la liste d'annonces
   - Noter les paramètres de pagination/filtrage

3. **Détail d'une annonce :**
   - Cliquer sur une annonce
   - Identifier les endpoints qui chargent les détails
   - Noter les IDs utilisés (ad_id, token, etc.)

4. **Photos :**
   - Identifier les endpoints de chargement des photos
   - Noter les URLs et tokens d'accès

**Documentation à créer :**
- `docs/api/jinka_endpoints.md` - Liste des endpoints découverts
- `docs/api/jinka_auth.md` - Processus d'authentification
- `docs/api/jinka_data_models.md` - Structure des données JSON

---

## 📋 Phase 2 : Analyse de l'Authentification

### 2.1 Identifier le mécanisme d'authentification

**À documenter :**
- Type d'auth : JWT, Session Cookie, OAuth token, API Key ?
- Comment obtenir le token initial ?
- Durée de validité du token ?
- Comment rafraîchir le token ?
- Headers requis pour chaque requête ?

**Endpoints à identifier :**
```
POST /api/auth/login
POST /api/auth/google
GET  /api/auth/me
POST /api/auth/refresh
```

**Script à créer : `analyze_jinka_auth.py`**
- Intercepter le processus de connexion complet
- Extraire tous les tokens/cookies
- Tester la réutilisation des tokens
- Documenter le flow d'authentification

---

### 2.2 Gestion des cookies et sessions

**À analyser :**
- Cookies de session (nom, valeur, domaine, path, httpOnly, secure)
- Cookies de tracking/analytics (à ignorer ou non ?)
- Headers requis : `Authorization`, `X-Requested-With`, `Referer`, etc.

**Stockage :**
- Sauvegarder les cookies dans un fichier JSON
- Permettre la réutilisation d'une session existante
- Gérer l'expiration automatique

---

## 📋 Phase 3 : Découverte des Endpoints

### 3.1 Endpoints principaux à identifier

**Liste des appels API probables :**

1. **Authentification :**
   - Login (Google OAuth)
   - Email code verification
   - Session refresh

2. **Dashboard/Alertes :**
   - Liste des alertes utilisateur
   - Liste des appartements d'une alerte
   - Pagination des résultats
   - Filtres et tri

3. **Détails d'appartement :**
   - Informations complètes d'un appartement (ad_id)
   - Photos d'un appartement
   - Localisation/coordonnées
   - Description complète

4. **Métadonnées :**
   - Quartiers
   - Stations de métro
   - Types de biens

**Patterns d'URLs à chercher :**
```
/api/v1/alerts
/api/v2/alerts/{alert_id}/properties
/api/properties/{ad_id}
/api/properties/{ad_id}/photos
/api/search
/api/dashboard
/graphql (si GraphQL)
```

---

### 3.2 Reverse engineering des paramètres

**Pour chaque endpoint identifié, documenter :**

**Requête (Request) :**
- Méthode HTTP (GET/POST/PUT/DELETE)
- URL complète avec paramètres
- Headers requis
- Body (si POST/PUT)
- Query parameters
- Path parameters

**Réponse (Response) :**
- Structure JSON
- Codes de statut possibles
- Gestion des erreurs
- Rate limiting

**Exemple de documentation :**
```markdown
## GET /api/v2/alerts/{alert_id}/properties

**Description :** Récupère la liste des appartements d'une alerte

**Headers requis :**
- Authorization: Bearer {token}
- Cookie: session={session_id}

**Paramètres :**
- alert_id (path): ID de l'alerte
- page (query, optional): Numéro de page (défaut: 1)
- limit (query, optional): Nombre de résultats (défaut: 20)

**Réponse :**
```json
{
  "properties": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "has_more": true
  }
}
```
```

---

## 📋 Phase 4 : Création d'un Client API

### 4.1 Structure du client API

**Fichier à créer : `jinka_api_client.py`**

**Classes à créer :**

```python
class JinkaAPIClient:
    """Client pour l'API privée Jinka"""
    
    def __init__(self, email=None, password=None):
        """Initialise le client avec les credentials"""
        
    async def authenticate(self):
        """Authentifie l'utilisateur et récupère les tokens"""
        
    async def get_alert_properties(self, alert_id, page=1, limit=20):
        """Récupère les appartements d'une alerte"""
        
    async def get_property_details(self, ad_id):
        """Récupère les détails complets d'un appartement"""
        
    async def get_property_photos(self, ad_id):
        """Récupère les photos d'un appartement"""
        
    def _make_request(self, method, endpoint, **kwargs):
        """Méthode interne pour faire les requêtes HTTP"""
        
    def _refresh_token_if_needed(self):
        """Rafraîchit le token si nécessaire"""
```

---

### 4.2 Gestion des erreurs et rate limiting

**À implémenter :**
- Retry automatique sur erreurs réseau
- Détection du rate limiting (429)
- Backoff exponentiel
- Gestion des tokens expirés
- Logging des erreurs

**Code à ajouter :**
```python
async def _make_request_with_retry(self, method, endpoint, max_retries=3, **kwargs):
    """Fait une requête avec retry automatique"""
    for attempt in range(max_retries):
        try:
            response = await self._make_request(method, endpoint, **kwargs)
            if response.status == 429:
                wait_time = 2 ** attempt  # Backoff exponentiel
                await asyncio.sleep(wait_time)
                continue
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

---

### 4.3 Cache et optimisation

**Stratégies de cache :**
- Cache des tokens (éviter de reconnecter à chaque fois)
- Cache des données statiques (quartiers, métros)
- Cache des détails d'appartements (avec TTL)
- Utilisation de `aiohttp` avec session réutilisable

---

## 📋 Phase 5 : Migration du Scraper

### 5.1 Adapter `JinkaScraper` pour utiliser l'API

**Étapes :**
1. Créer une nouvelle classe `JinkaAPIScraper` qui utilise `JinkaAPIClient`
2. Conserver `JinkaScraper` comme fallback si l'API échoue
3. Adapter les méthodes existantes :
   - `scrape_alert_page()` → utilise `get_alert_properties()`
   - `scrape_apartment()` → utilise `get_property_details()`
   - `extract_photos()` → utilise `get_property_photos()`

**Avantages :**
- Plus rapide (pas de rendu HTML)
- Plus stable (moins fragile aux changements CSS)
- Moins de ressources (pas de navigateur)
- Plus facile à déboguer

---

### 5.2 Tests et validation

**Scripts de test à créer :**
- `test_jinka_api_client.py` - Tests unitaires du client API
- `test_api_vs_scraping.py` - Comparaison données API vs scraping
- `test_api_performance.py` - Benchmarks de performance

**Métriques à comparer :**
- Temps d'exécution
- Taux de succès
- Utilisation mémoire
- Utilisation CPU

---

## 📋 Phase 6 : Documentation et Maintenance

### 6.1 Documentation complète

**Fichiers à créer/mettre à jour :**

1. **`docs/api/jinka_api_reference.md`**
   - Liste complète des endpoints
   - Exemples d'utilisation
   - Codes d'erreur
   - Rate limits

2. **`docs/api/jinka_api_examples.py`**
   - Exemples de code pour chaque endpoint
   - Cas d'usage courants

3. **`docs/api/jinka_auth_flow.md`**
   - Diagramme de séquence du flow d'authentification
   - Gestion des tokens
   - Refresh automatique

---

### 6.2 Monitoring et alertes

**À implémenter :**
- Logging structuré des appels API
- Métriques de performance (temps de réponse, taux d'erreur)
- Alertes si l'API change (détection de breaking changes)
- Backup automatique des tokens/cookies

---

## 🛠️ Outils et Technologies

### Outils recommandés

1. **Interception réseau :**
   - Playwright (déjà utilisé)
   - Chrome DevTools HAR export
   - Mitmproxy (proxy HTTP)
   - Charles Proxy (optionnel)

2. **Analyse :**
   - `jq` pour parser JSON
   - `curl` pour tester les endpoints
   - Postman/Insomnia pour explorer l'API

3. **Client HTTP :**
   - `aiohttp` (asynchrone, déjà utilisé)
   - `httpx` (alternative moderne)

4. **Documentation :**
   - Markdown pour la doc
   - OpenAPI/Swagger si possible
   - Diagrammes (Mermaid)

---

## 📅 Plan d'Exécution

### Semaine 1 : Exploration
- [ ] Améliorer `explore_jinka_api.py`
- [ ] Capturer toutes les requêtes réseau
- [ ] Analyser manuellement avec DevTools
- [ ] Documenter les endpoints découverts

### Semaine 2 : Authentification
- [ ] Créer `analyze_jinka_auth.py`
- [ ] Documenter le flow d'authentification
- [ ] Implémenter la gestion des tokens
- [ ] Tester la réutilisation de session

### Semaine 3 : Client API
- [ ] Créer `jinka_api_client.py`
- [ ] Implémenter les endpoints principaux
- [ ] Gestion des erreurs et retry
- [ ] Tests unitaires

### Semaine 4 : Migration
- [ ] Adapter `JinkaScraper` pour utiliser l'API
- [ ] Tests de comparaison API vs scraping
- [ ] Migration progressive
- [ ] Documentation finale

---

## ⚠️ Considérations Légales et Éthiques

**Important :**
- Vérifier les Terms of Service de Jinka
- Respecter les rate limits
- Ne pas surcharger les serveurs
- Utiliser uniquement pour usage personnel/automatisation légitime
- Ne pas partager les tokens/credentials

**Bonnes pratiques :**
- Ajouter des délais entre les requêtes
- Respecter les headers `User-Agent`
- Ne pas bypasser les protections anti-bot
- Implémenter un cache pour réduire les requêtes

---

## 📝 Notes et Observations

### Points d'attention

1. **Sécurité :**
   - Les tokens peuvent expirer rapidement
   - Les cookies peuvent être liés à une session navigateur
   - Certains endpoints peuvent nécessiter des headers spécifiques

2. **Stabilité :**
   - L'API peut changer sans préavis
   - Certains endpoints peuvent être privés/internes
   - Garder le scraping comme fallback

3. **Performance :**
   - L'API peut être plus rapide mais avec des limites
   - Le scraping peut être plus lent mais plus flexible
   - Évaluer selon les besoins

---

## 🎯 Résultats Attendus

À la fin de ce plan, vous devriez avoir :

1. ✅ Une documentation complète de l'API Jinka
2. ✅ Un client API fonctionnel (`jinka_api_client.py`)
3. ✅ Un scraper migré utilisant l'API au lieu du HTML
4. ✅ Des tests validant la migration
5. ✅ Une amélioration des performances (3-5x plus rapide estimé)
6. ✅ Une meilleure stabilité (moins de breaking changes)

---

## 📚 Ressources et Références

- [Playwright Network Interception](https://playwright.dev/python/docs/network)
- [Reverse Engineering APIs Guide](https://www.apisec.ai/blog/api-reverse-engineering)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [HAR Format Specification](http://www.softwareishard.com/blog/har-12-spec/)

---

**Dernière mise à jour :** 2024-01-XX
**Auteur :** HomeScore Team
**Statut :** Plan initial - À exécuter



