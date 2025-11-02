# Design System - Scorecard Maquette

Documentation complète du design system pour la maquette HTML des scorecards d'appartements.

## Vue d'ensemble

- **Grille** : 3 colonnes par défaut
- **Police principale** : Cera Pro (avec fallbacks système)
- **Couleurs principales** : 
  - Vert (good) : `#00966D`
  - Jaune (moyen) : `#FFC107` / `#F59E0B`
  - Rouge (bad) : `#F85457`

---

## Structure de la grille

### `.apartments-grid`
- **Display** : `grid`
- **Colonnes** : `repeat(3, 1fr)` (3 colonnes égales)
- **Gap** : `30px`
- **Marges** : `20px 0`

### Media Queries
- **≤ 1400px** : 2 colonnes (`repeat(2, 1fr)`)
- **≤ 900px** : 1 colonne (`1fr`)
- **≤ 768px** : Gap réduit à `20px`

---

## Typographie

### Police Cera Pro - Design System Standard

**IMPORTANT** : Cera Pro est la police principale utilisée dans tout le design system. Elle doit être utilisée partout pour garantir la cohérence visuelle.

#### Chargement de la police
```html
<link rel="preconnect" href="https://fonts.cdnfonts.com" crossorigin>
<link href="https://fonts.cdnfonts.com/css/cera-pro" rel="stylesheet">
```

```css
@import url('https://fonts.cdnfonts.com/css/cera-pro');
```

#### Font-family standard
Tous les éléments doivent utiliser :
```css
font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
```

### Body
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `14px`
- **Line-height** : `1.5`
- **Color** : `#212529`
- **Background** : `white`

⚠️ **Règle du design system** : Tous les textes (titres, sous-titres, critères, badges, détails) utilisent Cera Pro comme police principale avec `!important` pour forcer l'application.

---

## Scorecard Container

### `.scorecard`
- **Background** : `white`
- **Border-radius** : `8px` (ou `16px` selon le design)
- **Box-shadow** : `0 4px 12px rgba(0,0,0,0.1)`
- **Transition** : `all 0.2s ease`
- **Cursor** : `pointer`

### Hover
- **Box-shadow** : `0 6px 16px rgba(0,0,0,0.15)`
- **Transform** : `translateY(-2px)`

---

## Image Container

### `.apartment-image-container`
- **Height** : `280px`
- **Border-radius** : `16px 16px 0 0`
- **Background** : `#f0f0f0`
- **Overflow** : `hidden`
- **Position** : `relative`

---

## Mega Score Badge

### `.score-badge-top`
- **Position** : `absolute`
- **Top** : `15px`
- **Right** : `15px`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `20px`
- **Font-weight** : `500` (Medium)
- **Color** : `white !important` (TOUJOURS blanc, jamais noir)
- **Padding** : `8px 16px`
- **Border-radius** : `12px`
- **Display** : `inline-block`
- **Box-shadow** : AUCUN (supprimé)

⚠️ **IMPORTANT** : Le texte du mega score est TOUJOURS blanc, quelle que soit la couleur de fond.

---

## Informations Appartement

### `.apartment-info`
- **Padding** : `24px`

### `.apartment-title`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `20px`
- **Font-weight** : `500` (Medium)
- **Color** : `#212529`
- **Margin-bottom** : `4px`
- **Line-height** : `1.2`

### `.apartment-subtitle`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `14px`
- **Font-weight** : `400`
- **Color** : `#6c757d`
- **Margin-bottom** : `24px`

---

## Critères de Scoring

### `.criterion`
- **Margin-bottom** : `16px`
- **Padding-bottom** : `16px`
- **Border-bottom** : `1px solid rgba(0, 0, 0, 0.06)` (séparateur très clair, 70% plus clair que 0.2)

### `.criterion:last-child`
- **Border-bottom** : `none`
- **Padding-bottom** : `0`
- **Margin-bottom** : `0`

### `.criterion-header`
- **Display** : `flex`
- **Justify-content** : `space-between`
- **Align-items** : `center` (pour centrer verticalement la pill score avec le texte du critère)
- **Margin-bottom** : `0` (pas de gap entre titre et output)
- **Gap** : `12px`

**Structure en deux colonnes** :
- **Colonne gauche** (`.criterion-name`) : `flex: 1` + `min-width: 0` pour occuper tout l'espace disponible et éviter que le texte passe en dessous
- **Colonne droite** (`.criterion-score-badge`) : `flex-shrink: 0` pour garder sa largeur naturelle et s'adapter à la largeur de la pastille
- Les deux colonnes sont centrées verticalement avec `align-items: center` sur le conteneur flex

### `.criterion-name`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `14px`
- **Font-weight** : `500` (Medium)
- **Color** : `#212529`
- **Flex** : `1`
- **Min-width** : `0`
- **Note** : Pas de `display: flex` sur `.criterion-name` car le centrage vertical est géré par `align-items: center` sur `.criterion-header`

### `.criterion-details`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `13px`
- **Font-weight** : `400`
- **Color** : `#6c757d`
- **Margin-top** : `4px`

### `.criterion-sub-details`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `12px`
- **Color** : `#999`
- **Margin-top** : `2px`

---

## Pills POINTS

