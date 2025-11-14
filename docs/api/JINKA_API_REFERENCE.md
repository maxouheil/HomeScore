# Référence API Jinka - Documentation Complète

**Date de génération :** 2025-11-05  
**Source :** Reverse engineering depuis l'exploration réseau

---

## 🎯 Vue d'Ensemble

**Base URL :** `https://api.jinka.fr/apiv2/`

**Authentification :** JWT Token (Bearer Token dans header `Authorization` + Cookie `LA_API_TOKEN`)

**Format des réponses :** JSON

---

## 🔐 Authentification

### Mécanisme

L'API utilise un **JWT Token** stocké dans :
1. **Cookie** : `LA_API_TOKEN` (accessible depuis JavaScript)
2. **Header** : `Authorization: Bearer {token}` (recommandé)

### Token JWT

Le token contient :
```json
{
  "id": 879001,
  "email": "souheil.medaghri@gmail.com",
  "created_at": "2022-12-25T12:13:30.000Z",
  "iat": 1762349458,
  "exp": 1764941458
}
```

**Durée de validité :** ~30 jours (1764941458 - 1762349458 = 2592000 secondes)

### Endpoints d'Authentification

#### `POST /api/auth/callback/email-code-signin`

Connexion avec code email.

**Body (form-data) :**
```
email=souheil.medaghri%40gmail.com
code=0588
redirect=false
csrfToken={csrf_token}
callbackUrl=https%3A%2F%2Fwww.jinka.fr%2Fsign%2Fin%2Femail
json=true
```

**Réponse :** Redirection + cookies de session

#### `GET /api/auth/session`

Récupère la session utilisateur actuelle.

**Réponse :**
```json
{
  "user": {
    "id": 879001,
    "email": "souheil.medaghri@gmail.com"
  }
}
```

---

## 📋 Endpoints Principaux

### 1. Configuration

#### `GET /apiv2/config`

Récupère la configuration générale (agglomérations, etc.).

**Headers requis :**
- `Cookie: LA_API_TOKEN={token}` (optionnel)

**Réponse :**
```json
{
  "agglomerations": [
    {
      "value": "paris",
      "postalCodes": ["75", "77", "78", "91", "92", "93", "94", "95"],
      "label": "Ile-de-France",
      "label_extended": "Ile-de-France",
      "illu": "https://res.cloudinary.com/loueragile/image/upload/...",
      "placeholderInput": "Villes, Codes postaux, Métros, RER",
      "placeholderDesc": "Vous pouvez ajouter plusieurs villes...",
      "latLng": [48.864716, 2.349014]
    }
    // ... 100 autres agglomérations
  ],
  "last_build_available": 1234567890
}
```

---

### 2. Utilisateur

#### `GET /apiv2/user/authenticated`

Vérifie si l'utilisateur est authentifié.

**Headers requis :**
- `Authorization: Bearer {token}`
- `Cookie: LA_API_TOKEN={token}`

**Réponse :**
```json
{
  "result": true,
  "email": "souheil.medaghri@gmail.com",
  "name": null,
  "email_editing": null,
  "id": 879001,
  "isOwner": false,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "active": true,
  "mobilipass_infos": null,
  "settings": {
    "has_seen_option_display": false,
    "ad_expired_hidden": true,
    "has_alert_settings_advanced": false,
    "suggestion_blocked": false
  },
  "has_partner_optin": true
}
```

---

### 3. Alertes

#### `GET /apiv2/alert`

Récupère la liste des alertes de l'utilisateur.

**Headers requis :**
- `Authorization: Bearer {token}`
- `Cookie: LA_API_TOKEN={token}`

