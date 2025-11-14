# Récapitulatif : Photos - Scraping HTML vs API

**Date :** 2025-11-05  
**Focus :** Comparaison détaillée de l'extraction des photos

---

## 📸 Photos Actuellement Récupérées (Scraping HTML)

### Format Actuel

```json
{
  "photos": [
    {
      "url": "https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/42f489c1-625e-41fa-b3aa-c66a23bcf7e2.png",
      "alt": "70 m² · 4e étage · Contemporain",
      "selector": "gallery_div",
      "width": 1600,
      "height": 1200
    },
    {
      "url": "https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/1131ac6e-e19f-4849-9943-4c9ff739c50d.png",
      "alt": "70 m² · 4e étage · Contemporain",
      "selector": "gallery_div",
      "width": 1600,
      "height": 1200
    }
    // ... autres photos
  ]
}
```

### Ce Qu'on Récupère avec le Scraping

| Propriété | Source | Format | Notes |
|-----------|--------|--------|-------|
| **URL** | DOM `<img src>` | `string` | ✅ URLs complètes |
| **Alt text** | DOM `<img alt>` | `string` | ⚠️ Souvent "preloader" ou généré |
| **Selector** | Origine extraction | `string` | ✅ Info de debug |
| **Width** | DOM `naturalWidth` | `number` | ✅ Dimensions réelles |
| **Height** | DOM `naturalHeight` | `number` | ✅ Dimensions réelles |
| **Ordre** | Position DOM | `array` | ⚠️ Préservation ordre complexe |
| **Lazy loading** | `data-src` | Détecté | ✅ Gestion lazy loading |

### Complexité du Scraping

**Extraction très complexe avec :**
1. ✅ Parsing DOM multi-sélecteurs (galerie visible + cachée)
2. ✅ Gestion lazy loading (`data-src`, `data-lazy-src`)
3. ✅ Filtrage placeholders (FNAIM, etc.)
4. ✅ Préservation ordre (visible + cachées)
5. ✅ Détection dimensions (exclure logos < 200px)
6. ✅ Déduplication par URL
7. ✅ Génération alt text custom (surface + étage + style)

**Points fragiles :**
- ⚠️ Sélecteurs CSS fragiles (changent souvent)
- ⚠️ Gestion complexe photos cachées/visibles
- ⚠️ Filtrage placeholders heuristique
- ⚠️ Ordre peut être incorrect si lazy loading

---

## 📡 Photos Disponibles via API

### Format API

```json
{
  "ad": {
    "images": "https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/42f489c1-625e-41fa-b3aa-c66a23bcf7e2.png,https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/1131ac6e-e19f-4849-9943-4c9ff739c50d.png,https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/75e310f1-1168-4952-8137-3113077f24fc.png,..."
  }
}
```

### Ce Qu'on Récupère avec l'API

| Propriété | Format | Disponibilité | Notes |
|-----------|--------|---------------|-------|
| **URLs** | `string` (CSV) | ✅ Direct | URLs séparées par virgules |
| **Ordre** | Ordre dans CSV | ✅ Préservé | Ordre officiel Jinka |
| **Alt text** | ❌ Non disponible | ❌ | Perdu |
| **Dimensions** | ❌ Non disponible | ❌ | Perdu |
| **Lazy loading** | ✅ Pas nécessaire | ✅ | URLs directes |

### Conversion Nécessaire

Pour utiliser les photos de l'API, il faut :

```python
# API retourne : string CSV
images_csv = "url1,url2,url3"

# Conversion en array
photos = [
    {"url": url.strip()} 
    for url in images_csv.split(',') 
    if url.strip()
]
```

---

## 🔄 Comparaison Détaillée

### 1. URLs des Photos

| Aspect | Scraping HTML | API | Avantage |
|--------|---------------|-----|----------|
| **Format** | Array d'objets | String CSV | **Scraping** (déjà structuré) |
| **Simplicité** | Parsing DOM complexe | Split simple | **API** (beaucoup plus simple) |
| **Fiabilité** | Fragile (sélecteurs CSS) | Stable | **API** (pas de dépendance DOM) |
| **Complétude** | Filtrage nécessaire | Toutes les photos | **API** (pas de filtrage) |

### 2. Ordre des Photos

| Aspect | Scraping HTML | API | Avantage |
|--------|---------------|-----|----------|
| **Préservation** | Position DOM (complexe) | Ordre CSV | **API** (ordre officiel) |
| **Fiabilité** | Peut être incorrect | Garanti correct | **API** |
| **Lazy loading** | Impact sur ordre | Pas d'impact | **API** |

### 3. Métadonnées

| Aspect | Scraping HTML | API | Avantage |
|--------|---------------|-----|----------|
| **Alt text** | ✅ Disponible (DOM) | ❌ Non disponible | **Scraping** |
| **Dimensions** | ✅ Disponible (DOM) | ❌ Non disponible | **Scraping** |
| **Selector** | ✅ Info debug | ❌ Non disponible | **Scraping** (peu utile) |

### 4. Performance

| Aspect | Scraping HTML | API | Avantage |
|--------|---------------|-----|----------|
| **Vitesse** | Lent (parse DOM) | Rapide (split string) | **API** (10x+ plus rapide) |
| **Ressources** | Navigateur requis | HTTP simple | **API** |
| **Stabilité** | Fragile aux changements | Stable | **API** |

---

## ✅ Avantages de l'API

