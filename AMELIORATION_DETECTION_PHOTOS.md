# Amélioration de la détection des photos

## Problème identifié

D'après l'inspection des pages Jinka, deux types d'appartements sans photos ont été identifiés :

1. **Appartements avec placeholders FNAIM** :
   - Images avec `alt="preloader"`
   - URLs de type `https://imagesv2.fnaim.fr/images1/img/68ffd5c.....jpg`
   - Ces images sont des placeholders génériques, pas de vraies photos

2. **Appartements avec proxy Jinka** :
   - Images utilisant le proxy Jinka : `https://api.jinka.fr/apiv2/media/imgsrv?url=...`
   - Les vraies photos passent par ce proxy mais pointent vers des URLs originales comme `photos.ubif`
   - Ces images doivent être acceptées comme de vraies photos

## Améliorations apportées

### 1. Filtrage des placeholders FNAIM

Le code détecte maintenant et exclut :
- URLs contenant `imagesv2.fnaim.fr/images1/img/` (pattern placeholder FNAIM)
- Images avec `alt="preloader"` ET URL placeholder FNAIM
- Autres patterns de placeholders : `placeholder`, `no-image`, `default-image`, etc.

### 2. Support du proxy Jinka

Le code accepte maintenant :
- URLs avec `api.jinka.fr/apiv2/media/imgsrv` (proxy Jinka)
- URLs contenant `photos.ubif` (photos originales via proxy)
- URLs Cloudinary (`res.cloudinary.com`, `cloudinary.com`)

### 3. Patterns de photos étendus

Ajout de nouveaux patterns pour détecter les vraies photos :
- `api.jinka.fr/apiv2/media/imgsrv` - Proxy Jinka
- `photos.ubif` - Photos via proxy Jinka
- `res.cloudinary.com` - Cloudinary
- `cloudinary.com` - Cloudinary
- `photos.` - Pattern générique pour photos

### 4. Double vérification

Le code vérifie maintenant :
1. L'URL de l'image (exclut les placeholders)
2. L'attribut `alt` (exclut les preloaders si c'est un placeholder FNAIM)
3. Les patterns de vraies photos (accepte seulement les patterns valides)

## Fichiers modifiés

- `scrape_jinka.py` - Fonction `extract_photos()` améliorée avec :
  - Filtrage JavaScript amélioré dans la galerie
  - Filtrage Python amélioré pour les images visibles
  - Filtrage Python amélioré pour les images lazy-loaded

## Tests recommandés

Pour tester les améliorations :

```bash
# Tester le rescraping des appartements sans photos
python rescrape_missing_photos.py
```

Les appartements avec placeholders FNAIM ne devraient plus être détectés comme ayant des photos.

## Cas d'usage

### Cas 1 : Appartement avec placeholder FNAIM
- **Avant** : Détecté comme ayant des photos (à tort)
- **Après** : Correctement identifié comme sans photos

### Cas 2 : Appartement avec proxy Jinka
- **Avant** : Peut ne pas détecter les photos via proxy
- **Après** : Détecte correctement les photos via proxy Jinka

### Cas 3 : Appartement avec preloader mais vraie photo
- **Avant** : Peut exclure de vraies photos avec alt="preloader"
- **Après** : Accepte les vraies photos même avec alt="preloader" (sauf si placeholder FNAIM)





