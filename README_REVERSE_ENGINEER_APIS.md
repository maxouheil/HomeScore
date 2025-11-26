# Reverse Engineer APIs SeLoger et LeBonCoin

Ce document résume l'implémentation complète du reverse engineering des APIs de SeLoger et LeBonCoin, similaire à ce qui a été fait pour Jinka.

## 📁 Fichiers Créés

### Scripts d'Exploration

- **`explore_seloger_api.py`** - Script pour intercepter et capturer toutes les requêtes réseau SeLoger
- **`explore_leboncoin_api.py`** - Script pour intercepter et capturer toutes les requêtes réseau LeBonCoin

### Clients API

- **`seloger_api_client.py`** - Client API pour SeLoger avec retry, rate limiting et cache
- **`leboncoin_api_client.py`** - Client API pour LeBonCoin avec retry, rate limiting et cache
- **`api_client_base.py`** - Classe de base et interface commune pour tous les clients API

### Scrapers

- **`scrape_seloger.py`** - Scraper SeLoger utilisant l'API avec fallback HTML
- **`scrape_leboncoin.py`** - Scraper LeBonCoin utilisant l'API avec fallback HTML

### Documentation

- **`docs/api/seloger_endpoints.md`** - Documentation des endpoints SeLoger (à compléter)
- **`docs/api/leboncoin_endpoints.md`** - Documentation des endpoints LeBonCoin (à compléter)
- **`GUIDE_REVERSE_ENGINEER_SELOGER.md`** - Guide complet pour SeLoger
- **`GUIDE_REVERSE_ENGINEER_LEBONCOIN.md`** - Guide complet pour LeBonCoin

## 🚀 Utilisation

### Étape 1 : Explorer les APIs

Pour découvrir les endpoints réels, exécutez les scripts d'exploration :

```bash
# Explorer SeLoger
python explore_seloger_api.py

# Explorer LeBonCoin
python explore_leboncoin_api.py
```

Ces scripts vont :
1. Ouvrir un navigateur Chrome (visible)
2. Naviguer sur le site
3. Effectuer des recherches
4. Capturer toutes les requêtes réseau
5. Sauvegarder les résultats dans `data/api_exploration/`

### Étape 2 : Analyser les Résultats

Les résultats sont sauvegardés dans :
- `data/api_exploration/seloger/` pour SeLoger
- `data/api_exploration/leboncoin/` pour LeBonCoin

Analysez les fichiers générés :
- `endpoints_*.json` - Liste des endpoints identifiés
- `responses_*.json` - Réponses complètes des APIs
- `cookies_*.json` - Cookies de session
- `tokens_*.json` - Tokens d'authentification
- `report_*.txt` - Rapport textuel

### Étape 3 : Adapter les Clients API

Une fois les endpoints identifiés, adaptez les clients API :

1. **Mettre à jour les URLs de base** dans `seloger_api_client.py` et `leboncoin_api_client.py`
2. **Adapter les méthodes** selon les endpoints réels découverts
3. **Mettre à jour la structure des données** selon les réponses JSON réelles

### Étape 4 : Utiliser les Scrapers

Les scrapers peuvent être utilisés directement :

```python
from scrape_seloger import SeLogerScraper

scraper = SeLogerScraper()
await scraper.setup()
properties = await scraper.search_properties(location="Paris", rooms=[2, 3])
```

## 📊 Structure des Données

Toutes les propriétés sont normalisées dans la classe `PropertyData` :

```python
from api_client_base import PropertyData

property = PropertyData(
    source='seloger',
    property_id='12345',
    title='Appartement 2 pièces',
    price=1500,
    surface=50,
    rooms=2,
    location={'city': 'Paris'},
    photos=['https://...'],
    url='https://...'
)
```

## 🔧 Configuration

Les clients API supportent plusieurs options :

- **Cache** : Activé par défaut pour améliorer les performances
- **Rate Limiting** : Délais automatiques entre les requêtes
- **Retry** : Retry automatique avec backoff exponentiel
- **Fallback** : Les scrapers peuvent basculer sur le scraping HTML si l'API échoue

## ⚠️ Points Importants

1. **Les endpoints sont des estimations** - Ils doivent être confirmés lors de l'exploration réelle
2. **Respecter les limites** - Ne pas surcharger les serveurs avec trop de requêtes
3. **Usage personnel** - Utiliser uniquement pour usage personnel/automatisation légitime
4. **Terms of Service** - Respecter les conditions d'utilisation de chaque site

## 📚 Documentation Complète

Pour plus de détails, consultez :

- [Guide SeLoger](GUIDE_REVERSE_ENGINEER_SELOGER.md)
- [Guide LeBonCoin](GUIDE_REVERSE_ENGINEER_LEBONCOIN.md)
- [Documentation endpoints SeLoger](docs/api/seloger_endpoints.md)
- [Documentation endpoints LeBonCoin](docs/api/leboncoin_endpoints.md)

## 🔄 Prochaines Étapes

1. ✅ Scripts d'exploration créés
2. ✅ Clients API créés (structure de base)
3. ✅ Scrapers créés avec fallback
4. ✅ Documentation créée
5. ⏳ **À faire** : Exécuter les scripts d'exploration pour découvrir les vrais endpoints
6. ⏳ **À faire** : Adapter les clients API avec les endpoints réels
7. ⏳ **À faire** : Tester et valider le fonctionnement

## 🎯 Résultat Final

Une fois complété, vous aurez :

- ✅ Des clients API fonctionnels pour SeLoger et LeBonCoin
- ✅ Des scrapers utilisant les APIs avec fallback HTML
- ✅ Une interface commune pour tous les clients API
- ✅ Une documentation complète des endpoints
- ✅ Des guides d'utilisation détaillés

Tout est prêt pour l'exploration et l'adaptation selon les endpoints réels découverts !