**Réponse :**
```json
[
  {
    "id": "26c2ec3064303aa68ffa43f7c6518733",
    "user_id": 879001,
    "email": "s...s@gmail.com",
    "created_at": "2025-02-22T12:10:50.000Z",
    "search_type": "for_buy",
    "rent_max": 850000,
    "rent_min": 700000,
    "area_min": 60,
    "area_max": 100,
    "room_min": 3,
    "room_max": 3,
    "bedroom_min": 2,
    "token": "26c2ec3064303aa68ffa43f7c6518733",
    "state": "OFFERED",
    "agglomeration": "paris",
    "stops": [
      {
        "name": "Alexandre-Dumas",
        "ids": ["2041"],
        "lines": ["Ligne 2"],
        "line_ordered": [
          {
            "line_id": "Ligne 2",
            "stop_id": "2041"
          }
        ]
      }
    ]
  }
]
```

---

#### `GET /apiv2/alert/{alert_token}/dashboard`

Récupère le dashboard d'une alerte avec la liste des appartements.

**Paramètres de requête :**
- `filter` : `all` | `new` | `favorite` | etc.
- `page` : Numéro de page (défaut: 1)
- `rrkey` : Clé de pagination (optionnel)
- `sorting` : Tri (optionnel)

**Headers requis :**
- `Authorization: Bearer {token}`
- `Cookie: LA_API_TOKEN={token}`

**Exemple :**
```
GET /apiv2/alert/26c2ec3064303aa68ffa43f7c6518733/dashboard?filter=all&page=1&rrkey=d4y30v&sorting=
```

**Réponse :**
```json
{
  "alert": {
    "id": "26c2ec3064303aa68ffa43f7c6518733",
    "user_id": 879001,
    "token": "26c2ec3064303aa68ffa43f7c6518733",
    "rent_max": 850000,
    "rent_min": 700000,
    "area_min": 60,
    "area_max": 100,
    "room_min": 3,
    "room_max": 3,
    "bedroom_min": 2,
    "agglomeration": "paris",
    "stops": [...]
  },
  "ads": [
    {
      "id": "90931157",
      "uuid": "c40c9fa4-f497-4f1a-9ed6-58934fa932db",
      "favorite": false,
      "rent": 775000,
      "type": "Appartement",
      "area": 70,
      "room": 3,
      "bedroom": 2,
      "floor": 4,
      "lat": 48.8767,
      "lng": 2.38578,
      "city": "Paris 19e",
      "postal_code": "75019",
      "quartier_name": "Combat",
      "images": "https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/42f489c1-625e-41fa-b3aa-c66a23bcf7e2.png,...",
      "stops": [
        {
          "id": 1758,
          "name": "Pyrénées",
          "lines": ["Ligne 11"]
        }
      ],
      "features": {
        "lift": 0,
        "shower": 0,
        "bath": null,
        "parking": 0,
        "balcony": 0,
        "cave": 0,
        "garden": 0
      },
      "description": "Globalstone vous propose...",
      "source": "globalstone",
      "source_label": "Globalstone",
      "source_logo": "https://loueragile-media.s3.eu-west-3.amazonaws.com/source_logos/logo-globalstone.png",
      "owner_type": "Agence",
      "buy_type": "new",
      "created_at": "2025-10-24T15:08:59.000Z",
      "price_sector": 8448.28
    }
    // ... autres appartements
  ],
  "pagination": {
    "page": 1,
    "per_page": 24,
    "total": 150,
    "has_more": true,
    "next_rrkey": "d4y30v"
  }
}
```

---

### 4. Détails d'Appartement

#### `GET /apiv2/alert/{alert_token}/ad/{ad_id}`

Récupère les détails complets d'un appartement.

**Headers requis :**
- `Authorization: Bearer {token}`
- `Cookie: LA_API_TOKEN={token}`

**Exemple :**
```
GET /apiv2/alert/26c2ec3064303aa68ffa43f7c6518733/ad/90931157
```

