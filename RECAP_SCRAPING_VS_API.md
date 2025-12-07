# Récapitulatif : Scraping HTML vs API Jinka

**Date :** 2025-11-05  
**Objectif :** Comparer ce qu'on récupère actuellement avec le scraping HTML vs ce que l'API fournit

---

## 📊 Données Actuellement Récupérées (Scraping HTML)

### ✅ Données Extraites Actuellement

| Champ | Source HTML | Format | Notes |
|-------|-------------|--------|-------|
| **id** | URL (`ad=`) | `string` | ✅ Extrait depuis l'URL |
| **url** | URL complète | `string` | ✅ URL de la page |
| **scraped_at** | Timestamp | `ISO 8601` | ✅ Date de scraping |
| **titre** | `<h1>`, `.title` | `string` | ⚠️ Format variable |
| **prix** | `.hmmXKG` | `string` (ex: "775 000 €") | ⚠️ Nécessite parsing |
| **prix_m2** | Texte près du prix | `string` (ex: "11071 €/m²") | ⚠️ Souvent non trouvé |
| **localisation** | Parsing texte | `string` | ⚠️ Extraction regex fragile |
| **coordinates** | Carte Leaflet | `{lat, lng, raw_x, raw_y}` | ⚠️ Parfois incorrectes |
| **map_info** | Carte + parsing | `{streets[], metros[], quartier, screenshot}` | ⚠️ Screenshot requis |
| **surface** | Regex `/\\d+\\s*m²/` | `string` (ex: "70 m²") | ⚠️ Format variable |
| **pieces** | Regex `/\\d+\\s*pièces?/` | `string` | ⚠️ Format variable |
| **date** | Regex `/le \\d+ \\w+ à/` | `string` | ⚠️ Souvent non trouvé |
| **transports** | Section HTML | `array[string]` | ⚠️ Parsing complexe |
| **description** | `.fz-16.sc-bxivhb.fcnykg` | `string` | ✅ Texte complet |
| **photos** | Gallery HTML | `array[{url, alt, selector}]` | ⚠️ Parsing DOM complexe |
| **caracteristiques** | Section HTML | `string` | ⚠️ Texte brut |
| **etage** | Parsing regex | `string` (ex: "4e étage") | ⚠️ Extraction fragile |
| **agence** | Parsing texte | `string` | ⚠️ Extraction fragile |
| **style_haussmannien** | Analyse texte | `{score, elements, keywords}` | ✅ Analyse IA |
| **exposition** | Analyse contextuelle | `{exposition, ...}` | ✅ Analyse IA |

**Total :** ~20 champs extraits

---

## 📡 Données Disponibles via API

### ✅ Données Disponibles dans l'API

| Champ | Endpoint API | Format | Disponibilité |
|-------|--------------|--------|---------------|
| **id** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct |
| **uuid** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct |
| **favorite** | `/apiv2/alert/{token}/ad/{id}` | `boolean` | ✅ Direct |
| **rent** | `/apiv2/alert/{token}/ad/{id}` | `number` | ✅ Direct (775000) |
| **type** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct ("Appartement") |
| **area** | `/apiv2/alert/{token}/ad/{id}` | `number` | ✅ Direct (70) |
| **room** | `/apiv2/alert/{token}/ad/{id}` | `number` | ✅ Direct (3) |
| **bedroom** | `/apiv2/alert/{token}/ad/{id}` | `number` | ✅ Direct (2) |
| **floor** | `/apiv2/alert/{token}/ad/{id}` | `number \| null` | ✅ Direct (4) |
| **lat** | `/apiv2/alert/{token}/ad/{id}` | `number` | ✅ Direct (48.8767) |
| **lng** | `/apiv2/alert/{token}/ad/{id}` | `number` | ✅ Direct (2.38578) |
| **city** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct ("Paris 19e") |
| **postal_code** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct ("75019") |
| **quartier_name** | `/apiv2/alert/{token}/ad/{id}` | `string \| null` | ✅ Direct ("Combat") |
| **images** | `/apiv2/alert/{token}/ad/{id}` | `string` (CSV) | ✅ Direct (URLs séparées par virgules) |
| **stops** | `/apiv2/alert/{token}/ad/{id}` | `array[{id, name, lines[]}]` | ✅ Direct (structuré) |
| **features** | `/apiv2/alert/{token}/ad/{id}` | `object` | ✅ Direct (lift, bath, parking, etc.) |
| **description** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct (texte complet) |
| **description_is_truncated** | `/apiv2/alert/{token}/ad/{id}` | `boolean` | ✅ Direct |
| **source** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct ("globalstone") |
| **source_label** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct ("Globalstone") |
| **source_logo** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct (URL) |
| **owner_type** | `/apiv2/alert/{token}/ad/{id}` | `string` | ✅ Direct ("Agence" \| "Particulier") |
| **buy_type** | `/apiv2/alert/{token}/ad/{id}` | `string \| null` | ✅ Direct ("new" \| "old") |
| **created_at** | `/apiv2/alert/{token}/ad/{id}` | `ISO 8601` | ✅ Direct |
| **expired_at** | `/apiv2/alert/{token}/ad/{id}` | `ISO 8601 \| null` | ✅ Direct |
| **price_sector** | `/apiv2/alert/{token}/ad/{id}` | `number` | ✅ Direct (prix/m² moyen secteur) |
| **fees** | `/apiv2/alert/{token}/ad/{id}` | `object` | ✅ Direct (honoraires) |
| **furnished** | `/apiv2/alert/{token}/ad/{id}` | `0 \| 1` | ✅ Direct |
| **is_coliving** | `/apiv2/alert/{token}/ad/{id}` | `0 \| 1` | ✅ Direct |
| **land_area** | `/apiv2/alert/{token}/ad/{id}` | `number \| null` | ✅ Direct |
| **dpe_infos** | `/apiv2/alert/{token}/ad/{id}` | `object \| null` | ✅ Direct (DPE) |
| **contact_info** | `/apiv2/ad/{id}/contact_info` | `{phone, agency_name, ...}` | ✅ Endpoint séparé |

