# Design System - Scorecard Card

Documentation complète de tous les détails d'UI d'une card de scorecard d'appartement.

---

## 📐 Structure Globale

### Container Principal
```
┌─────────────────────────────────┐
│  .scorecard                      │
│  ┌─────────────────────────────┐ │
│  │ Image Container (280px)     │ │
│  │ ┌─────────────────────────┐ │ │
│  │ │ Mega Score Badge        │ │ │
│  │ │ (top-right)             │ │ │
│  │ └─────────────────────────┘ │ │
│  └─────────────────────────────┘ │
│  ┌─────────────────────────────┐ │
│  │ .apartment-info (padding 24) │ │
│  │ • Titre                     │ │
│  │ • Sous-titre                │ │
│  │ • Critères (×6)             │ │
│  └─────────────────────────────┘ │
└─────────────────────────────────┘
```

---

## 🎨 Card Container

### `.scorecard`
- **Background** : `white` (#FFFFFF)
- **Border-radius** : `8px`
- **Box-shadow** : `0 4px 12px rgba(0,0,0,0.1)`
- **Overflow** : `hidden`
- **Cursor** : `pointer`
- **Transition** : `all 0.2s ease`

### Hover State
- **Box-shadow** : `0 6px 16px rgba(0,0,0,0.15)`
- **Transform** : `translateY(-2px)`

**Dimensions** : Largeur automatique selon la grille, hauteur automatique selon le contenu

---

## 🖼️ Image Container

### `.apartment-image-container`
- **Height** : `280px`
- **Border-radius** : `16px 16px 0 0` (coins supérieurs arrondis uniquement)
- **Background** : `#f0f0f0` (gris clair pour placeholder)
- **Position** : `relative`
- **Overflow** : `hidden`

### Image Single (`.apartment-image`)
- **Width** : `100%`
- **Height** : `286px`
- **Object-fit** : `cover`
- **Background-size** : `cover`
- **Background-position** : `center`
- **Position** : `relative`

### Image Placeholder (`.apartment-image-placeholder`)
- **Width** : `100%`
- **Height** : `286px`
- **Background** : `#f0f0f0`
- **Display** : `flex`
- **Align-items** : `center`
- **Justify-content** : `center`
- **Font-size** : `2rem`
- **Color** : `#999`
- **Emoji** : `📷` (via `::before`)

---

## 🏆 Mega Score Badge

### `.score-badge-top`
- **Position** : `absolute`
- **Top** : `15px`
- **Right** : `15px`
- **Z-index** : `10`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `20px`
- **Font-weight** : `500` (Medium)
- **Color** : `white !important` (TOUJOURS blanc)
- **Padding** : `8px 16px` (vertical horizontal)
- **Border-radius** : `12px`
- **Display** : `inline-block`

### Couleurs du Badge (dynamiques selon le score)
- **≥ 80%** : `#00966D` (vert)
- **≥ 60%** : `#F59E0B` (jaune)
- **< 60%** : `#F85457` (rouge)

**⚠️ IMPORTANT** : Le texte est TOUJOURS blanc, quelle que soit la couleur de fond.

---

## 🎠 Carousel (si plusieurs photos)

### `.carousel-container`
- **Position** : `relative`
- **Width** : `100%`
- **Height** : `286px`
- **Border-radius** : `8px 8px 0 0`
- **Overflow** : `hidden`

### `.carousel-track`
- **Display** : `flex`
- **Transition** : `transform 0.3s ease`
- **Height** : `100%`

### `.carousel-slide`
- **Min-width** : `100%`
- **Height** : `100%`

### `.carousel-slide img`
- **Width** : `100%`
- **Height** : `286px`
- **Object-fit** : `cover`

### Navigation Buttons (`.carousel-nav`)
- **Position** : `absolute`
- **Top** : `50%`
- **Transform** : `translateY(-50%)`
- **Background** : `rgba(255, 255, 255, 0.9)`
- **Border** : `none`
- **Width** : `32px`
- **Height** : `32px`
- **Border-radius** : `50%` (cercle)
- **Display** : `flex`
- **Align-items** : `center`
- **Justify-content** : `center`
- **Cursor** : `pointer`
- **Z-index** : `10`
- **Transition** : `all 0.2s ease`
- **Font-size** : `20px`
- **Color** : `#333`

#### Positions
- **Prev** : `left: 10px`
- **Next** : `right: 10px`

#### Hover State
- **Background** : `rgba(255, 255, 255, 1)`
- **Box-shadow** : `0 2px 8px rgba(0,0,0,0.2)`

#### Disabled State
- **Opacity** : `0.3`
- **Cursor** : `not-allowed`

### Dots Navigation (`.carousel-dots`)
- **Position** : `absolute`
- **Bottom** : `10px`
- **Left** : `50%`
- **Transform** : `translateX(-50%)`
- **Display** : `flex`
- **Gap** : `6px`
- **Z-index** : `10`

### Dot (`.carousel-dot`)
- **Width** : `8px`
- **Height** : `8px`
- **Border-radius** : `50%` (cercle)
- **Background** : `rgba(255, 255, 255, 0.5)`
- **Cursor** : `pointer`
- **Transition** : `all 0.2s ease`

### Dot Active (`.carousel-dot.active`)
- **Background** : `white`
- **Width** : `24px`
- **Border-radius** : `4px` (arrondi)

---

## 📝 Informations Appartement

### Container (`.apartment-info`)
- **Padding** : `24px` (tous les côtés)

### Titre (`.apartment-title`)
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `20px`
- **Font-weight** : `500` (Medium)
- **Color** : `#212529` (gris foncé)
- **Margin-bottom** : `4px`
- **Line-height** : `1.2`

**Exemple** : `"780k · Place de la Réunion"`

### Sous-titre (`.apartment-subtitle`)
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `14px`
- **Font-weight** : `400` (Regular)
- **Color** : `#6c757d` (gris moyen)
- **Margin-bottom** : `24px`

**Exemple** : `"76 m² · 10 714 € / m² · Style 70s"`

---

## 📊 Critères de Scoring

### Container Critère (`.criterion`)
- **Margin-bottom** : `16px`
- **Padding-bottom** : `16px`
- **Border-bottom** : `1px solid rgba(0, 0, 0, 0.06)` (séparateur très clair)

### Dernier Critère (`.criterion:last-child`)
- **Border-bottom** : `none`
- **Padding-bottom** : `0`
- **Margin-bottom** : `0`

### Header Critère (`.criterion-header`)
- **Display** : `flex`
- **Justify-content** : `space-between`
- **Align-items** : `center` (centrage vertical)
- **Margin-bottom** : `0`
- **Gap** : `12px`

**Structure** :
```
┌─────────────────────────────────────┐
│ [Nom Critère]        [Badge Score] │
└─────────────────────────────────────┘
```

### Nom Critère (`.criterion-name`)
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `16px` ⚠️ (augmenté de 14px à 16px)
- **Font-weight** : `500` (Medium)
- **Color** : `#212529`
- **Text-transform** : `none !important`
- **Flex** : `1`
- **Min-width** : `0`

**Exemples** : `"Localisation"`, `"Prix"`, `"Style"`, `"Exposition"`, `"Cuisine ouverte"`, `"Baignoire"`

### Détails Critère (`.criterion-details`)
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `13px`
- **Font-weight** : `400` (Regular)
- **Color** : `#6c757d`
- **Margin-top** : `4px`

**Exemple** : `"Metro Ménilmontant · Belleville"` ou `"70's"` avec confidence badge

### Sous-détails (`.criterion-sub-details`)
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `12px`
- **Color** : `#999` (gris clair)
- **Margin-top** : `2px`

**Exemple** : `"Indices: moulures · cheminée · parquet"`

---

## 🏷️ Badge Score (Points)

### `.criterion-score-badge`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Font-size** : `14px`
- **Font-weight** : `500` (Medium)
- **Padding** : `4px 12px` (vertical horizontal)
- **Border-radius** : `9999px` (100% arrondi, pill shape)
- **Text-align** : `center`
- **Display** : `inline-flex`
- **Align-items** : `center`
- **Justify-content** : `center`
- **Flex-shrink** : `0`
- **Height** : `fit-content`
- **Line-height** : `1.2`

### Couleurs selon Tier

#### Green (`.criterion-score-badge.green`)
- **Color** : `#00966D` (vert plein)
- **Background** : `rgba(0, 150, 109, 0.1)` (vert à 10% d'opacité)

#### Yellow (`.criterion-score-badge.yellow`)
- **Color** : `#F59E0B` (jaune plein)
- **Background** : `rgba(245, 158, 11, 0.1)` (jaune à 10% d'opacité)

#### Red (`.criterion-score-badge.red`)
- **Color** : `#F85457` (rouge plein)
- **Background** : `rgba(248, 84, 87, 0.1)` (rouge à 10% d'opacité)

**Format** : `"20 pts"`, `"10 pts"`, etc.

---

## 💬 Badge Confiance

### `.confidence-badge`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `10px`
- **Font-weight** : `500` (Medium)
- **Color** : `rgba(0, 0, 0, 0.3)` ⚠️ (éclairci de 40% depuis 0.5)
- **Background** : `rgba(0, 0, 0, 0.06)` ⚠️ (éclairci de 40% depuis 0.1)
- **Padding** : `0 8px` (horizontal uniquement)
- **Height** : `18px` (fixe)
- **Line-height** : `18px`
- **Border-radius** : `9999px` (100% arrondi, pill shape)
- **Margin-left** : `4px`
- **Display** : `inline-block`

**Format** : `"90% confiance"`, `"75% confiance"`, etc.

**Usage** : Placé après le texte principal dans `.criterion-details`

---

## 🎯 Tier Labels (dans les détails)

### `.tier-label`
- **Font-weight** : `600` (Semi-bold)

### Couleurs

#### Good (`.tier-label.good`)
- **Color** : `#00966D`

#### Moyen (`.tier-label.moyen`)
- **Color** : `#F59E0B !important`

#### Bad (`.tier-label.bad`)
- **Color** : `#F85457`

**Usage** : Utilisé dans `.criterion-details` pour afficher "Good", "Moyen", "Bad"

---

## 📐 Grille et Layout

### Container Global (`.container`)
- **Width** : `100%` (pleine largeur)
- **Margin** : `0`
- **Padding** : `30px` (haut, bas, gauche, droite)

### Body
- **Margin** : `0`
- **Padding** : `0`
- **Background** : `#f8f9fa`

### Grille Appartements (`.apartments-grid`)
- **Display** : `grid`
- **Grid-template-columns** : `repeat(3, 1fr)` (3 colonnes par défaut)
- **Gap** : `30px`
- **Margin** : `0`
- **Padding** : `0`
- **Width** : `100%`

### Media Queries

#### > 1000px
- **Grid-template-columns** : `repeat(3, 1fr)` (3 colonnes)

#### ≤ 1000px
- **Grid-template-columns** : `repeat(2, 1fr)` (2 colonnes)

#### ≤ 600px
- **Grid-template-columns** : `1fr` (1 colonne)
- **Apartment-title font-size** : `1.1em` (responsive)

---

## 🎨 Palette de Couleurs

### Couleurs Principales
- **Vert (Good)** : `#00966D`
- **Jaune (Moyen)** : `#F59E0B`
- **Rouge (Bad)** : `#F85457`

### Couleurs Texte
- **Texte Principal** : `#212529` (gris très foncé)
- **Texte Secondaire** : `#6c757d` (gris moyen)
- **Texte Tertiaire** : `#999` (gris clair)
- **Texte Blanc** : `white` (pour mega score badge)

### Couleurs Background
- **Card Background** : `white` (#FFFFFF)
- **Page Background** : `#f8f9fa` (gris très clair)
- **Image Placeholder** : `#f0f0f0` (gris clair)

### Opacités
- **Séparateur critères** : `rgba(0, 0, 0, 0.06)` (6% d'opacité)
- **Badge confiance texte** : `rgba(0, 0, 0, 0.3)` (30% d'opacité)
- **Badge confiance fond** : `rgba(0, 0, 0, 0.06)` (6% d'opacité)
- **Badge score fond** : `rgba(couleur, 0.1)` (10% d'opacité de la couleur)

---

## 🔤 Typographie

### Police Principale
**Cera Pro** - Chargée depuis `fonts.cdnfonts.com`

```css
font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
```

### Hiérarchie Typographique

| Élément | Font-size | Font-weight | Color | Line-height |
|---------|-----------|-------------|-------|-------------|
| Mega Score Badge | `20px` | `500` (Medium) | `white` | `1` |
| Titre Appartement | `20px` | `500` (Medium) | `#212529` | `1.2` |
| Nom Critère | `16px` | `500` (Medium) | `#212529` | `1` |
| Badge Score | `14px` | `500` (Medium) | Couleur tier | `1.2` |
| Sous-titre | `14px` | `400` (Regular) | `#6c757d` | `1.5` |
| Détails Critère | `13px` | `400` (Regular) | `#6c757d` | `1.5` |
| Sous-détails | `12px` | `400` (Regular) | `#999` | `1.5` |
| Badge Confiance | `10px` | `500` (Medium) | `rgba(0,0,0,0.3)` | `18px` |

### Body Default
- **Font-size** : `14px`
- **Line-height** : `1.5`
- **Color** : `#212529`

---

## 📏 Espacements

### Padding
- **Card Info** : `24px` (tous les côtés)
- **Mega Score Badge** : `8px 16px` (vertical horizontal)
- **Badge Score** : `4px 12px` (vertical horizontal)
- **Badge Confiance** : `0 8px` (horizontal uniquement)

### Marges
- **Titre → Sous-titre** : `4px`
- **Sous-titre → Critères** : `24px`
- **Critère → Critère** : `16px` (margin-bottom)
- **Header → Détails** : `0px` (pas de gap)
- **Détails → Sous-détails** : `2px`

### Gaps
- **Grille appartements** : `30px` (tous les breakpoints)
- **Header critère** : `12px` (entre nom et badge)
- **Carousel dots** : `6px`

---

## 🎭 États et Interactions

### Hover
- **Card** : Élévation (`translateY(-2px)`) + ombre plus prononcée
- **Carousel Nav** : Background opaque + ombre

### Focus
- **Card** : Cursor pointer (indique cliquable)

### Disabled
- **Carousel Nav** : Opacité réduite + cursor not-allowed

---

## 📱 Responsive Breakpoints

| Breakpoint | Colonnes | Gap | Notes |
|------------|----------|-----|-------|
| > 1000px | 3 | 30px | Desktop large |
| ≤ 1000px | 2 | 30px | Desktop |
| ≤ 600px | 1 | 30px | Mobile (titre réduit) |

---

## 🎯 Checklist Complète

### Structure
- [ ] Card avec border-radius 8px
- [ ] Image container 280px de hauteur
- [ ] Mega score badge en haut à droite
- [ ] Info container avec padding 24px
- [ ] 6 critères avec séparateurs

### Typographie
- [ ] Tous les textes en Cera Pro avec !important
- [ ] Titre appartement : 20px Medium
- [ ] Nom critère : 16px Medium
- [ ] Détails : 13px Regular
- [ ] Badge confiance : 10px Medium

### Couleurs
- [ ] Badge score : couleur tier + fond 10% opacité
- [ ] Badge confiance : texte 30% opacité, fond 6% opacité
- [ ] Séparateurs : 6% opacité
- [ ] Mega score : texte blanc toujours

### Layout
- [ ] Header critère en flex space-between
- [ ] Badge score aligné verticalement avec nom
- [ ] Gap de 12px entre nom et badge
- [ ] Pas de gap entre header et détails

### Interactions
- [ ] Hover sur card avec élévation
- [ ] Carousel fonctionnel si plusieurs photos
- [ ] Navigation carousel visible au hover

---

## 📝 Notes Importantes

1. **Police Cera Pro** : Toujours utiliser avec `!important` pour garantir l'application
2. **Mega Score** : Texte TOUJOURS blanc, quelle que soit la couleur de fond
3. **Badge Confiance** : Éclairci de 40% (texte 0.3, fond 0.06)
4. **Nom Critère** : Augmenté à 16px (au lieu de 14px) pour meilleure lisibilité
5. **Séparateurs** : Très clairs (6% opacité) pour subtilité
6. **Carousel** : Apparaît automatiquement si plusieurs photos disponibles
7. **Responsive** : Grille adaptative de 3 → 2 → 1 colonnes

---

## 🔄 Évolutions Récentes

- **2024-XX-XX** : Augmentation taille nom critère de 14px à 16px
- **2024-XX-XX** : Éclaircissement badge confiance de 40%
- **2024-XX-XX** : Changement noms critères de majuscules à capitalisation normale
- **2024-XX-XX** : Ajout `text-transform: none !important` sur nom critère
- **2024-XX-XX** : Container mis à jour : width 100%, padding 30px (au lieu de max-width 1200px et padding 20px)
- **2024-XX-XX** : Body avec margin 0 et padding 0 pour supprimer les espacements par défaut
- **2024-XX-XX** : Breakpoints mis à jour : 3 colonnes jusqu'à 1000px (au lieu de 1400px), 2 colonnes jusqu'à 600px (au lieu de 900px)
- **2024-XX-XX** : Gap uniforme de 30px sur tous les breakpoints (plus de réduction à 20px sur mobile)

---

## 📚 Références

- Fichier source : `generate_scorecard_html.py`
- Documentation design : `DESIGN_SCORECARD.md`
- Police : `fonts.cdnfonts.com/css/cera-pro`

