# 📋 Récapitulatif - Fonctionnement Actuel de l'Exposition

## 🎯 Vue d'ensemble

Le système d'analyse d'exposition utilise **3 phases** combinées avec une logique de **fallback** hiérarchique pour déterminer l'exposition d'un appartement.

---

## 🔄 Flux Principal : `extract_exposition_ultimate()`

**Utilisé dans** : `scrape_jinka.py` (ligne 219)

```python
data['exposition'] = self.exposition_extractor.extract_exposition_ultimate(data)
```

### Étapes du traitement

1. **Phase 1** : Analyse textuelle (`extract_exposition_textuelle`)
2. **Phase 2** : Analyse des photos (`extract_exposition_photos`) - si photos disponibles
3. **Phase 3** : Analyse contextuelle (`extract_exposition_contextual`)
4. **Combinaison** : `_combine_all_results()` avec priorité : **Photos > Contextuel > Textuel**

---

## 📝 Phase 1 : Analyse Textuelle

**Module** : `extract_exposition.py` → `extract_exposition_textuelle()`

### Fonctionnalités

- ✅ **Détection d'exposition explicite** dans description + caractéristiques
  - Sud, Sud-Ouest, Ouest, Est, Nord, Nord-Est
  - Utilise des **word boundaries** pour éviter les faux positifs
  - Ordre de priorité : composées d'abord (Sud-Ouest), puis simples (Sud)

- ✅ **Analyse de luminosité**
  - Mots-clés : "très lumineux" (10), "lumineux" (7), "assez lumineux" (5), "peu lumineux" (3)

- ✅ **Analyse de vue**
  - Mots-clés : "vue dégagée" (10), "vue correcte" (7), "vue limitée" (5), "vis-à-vis" (3)

- ✅ **Score final**
  - Prend le **maximum** entre : exposition_score, luminosite_score, vue_score
  - Tier basé sur le score : tier1 (≥10), tier2 (≥7), tier3 (<7)

### Résultat

```python
{
    'exposition': 'sud' | None,  # Exposition explicite ou None
    'score': 0-10,
    'tier': 'tier1' | 'tier2' | 'tier3',
    'justification': 'Excellente exposition Sud',
    'luminosite': 'excellent' | 'bon' | 'moyen' | 'faible' | 'inconnue',
    'vue': 'excellent' | 'bon' | 'moyen' | 'faible' | 'inconnue',
    'details': {
        'exposition_score': 10,
        'luminosite_score': 7,
        'vue_score': 5
    }
}
```

---

## 📸 Phase 2 : Analyse des Photos

**Module** : `analyze_photos.py` → `PhotoAnalyzer.analyze_photos_exposition()`

### Fonctionnalités

- ✅ **Analyse avec OpenAI Vision API** (GPT-4o)
  - Analyse maximum **3 photos** (pour économiser les tokens)
  - Timeout : 15 secondes par photo
  - Fallback gracieux en cas d'erreur

- ✅ **Critères analysés par photo** :
  1. Orientation des fenêtres (Sud, Sud-Ouest, Ouest, Est, Nord, Nord-Est)
  2. Luminosité naturelle (excellent, bon, moyen, faible)
  3. Qualité de la vue (dégagée, correcte, limitée, obstruée)
  4. Présence d'ombres/lumière directe
  5. Orientation des pièces

- ✅ **Agrégation multi-photos** :
  - Exposition la plus fréquente parmi les photos analysées
  - Scores moyens pour luminosité et vue
  - Score final = **max(exposition_score, avg_luminosite, avg_vue)**

### Conditions de succès

- ✅ Clé API OpenAI présente (`OPENAI_API_KEY`)
- ✅ Photos téléchargeables (HTTP 200)
- ✅ Réponse JSON valide de l'API
- ✅ Au moins 1 photo analysée avec succès

### Résultat si succès

```python
{
    'exposition': 'sud_ouest',
    'score': 0-10,
    'tier': 'tier1' | 'tier2' | 'tier3',
    'justification': 'Analyse de 3 photos: sud_ouest',
    'photos_analyzed': 1-3,
    'luminosite': 'excellent' | 'bon' | 'moyen' | 'faible',
    'vue': 'excellent' | 'bon' | 'moyen' | 'faible',
    'details': {
        'exposition_score': 10,
        'luminosite_score': 8.5,
        'vue_score': 9,
        'confidence': 0.85
    }
}
```