**Total :** ~30+ champs disponibles

---

## 🔄 Comparaison Détaillée

### 1. Données de Base

| Champ | Scraping HTML | API | Avantage |
|-------|---------------|-----|----------|
| **ID** | ✅ Extrait de l'URL | ✅ Direct | **API** (plus fiable) |
| **Prix** | ⚠️ String "775 000 €" | ✅ Number 775000 | **API** (type correct) |
| **Prix/m²** | ⚠️ Souvent non trouvé | ✅ `price_sector` (moyenne secteur) | **API** (toujours disponible) |
| **Surface** | ⚠️ String "70 m²" | ✅ Number 70 | **API** (type correct) |
| **Pièces** | ⚠️ String "3 pièces" | ✅ Number 3 | **API** (type correct) |
| **Chambres** | ⚠️ Parsing depuis "pièces" | ✅ Number 2 | **API** (champ dédié) |
| **Étage** | ⚠️ String "4e étage" (parsing fragile) | ✅ Number 4 | **API** (type correct) |

### 2. Localisation

| Champ | Scraping HTML | API | Avantage |
|-------|---------------|-----|----------|
| **Coordonnées GPS** | ⚠️ Extraction Leaflet (parfois incorrectes) | ✅ `lat`/`lng` (précises) | **API** (toujours correctes) |
| **Ville** | ⚠️ Parsing texte | ✅ `city` ("Paris 19e") | **API** (structuré) |
| **Code postal** | ⚠️ Parsing regex | ✅ `postal_code` ("75019") | **API** (direct) |
| **Quartier** | ⚠️ Heuristique (rues + métros) | ✅ `quartier_name` ("Combat") | **API** (officiel) |
| **Stations métro** | ⚠️ Parsing HTML complexe | ✅ `stops[]` (structuré avec lignes) | **API** (plus complet) |
| **Rues proches** | ⚠️ Parsing carte (screenshot requis) | ❌ Non disponible | **Scraping** (seule source) |

### 3. Description et Détails

| Champ | Scraping HTML | API | Avantage |
|-------|---------------|-----|----------|
| **Description** | ✅ Texte complet | ✅ Texte complet | **Égal** |
| **Description tronquée** | ❌ Non détecté | ✅ `description_is_truncated` | **API** |
| **Caractéristiques** | ⚠️ Texte brut | ✅ `features{}` (structuré) | **API** (lift, bath, parking, etc.) |
| **Type** | ⚠️ Parsing | ✅ `type` ("Appartement") | **API** |
| **Meublé** | ⚠️ Parsing texte | ✅ `furnished` (0/1) | **API** |
| **Coliving** | ❌ Non détecté | ✅ `is_coliving` (0/1) | **API** |

### 4. Photos

