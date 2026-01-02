# Archive - Bouton "Tous"

## Date d'archivage
2024-12-XX

## Raison de l'archivage
Le bouton "Tous" et son contenu ne sont plus pertinents dans l'interface utilisateur.

## Éléments archivés

### 1. Bouton "Tous" dans App.jsx
**Fichier:** `frontend/src/App.jsx`  
**Lignes:** 222-227 (dans la vue ALERTS)

**Code archivé:**
```jsx
<button
  className="nav-button nav-button-all"
  onClick={() => setView(VIEWS.APARTMENTS)}
>
  Tous
</button>
```

**Action:** Le code a été commenté avec la mention `ARCHIVÉ` pour faciliter la restauration si nécessaire.

### 2. Styles CSS .nav-button-all
**Fichier:** `frontend/src/App.css`  
**Lignes:** 66-75

**Code archivé:**
```css
.nav-button-all {
  background: white;
  color: #0D99FF;
  border: 1px solid #0D99FF;
  border-radius: 6px;
}

.nav-button-all:hover {
  background: #f0f5ff;
}
```

**Action:** Les styles ont été commentés avec la mention `ARCHIVÉ` pour faciliter la restauration si nécessaire.

## Fonctionnalité
Le bouton "Tous" permettait de revenir à la vue APARTMENTS depuis la vue ALERTS. Cette fonctionnalité n'est plus nécessaire car la navigation se fait désormais via d'autres moyens (sidebar, navigation principale).

## Restauration
Pour restaurer le bouton "Tous":
1. Décommenter le code dans `App.jsx` (lignes 222-227)
2. Décommenter les styles dans `App.css` (lignes 66-75)