1. **Simplicité** ✅
   - Split simple d'une string CSV
   - Pas de parsing DOM complexe
   - Pas de gestion lazy loading

2. **Fiabilité** ✅
   - Ordre garanti correct
   - Pas de filtrage nécessaire
   - Pas de dépendance aux sélecteurs CSS

3. **Performance** ✅
   - 10x+ plus rapide
   - Pas de rendu HTML
   - Moins de ressources

4. **Stabilité** ✅
   - Pas de breaking changes CSS
   - Données officielles

---

## ❌ Inconvénients de l'API

1. **Pas d'alt text** ❌
   - Scraping : Alt text du DOM
   - API : Non disponible
   - Impact : **Faible** (peut être généré si nécessaire)

2. **Pas de dimensions** ❌
   - Scraping : Width/Height depuis DOM
   - API : Non disponible
   - Impact : **Moyen** (peut être récupéré depuis headers HTTP)

3. **Format CSV** ⚠️
   - Nécessite conversion en array
   - Impact : **Très faible** (split simple)

---

## 🎯 Solution Hybride Recommandée

### Utiliser l'API pour les URLs

```python
# 1. Récupérer depuis API
images_csv = api_data['ad']['images']  # "url1,url2,url3"

# 2. Convertir en array
photo_urls = [url.strip() for url in images_csv.split(',') if url.strip()]

# 3. Optionnel : Récupérer dimensions depuis headers HTTP
photos = []
for url in photo_urls:
    photo = {'url': url}
    
    # Optionnel : Récupérer dimensions
    async with session.head(url) as response:
        # Headers peuvent contenir dimensions si disponibles
        pass
    
    photos.append(photo)
```

### Générer Alt Text si Nécessaire

```python
# Générer alt text depuis données API
def generate_photo_alt(ad_data, index):
    """Génère un alt text pour une photo"""
    surface = ad_data.get('area', '')
    floor = ad_data.get('floor')
    style = detect_style_from_description(ad_data.get('description', ''))
    
    parts = []
    if surface:
        parts.append(f"{surface} m²")
    if floor is not None:
        parts.append(f"{floor}e étage" if floor > 1 else "1er étage")
    if style:
        parts.append(style)
    
    return " · ".join(parts) if parts else f"Photo {index + 1}"
```

---

## 📊 Tableau Synthétique Photos

| Critère | Scraping HTML | API | Gagnant |
|---------|---------------|-----|---------|
| **Simplicité extraction** | ⚠️ Complexe (500+ lignes) | ✅ Simple (split CSV) | **API** |
| **Fiabilité URLs** | ⚠️ Filtrage nécessaire | ✅ Toutes valides | **API** |
| **Ordre photos** | ⚠️ Peut être incorrect | ✅ Ordre officiel | **API** |
| **Performance** | ⚠️ Lent (DOM parsing) | ✅ Rapide (string) | **API** |
| **Stabilité** | ⚠️ Fragile (CSS changes) | ✅ Stable | **API** |
| **Alt text** | ✅ Disponible | ❌ Non disponible | **Scraping** |
| **Dimensions** | ✅ Disponible | ❌ Non disponible | **Scraping** |
| **Métadonnées** | ✅ Complètes | ⚠️ Minimales | **Scraping** |

---

## 💡 Recommandation pour les Photos

### ✅ Utiliser l'API pour les URLs

**Avantages :**
- ✅ **Simplicité** : Split CSV vs 500+ lignes de parsing DOM
- ✅ **Fiabilité** : Ordre garanti, pas de filtrage nécessaire
- ✅ **Performance** : 10x+ plus rapide
- ✅ **Stabilité** : Pas de breaking changes CSS

**Inconvénients :**
- ❌ Pas d'alt text (peut être généré)
- ❌ Pas de dimensions (peut être récupéré depuis HTTP headers)

### 🔧 Solution pour Données Manquantes

1. **Alt text** : Générer depuis `area`, `floor`, `description`
2. **Dimensions** : Optionnel - récupérer depuis HTTP `HEAD` request
3. **Ordre** : Préservé dans le CSV de l'API

---

## 📝 Exemple de Migration

### Avant (Scraping HTML)

```python
# 500+ lignes de code complexe
photos = await self.extract_photos()  # Parsing DOM complexe
# Résultat : [{url, alt, selector, width, height}, ...]
```

### Après (API)

```python
# Simple et rapide
images_csv = api_data['ad']['images']
photos = [
    {
        'url': url.strip(),
        'alt': generate_photo_alt(api_data['ad'], i),  # Généré
        'width': None,  # Optionnel : récupérer depuis HTTP
        'height': None  # Optionnel : récupérer depuis HTTP
    }
    for i, url in enumerate(images_csv.split(','))
    if url.strip()
]
```

---

## ✅ Conclusion pour les Photos

**Migration recommandée :** ✅ **OUI**

**Raisons :**
1. ✅ **Simplicité** : Split CSV vs parsing DOM complexe
2. ✅ **Fiabilité** : Ordre garanti, toutes les photos
3. ✅ **Performance** : 10x+ plus rapide
4. ✅ **Stabilité** : Pas de dépendance CSS

**Données perdues :**
- ❌ Alt text (peut être généré)
- ❌ Dimensions (peut être récupéré depuis HTTP headers)

**Impact :** **Faible** - Les données perdues peuvent être complétées facilement

---

**Dernière mise à jour :** 2025-11-05