### `.criterion-score-badge`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `14px`
- **Font-weight** : `500` (Medium)
- **Padding** : `4px 12px`
- **Border-radius** : `9999px` (100% arrondi)
- **Text-align** : `center`
- **Display** : `inline-flex`
- **Align-items** : `center`
- **Justify-content** : `center`
- **Flex-shrink** : `0`
- **Height** : `fit-content`
- **Line-height** : `1.2`
- **Alignement** : Centré verticalement avec le texte du critère grâce à `align-items: center` sur `.criterion-header`

### Couleurs POINTS

#### `.criterion-score-badge.green` (Good)
- **Color** : `#00966D` (texte full color vert)
- **Background** : `rgba(0, 150, 109, 0.1)` (vert à 10% d'opacité)

#### `.criterion-score-badge.yellow` (Moyen)
- **Color** : `#F59E0B` (texte full color jaune)
- **Background** : `rgba(245, 158, 11, 0.1)` (jaune à 10% d'opacité)

#### `.criterion-score-badge.red` (Bad)
- **Color** : `#F85457` (texte full color rouge)
- **Background** : `rgba(248, 84, 87, 0.1)` (rouge à 10% d'opacité)

---

## Pills CONFIDENCE

### `.confidence-badge`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `10px`
- **Font-weight** : `500` (Medium)
- **Color** : `rgba(0, 0, 0, 0.5)` (texte grey 0.5)
- **Background** : `rgba(0, 0, 0, 0.1)` (fond grey 0.1)
- **Padding** : `0 8px`
- **Height** : `18px`
- **Line-height** : `18px`
- **Border-radius** : `9999px` (100% arrondi)
- **Margin-left** : `4px`
- **Display** : `inline-block`

⚠️ **Usage** : Les confidence badges sont ajoutés dans les détails des critères, généralement après le texte principal. Exemple :
```html
<div class="criterion-details">Texte descriptif<span class="confidence-badge">90% confiance</span></div>
```

---

## Structure HTML recommandée

```html
<div class="scorecard">
    <div class="apartment-image-container">
        <!-- Carousel ou image -->
        <div class="score-badge-top" style="background: #00966D;">92</div>
    </div>
    <div class="apartment-info">
        <div class="apartment-title">780k • Rue des Boulets</div>
        <div class="apartment-subtitle">68m2 • 9e étage • 70s</div>
        
        <div class="criterion">
            <div class="criterion-header">
                <span class="criterion-name">Localisation</span>
                <span class="criterion-score-badge green">20 pts</span>
            </div>
            <div class="criterion-details">Description du critère<span class="confidence-badge">90% confiance</span></div>
            <div class="criterion-sub-details">Détails supplémentaires</div>
        </div>
        
        <!-- Autres critères -->
    </div>
</div>
```

---

## Règles importantes

### Structure en deux colonnes pour les critères
- **Colonne gauche** (`.criterion-name`) : `flex: 1` + `min-width: 0` pour occuper tout l'espace disponible et éviter que le texte passe en dessous
- **Colonne droite** (`.criterion-score-badge`) : `flex-shrink: 0` pour garder sa largeur naturelle et s'adapter à la largeur de la pastille
- **Gap** : `12px` entre les deux colonnes
- **Align-items** : `center` sur `.criterion-header` pour centrer verticalement les deux éléments dans leur ligne, afin que la pastille soit parfaitement alignée avec le texte, quelle que soit sa hauteur

### Séparateurs entre critères
- **Opacité** : `rgba(0, 0, 0, 0.06)` (très clair, 70% plus clair que 0.2)
- **Padding-bottom** : `16px` sur chaque critère
- **Dernier critère** : pas de séparateur ni de padding-bottom

### Pills
- **POINTS** : Texte en couleur pleine (vert/jaune/rouge), fond à 10% d'opacité, 100% arrondi
- **CONFIDENCE** : Texte grey 0.5, fond grey 0.1, 100% arrondi, hauteur fixe 18px

### Mega Score
- **Texte TOUJOURS blanc** : `color: white !important`
- **Pas de drop shadow** : `box-shadow` supprimé
- **Cera Pro Medium 20px**

---

## Checklist de vérification

- [ ] Grille en 3 colonnes par défaut
- [ ] Tous les textes utilisent Cera Pro (chargé depuis cdnfonts.com)
- [ ] Font-family standard : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- [ ] Titre global : Cera Pro Medium 20px
- [ ] Titre critère : Cera Pro Medium 14px
- [ ] Pills POINTS : texte full color, fond 10%, 100% arrondi
- [ ] Pills CONFIDENCE : texte grey 0.5, fond grey 0.1, hauteur 18px
- [ ] Mega score : texte blanc, pas de shadow, Cera Pro Medium 20px
- [ ] Séparateurs entre critères : rgba(0, 0, 0, 0.06)
- [ ] Pas de gap entre titre critère et output (margin-bottom: 0)
- [ ] Structure en deux colonnes avec flex pour éviter que le texte passe en dessous
- [ ] Pill score centrée verticalement avec le critère (align-items: center sur .criterion-header)

---

## Historique des modifications

- **2024-01-XX** : Documentation initiale créée
- Structure en 3 colonnes
- Pills POINTS et CONFIDENCE avec styles spécifiques
- Mega score toujours blanc, sans shadow
- Séparateurs très clairs (0.06)
- Typographie Cera Pro Medium partout avec `!important`
- Centrage vertical avec `align-items: center` sur `.criterion-header`
