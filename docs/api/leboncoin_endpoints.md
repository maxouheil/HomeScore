# Documentation des Endpoints API LeBonCoin

## Vue d'ensemble

Cette documentation décrit les endpoints API découverts pour LeBonCoin via reverse engineering. Les endpoints sont identifiés en interceptant les requêtes réseau lors de la navigation sur le site.

## Base URL

- **Site web**: `https://www.leboncoin.fr`
- **API**: `https://api.leboncoin.fr` (à confirmer lors de l'exploration)

## Authentification

### Mécanisme

L'authentification LeBonCoin utilise probablement :
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
- `category`: Catégorie (9 = Locations immobilières)
- `real_estate_type`: Type de bien (2 = Appartement)
- `locations`: Localisation (ex: "Paris")
- `min_price`: Prix minimum
- `max_price`: Prix maximum
- `rooms`: Nombre de pièces (ex: "2-3-4")
- `page`: Numéro de page
- `limit`: Nombre de résultats par page

**Réponse** (exemple):
```json
{
  "ads": [
    {
      "ad_id": "...",
      "subject": "...",
      "price": [1500],
      "surface": 50,
      "rooms": 2,
      "location": {...},
      "images": {...}
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

**Endpoint**: `/api/ads/{ad_id}` (à confirmer)

**Méthode**: `GET`

**Réponse** (exemple):
```json
{
  "ad_id": "...",
  "subject": "...",
  "body": "...",
  "price": [1500],
  "surface": 50,
  "rooms": 2,
  "location": {
    "city": "...",
    "zipcode": "...",
    "region": "..."
  },
  "images": {
    "thumb_url": "...",
    "urls": [...]
  },
  "attributes": [...]
}
```

### Photos d'une annonce

**Endpoint**: `/api/ads/{ad_id}/photos` (à confirmer)

**Méthode**: `GET`

**Réponse** (exemple):
```json
{
  "images": {
    "thumb_url": "...",
    "urls": [
      "https://...",
      "https://..."
    ]
  }
}
```

## Notes importantes

⚠️ **Ces endpoints sont des estimations basées sur les patterns communs. Ils doivent être confirmés lors de l'exploration réelle avec `explore_leboncoin_api.py`.**

## Prochaines étapes

1. Exécuter `explore_leboncoin_api.py` pour capturer les vraies requêtes
2. Analyser les fichiers générés dans `data/api_exploration/leboncoin/`
3. Mettre à jour cette documentation avec les vrais endpoints
4. Adapter `leboncoin_api_client.py` avec les endpoints réels

## Références

- [Guide d'exploration](GUIDE_REVERSE_ENGINEER_LEBONCOIN.md)
- [Client API](../leboncoin_api_client.py)
- [Scraper](../scrape_leboncoin.py)



