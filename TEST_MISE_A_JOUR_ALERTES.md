# Guide de test - Mise à jour automatique des alertes

## Tests à effectuer

### 1. Test du scraping et mise à jour automatique

#### Prérequis
- Backend démarré : `python start_backend.py` ou `python dev.py`
- Frontend démarré (si nécessaire)

#### Étapes

1. **Vérifier l'état initial**
   ```bash
   # Compter les appartements actuels
   python -c "import json; data = json.load(open('data/scraped_apartments.json')); print(f'{len(data)} appartements dans scraped_apartments.json')"
   
   # Compter les fichiers individuels
   python -c "import os; files = [f for f in os.listdir('data/appartements') if f.endswith('.json')]; print(f'{len(files)} fichiers dans data/appartements/')"
   ```

2. **Lancer un scraping de nouveaux appartements**
   ```bash
   # Option 1: Scraper depuis une alerte Jinka
   python scrape_new_apartments.py
   
   # Option 2: Scraper depuis une alerte spécifique
   python -c "
   import asyncio
   from scrape_jinka import JinkaScraper
   
   async def test():
       scraper = JinkaScraper()
       await scraper.setup()
       if await scraper.login():
           await scraper.scrape_alert_page('VOTRE_URL_ALERTE_JINKA')
           scraper.update_scraped_apartments_json()
       await scraper.cleanup()
   
   asyncio.run(test())
   "
   ```

3. **Vérifier que scraped_apartments.json est mis à jour**
   ```bash
   # Vérifier le nombre d'appartements après scraping
   python -c "import json; data = json.load(open('data/scraped_apartments.json')); print(f'{len(data)} appartements dans scraped_apartments.json')"
   ```

4. **Vérifier que les nouveaux appartements apparaissent dans l'alerte**
   - Ouvrir le frontend dans le navigateur
   - Aller sur la page de l'alerte
   - Vérifier que les nouveaux appartements apparaissent (même sans scores complets)

### 2. Test de l'invalidation du cache

#### Test manuel

1. **Vérifier le cache avant invalidation**
   ```bash
   # Appeler l'API pour voir les appartements
   curl http://localhost:8000/api/apartments | jq 'length'
   ```

2. **Scraper un nouvel appartement**
   ```bash
   python scrape_new_apartments.py
   ```

3. **Vérifier que le cache est invalidé**
   ```bash
   # Appeler l'API à nouveau - devrait inclure les nouveaux appartements
   curl http://localhost:8000/api/apartments | jq 'length'
   ```

4. **Invalider manuellement si nécessaire**
   ```bash
   curl -X POST http://localhost:8000/api/apartments/invalidate-cache
   ```

### 3. Test des placeholders (appartements sans scores)

#### Créer un appartement de test sans scores

```python
# test_placeholder_apartment.py
import json
import os

# Créer un appartement de test minimal
test_apartment = {
    "id": "test_placeholder_123",
    "titre": "Appartement test sans scores",
    "prix": "500 000 €",
    "surface": "65 m²",
    "pieces": "3",
    "localisation": "Paris 20e",
    "description": "Appartement de test pour vérifier les placeholders"
}

# Sauvegarder dans data/appartements/
os.makedirs('data/appartements', exist_ok=True)
with open('data/appartements/test_placeholder_123.json', 'w', encoding='utf-8') as f:
    json.dump(test_apartment, f, ensure_ascii=False, indent=2)

# Mettre à jour scraped_apartments.json
from scrape_jinka import JinkaScraper
scraper = JinkaScraper()
scraper.update_scraped_apartments_json()

print("✅ Appartement de test créé")
```

#### Vérifier dans l'alerte

1. Invalider le cache : `curl -X POST http://localhost:8000/api/apartments/invalidate-cache`
2. Ouvrir l'alerte dans le frontend
3. Vérifier que l'appartement de test apparaît avec :
   - Score = 0 (ou N/A)
   - Tier = tier3
   - Pas d'erreur de chargement

### 4. Test que les analyses ne bloquent pas

#### Vérifier les logs du backend

1. **Démarrer le backend avec logs détaillés**
   ```bash
   python start_backend.py
   ```

2. **Charger une alerte avec beaucoup d'appartements**
   - Ouvrir le frontend
   - Aller sur une alerte
   - Observer les logs du backend

3. **Vérifier qu'il n'y a pas d'appels API bloquants**
   - Les logs ne doivent pas montrer d'appels à `analyze_apartment_photos_from_data`
   - Les logs ne doivent pas montrer d'appels OpenAI Vision API
   - Le chargement doit être rapide (< 2 secondes)

### 5. Test complet end-to-end

#### Scénario complet

1. **État initial**
   ```bash
   # Noter le nombre d'appartements
   python -c "import json; data = json.load(open('data/scraped_apartments.json')); print(f'État initial: {len(data)} appartements')"
   ```

