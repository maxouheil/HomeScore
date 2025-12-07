# 🔧 Correction du problème d'affichage des images dans le carousel

## ⚠️ IMPORTANT: Fichier HTML unique

**🚨 ON TRAVAILLE UNIQUEMENT SUR `output/homepage.html`**

- **Fichier généré par:** `generate_scorecard_html.py`
- **NE JAMAIS créer d'autres fichiers HTML**
- **Toujours modifier:** `generate_scorecard_html.py` puis régénérer `homepage.html`
- **Voir:** `REGLE_HTML_UNIQUE.md` pour les règles complètes

## Problème identifié

D'après la capture d'écran, certaines images avaient `display: none` appliqué, ce qui les rendait invisibles même si les fichiers existaient.

## Causes identifiées

### 1. Carousel non initialisé correctement
Le carousel n'appelait pas `updateCarousel()` après l'initialisation, ce qui empêchait le positionnement correct des slides au chargement de la page.

**Avant:**
```javascript
function initCarousel(carouselId, totalSlides) {
    carouselStates[carouselId] = { current: 0, total: totalSlides };
    // ❌ Pas d'appel à updateCarousel()
}
```

**Après:**
```javascript
function initCarousel(carouselId, totalSlides) {
    carouselStates[carouselId] = { current: 0, total: totalSlides };
    // ✅ Positionner immédiatement le carousel à la première slide
    updateCarousel(carouselId);
}
```

### 2. Gestion d'erreur trop agressive
Les images avec `onerror="this.style.display='none'"` se cachaient complètement en cas d'erreur de chargement, même si le problème était temporaire.

**Avant:**
```html
<img src="..." onerror="this.style.display='none'">
```

**Après:**
```html
<img src="..." onerror="console.error('Erreur chargement image:', this.src); this.parentElement.style.display='none'">
```

Maintenant, seule la slide parente est cachée (et un message d'erreur est loggé), ce qui permet de mieux diagnostiquer les problèmes.

## Solutions appliquées

1. ✅ Ajout de `updateCarousel()` dans `initCarousel()` pour positionner correctement les slides au chargement
2. ✅ Amélioration de la gestion d'erreur avec logging dans la console
3. ✅ Cacher la slide au lieu de l'image individuelle pour éviter les problèmes d'affichage

## Test

Pour vérifier que les corrections fonctionnent :

1. Régénérer le HTML :
   ```bash
   python3 generate_scorecard_html.py
   ```
   (Génère `output/homepage.html`)

2. Ouvrir `output/homepage.html` dans le navigateur

3. Vérifier dans la console développeur :
   - Les images doivent se charger sans erreur
   - Les slides doivent être positionnées correctement
   - Si une erreur survient, elle doit être loggée dans la console

## Notes

- Les fichiers photos existent bien dans `data/photos/{id}/`
- Le problème était uniquement dans l'affichage JavaScript du carousel
- Les chemins relatifs `../data/photos/` sont corrects

