# Documentation des Endpoints API SeLoger

## Vue d'ensemble

Cette documentation décrit les endpoints API découverts pour SeLoger via reverse engineering. Les endpoints sont identifiés en interceptant les requêtes réseau lors de la navigation sur le site.

## Base URL

- **Site web**: `https://www.seloger.com`
- **API**: `https://api.seloger.com` (à confirmer lors de l'exploration)

## Authentification

### Mécanisme

L'authentification SeLoger utilise probablement :
- Cookies de session
- Tokens d'authentification dans les headers
- Possiblement OAuth pour les utilisateurs connectés

### Headers requis

```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
Accept: application/json
Cookie: session=...
```

## Endpoints (À compléter après exploration)

### Recherche d'annonces

**Endpoint**: `/api/search` (à confirmer)

**Méthode**: `GET`

**Paramètres**:
- `location`: Localisation (ex: "Paris")
- `type`: Type de bien (ex: "appartement")
- `min_price`: Prix minimum
- `max_price`: Prix maximum
- `min_surface`: Surface minimum (m²)
- `max_surface`: Surface maximum (m²)
- `rooms`: Nombre de pièces (ex: "2,3,4")
- `page`: Numéro de page
- `limit`: Nombre de résultats par page

**Réponse** (exemple):
```json
{
  "properties": [
    {
      "id": "...",
      "title": "...",
      "price": 1500,
      "surface": 50,
      "rooms": 2,
      "location": {...},
      "photos": [...]
    }
  ],
  "pagination": {
    "page": 1,
    "total": 100,
    "has_more": true
  }
}
```

### Détails d'une annonce

**Endpoint**: `/api/properties/{property_id}` (à confirmer)

**Méthode**: `GET`

**Réponse** (exemple):
```json
{
  "id": "...",
  "title": "...",
  "description": "...",
  "price": 1500,
  "surface": 50,
  "rooms": 2,
  "location": {
    "address": "...",
    "city": "...",
    "postal_code": "..."
  },
  "photos": [...],
  "features": [...]
}
```

### Photos d'une annonce

**Endpoint**: `/api/properties/{property_id}/photos` (à confirmer)

**Méthode**: `GET`

**Réponse** (exemple):
```json
{
  "photos": [
    "https://...",
    "https://..."
  ]
}
```

## Notes importantes

⚠️ **Ces endpoints sont des estimations basées sur les patterns communs. Ils doivent être confirmés lors de l'exploration réelle avec `explore_seloger_api.py`.**

## Prochaines étapes

1. Exécuter `explore_seloger_api.py` pour capturer les vraies requêtes
2. Analyser les fichiers générés dans `data/api_exploration/seloger/`
3. Mettre à jour cette documentation avec les vrais endpoints
4. Adapter `seloger_api_client.py` avec les endpoints réels

## Références

- [Guide d'exploration](GUIDE_REVERSE_ENGINEER_SELOGER.md)
- [Client API](../seloger_api_client.py)
- [Scraper](../scrape_seloger.py)



