# 📖 Exemple concret : Comment ça marche maintenant

## 🎯 Scénario : Vous modifiez le style du scorecard

### Avant (sans watch) ❌
```bash
# 1. Vous modifiez generate_scorecard_html.py
nano generate_scorecard_html.py
# ... vous changez les couleurs, les styles CSS ...

# 2. Vous devez manuellement relancer le script
python generate_scorecard_html.py

# 3. Vous ouvrez le HTML pour voir les changements
open output/homepage.html

# 4. Si ça ne vous plaît pas, retour à l'étape 1...
```

### Maintenant (avec watch) ✅

#### Étape 1 : Lancer le watch (une seule fois)
```bash
python watch_scorecard.py
```

Vous verrez :
```
👀 SURVEILLANCE DU SCORECARD HTML
============================================================
📁 Fichiers surveillés:
   ✓ analyze_apartment_style.py
   ✓ analyze_photos.py
   ✓ criteria/baignoire.py
   ✓ criteria/cuisine.py
   ...
   ✓ generate_scorecard_html.py  ← Celui-ci !
   ✓ data/scores/all_apartments_scores.json
   ✓ data/scraped_apartments.json

⏱️  Intervalle de vérification: 1 seconde(s)
⏳ Debounce: 2 seconde(s)

💡 Le HTML sera régénéré automatiquement lors des modifications
   Appuyez sur Ctrl+C pour arrêter
```

#### Étape 2 : Modifier votre fichier
Dans votre éditeur (VS Code, Cursor, etc.), ouvrez `generate_scorecard_html.py` et modifiez :

```python
# AVANT
.score-badge-top {
    background: #667eea;  ← Ancienne couleur
}

# APRÈS
.score-badge-top {
    background: #FF5733;  ← Nouvelle couleur que vous voulez tester
}
```

**Sauvegardez le fichier** (Cmd+S ou Ctrl+S)

#### Étape 3 : Regardez le terminal du watch

Automatiquement, vous verrez :
```
============================================================
🔄 [14:32:15] Régénération du scorecard HTML...
============================================================
📝 Fichiers modifiés:
   • generate_scorecard_html.py
✅ HTML régénéré avec succès!
   ✅ Rapport généré: output/homepage.html
   📋 42 appartements trouvés
```

**C'est tout !** Le HTML a été régénéré automatiquement.

#### Étape 4 : Voir les changements
```bash
open output/homepage.html
# ou simplement rafraîchir si déjà ouvert
```

## 🔄 Exemples de changements détectés automatiquement

### 1. Modification du backend Python

**Vous modifiez `extract_baignoire.py` :**
```python
# Vous changez la logique de détection
def extract_baignoire_textuelle(self, description, caracteristiques):
    # Nouvelle logique...
```

**→ HTML régénéré automatiquement !**

### 2. Modification des données JSON

**Vous modifiez `data/scores/all_apartments_scores.json` :**
```json
{
  "id": "12345",
  "score_total": 85,  ← Vous changez le score
  ...
}
```

**→ HTML régénéré automatiquement avec le nouveau score !**

### 3. Modification d'un critère

**Vous modifiez `criteria/style.py` :**
```python
def format_style_criterion(apartment):
    # Nouvelle façon de formater le style
    return {...}
```

**→ HTML régénéré automatiquement avec le nouveau formatage !**

### 4. Modification du prompt de scoring

**Vous modifiez `scoring_prompt.txt` :**
```
Nouvelle instruction pour l'IA...
```

**→ Si vous rescorez les appartements, le HTML sera régénéré !**

## ⏱️ Comment ça fonctionne techniquement

1. **Polling toutes les 1 seconde**
   - Le script vérifie les dates de modification de tous les fichiers surveillés

2. **Cache intelligent**
   - Un fichier `.watch_scorecard_cache.txt` stocke les dernières dates de modification
   - Permet de détecter uniquement les vrais changements

3. **Debounce de 2 secondes**
   - Si vous sauvegardez plusieurs fois rapidement, il attend 2 secondes avant de régénérer
   - Évite les régénérations inutiles multiples

4. **Régénération automatique**
   - Lance `python generate_scorecard_html.py` automatiquement
   - Affiche les résultats dans le terminal

## 🎨 Workflow réel d'un développeur

### Scenario : Vous développez le design du scorecard

```bash
# Terminal 1 : Le watch tourne en arrière-plan
$ python watch_scorecard.py
👀 SURVEILLANCE DU SCORECARD HTML
...

# Terminal 2 (ou votre éditeur) : Vous modifiez le code
# Vous ouvrez generate_scorecard_html.py dans Cursor
# Vous changez la couleur du badge de score
# Vous sauvegardez (Cmd+S)

# Terminal 1 : Automatiquement
📝 Fichiers modifiés:
   • generate_scorecard_html.py
🔄 [14:32:15] Régénération du scorecard HTML...
✅ HTML régénéré avec succès!

# Vous ouvrez output/homepage.html dans le navigateur
# Vous voyez vos changements !
# Si ça ne vous plaît pas, vous modifiez encore...
# → Le cycle continue automatiquement !
```

## 💡 Avantages

1. **Pas besoin de relancer manuellement** → Gain de temps
2. **Feedback immédiat** → Vous voyez vos changements en 2-3 secondes
3. **Moins d'erreurs** → Impossible d'oublier de régénérer
4. **Workflow fluide** → Vous pouvez vous concentrer sur le code

## 🛑 Arrêter le watch

Quand vous avez fini vos modifications :
- Appuyez sur `Ctrl+C` dans le terminal où le watch tourne
- Le cache est nettoyé automatiquement

## 📝 Notes importantes

- Le watch doit tourner pour que ça fonctionne
- Il surveille uniquement les fichiers listés
- Les modifications dans `output/` ne déclenchent pas de régénération (évite les boucles)
- Si le script de génération plante, le watch continue de tourner










