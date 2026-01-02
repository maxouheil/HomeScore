# 🚨 RÈGLE CRITIQUE : Chemins de fichiers

## ⚠️ PROBLÈME RÉCURRENT

Les fichiers sont créés dans `/Users/sou/Desktop/HomeScore` au lieu de `/Users/sou/Desktop/CURSOR/HomeScore`.

## ✅ SOLUTION : TOUJOURS utiliser `PROJECT_ROOT`

### Règle #1 : Import obligatoire

**TOUJOURS** importer `PROJECT_ROOT` depuis `project_config.py` :

```python
from project_config import PROJECT_ROOT, DATA_DIR, PHOTOS_DIR, SCORES_DIR
```

### Règle #2 : Ne JAMAIS utiliser `Path(__file__).parent`

❌ **MAUVAIS** :
```python
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
```

✅ **BON** :
```python
from project_config import DATA_DIR
```

### Règle #3 : Ne JAMAIS utiliser de chemins relatifs sans PROJECT_ROOT

❌ **MAUVAIS** :
```python
data_dir = Path('data')
with open('data/scores.json', 'w') as f:
    ...
```

✅ **BON** :
```python
from project_config import SCORES_DIR
with open(SCORES_DIR / 'scores.json', 'w') as f:
    ...
```

### Règle #4 : Ne JAMAIS coder en dur des chemins absolus

❌ **MAUVAIS** :
```python
fichier = '/Users/sou/Desktop/HomeScore/data/scores.json'
```

✅ **BON** :
```python
from project_config import SCORES_DIR
fichier = SCORES_DIR / 'scores.json'
```

## 📋 Checklist avant de créer un fichier

- [ ] J'ai importé `PROJECT_ROOT` ou les chemins depuis `project_config.py`
- [ ] Je n'utilise pas `Path(__file__).parent` pour les chemins de données
- [ ] Je n'utilise pas de chemins relatifs sans `PROJECT_ROOT`
- [ ] Je n'ai pas codé en dur de chemin absolu
- [ ] J'utilise `PROJECT_ROOT / "chemin/relatif"` ou les constantes prédéfinies

## 🔧 Chemins disponibles dans `project_config.py`

- `PROJECT_ROOT` : `/Users/sou/Desktop/CURSOR/HomeScore`
- `DATA_DIR` : `PROJECT_ROOT / "data"`
- `PHOTOS_DIR` : `DATA_DIR / "photos"`
- `SCORES_DIR` : `DATA_DIR / "scores"`
- `OUTPUT_DIR` : `PROJECT_ROOT / "output"`
- `LOGS_DIR` : `PROJECT_ROOT / "logs"`
- `APARTMENTS_FILE` : `SCORES_DIR / "all_apartments_scores.json"`
- `JINKA_APARTMENTS_FILE` : `DATA_DIR / "jinka_apartments.json"`

## 📝 Exemples d'utilisation

### Créer un fichier dans data/
```python
from project_config import DATA_DIR

output_file = DATA_DIR / "mon_fichier.json"
with open(output_file, 'w') as f:
    json.dump(data, f)
```

### Créer un fichier dans scores/
```python
from project_config import SCORES_DIR

score_file = SCORES_DIR / "scores.json"
with open(score_file, 'w') as f:
    json.dump(scores, f)
```

### Créer un fichier personnalisé
```python
from project_config import PROJECT_ROOT

custom_file = PROJECT_ROOT / "mon_dossier" / "mon_fichier.txt"
custom_file.parent.mkdir(parents=True, exist_ok=True)
with open(custom_file, 'w') as f:
    f.write("contenu")
```

## 🚫 Fichiers à NE JAMAIS modifier

Si vous voyez ces patterns, **STOP** et utilisez `PROJECT_ROOT` :

- `Path(__file__).parent / "data"`
- `Path('data')`
- `'/Users/sou/Desktop/HomeScore/...'` (chemins codés en dur)
- `os.path.join(os.path.dirname(__file__), 'data')`

## ✅ Fichiers déjà corrigés

- `project_config.py` - Configuration centralisée
- `config_jinka.py` - Utilise `PROJECT_ROOT`
- `data_loader.py` - Utilise `PROJECT_ROOT`
- `photo_downloader.py` - Utilise `PROJECT_ROOT`
- `photo_manager.py` - Utilise `PROJECT_ROOT`
- `extraire_dates_creation.py` - Utilise `PROJECT_ROOT`
- `ajouter_date_creation.py` - Utilise `PROJECT_ROOT`
- `analyser_appartement.py` - Utilise `PROJECT_ROOT`
- `trouver_appartement.py` - Utilise `PROJECT_ROOT`

## 🔍 Comment vérifier

Si vous n'êtes pas sûr, utilisez la fonction de validation :

```python
from project_config import validate_path, PROJECT_ROOT

file_path = PROJECT_ROOT / "data" / "test.json"
if validate_path(file_path):
    print("✅ Chemin valide")
```

## 📞 En cas de doute

**TOUJOURS** utiliser `PROJECT_ROOT` depuis `project_config.py`. C'est la seule source de vérité pour les chemins de fichiers.

---

## 🚨 RÈGLE : Format des chemins dans la documentation Markdown

### ⚠️ PROBLÈME RÉCURRENT

Dans tous les fichiers Markdown (`.md`), les références au chemin du projet utilisent parfois `Cursor /homescore` avec un espace, ce qui est **INTERDIT**.

### ✅ SOLUTION : TOUJOURS utiliser `Cursor/homescore` (SANS espace)

**RÈGLE ABSOLUE** : 

❌ **INTERDIT** : `Cursor /homescore` (avec espace)
✅ **OBLIGATOIRE** : `Cursor/homescore` (sans espace)

### Exemples dans les fichiers Markdown

❌ **MAUVAIS** :
```markdown
Le projet est situé dans Cursor /homescore
Le chemin est Cursor /homescore/data
```

✅ **BON** :
```markdown
Le projet est situé dans Cursor/homescore
Le chemin est Cursor/homescore/data
```

### 📋 Checklist pour tous les fichiers `.md`

- [ ] J'ai vérifié que toutes les références utilisent `Cursor/homescore` (sans espace)
- [ ] Je n'ai pas utilisé `Cursor /homescore` (avec espace)
- [ ] Tous les chemins relatifs au projet utilisent le format correct

**Cette règle s'applique à TOUS les fichiers Markdown du projet.**