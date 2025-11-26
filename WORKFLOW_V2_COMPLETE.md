# 🔄 Workflow HomeScore v2 - Complet et Clarifié

## 📋 Principe Fondamental

**Télécharger les images UNE SEULE FOIS lors du scraping, puis utiliser les fichiers locaux pour TOUTES les analyses.**

---

## 🎯 Workflow en 3 Étapes

### Étape 1 : Scraping + Téléchargement des Images

```bash
python scrape_with_api.py
```

**Actions automatiques :**
1. ✅ Scrape les données depuis l'API Jinka (rapide)
2. ✅ **Télécharge les images en local** via `photo_manager.py`
3. ✅ Ajoute `local_path` à chaque photo dans les données
4. ✅ Sauvegarde dans `data/scraped_apartments_api_*.json`

**Structure des photos après scraping :**
```json
{
  "id": "78267327",
  "photos": [
    {
      "url": "https://media.apimo.pro/...",  // URL originale
      "local_path": "data/photos/78267327/photo_1_abc123.jpg",  // Chemin local
      "alt": "72 m² · 2e étage",
      "downloaded": true
    }
  ]
}
```

**Avantages :**
- ✅ Images téléchargées une seule fois
- ✅ Vérification automatique si déjà présentes (évite re-téléchargement)
- ✅ Noms de fichiers uniques avec hash de l'URL

---

### Étape 2 : Analyses avec Images Locales

```bash
python homescore_v2.py
```

**Ce qui se passe :**
1. ✅ Charge les données scrapées (avec `local_path`)
2. ✅ **Utilise les images locales** pour toutes les analyses :
   - Analyse de style (`analyze_apartment_style.py`)
   - Analyse de cuisine (`analyze_photos_unified.py`)
   - Analyse de baignoire (`criteria/baignoire.py`)
   - Analyse d'exposition (`criteria/exposition.py`)
   - Analyse de luminosité (`recalculate_brightness.py`)
3. ✅ **Pas de re-téléchargement** - utilise `local_path` en priorité
4. ✅ Génère les scores et le HTML

**Comment les scripts utilisent les images :**
```python
from photo_manager import PhotoManager

manager = PhotoManager()

# Dans les scripts d'analyse
for photo in apartment['photos']:
    # Utiliser le chemin local si disponible
    image_path = manager.get_photo_url_or_path(photo)
    # image_path sera soit le chemin local, soit l'URL
    
    # Charger l'image
    image_data = manager.load_photo_for_analysis(photo)
    # Charge depuis local_path si disponible, sinon télécharge depuis URL
```

---

### Étape 3 : Génération HTML avec Images Locales

Le HTML généré utilise les images locales en priorité :
- Si `local_path` existe → utilise le fichier local
- Sinon → utilise l'URL originale (fallback)

---

## 📁 Structure des Fichiers

```
data/
├── photos/                          # Images téléchargées
│   ├── 78267327/
│   │   ├── photo_1_abc123.jpg
│   │   ├── photo_2_def456.jpg
│   │   └── ...
│   ├── 93620099/
│   │   └── ...
│   └── ...
├── scraped_apartments_api_*.json    # Données avec local_path
├── scraped_apartments_v2.json      # Format unifié v2
└── scores_v2/
    └── scores.json                  # Scores avec analyses
```

---

## 🔧 Modules Créés

### `photo_manager.py`
- `PhotoManager` : Gestionnaire de téléchargement et stockage
- `download_photos_for_apartments()` : Fonction utilitaire pour télécharger en batch
- Méthodes :
  - `download_apartment_photos()` : Télécharge les photos d'un appartement
  - `get_photo_path()` : Retourne le chemin local si disponible
  - `get_photo_url_or_path()` : Retourne local_path ou URL
  - `load_photo_for_analysis()` : Charge l'image depuis local ou URL

---

## ✅ Avantages du Workflow

1. **Performance** : Images téléchargées une seule fois
2. **Fiabilité** : Pas de dépendance réseau pour les analyses
3. **Rapidité** : Analyses plus rapides (fichiers locaux)
4. **Économie** : Pas de re-téléchargement inutile
5. **Offline** : Possibilité d'analyser sans connexion
6. **Déduplication** : Hash de l'URL évite les doublons

---

## 🔄 Migration des Scripts d'Analyse

Pour utiliser les images locales dans les scripts existants :

### Avant (télécharge à chaque fois)
```python
response = requests.get(photo_url)
image = Image.open(BytesIO(response.content))
```

### Après (utilise le local_path)
```python
from photo_manager import PhotoManager

manager = PhotoManager()
image_data = manager.load_photo_for_analysis(photo)
if image_data:
    image = Image.open(BytesIO(image_data))
```

---

## 📝 Checklist d'Intégration

- [x] ✅ Créer `photo_manager.py`
- [x] ✅ Intégrer dans `scrape_with_api.py`
- [ ] Modifier `analyze_apartment_style.py` pour utiliser `photo_manager`
- [ ] Modifier `analyze_photos_unified.py` pour utiliser `photo_manager`
- [ ] Modifier `criteria/baignoire.py` pour utiliser `photo_manager`
- [ ] Modifier `criteria/exposition.py` pour utiliser `photo_manager`
- [ ] Modifier `recalculate_brightness.py` pour utiliser `photo_manager`
- [ ] Tester le workflow complet

---

## 🚀 Utilisation

### Scraping avec téléchargement des photos
```bash
python scrape_with_api.py
```

### Scoring avec images locales
```bash
python homescore_v2.py
```

Les images seront automatiquement utilisées depuis `data/photos/` si disponibles.

---

**Dernière mise à jour** : 2025-11-14