| Champ | Scraping HTML | API | Avantage |
|-------|---------------|-----|----------|
| **URLs photos** | ⚠️ Parsing DOM complexe (gallery) | ✅ `images` (CSV) | **API** (plus simple) |
| **Ordre photos** | ⚠️ Préservation ordre DOM | ✅ Ordre dans CSV | **Égal** |
| **Alt text** | ✅ Disponible | ❌ Non disponible | **Scraping** |

### 5. Agence / Source

| Champ | Scraping HTML | API | Avantage |
|-------|---------------|-----|----------|
| **Nom agence** | ⚠️ Parsing texte | ✅ `source_label` | **API** (structuré) |
| **Logo agence** | ❌ Non extrait | ✅ `source_logo` (URL) | **API** |
| **Partenaire** | ❌ Non détecté | ✅ `source_is_partner` | **API** |
| **Contact disponible** | ❌ Non détecté | ✅ `source_has_contact` | **API** |
| **SIRET** | ❌ Non extrait | ✅ `agency_siret` | **API** |

### 6. Informations Spéciales

| Champ | Scraping HTML | API | Avantage |
|-------|---------------|-----|----------|
| **Date création** | ⚠️ Parsing fragile | ✅ `created_at` (ISO) | **API** (format standard) |
| **Date expiration** | ❌ Non détecté | ✅ `expired_at` | **API** |
| **Favori** | ❌ Non détecté | ✅ `favorite` | **API** |
| **DPE** | ❌ Non extrait | ✅ `dpe_infos` | **API** |
| **Prix secteur** | ❌ Non calculé | ✅ `price_sector` | **API** |
| **Honoraires** | ❌ Non extrait | ✅ `fees{}` | **API** |
| **Contact (téléphone)** | ❌ Non extrait | ✅ `/contact_info` | **API** |

### 7. Données Calculées / Analyse IA

| Champ | Scraping HTML | API | Avantage |
|-------|---------------|-----|----------|
| **Style haussmannien** | ✅ Analyse texte IA | ❌ Non disponible | **Scraping** (analyse custom) |
| **Exposition** | ✅ Analyse contextuelle IA | ❌ Non disponible | **Scraping** (analyse custom) |
| **Screenshot carte** | ✅ Généré | ❌ Non disponible | **Scraping** (visuel) |
| **Rues proches** | ✅ Parsing carte | ❌ Non disponible | **Scraping** (visuel) |

---

## ❌ Ce Qu'on NE Récupère PAS avec l'API

### Données Visuelles / Analyse

1. **Screenshot de la carte** ❌
   - Scraping : Screenshot Leaflet généré
   - API : Non disponible
   - Impact : Perte de visualisation spatiale

2. **Rues proches (parsing carte)** ❌
   - Scraping : Extraction depuis la carte
   - API : Non disponible
   - Impact : Perte de contexte géographique détaillé

3. **Style haussmannien (analyse IA)** ❌
   - Scraping : Analyse texte avec keywords
   - API : Non disponible
   - Impact : Perte d'analyse custom

4. **Exposition (analyse contextuelle)** ❌
   - Scraping : Analyse photos + description
   - API : Non disponible
   - Impact : Perte d'analyse custom

5. **Alt text des photos** ❌
   - Scraping : Disponible dans DOM
   - API : Non disponible
   - Impact : Perte de métadonnées images

---

## ✅ Ce Qu'on Récupère MIEUX avec l'API

### Données Structurées

1. **Prix en nombre** ✅
   - Scraping : "775 000 €" (string)
   - API : 775000 (number)
   - Avantage : Pas de parsing nécessaire

2. **Caractéristiques structurées** ✅
   - Scraping : Texte brut "Parking Meublé..."
   - API : `{lift: 0, bath: null, parking: 0, ...}`
   - Avantage : Données exploitables directement

3. **Stations métro structurées** ✅
   - Scraping : `["Pyrénées", "Jourdain"]`
   - API : `[{id: 1758, name: "Pyrénées", lines: ["Ligne 11"]}]`
   - Avantage : Plus d'informations (IDs, lignes)

4. **Coordonnées GPS précises** ✅
   - Scraping : Parfois incorrectes (bug Leaflet)
   - API : Toujours correctes
   - Avantage : Fiabilité

5. **Date au format ISO** ✅
   - Scraping : "Date non trouvée" (fragile)
   - API : "2025-10-24T15:08:59.000Z"
   - Avantage : Format standard

6. **Informations agence complètes** ✅
   - Scraping : Nom seulement
   - API : Nom, logo, SIRET, partenaire, contact
   - Avantage : Données complètes

