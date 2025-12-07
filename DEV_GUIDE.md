# 🛠️ Guide de Développement - HomeScore

## 🚀 Démarrage Rapide

### Mode Développement (Recommandé)

Lancez le serveur de développement qui démarre automatiquement le backend et le frontend :

```bash
python dev.py
```

**Ce que fait `dev.py` :**
- ✅ Vérifie les dépendances Python (FastAPI, Uvicorn, etc.)
- ✅ Installe les dépendances npm si nécessaire
- ✅ Démarre le backend FastAPI sur `http://localhost:8000`
- ✅ Démarre le frontend Vite sur `http://localhost:5173`
- ✅ Ouvre automatiquement le navigateur

### URLs Disponibles

- **Frontend React** : http://localhost:5173
- **Backend API** : http://localhost:8000
- **API Documentation** : http://localhost:8000/docs
- **WebSocket** : ws://localhost:8000/ws

## 📁 Architecture

### Backend (FastAPI)

**Structure :**
```
backend/
├── main.py              # Application FastAPI principale
├── api/
│   └── apartments.py    # Endpoint REST /api/apartments
└── watch_service.py     # Surveillance fichiers + WebSocket
```

**Endpoints disponibles :**
- `GET /api/apartments` : Liste tous les appartements avec scores
- `GET /docs` : Documentation interactive Swagger
- `WS /ws` : WebSocket pour mises à jour temps réel

**Surveillance automatique :**
Le `WatchService` surveille automatiquement :
- `data/scores/all_apartments_scores.json`
- `data/scraped_apartments.json`
- Fichiers Python de scoring et génération HTML

Lorsqu'un fichier change, le service :
1. Invalide le cache API
2. Envoie une notification WebSocket aux clients connectés
3. Le frontend recharge automatiquement les données

### Frontend (React + Vite)

**Structure :**
```
frontend/src/
├── App.jsx                    # Composant principal
├── components/
│   ├── ApartmentCard.jsx     # Carte d'appartement
│   ├── Carousel.jsx          # Carousel de photos
│   └── ScoreBadge.jsx       # Badge de score
└── utils/
    └── scoreUtils.js         # Calcul mega score
```

**Fonctionnalités :**
- **Hot Module Replacement (HMR)** : Rechargement instantané des modifications
- **WebSocket** : Écoute des mises à jour depuis le backend
- **Tri automatique** : Appartements triés par mega score décroissant
- **Formatage intelligent** : Extraction automatique de prix, quartier, étage, prix/m²

## 🔧 Développement

### Modifier le Backend

1. Modifiez les fichiers dans `backend/`
2. Le serveur redémarre automatiquement (Uvicorn reload)
3. Les changements sont immédiatement visibles

### Modifier le Frontend

1. Modifiez les fichiers dans `frontend/src/`
2. Vite recharge automatiquement (HMR)
3. Les changements sont instantanés dans le navigateur

### Ajouter un Nouveau Critère

1. **Backend** : Ajoutez le critère dans `scoring.py` et `criteria/`
2. **Frontend** : Ajoutez l'affichage dans `ApartmentCard.jsx`
3. **Utils** : Mettez à jour `calculateMegaScore()` dans `scoreUtils.js`

### Debugging

**Backend :**
```bash
# Voir les logs du backend
tail -f logs/backend.log  # Si logging configuré
```

**Frontend :**
- Ouvrez la console du navigateur (F12)
- Les logs WebSocket apparaissent dans la console
- Les erreurs React sont affichées dans la console

## 🐛 Troubleshooting

### Le frontend ne se connecte pas au backend

**Vérifier :**
1. Le backend est démarré sur le port 8000
2. Le frontend utilise le proxy configuré dans `vite.config.js`
3. Pas de CORS errors dans la console

**Solution :**
```bash
# Vérifier que le backend écoute
curl http://localhost:8000/api/apartments
```

### Les mises à jour WebSocket ne fonctionnent pas

**Vérifier :**
1. Le WebSocket est connecté (console navigateur)
2. Le `WatchService` est démarré (logs backend)
3. Les fichiers surveillés existent

**Solution :**
```bash
# Tester le WebSocket manuellement
# Dans la console navigateur :
const ws = new WebSocket('ws://localhost:8000/ws')
ws.onmessage = (e) => console.log('Message:', e.data)
```

### Les scores ne sont pas corrects

**Vérifier :**
1. Les scores dans `data/scores/all_apartments_scores.json`
2. Le calcul dans `scoreUtils.js`
3. La cohérence entre backend et frontend

**Solution :**
```bash
# Recalculer les scores
python homescore.py
```

## 📊 Format des Données

### Structure d'un Appartement

```json
{
  "id": "90931157",
  "url": "https://www.jinka.fr/...",
  "prix": "775 000 €",
  "prix_m2": "11071 €/m²",
  "surface": "70 m²",
  "etage": "4e étage",
  "localisation": "Paris 19e (75019)",
  "scores_detaille": {
    "localisation": { "score": 20, "tier": "tier1" },
    "prix": { "score": 10, "tier": "tier2" },
    "style": { "score": 20, "tier": "tier1" },
    "ensoleillement": { "score": 20, "tier": "tier1" },
    "cuisine": { "score": 10, "tier": "tier1" },
    "baignoire": { "score": 10, "tier": "tier1" }
  },
  "style_analysis": {
    "style": { "type": "haussmannien", "confidence": 0.85 },
    "cuisine": { "ouverte": true, "confidence": 0.95 },
    "luminosite": { "type": "excellente", "confidence": 0.90 }
  }
}
```

## 🎯 Bonnes Pratiques

### Calcul des Scores

- Utilisez toujours `calculateMegaScore()` pour garantir la cohérence
- Les scores affichés doivent correspondre au mega score
- Vérifiez la cohérence entre tier et score

### Formatage des Données

- Extrayez les données depuis plusieurs sources (fallback)
- Formatez les prix en "k" (ex: 775k)
- Extrayez le quartier depuis `map_info`, `scores_detaille`, ou `exposition`
- Calculez le prix/m² si non disponible

### Performance

- Utilisez `useMemo` pour les calculs coûteux
- Limitez le nombre de photos affichées (max 10)
- Le tri se fait côté client (rapide pour < 100 appartements)

## 📝 Scripts Utiles

### Redémarrer le Serveur

```bash
# Arrêter (Ctrl+C) puis relancer
python dev.py
```

### Vérifier les Dépendances

```bash
# Python
pip list | grep -E "fastapi|uvicorn|websockets"

# Node.js
cd frontend && npm list
```

### Nettoyer le Cache

```bash
# Cache Vite
rm -rf frontend/node_modules/.vite

# Cache Python
find . -type d -name __pycache__ -exec rm -r {} +
```

---

**Dernière mise à jour** : 2025-01-31