2. **Scraper de nouveaux appartements**
   ```bash
   python scrape_new_apartments.py
   ```

3. **Vérifier la mise à jour**
   ```bash
   # Vérifier scraped_apartments.json
   python -c "import json; data = json.load(open('data/scraped_apartments.json')); print(f'Après scraping: {len(data)} appartements')"
   
   # Vérifier les fichiers individuels
   python -c "import os; files = [f for f in os.listdir('data/appartements') if f.endswith('.json') and not f.startswith('test_')]; print(f'Fichiers individuels: {len(files)}')"
   ```

4. **Vérifier dans l'API**
   ```bash
   # Compter via l'API
   curl http://localhost:8000/api/apartments | jq 'length'
   
   # Vérifier qu'un nouvel appartement spécifique est présent
   curl http://localhost:8000/api/apartments | jq '.[] | select(.id == "ID_DU_NOUVEL_APPARTEMENT")'
   ```

5. **Vérifier dans l'alerte**
   - Ouvrir le frontend
   - Aller sur l'alerte
   - Vérifier que les nouveaux appartements apparaissent
   - Vérifier qu'ils ont des scores (même si 0) ou des placeholders

### 6. Script de test automatisé

```python
# test_mise_a_jour_alertes.py
import json
import os
import requests
import time

def test_mise_a_jour():
    """Test complet de la mise à jour des alertes"""
    
    print("🧪 TEST: Mise à jour automatique des alertes")
    print("=" * 60)
    
    # 1. État initial
    print("\n1️⃣ État initial")
    if os.path.exists('data/scraped_apartments.json'):
        with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
            initial_data = json.load(f)
        initial_count = len(initial_data)
        print(f"   ✅ {initial_count} appartements dans scraped_apartments.json")
    else:
        initial_count = 0
        print("   ⚠️  scraped_apartments.json n'existe pas")
    
    # 2. Vérifier l'API
    print("\n2️⃣ Vérification de l'API")
    try:
        response = requests.get('http://localhost:8000/api/apartments', timeout=5)
        if response.status_code == 200:
            api_apartments = response.json()
            api_count = len(api_apartments)
            print(f"   ✅ API retourne {api_count} appartements")
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur connexion API: {e}")
        print("   💡 Assurez-vous que le backend est démarré: python start_backend.py")
        return False
    
    # 3. Vérifier le chargement depuis data/appartements/
    print("\n3️⃣ Vérification du chargement depuis data/appartements/")
    if os.path.exists('data/appartements'):
        files = [f for f in os.listdir('data/appartements') 
                if f.endswith('.json') and not f.startswith('test_')]
        print(f"   ✅ {len(files)} fichiers dans data/appartements/")
    else:
        print("   ⚠️  Dossier data/appartements/ n'existe pas")
    
    # 4. Test d'invalidation du cache
    print("\n4️⃣ Test d'invalidation du cache")
    try:
        response = requests.post('http://localhost:8000/api/apartments/invalidate-cache', timeout=5)
        if response.status_code == 200:
            print("   ✅ Cache invalidé avec succès")
        else:
            print(f"   ⚠️  Erreur invalidation: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Erreur invalidation: {e}")
    
    # 5. Vérifier qu'un appartement sans scores est géré
    print("\n5️⃣ Test des placeholders")
    try:
        # Chercher un appartement sans scores_detaille
        response = requests.get('http://localhost:8000/api/apartments', timeout=5)
        if response.status_code == 200:
            apartments = response.json()
            apts_without_scores = [apt for apt in apartments if not apt.get('scores_detaille')]
            if apts_without_scores:
                print(f"   ✅ {len(apts_without_scores)} appartements sans scores détectés (seront affichés avec placeholders)")
            else:
                print("   ℹ️  Tous les appartements ont des scores")
    except Exception as e:
        print(f"   ⚠️  Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés")
    print("\n💡 Pour tester le scraping complet:")
    print("   python scrape_new_apartments.py")
    
    return True

if __name__ == '__main__':
    test_mise_a_jour()
```

## Commandes rapides

```bash
# Test rapide
python test_mise_a_jour_alertes.py

# Vérifier les stats
curl http://localhost:8000/api/apartments/stats | jq

# Invalider le cache
curl -X POST http://localhost:8000/api/apartments/invalidate-cache

# Compter les appartements
python -c "import json; data = json.load(open('data/scraped_apartments.json')); print(f'{len(data)} appartements')"
```

## Points à vérifier

✅ Les nouveaux appartements apparaissent dans l'alerte après le scraping  
✅ Le cache est invalidé automatiquement  
✅ Les appartements sans scores sont affichés avec des placeholders (score 0, tier3)  
✅ Le chargement est rapide (pas d'analyses bloquantes)  
✅ scraped_apartments.json est mis à jour après chaque scraping  
✅ Les fichiers individuels dans data/appartements/ sont pris en compte