### Résultat si échec

```python
{
    'exposition': None,
    'score': 0,
    'tier': 'tier3',
    'justification': 'Aucune photo disponible' | 'Erreur analyse photos: ...',
    'photos_analyzed': 0,
    'details': {}
}
```

---

## 🏘️ Phase 3 : Analyse Contextuelle

**Module** : `analyze_contextual_exposition.py` → `ContextualExpositionAnalyzer.analyze_contextual_exposition()`

### Fonctionnalités

- ✅ **Analyse du quartier** (base de données d'orientations typiques)
  - Buttes-Chaumont → Sud-Est (score +8)
  - Belleville → Sud (score +9)
  - Pyrénées → Sud-Ouest (score +8)
  - Jourdain → Sud (score +8)

- ✅ **Indices architecturaux**
  - Duplex (+2), Cuisine américaine (+2), Balcon (+1), Terrasse (+1), Jardin (+1)

- ✅ **Analyse de l'étage**
  - 3ème-5ème étage : bonus +2
  - 6ème étage : bonus +1
  - RDC/1er/2ème : bonus 0

- ✅ **Luminosité contextuelle**
  - "très lumineux" (+3), "lumineux" (+2), "clair" (+2), etc.

- ✅ **Calcul de confiance**
  - Formule : `min(0.9, (total_score - 5) / 15)`
  - Base score : 5 points
  - Score max : 20 points → confiance max 0.9

### Résultat

```python
{
    'exposition': 'Sud-Est',  # Basé sur quartier ou architecture
    'score': 0-10,
    'tier': 'tier1' | 'tier2' | 'tier3',
    'justification': 'Analyse contextuelle: Quartier: ...; Indices architecturaux: ...',
    'confidence': 0.0-0.9,  # IMPORTANT pour la combinaison
    'details': {
        'quartier': {...},
        'architectural': {...},
        'etage': {...},
        'luminosite': {...}
    }
}
```

---

## 🔀 Logique de Combinaison : `_combine_all_results()`

**Priorité** : **Photos > Contextuel > Textuel**

### Règle 1 : Photos disponibles et analysées

```python
if photo_result and photo_result.get('photos_analyzed', 0) > 0:
    if contextual_result.get('confidence', 0) > 0.7:
        # Contextuel très confiant → combiner photos + contextuel
        return combine(photo_result, contextual_result)
    else:
        # Utiliser uniquement les photos
        return photo_result
```

**Combinaison photos + contextuel** :
- Exposition : priorité aux photos
- Score : **70% photos + 30% contextuel**
- Justification : combinée

### Règle 2 : Pas de photos, mais contextuel confiant

```python
elif contextual_result.get('confidence', 0) > 0.5:
    # Contextuel confiant → combiner contextuel + textuel
    return combine(contextual_result, text_result)
```

**Combinaison contextuel + textuel** :
- Exposition : priorité au contextuel
- Score : **70% contextuel + 30% textuel**
- Justification : combinée

### Règle 3 : Fallback final

```python
else:
    # Utiliser uniquement l'analyse textuelle
    return text_result
```

---

## 🛡️ Système de Fallback Complet

### Scénario 1 : Exposition explicite dans le texte
```
✅ Phase 1 trouve "exposition Sud" → score 10, tier1
⚠️ Phase 2 : Photos analysées si disponibles
⚠️ Phase 3 : Contextuel toujours exécuté
→ Si photos analysées → utilise photos (ignore exposition explicite !)
→ Sinon si contextuel confiant → combine contextuel + textuel
→ Sinon → utilise uniquement textuel (exposition explicite)
```

### Scénario 2 : Pas d'exposition explicite, mais photos disponibles
```
1. Phase 1 : exposition = None
2. Phase 2 : Analyse photos → trouve "Sud-Ouest"
3. Phase 3 : Contextuel confiant (0.8) → "Sud-Est"
→ Combine photos (70%) + contextuel (30%) → Résultat final
```

### Scénario 3 : Pas d'exposition explicite, pas de photos, contextuel confiant
```
1. Phase 1 : exposition = None
2. Phase 2 : photos_analyzed = 0
3. Phase 3 : Contextuel confiant (0.6) → "Sud-Est"
→ Combine contextuel (70%) + textuel (30%) → Résultat final
```

### Scénario 4 : Pas d'exposition explicite, pas de photos, contextuel peu confiant
```
1. Phase 1 : exposition = None, mais trouve "lumineux" → score 7
2. Phase 2 : photos_analyzed = 0
3. Phase 3 : confidence = 0.3 (< 0.5)
→ Utilise uniquement Phase 1 (analyse textuelle) → score 7, tier2
```

### Scénario 5 : Aucune information disponible
```
1. Phase 1 : exposition = None, pas de mots-clés → score 3
2. Phase 2 : photos_analyzed = 0
3. Phase 3 : confidence = 0.2
→ Résultat final : exposition = None, score = 3, tier3
```

---

## 📊 Scores et Tiers

### Exposition (si détectée)
- **Sud / Sud-Ouest** : 10 points → tier1
- **Ouest / Est** : 7 points → tier2
- **Nord / Nord-Est** : 3 points → tier3

### Luminosité
- **Excellent** ("très lumineux") : 10 points
- **Bon** ("lumineux") : 7 points
- **Moyen** ("assez lumineux") : 5 points
- **Faible** ("peu lumineux") : 3 points

### Vue
- **Excellent** ("vue dégagée") : 10 points
- **Bon** ("vue correcte") : 7 points
- **Moyen** ("vue limitée") : 5 points
- **Faible** ("vis-à-vis") : 3 points

### Score final Phase 1
- **Maximum** entre : exposition_score, luminosite_score, vue_score
- Tier basé sur ce score max

---

## 🔧 Gestion des Erreurs

### Phase 1 (Textuelle)
- ✅ Try/except avec fallback : exposition = None, score = 3, tier3
- ✅ Erreur dans justification : `f"Erreur extraction: {e}"`

### Phase 2 (Photos)
- ✅ Pas de clé API → photos_analyzed = 0
- ✅ Timeout (15s) → photo ignorée, continue avec autres
- ✅ Erreur réseau → photo ignorée, continue avec autres
- ✅ JSON invalide → photo ignorée, continue avec autres
- ✅ Aucune photo analysée → retourne score 0, tier3

### Phase 3 (Contextuelle)
- ✅ Try/except avec fallback : exposition = None, score = 3, tier3, confidence = 0.0
- ✅ Erreur dans justification : `f"Erreur analyse contextuelle: {e}"`

---

## 📈 Exemples Concrets

### Exemple 1 : Exposition explicite Sud
```json
{
    "description": "Appartement très lumineux avec exposition Sud",
    "caracteristiques": "Balcon, 4ème étage",
    "photos": ["url1.jpg", "url2.jpg"]
}
```

**Résultat** :
- Phase 1 : exposition = "sud", score = 10, tier1
- Phase 2 : photos analysées → exposition = "sud_ouest", score = 10, tier1
- Phase 3 : contextuel → exposition = "Sud-Est", confidence = 0.8
- **Final** : ⚠️ Si photos analysées → utilise photos (ignore Phase 1 !)
- **Final** : Si pas de photos mais contextuel confiant → combine contextuel + textuel
- **Final** : Sinon → utilise textuel (exposition explicite)

---

### Exemple 2 : Pas d'exposition explicite, photos analysées
```json
{
    "description": "Appartement lumineux avec vue dégagée",
    "caracteristiques": "Balcon, 4ème étage",
    "photos": ["url1.jpg", "url2.jpg"],
    "localisation": "Paris 19e, Buttes-Chaumont"
}
```

**Résultat** :
- Phase 1 : exposition = None, score = 7 (lumineux), tier2
- Phase 2 : photos analysées → exposition = "sud_ouest", score = 10, tier1
- Phase 3 : contextuel → exposition = "Sud-Est", confidence = 0.8
- **Final** : Combine photos (70%) + contextuel (30%) → score ~9, tier1

---

### Exemple 3 : Pas de photos, contextuel confiant
```json
{
    "description": "Duplex très lumineux",
    "caracteristiques": "4ème étage",
    "photos": [],
    "localisation": "Paris 19e, Belleville"
}
```

**Résultat** :
- Phase 1 : exposition = None, score = 10 (très lumineux), tier1
- Phase 2 : photos_analyzed = 0
- Phase 3 : contextuel → exposition = "Sud", confidence = 0.7
- **Final** : Combine contextuel (70%) + textuel (30%) → score ~9, tier1

---

### Exemple 4 : Aucune information
```json
{
    "description": "Appartement spacieux",
    "caracteristiques": "Parking",
    "photos": [],
    "localisation": "Paris"
}
```

**Résultat** :
- Phase 1 : exposition = None, score = 3 (aucun mot-clé), tier3
- Phase 2 : photos_analyzed = 0
- Phase 3 : confidence = 0.2 (< 0.5)
- **Final** : exposition = None, score = 3, tier3

---

## 🎯 Points Clés à Retenir

1. **⚠️ ATTENTION** : Exposition explicite dans le texte N'A PAS priorité absolue
   - Si photos analysées → photos sont utilisées (même si exposition explicite trouvée)
   - Si pas de photos mais contextuel confiant → contextuel est utilisé
   - Sinon → exposition explicite utilisée
2. **Fallback hiérarchique** : Photos > Contextuel > Textuel
3. **Seuils de confiance** :
   - Contextuel très confiant : ≥ 0.7 → combine avec photos
   - Contextuel confiant : ≥ 0.5 → combine avec textuel
   - Sinon : utilise uniquement textuel
4. **Photos** : Maximum 3 analysées, fallback gracieux si erreur
5. **Score final** : Prend le meilleur entre exposition, luminosité, vue (Phase 1)
6. **Combinaison** : 70% méthode principale + 30% méthode secondaire

---

## 🔍 Points d'Attention

### ⚠️ Analyse Contextuelle toujours appelée
- Même si exposition explicite trouvée, Phase 3 est toujours exécutée
- **Optimisation possible** : Skip Phase 3 si exposition explicite trouvée

### ⚠️ Analyse Photos coûteuse
- Requiert clé API OpenAI
- Coût par photo (tokens GPT-4o)
- Timeout possible (15s)

### ⚠️ Confiance contextuelle variable
- Basée sur nombre d'indices trouvés
- Peut être faible même avec informations utiles

### ⚠️ IMPORTANT : Différence CHANGELOG vs Code Réel

Le fichier `CHANGELOG_EXPOSITION.md` décrit des fonctionnalités **NON IMPLÉMENTÉES** :

**CHANGELOG dit (mais pas dans le code)** :
- ❌ Bonus étage >=4 (`_calculate_etage_bonus()`)
- ❌ Flag `exposition_explicite: true/false`
- ❌ Détection fenêtres/balcon dans photos (nb_fenetres, taille_fenetres, balcon_visible)
- ❌ Score relatif pondéré (30% exposition, 30% luminosité, 20% fenêtres, 20% vue)
- ❌ Suppression de `ContextualExpositionAnalyzer`

**CODE RÉEL** :
- ✅ Les 3 phases sont TOUJOURS exécutées
- ✅ `ContextualExpositionAnalyzer` est TOUJOURS utilisé
- ✅ `_combine_all_results()` utilise les seuils de confiance (0.7, 0.5)
- ✅ Analyse photos : prompt simple (exposition, luminosité, vue, confidence)
- ✅ Pas de bonus étage, pas de détection fenêtres/balcon

**Conclusion** : Le CHANGELOG semble être un document de **planning/intention**, pas la réalité du code actuel.

---

## 📝 Recommandations d'Amélioration

1. **Skip Phase 3 si exposition explicite** : Économiser du temps
2. **Cache résultats photos** : Éviter ré-analyses coûteuses
3. **Logging détaillé** : Traçabilité des décisions de fallback
4. **Métriques** : Taux de succès par phase
5. **Implémenter le CHANGELOG** : Ajouter bonus étage et détection fenêtres/balcon si souhaité
6. **Synchroniser documentation** : Mettre à jour CHANGELOG pour refléter le code réel

---

**Date de création** : 2025-01-31  
**Version** : Documentation actuelle du système

