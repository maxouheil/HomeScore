# 🚀 Quick Start - Auto-reload du Scorecard

## ✅ Ce qui a été créé

J'ai créé **2 nouveaux scripts** pour éviter de relancer manuellement `generate_scorecard_html.py` :

1. **`watch_scorecard.py`** - Watch simple et efficace
2. **`watch_scorecard_server.py`** - Watch avec serveur HTTP intégré

## 🎯 Utilisation rapide

### Option 1: Watch simple (recommandé)

```bash
python watch_scorecard.py
```

**Ce que ça fait :**
- ✅ Surveille automatiquement tous les fichiers backend/frontend
- ✅ Régénère le HTML dès qu'un fichier change
- ✅ Affiche les logs dans le terminal

**Fichiers surveillés :**
- `generate_scorecard_html.py`
- `extract_baignoire.py`, `analyze_photos.py`, etc.
- `data/scores/all_apartments_scores.json`
- `data/scraped_apartments.json`
- Tous les fichiers dans `criteria/`

### Option 2: Watch avec serveur HTTP

```bash
python watch_scorecard_server.py
```

**Ce que ça fait :**
- ✅ Tout ce que fait l'option 1
- ✅ Lance un serveur HTTP sur `http://localhost:8000`
- ✅ Ouvre automatiquement le navigateur
- ✅ Visualisation en temps réel des changements

## 📝 Workflow recommandé

### Terminal 1 : Lancer le watch
```bash
python watch_scorecard.py
```

### Terminal 2 : Faire vos modifications
```bash
# Modifiez vos fichiers Python, JSON, etc.
# Le HTML sera régénéré automatiquement !
```

## ✅ Tests effectués

Tous les tests passent avec succès :
- ✅ Initialisation du watcher
- ✅ Détection de 15 fichiers à surveiller
- ✅ Détection des changements de fichiers
- ✅ Régénération automatique du HTML

## 💡 Exemple d'utilisation

1. **Lancez le watch :**
   ```bash
   python watch_scorecard.py
   ```

2. **Dans un autre terminal, modifiez un fichier :**
   ```bash
   # Par exemple, modifiez generate_scorecard_html.py
   nano generate_scorecard_html.py
   # ou
   code generate_scorecard_html.py
   ```

3. **Sauvegardez le fichier** → Le HTML se régénère automatiquement !

4. **Vérifiez le résultat :**
   ```bash
   open output/homepage.html
   ```

## 🛑 Arrêter le watch

Appuyez sur `Ctrl+C` dans le terminal où le watch tourne.

## 📚 Documentation complète

Voir `WATCH_GUIDE.md` pour plus de détails et d'options avancées.

