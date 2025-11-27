# 🎯 Changelog - Système de Scoring des Alertes

## Date: 2025-11-27

### ✅ Modifications Effectuées

#### 1. **Clarification de la Logique de Scoring**

**Ancien système :**
- 3 critères principaux + 1 critère secondaire
- Les 2 premiers critères principaux = 30 pts
- Le 3ème critère principal + le critère secondaire = 20 pts

**Nouveau système :**
- **2 critères principaux (primary)** → 30 pts max chacun
- **2 critères secondaires (secondary)** → 20 pts max chacun
- **Total : 100 pts max**

**Logique de scoring par tier :**
- **tier1 (good)** = 100% → 30 pts (primary) ou 20 pts (secondary)
- **tier2 (moyen)** = 50% → 15 pts (primary) ou 10 pts (secondary)
- **tier3 (bad)** = 0 pts

#### 2. **Modifications Backend**

**`backend/api/alerts.py` :**
- ✅ Validation mise à jour : `primary` doit avoir exactement 2 critères
- ✅ Validation mise à jour : `secondary` doit avoir exactement 2 critères

**`alert_scoring.py` :**
- ✅ Nouvelle fonction `get_score_from_tier()` qui attribue les scores selon le tier (good/moyen/bad)
- ✅ Remplacement de la normalisation proportionnelle par un système basé sur les tiers
- ✅ Logique simplifiée : tous les critères dans `primary[]` = 30 pts max, tous dans `secondary[]` = 20 pts max
- ✅ Suppression de l'ancienne fonction `normalize_score()`

#### 3. **Modifications Frontend**

**`frontend/src/components/ScoreBadge.jsx` :**
- ✅ Le popup de breakdown des scores suit maintenant l'ordre des critères définis dans l'alerte
- ✅ Les scores sont affichés dans l'ordre : d'abord les 2 critères `primary`, puis les 2 critères `secondary`
- ✅ Couleur des scores basée sur le tier :
  - **tier1 (good)** = vert
  - **tier2 (moyen)** = orange/jaune
  - **tier3 (bad)** = rouge
- ✅ Utilisation des scores d'alerte (`alert_criteria_scores`) au lieu des scores standards

**`frontend/src/components/Carousel.jsx` :**
- ✅ Passage de `alertCriteria` au composant `ScoreBadge`

**`frontend/src/components/ApartmentCard.jsx` :**
- ✅ Passage de `alertCriteria` au composant `Carousel`
- ✅ Ajout de logs de debug pour vérifier que `alertCriteria` est bien passé

#### 4. **Structure de l'Alerte "Belleville"**

Mise à jour de l'alerte pour respecter la nouvelle structure :
```json
{
  "criteria": {
    "primary": ["haussmanien", "quartier"],
    "secondary": ["luminosite", "cuisine_ouverte"]
  }
}
```

**Scores attendus :**
- `haussmanien` (primary) : tier1 = 30 pts, tier2 = 15 pts, tier3 = 0 pts
- `quartier` (primary) : tier1 = 30 pts, tier2 = 15 pts, tier3 = 0 pts
- `luminosite` (secondary) : tier1 = 20 pts, tier2 = 10 pts, tier3 = 0 pts
- `cuisine_ouverte` (secondary) : tier1 = 20 pts, tier2 = 10 pts, tier3 = 0 pts

### 📊 Exemple de Scores

Pour un appartement avec :
- `haussmanien` : tier1 (good) → **30 pts**
- `quartier` : tier1 (good) → **30 pts**
- `luminosite` : tier2 (moyen) → **10 pts** (50% de 20)
- `cuisine_ouverte` : tier1 (good) → **20 pts**

**Score total : 90/100**

### 🔧 Fichiers Modifiés

1. `alert_scoring.py` - Logique de scoring basée sur les tiers
2. `backend/api/alerts.py` - Validation des critères (2 primary + 2 secondary)
3. `frontend/src/components/ScoreBadge.jsx` - Affichage dynamique selon l'ordre de l'alerte
4. `frontend/src/components/Carousel.jsx` - Passage de `alertCriteria`
5. `frontend/src/components/ApartmentCard.jsx` - Passage de `alertCriteria` et logs de debug
6. `data/alerts/07da13bb-762c-46eb-91f2-21d1dcfda0e2.json` - Structure mise à jour

### 🎨 Améliorations UX

- ✅ Popup de breakdown des scores dans l'ordre défini par l'utilisateur
- ✅ Couleurs cohérentes : vert pour "good", orange pour "moyen", rouge pour "bad"
- ✅ Affichage des scores d'alerte au lieu des scores standards quand disponible

### 📝 Notes Techniques

- Les scores sont calculés à la volée par le backend lors de l'appel API `/api/alerts/{id}/apartments`
- Le frontend utilise les scores d'alerte quand disponibles, sinon fallback sur les scores standards
- L'ordre des critères dans le popup suit exactement l'ordre défini dans l'alerte (primary puis secondary)