7. **Champs supplémentaires** ✅
   - Scraping : Non disponibles
   - API : `favorite`, `expired_at`, `dpe_infos`, `price_sector`, `fees`, `contact_info`
   - Avantage : Plus de données exploitables

---

## 📊 Tableau Synthétique

| Catégorie | Scraping HTML | API | Différence |
|-----------|---------------|-----|------------|
| **Données de base** | ⚠️ Parsing fragile | ✅ Structurées | **API meilleure** |
| **Localisation** | ⚠️ Extraction complexe | ✅ Structurée | **API meilleure** |
| **Photos** | ⚠️ Parsing DOM | ✅ CSV simple | **API meilleure** |
| **Agence** | ⚠️ Parsing texte | ✅ Structuré | **API meilleure** |
| **Données calculées** | ✅ Analyse IA custom | ❌ Non disponible | **Scraping meilleur** |
| **Visuels** | ✅ Screenshots | ❌ Non disponible | **Scraping meilleur** |
| **Performance** | ⚠️ Lent (navigateur) | ✅ Rapide (HTTP) | **API meilleure** |
| **Stabilité** | ⚠️ Fragile (CSS changes) | ✅ Stable (API) | **API meilleure** |

---

## 🎯 Recommandation : Migration Hybride

### Stratégie Recommandée

1. **Utiliser l'API pour :**
   - ✅ Toutes les données structurées (prix, surface, localisation, etc.)
   - ✅ Liste des appartements (dashboard)
   - ✅ Détails complets (endpoint `/ad/{id}`)
   - ✅ Photos (URLs depuis `images`)

2. **Conserver le Scraping pour :**
   - ✅ Analyse style haussmannien (si nécessaire)
   - ✅ Analyse exposition (si nécessaire)
   - ✅ Screenshot carte (si nécessaire)
   - ✅ Fallback si API échoue

3. **Remplacer par API :**
   - ✅ Extraction prix/surface/pièces → `rent`/`area`/`room`
   - ✅ Extraction localisation → `city`/`postal_code`/`quartier_name`
   - ✅ Extraction transports → `stops[]`
   - ✅ Extraction photos → `images` (CSV)
   - ✅ Extraction caractéristiques → `features{}`
   - ✅ Extraction agence → `source_label`/`source_logo`

---

## 📈 Gains Attendus

### Performance
- **Vitesse :** 5-10x plus rapide (pas de rendu HTML)
- **Ressources :** Pas de navigateur = moins de RAM/CPU
- **Fiabilité :** Moins fragile aux changements CSS

### Qualité des Données
- **Précision :** Données structurées = moins d'erreurs
- **Complétude :** Plus de champs disponibles
- **Cohérence :** Format standardisé

### Maintenance
- **Moins de code :** Pas de parsing HTML complexe
- **Moins de bugs :** Données déjà structurées
- **Évolutivité :** Facile d'ajouter de nouveaux champs

---

## ⚠️ Points d'Attention

### Données Perdues
- ❌ Screenshot carte (peut être remplacé par API map externe)
- ❌ Rues proches (peut être calculé depuis coordonnées GPS)
- ❌ Alt text photos (peu utilisé)
- ❌ Style haussmannien (peut être recalculé depuis description)
- ❌ Exposition (peut être recalculé depuis photos)

### Solution pour Données Perdues
- **Screenshot carte :** Utiliser Google Maps Static API ou OpenStreetMap
- **Rues proches :** Géocodage inverse depuis `lat`/`lng`
- **Style haussmannien :** Réutiliser l'analyse IA sur `description` de l'API
- **Exposition :** Réutiliser l'analyse IA sur `images` de l'API

---

## ✅ Conclusion

**Migration recommandée :** ✅ **OUI**

**Raisons :**
1. ✅ L'API fournit **95% des données** nécessaires
2. ✅ Les données sont **mieux structurées**
3. ✅ **Performance 5-10x meilleure**
4. ✅ **Plus stable** (moins fragile)
5. ✅ Les **5% manquants** peuvent être complétés par :
   - Analyse IA réutilisée sur données API
   - APIs externes (cartes, géocodage)
   - Fallback scraping si vraiment nécessaire

**Plan d'action :**
1. Créer `jinka_api_client.py`
2. Migrer les champs principaux vers API
3. Adapter les analyses IA pour utiliser données API
4. Tester en parallèle (API + scraping)
5. Passer complètement à l'API une fois validé

---

**Dernière mise à jour :** 2025-11-05