**Réponse :**
```json
{
  "alert": {
    // Même structure que dans /dashboard
  },
  "ad": {
    "id": "90931157",
    "uuid": "c40c9fa4-f497-4f1a-9ed6-58934fa932db",
    "favorite": false,
    "favorite_id": null,
    "fees": {
      "honorais_charges_de": "Vendeur"
    },
    "rent": 775000,
    "type": "Appartement",
    "area": 70,
    "room": 3,
    "bedroom": 2,
    "floor": 4,
    "lat": 48.8767,
    "lng": 2.38578,
    "city": "Paris 19e",
    "postal_code": "75019",
    "quartier_name": "Combat",
    "quartier": null,
    "images": "https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/42f489c1-625e-41fa-b3aa-c66a23bcf7e2.png,https://...",
    "stops": [
      {
        "id": 1758,
        "name": "Pyrénées",
        "lines": ["Ligne 11"]
      },
      {
        "id": 1905,
        "name": "Jourdain",
        "lines": ["Ligne 11"]
      }
    ],
    "features": {
      "id": 90931157,
      "lift": 0,
      "shower": 0,
      "bath": null,
      "year": null,
      "parking": 0,
      "box": null,
      "balcony": 0,
      "terracy": 0,
      "cave": 0,
      "garden": 0
    },
    "is_coliving": 0,
    "furnished": 0,
    "description": "Globalstone vous propose en exclusivité...",
    "description_is_truncated": false,
    "should_reduce_info": false,
    "source": "globalstone",
    "source_is_partner": 1,
    "source_is_subscribed": true,
    "source_has_contact": true,
    "source_logo": "https://loueragile-media.s3.eu-west-3.amazonaws.com/source_logos/logo-globalstone.png",
    "source_label": "Globalstone",
    "source_description": "Cette agence est partenaire de Jinka.",
    "search_type": "for_buy",
    "owner_type": "Agence",
    "buy_type": "new",
    "rentMinPerM2": null,
    "created_at": "2025-10-24T15:08:59.000Z",
    "expired_at": null,
    "nb_spam": 0,
    "webview_link": null,
    "spam_content_warning": false,
    "reported_error": false,
    "land_area": null,
    "coduminium_lots": null,
    "coduminium_charges": null,
    "coduminium_pending_prejudice": null,
    "coduminum_pending_prejudice_details": null,
    "dpe_infos": null,
    "high_demand": 0,
    "agency_siret": "80056456900021",
    "should_open_browser": false,
    "price_sector": 8448.27586206897,
    "sendDate": "2025-10-24T15:08:59.000Z"
  }
}
```

---

### 5. Informations de Contact

#### `GET /apiv2/ad/{ad_id}/contact_info`

Récupère les informations de contact pour un appartement.

**Headers requis :**
- `Authorization: Bearer {token}`
- `Cookie: LA_API_TOKEN={token}`

**Exemple :**
```
GET /apiv2/ad/90931157/contact_info
```

**Réponse :**
```json
{
  "mode": "inapp",
  "phone": "06 38 83 38 76",
  "agency_name": "Globalstone",
  "redirect_url": "https://pro.jinka.fr/api/crawler?id=3123395610&secret=lesecretducrawlerdejinka&id=T3DUPFES²",
  "message_form": "form_buy"
}
```

---

## 📊 Structures de Données

### Objet Alert

```typescript
interface Alert {
  id: string;
  user_id: number;
  email: string;
  created_at: string;  // ISO 8601
  search_type: "for_buy" | "for_rent";
  rent_max: number | null;
  rent_min: number | null;
  area_min: number | null;
  area_max: number | null;
  room_min: number | null;
  room_max: number | null;
  bedroom_min: number | null;
  agglomeration: string;
  token: string;
  state: "OFFERED" | "EXPIRED" | ...;
  stops: Stop[];
  // ... autres champs
}
```

### Objet Ad (Appartement)

