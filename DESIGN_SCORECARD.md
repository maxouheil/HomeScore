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

### `.container`
- **Width** : `100%` (pleine largeur)
- **Margin** : `0`
- **Padding** : `30px` (haut, bas, gauche, droite)

### `.apartments-grid`
- **Display** : `grid`
- **Colonnes** : `repeat(3, 1fr)` (3 colonnes égales)
- **Gap** : `30px`
- **Margin** : `0`
- **Padding** : `0`
- **Width** : `100%`

### Media Queries
- **> 1000px** : 3 colonnes (`repeat(3, 1fr)`)
- **≤ 1000px** : 2 colonnes (`repeat(2, 1fr)`)
- **≤ 600px** : 1 colonne (`1fr`)

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
- **Background** : `#f8f9fa`
- **Margin** : `0`
- **Padding** : `0`

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

### `.criterion`
- **Display** : `grid`
- **Grid-template-columns** : `1fr auto` (colonne gauche flexible, droite adaptée au badge)
- **Align-items** : `center` (pour centrer verticalement la pill score avec tout le contenu du critère)
- **Gap** : `16px` entre les deux colonnes
- **Margin-bottom** : `16px`
- **Padding-bottom** : `16px`
- **Border-bottom** : `1px solid rgba(0, 0, 0, 0.06)`

**Structure en deux colonnes distinctes** :
- **Colonne gauche** (`.criterion-content`) : `1fr` - occupe tout l'espace disponible pour le texte
- **Colonne droite** (`.criterion-score-badge`) : `auto` - s'adapte à la largeur de la pastille
- Les deux colonnes sont centrées verticalement avec `align-items: center` sur `.criterion`
- Le texte (titre + détails) reste dans la colonne de gauche et ne passe jamais sous le badge

### `.criterion-content`
- **Display** : `flex`
- **Flex-direction** : `column` (empile titre et détails verticalement)
- **Min-width** : `0` (permet au texte de se réduire si nécessaire)
- Contient `.criterion-name` et `.criterion-details`

### `.criterion-name`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `16px`
- **Font-weight** : `500` (Medium)
- **Color** : `#212529`
- **Margin-bottom** : `0`
- **Word-wrap** : `break-word`
- **Overflow-wrap** : `break-word`

### `.criterion-details`
- **Font-family** : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- **Font-size** : `13px`
- **Font-weight** : `400`
- **Color** : `#212529`
- **Margin-top** : `4px`
- Reste dans la colonne de gauche (`.criterion-content`), ne passe jamais sous le badge

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
- **Align-self** : `center` (centré verticalement dans sa colonne)
- **White-space** : `nowrap` (le badge reste sur une seule ligne)
- **Alignement** : Centré verticalement avec tout le contenu du critère (titre + détails) grâce à `align-items: center` sur `.criterion`

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
            <div class="criterion-content">
                <div class="criterion-name">Localisation</div>
                <div class="criterion-details">Description du critère<span class="confidence-badge">90% confiance</span></div>
                <div class="criterion-sub-details">Détails supplémentaires</div>
            </div>
            <span class="criterion-score-badge green">20 pts</span>
        </div>
        
        <!-- Autres critères -->
    </div>
</div>
```

---

## Règles importantes

### Structure en deux colonnes pour les critères
- **Structure** : `.criterion` utilise `display: grid` avec `grid-template-columns: 1fr auto`
- **Colonne gauche** (`.criterion-content`) : `1fr` - occupe tout l'espace disponible pour le texte (titre + détails)
  - Contient `.criterion-name` (titre) et `.criterion-details` (détails) empilés verticalement
  - Le texte reste dans cette colonne et ne passe jamais sous le badge
- **Colonne droite** (`.criterion-score-badge`) : `auto` - s'adapte à la largeur de la pastille
- **Gap** : `16px` entre les deux colonnes
- **Align-items** : `center` sur `.criterion` pour centrer verticalement la pastille par rapport à tout le contenu (titre + détails), quelle que soit la hauteur du texte
- **Avantage** : Même si les détails font plusieurs lignes, ils restent dans la colonne de gauche et la pastille reste centrée verticalement

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

- [ ] Container : width 100%, padding 30px, margin 0
- [ ] Body : margin 0, padding 0, background #f8f9fa
- [ ] Grille en 3 colonnes par défaut jusqu'à 1000px
- [ ] Gap de 30px entre les cards
- [ ] Breakpoints : 3 colonnes (>1000px), 2 colonnes (≤1000px), 1 colonne (≤600px)
- [ ] Tous les textes utilisent Cera Pro (chargé depuis cdnfonts.com)
- [ ] Font-family standard : `'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important`
- [ ] Titre global : Cera Pro Medium 20px
- [ ] Titre critère : Cera Pro Medium 14px
- [ ] Pills POINTS : texte full color, fond 10%, 100% arrondi
- [ ] Pills CONFIDENCE : texte grey 0.5, fond grey 0.1, hauteur 18px
- [ ] Mega score : texte blanc, pas de shadow, Cera Pro Medium 20px
- [ ] Séparateurs entre critères : rgba(0, 0, 0, 0.06)
- [ ] Pas de gap entre titre critère et output (margin-bottom: 0)
- [ ] Structure en deux colonnes avec grid (`.criterion` en grid, colonnes `1fr auto`)
- [ ] Colonne gauche (`.criterion-content`) contient titre + détails, colonne droite contient le badge
- [ ] Le texte ne passe jamais sous le badge grâce à la structure grid
- [ ] Pill score centrée verticalement avec tout le contenu du critère (align-items: center sur .criterion)

---

## Historique des modifications

- **2024-01-XX** : Documentation initiale créée
- Structure en 3 colonnes
- Pills POINTS et CONFIDENCE avec styles spécifiques
- Mega score toujours blanc, sans shadow
- Séparateurs très clairs (0.06)
- Typographie Cera Pro Medium partout avec `!important`
- Centrage vertical avec `align-items: center` sur `.criterion` (grid layout)
- Structure grid avec deux colonnes distinctes : `.criterion-content` (texte) et `.criterion-score-badge` (badge)
- Le texte (titre + détails) reste dans la colonne de gauche et ne passe jamais sous le badge
- **2024-XX-XX** : Container mis à jour : width 100%, padding 30px, margin 0
- **2024-XX-XX** : Body avec margin 0 et padding 0
- **2024-XX-XX** : Breakpoints mis à jour : 3 colonnes jusqu'à 1000px, 2 colonnes jusqu'à 600px, 1 colonne en dessous
- **2024-XX-XX** : Gap de 30px entre les cards conservé sur tous les breakpoints
