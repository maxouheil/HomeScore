# 🔄 Workflow HomeScore v2 - Gestion des Images

## 📋 Principe

**Télécharger les images une seule fois lors du scraping, puis les utiliser localement pour toutes les analyses.**

---

## 🎯 Workflow Complet

### Phase 1 : Scraping avec Téléchargement des Images

```bash
python scrape_with_api.py
```

**Ce qui se passe :**
1. ✅ Scrape les données depuis l'API (rapide, ~5 secondes pour 42 appartements)
2. ✅ **Télécharge automatiquement les images en local** (`data/photos/{apartment_id}/`)
3. ✅ Sauvegarde les chemins locaux dans les données (`local_path`)
4. ✅ Sauvegarde dans `data/scraped_apartments_api_*.json`

**Gestion intelligente :**
- ✅ Vérifie si l'image existe déjà (évite re-téléchargement)
- ✅ Génère des noms de fichiers uniques avec hash de l'URL
- ✅ Conserve l'URL originale pour référence

**Format des données après scraping :**
```json
{
  "id": "78267327",
  "photos": [
    {
      "url": "https://...",  // URL originale (pour référence)
      "local_path": "data/photos/78267327/photo_1.jpg",  // Chemin local
      "alt": "72 m² · 2e étage"
    }
  ]
}
```

---

### Phase 2 : Analyses avec Images Locales

```bash
python homescore_v2.py
```

**Ce qui se passe :**
1. ✅ Charge les données scrapées (avec chemins locaux)
2. ✅ Utilise les images locales pour :
   - Analyse de style (`analyze_apartment_style.py`)
   - Analyse de cuisine (`analyze_photos_unified.py`)
   - Analyse de baignoire (`criteria/baignoire.py`)
   - Analyse d'exposition (`criteria/exposition.py`)
   - Analyse de luminosité (`recalculate_brightness.py`)
3. ✅ Évite de re-télécharger les images
4. ✅ Génère les scores et le HTML

---

## 🛠️ Implémentation

### 1. Modifier `scrape_jinka_api.py` pour télécharger les images

**Ajouter une fonction de téléchargement :**
```python
async def download_photos_locally(apartment_data):
    """Télécharge les photos en local et met à jour les chemins"""
    photos = apartment_data.get('photos', [])
    apartment_id = apartment_data.get('id')
    
    if not photos or not apartment_id:
        return apartment_data
    
    photos_dir = Path(f'data/photos/{apartment_id}')
    photos_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_photos = []
    for i, photo in enumerate(photos, 1):
        url = photo.get('url')
        if not url:
            continue
        
        # Vérifier si déjà téléchargée
        local_path = photos_dir / f'photo_{i}.jpg'
        if local_path.exists():
            print(f"   ✅ Photo {i} déjà téléchargée")
        else:
            # Télécharger
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    print(f"   ✅ Photo {i} téléchargée")
                else:
                    print(f"   ⚠️  Erreur téléchargement photo {i}")
                    continue
            except Exception as e:
                print(f"   ⚠️  Erreur: {e}")
                continue
        
        # Mettre à jour avec le chemin local
        photo['local_path'] = str(local_path)
        downloaded_photos.append(photo)
    
    apartment_data['photos'] = downloaded_photos
    return apartment_data
```

### 2. Modifier les scripts d'analyse pour utiliser les chemins locaux

**Dans `analyze_apartment_style.py` :**
```python
def get_photo_path(photo):
    """Retourne le chemin local si disponible, sinon l'URL"""
    return photo.get('local_path') or photo.get('url')
```

**Dans `criteria/exposition.py` :**
```python
def load_photo_for_analysis(photo):
    """Charge une photo depuis le chemin local ou télécharge depuis l'URL"""
    local_path = photo.get('local_path')
    if local_path and Path(local_path).exists():
        return Image.open(local_path)
    else:
        # Fallback : télécharger depuis l'URL
        url = photo.get('url')
        response = requests.get(url)
        return Image.open(BytesIO(response.content))
```

---

## 📁 Structure des Fichiers

```
data/
├── photos/
│   ├── 78267327/
│   │   ├── photo_1.jpg
│   │   ├── photo_2.jpg
│   │   └── photo_3.jpg
│   ├── 93620099/
│   │   └── ...
│   └── ...
├── scraped_apartments_api_*.json  (avec local_path dans photos)
└── scores_v2/
    └── scores.json
```

---

## ✅ Avantages

1. **Performance** : Images téléchargées une seule fois
2. **Fiabilité** : Pas de dépendance réseau pour les analyses
3. **Rapidité** : Analyses plus rapides (fichiers locaux)
4. **Économie** : Pas de re-téléchargement inutile
5. **Offline** : Possibilité d'analyser sans connexion

---

## 🔄 Migration depuis v1

Pour migrer les anciennes données :
1. Identifier les appartements sans images locales
2. Télécharger les images depuis les URLs
3. Mettre à jour les données avec les chemins locaux

---

**Dernière mise à jour** : 2025-11-14