```typescript
interface Ad {
  id: string;
  uuid: string;
  favorite: boolean;
  rent: number;
  type: string;
  area: number;
  room: number;
  bedroom: number;
  floor: number | null;
  lat: number;
  lng: number;
  city: string;
  postal_code: string;
  quartier_name: string | null;
  images: string;  // URLs séparées par des virgules
  stops: Stop[];
  features: Features;
  description: string;
  source: string;
  source_label: string;
  source_logo: string;
  owner_type: "Agence" | "Particulier";
  buy_type: "new" | "old" | null;
  created_at: string;
  price_sector: number;
  // ... autres champs
}
```

### Objet Stop (Station de métro)

```typescript
interface Stop {
  id: number;
  name: string;
  lines: string[];  // ["Ligne 11", "Ligne 7bis"]
}
```

### Objet Features

```typescript
interface Features {
  id: number;
  lift: 0 | 1;
  shower: 0 | 1;
  bath: number | null;
  year: number | null;
  parking: 0 | 1;
  box: number | null;
  balcony: 0 | 1;
  terracy: 0 | 1;
  cave: 0 | 1;
  garden: 0 | 1;
}
```

### Objet Pagination

```typescript
interface Pagination {
  page: number;
  per_page: number;
  total: number;
  has_more: boolean;
  next_rrkey?: string;
}
```

---

## 🔧 Headers Requis

Pour toutes les requêtes authentifiées :

```http
Authorization: Bearer {jwt_token}
Cookie: LA_API_TOKEN={jwt_token}
Origin: https://www.jinka.fr
Referer: https://www.jinka.fr/
Accept: application/json
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
```

---

## ⚠️ Codes d'Erreur

- **200** : Succès
- **401** : Non authentifié (token manquant ou expiré)
- **403** : Accès interdit
- **404** : Ressource non trouvée
- **429** : Rate limiting (trop de requêtes)

**Format d'erreur :**
```json
{
  "success": false,
  "message": "No authorization token was found",
  "error": "No authorization token was found"
}
```

---

## 🚀 Exemples d'Utilisation

### Python avec aiohttp

```python
import aiohttp

async def get_alert_dashboard(token, alert_token, page=1):
    headers = {
        'Authorization': f'Bearer {token}',
        'Cookie': f'LA_API_TOKEN={token}',
        'Origin': 'https://www.jinka.fr',
        'Referer': 'https://www.jinka.fr/',
    }
    
    url = f'https://api.jinka.fr/apiv2/alert/{alert_token}/dashboard'
    params = {
        'filter': 'all',
        'page': page,
        'rrkey': '',
        'sorting': ''
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Error {response.status}: {await response.text()}")
```

### curl

```bash
curl -X GET \
  "https://api.jinka.fr/apiv2/alert/26c2ec3064303aa68ffa43f7c6518733/dashboard?filter=all&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Cookie: LA_API_TOKEN=YOUR_TOKEN" \
  -H "Origin: https://www.jinka.fr" \
  -H "Referer: https://www.jinka.fr/"
```

---

## 📝 Notes Importantes

1. **Token JWT** : Le token est valide pendant ~30 jours. Il faut le rafraîchir après expiration.

2. **Pagination** : Utiliser le paramètre `rrkey` pour la pagination suivante. Il est retourné dans `pagination.next_rrkey`.

3. **Rate Limiting** : L'API peut limiter le nombre de requêtes. En cas d'erreur 429, attendre avant de réessayer.

4. **Images** : Les URLs d'images sont séparées par des virgules dans le champ `images`.

5. **Coordonnées** : `lat` et `lng` sont toujours présents pour localiser l'appartement.

6. **Stations de métro** : Le champ `stops` contient toutes les stations à proximité avec leurs lignes.

---

## 🔗 Fichiers de Référence

- **Exploration complète** : `data/api_exploration/responses_20251105_143129.json`
- **Structures détaillées** : `data/api_exploration/api_responses_detailed.json`
- **Rapport** : `data/api_exploration/api_structures_report.md`

---

**Dernière mise à jour :** 2025-11-05



