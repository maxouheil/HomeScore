# Guide d'utilisation - Auto-reload du Scorecard HTML

Ce guide explique comment utiliser les scripts de watch pour éviter de relancer manuellement `generate_scorecard_html.py` à chaque modification.

## 🎯 Solutions disponibles

### Solution 1: Watch simple (recommandé)

**Script:** `watch_scorecard.py`

Surveille automatiquement tous les fichiers pertinents et régénère le HTML dès qu'un changement est détecté.

```bash
python watch_scorecard.py
```

**Fonctionnalités:**
- ✅ Surveillance automatique des fichiers backend (Python)
- ✅ Surveillance des fichiers de données (JSON)
- ✅ Surveillance des fichiers de configuration
- ✅ Debounce pour éviter les régénérations trop fréquentes
- ✅ Aucune dépendance externe requise

**Fichiers surveillés:**
- `generate_scorecard_html.py` (script principal)
- `extract_baignoire.py`
- `analyze_photos.py`
- `analyze_apartment_style.py`
- `data/scores/all_apartments_scores.json`
- `data/scraped_apartments.json`
- `scoring_config.json`
- `scoring_prompt.txt`
- Tous les fichiers dans `criteria/`

### Solution 2: Serveur HTTP avec auto-reload

**Script:** `watch_scorecard_server.py`

Lance un serveur HTTP local et régénère automatiquement le HTML. Parfait pour visualiser les changements en direct dans le navigateur.

```bash
python watch_scorecard_server.py
```

**Fonctionnalités:**
- ✅ Toutes les fonctionnalités de la solution 1
- ✅ Serveur HTTP sur `http://localhost:8000`
- ✅ Ouverture automatique du navigateur
- ✅ Visualisation en temps réel des changements

**URL:** `http://localhost:8000/output/homepage.html`

### Solution 3: Watch avec watchdog (avancé)

**Script:** `watch_regenerate.py` (existant)

Utilise la bibliothèque `watchdog` pour une surveillance plus efficace des événements système.

```bash
pip install watchdog
python watch_regenerate.py
```

## 📋 Comparaison des solutions

| Solution | Simplicité | Performance | Visualisation | Dépendances |
|----------|------------|-------------|---------------|-------------|
| `watch_scorecard.py` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Aucune |
| `watch_scorecard_server.py` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Aucune |
| `watch_regenerate.py` | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | watchdog |

## 🚀 Utilisation recommandée

### Pour le développement quotidien

```bash
# Terminal 1: Lancer le watch
python watch_scorecard.py

# Terminal 2: Faire vos modifications
# Le HTML sera régénéré automatiquement
```

### Pour le développement avec visualisation

```bash
# Terminal unique: Serveur avec auto-reload
python watch_scorecard_server.py

# Le navigateur s'ouvrira automatiquement
# Modifiez les fichiers, le HTML se régénère automatiquement
# Rafraîchissez la page pour voir les changements
```

## ⚙️ Configuration

### Modifier l'intervalle de vérification

Dans `watch_scorecard.py`, modifiez la ligne:
```python
watcher.watch(poll_interval=1)  # Changez 1 à votre valeur (en secondes)
```

### Modifier le debounce

Dans `watch_scorecard.py`, modifiez:
```python
watcher = ScorecardWatcher(debounce_seconds=2)  # Changez 2 à votre valeur
```

### Modifier le port du serveur

Dans `watch_scorecard_server.py`, modifiez:
```python
server = ScorecardWatcherServer(port=8000)  # Changez 8000 à votre port
```

## 🔍 Comment ça marche?

1. **Polling**: Le script vérifie périodiquement les temps de modification des fichiers
2. **Cache**: Un fichier `.watch_scorecard_cache.txt` stocke les derniers temps de modification
3. **Détection**: Si un fichier a changé, le script détecte la différence
4. **Debounce**: Pour éviter les régénérations trop fréquentes, un délai de 2 secondes est appliqué
5. **Régénération**: Le script lance `generate_scorecard_html.py` automatiquement

## 🐛 Dépannage

### Le HTML ne se régénère pas

1. Vérifiez que les fichiers existent et sont accessibles
2. Vérifiez les permissions d'écriture dans le dossier `output/`
3. Consultez les messages d'erreur dans le terminal

### Trop de régénérations

Augmentez le `debounce_seconds` dans le script:
```python
watcher = ScorecardWatcher(debounce_seconds=5)  # 5 secondes au lieu de 2
```

### Le serveur HTTP ne démarre pas

Vérifiez que le port 8000 n'est pas déjà utilisé:
```bash
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

## 💡 Astuces

1. **Fichiers ignorés**: Le script ignore automatiquement les fichiers cachés (`.pyc`, `__pycache__`, etc.)

2. **Première génération**: Lancez `generate_scorecard_html.py` une première fois manuellement pour créer le fichier HTML initial

3. **Multi-terminaux**: Vous pouvez avoir plusieurs watchs qui tournent en parallèle (chacun dans son terminal)

4. **Intégration IDE**: Certains IDE permettent de lancer automatiquement le watch au démarrage du projet

## 📝 Notes

- Le fichier cache `.watch_scorecard_cache.txt` est créé automatiquement et peut être supprimé sans problème
- Les scripts fonctionnent sur macOS, Linux et Windows
- Aucune dépendance externe n'est requise (sauf pour `watch_regenerate.py` qui nécessite `watchdog`)

