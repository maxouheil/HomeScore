# 🔍 Diagnostic : Problème de Scraping Paris

## Problème Identifié

**Situation actuelle** :
- ✅ 15 alertes disponibles sur Jinka
- ❌ Seulement **42 appartements** dans `data/paris_apartments.json`
- ⚠️ Le script `scrape_all_paris.py` devrait scraper toutes les alertes

## Causes Possibles

### 1. **Le script n'a scrapé qu'une seule alerte**
   - Le script récupère automatiquement toutes les alertes via l'API
   - Mais peut-être qu'il n'a scrapé que l'alerte par défaut
   - Les autres alertes n'ont peut-être pas été traitées

### 2. **Les autres alertes ne contiennent pas d'appartements Paris**
   - Les alertes peuvent être pour d'autres villes ou critères
   - Le filtrage Paris (code postal 75xxx) peut exclure certains appartements

### 3. **Problème de pagination**
   - Le script peut ne scraper que la première page de chaque alerte
   - Il faut scraper toutes les pages (max_pages=50)

### 4. **Problème dans la récupération automatique des alertes**
   - La méthode `get_alert_list()` peut ne pas retourner toutes les alertes
   - Ou les tokens peuvent être dans un format différent

## Solutions

### Solution 1 : Diagnostic Complet (RECOMMANDÉ)

Exécuter le script de diagnostic pour comprendre le problème :

```bash
python scripts/diagnose_paris_scraping.py
```

Ce script va :
1. ✅ Se connecter à Jinka
2. ✅ Récupérer toutes les alertes disponibles
3. ✅ Diagnostiquer chaque alerte (combien d'appartements Paris)
4. ✅ Identifier les problèmes
5. ✅ Générer un rapport dans `data/diagnostic_paris_scraping.json`

### Solution 2 : Vérifier le Script Principal

Le script `scrape_all_paris.py` devrait :
- ✅ Récupérer toutes les alertes automatiquement
- ✅ Scraper toutes les pages de chaque alerte (max_pages=50)
- ✅ Filtrer les appartements Paris (code postal 75xxx)
- ✅ Supprimer les doublons
- ✅ Télécharger les photos

**Vérifier** :
- Est-ce que toutes les alertes sont bien récupérées ?
- Est-ce que toutes les pages sont scrapées ?
- Est-ce que le filtrage Paris fonctionne correctement ?

### Solution 3 : Forcer les Tokens d'Alertes

Si la récupération automatique ne fonctionne pas, créer `data/alert_tokens.json` :

```json
{
  "paris_alerts": [
    {
      "name": "Paris 1e-2e",
      "token": "TOKEN_ICI"
    },
    {
      "name": "Paris 3e-4e",
      "token": "TOKEN_ICI"
    }
    // ... etc pour toutes les alertes Paris
  ]
}
```

### Solution 4 : Tester avec une Alerte Spécifique

Tester le scraping avec une seule alerte pour voir si ça fonctionne :

```bash
python scripts/scrape_all_paris_simple.py
```

Ce script utilise une seule alerte (celle par défaut) et devrait récupérer plus d'appartements.

## Prochaines Étapes

1. **Exécuter le diagnostic** :
   ```bash
   python scripts/diagnose_paris_scraping.py
   ```

2. **Analyser les résultats** dans `data/diagnostic_paris_scraping.json`

3. **Corriger le problème identifié** :
   - Si les alertes ne sont pas toutes récupérées → Corriger `get_alert_list()`
   - Si la pagination ne fonctionne pas → Corriger `scrape_alert_page()`
   - Si le filtrage Paris est trop strict → Ajuster `is_paris_apartment()`

4. **Relancer le scraping complet** :
   ```bash
   python scripts/scrape_all_paris.py
   ```

## Estimation du Volume Attendu

Avec 15 alertes couvrant tous les arrondissements de Paris :
- **Attendu** : 5,000 - 20,000 appartements (selon les critères des alertes)
- **Actuel** : 42 appartements
- **Gap** : ~99% des appartements manquants

## Questions à Clarifier

1. **Les alertes couvrent-elles vraiment tous les arrondissements ?**
   - Vérifier les noms des alertes dans `data/alert_tokens_auto.json`
   - Certaines alertes peuvent être pour d'autres villes

2. **Les critères des alertes sont-ils assez larges ?**
   - Prix min/max ?
   - Surface min/max ?
   - Type d'appartement ?

3. **Le script a-t-il été exécuté récemment ?**
   - Vérifier la date de `data/paris_apartments.json`
   - Peut-être que le script n'a pas été exécuté avec toutes les alertes

## Commandes Utiles

```bash
# Diagnostic complet
python scripts/diagnose_paris_scraping.py

# Vérifier les alertes disponibles
python scripts/check_alerts.py

# Scraping simple (une alerte)
python scripts/scrape_all_paris_simple.py

# Scraping complet (toutes les alertes)
python scripts/scrape_all_paris.py

# Vérifier les données existantes
python -c "import json; data = json.load(open('data/paris_apartments.json')); print(f'{len(data)} appartements')"
```



