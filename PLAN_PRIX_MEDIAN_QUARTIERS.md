# 📊 Plan pour Obtenir les Prix Médians par Quartier/Arrondissement de Paris

## 🎯 Objectif

Récupérer les prix médians au m² pour chaque quartier de Paris (ou arrondissement si quartier non disponible) afin de comparer les prix des appartements avec le marché local.

---

## 🔍 Sources Possibles

### 1. **MeilleursAgents.com** ⭐ RECOMMANDÉ

**Avantages** :
- Données fiables et mises à jour régulièrement
- Prix médians par arrondissement disponibles publiquement
- API potentielle (à vérifier)
- Données par quartier parfois disponibles

**Approche** :
1. **Scraping** : Scraper les pages de prix par arrondissement
   - URL pattern : `https://www.meilleursagents.com/prix-immobilier/paris-75XXX/`
   - Exemple : `https://www.meilleursagents.com/prix-immobilier/paris-75010/`
   - Extraire le prix médian depuis la page

2. **API** : Vérifier si une API existe (peut nécessiter authentification)

**Données disponibles** :
- Prix médian par arrondissement
- Prix médian par quartier (si disponible)
- Évolution des prix

**Exemple de structure** :
```json
{
  "75010": {
    "arrondissement": "10e",
    "prix_median_m2": 10500,
    "quartiers": {
      "Entrepôt": 9800,
      "Hôpital-Saint-Louis": 11000,
      "Porte-Saint-Martin": 10200
    }
  }
}
```

---

### 2. **SeLoger.com**

**Avantages** :
- Grande base de données
- Données par arrondissement et quartier

**Approche** :
1. **Scraping** : Pages de statistiques par arrondissement
   - URL pattern : `https://www.seloger.com/prix-immobilier/paris-75XXX/`
   - Extraire prix médian depuis les graphiques/statistiques

2. **API** : Vérifier si API disponible (peut nécessiter clé API)

**Données disponibles** :
- Prix médian par arrondissement
- Prix médian par quartier
- Prix au m² moyen

---

### 3. **INSEE (Institut National de la Statistique)**

**Avantages** :
- Données officielles et fiables
- Gratuit et public
- Données historiques

**Approche** :
1. **API INSEE** : Utiliser l'API officielle
   - Documentation : `https://api.insee.fr/`
   - Endpoint : `/donnees-locales/V0/donnees/geo-GEO2020RP2017/COM-XXXXX`
   - Nécessite inscription pour clé API

2. **Téléchargement CSV** : Télécharger les fichiers CSV depuis le site
   - URL : `https://www.insee.fr/fr/statistiques/`
   - Chercher "Prix immobilier" ou "Logement"

**Données disponibles** :
- Prix médian par commune/arrondissement
- Données démographiques
- Données économiques

**Limitation** : Peut ne pas avoir les données par quartier

---

### 4. **DVF (Demandes de Valeurs Foncières) - Ministère des Finances**

**Avantages** :
- Données officielles des transactions immobilières
- Très détaillées (par adresse)
- Gratuit

**Approche** :
1. **Téléchargement** : Télécharger les fichiers DVF
   - URL : `https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/`
   - Format : CSV par département
   - Traiter les données pour calculer médian par arrondissement/quartier

2. **API** : Utiliser l'API data.gouv.fr
   - Endpoint : `https://www.data.gouv.fr/api/1/datasets/demandes-de-valeurs-foncieres/`

**Données disponibles** :
- Toutes les transactions immobilières
- Prix, surface, adresse exacte
- Permet de calculer médian par quartier précisément

**Avantage majeur** : Permet de calculer le médian exact par quartier avec les vraies transactions

---

### 5. **PAP.fr (Particulier à Particulier)**

**Avantages** :
- Données de marché
- Prix par arrondissement

**Approche** :
- Scraping des pages de statistiques
- Moins fiable que les sources officielles

---

### 6. **APUR (Atelier Parisien d'Urbanisme)**

**Avantages** :
- Données spécialisées sur Paris
- Analyses détaillées par quartier

**Approche** :
- Téléchargement des rapports PDF/Excel
- Extraction des données

**URL** : `https://www.apur.org/`

---

## 🛠️ Implémentation Recommandée

### Phase 1 : Solution Rapide (MeilleursAgents)

**Script Python** :
```python
import requests
from bs4 import BeautifulSoup
import re
import json

def scrape_meilleursagents_median(postal_code):
    """
    Scrape le prix médian depuis MeilleursAgents pour un arrondissement
    """
    url = f"https://www.meilleursagents.com/prix-immobilier/paris-{postal_code}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Chercher le prix médian (à adapter selon la structure HTML)
    # Exemple de sélecteur (à vérifier) :
    prix_element = soup.find('span', class_='prix-median')  # À adapter
    
    if prix_element:
        prix_text = prix_element.get_text()
        # Extraire le nombre
        prix_match = re.search(r'(\d+)\s*€', prix_text)
        if prix_match:
            return int(prix_match.group(1))
    
    return None

# Générer pour tous les arrondissements
arrondissements = {
    '75001': '1er',
    '75002': '2e',
    # ... jusqu'à 75020
}

medians = {}
for postal_code, arr in arrondissements.items():
    median = scrape_meilleursagents_median(postal_code)
    if median:
        medians[postal_code] = {
            'arrondissement': arr,
            'prix_median_m2': median
        }
        print(f"{arr}: {median} €/m²")
```

**Fichier de sortie** : `data/prix_medians_arrondissements.json`

---

### Phase 2 : Solution Complète (DVF)

**Script Python** :
```python
import pandas as pd
import requests
import zipfile
import io

def download_dvf_data():
    """
    Télécharge et traite les données DVF pour Paris
    """
    # URL du fichier DVF pour Paris (75)
    url = "https://www.data.gouv.fr/fr/datasets/r/90a98de0-f562-4328-aa16-fe1174b95636"
    
    response = requests.get(url)
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    
    # Extraire le CSV
    csv_file = zip_file.open('valeursfoncieres-2023.txt')  # Nom à vérifier
    
    # Lire le CSV
    df = pd.read_csv(csv_file, sep='|', low_memory=False)
    
    # Filtrer Paris (code postal commence par 75)
    df_paris = df[df['Code postal'].astype(str).str.startswith('75')]
    
    # Calculer prix/m²
    df_paris['prix_m2'] = df_paris['Valeur foncière'] / df_paris['Surface reelle bati']
    
    # Grouper par arrondissement et calculer médian
    medians_arr = df_paris.groupby('Code postal')['prix_m2'].median()
    
    # Si on a les quartiers dans les données, grouper aussi par quartier
    # (nécessite géocodage inverse ou données supplémentaires)
    
    return medians_arr.to_dict()

# Sauvegarder
medians = download_dvf_data()
with open('data/prix_medians_dvf.json', 'w') as f:
    json.dump(medians, f, indent=2)
```

**Avantages** :
- Données officielles
- Très précises
- Permet calcul par quartier si géocodage disponible

---

### Phase 3 : Solution Hybride (Recommandée)

**Combiner plusieurs sources** :

1. **MeilleursAgents** : Pour données rapides et mises à jour
2. **DVF** : Pour validation et précision
3. **Cache local** : Stocker les résultats pour éviter requêtes répétées

**Structure de données** :
```json
{
  "75010": {
    "arrondissement": "10e",
    "prix_median_m2": 10500,
    "source": "meilleursagents",
    "last_updated": "2025-01-15",
    "quartiers": {
      "Entrepôt": {
        "prix_median_m2": 9800,
        "source": "dvf",
        "nb_transactions": 45
      },
      "Hôpital-Saint-Louis": {
        "prix_median_m2": 11000,
        "source": "dvf",
        "nb_transactions": 32
      }
    }
  }
}
```

---

## 📁 Structure de Fichiers Proposée

```
HomeScore/
├── data/
│   ├── prix_medians/
│   │   ├── arrondissements.json      # Prix médians par arrondissement
│   │   ├── quartiers.json            # Prix médians par quartier (si disponible)
│   │   └── cache_meilleursagents/    # Cache des pages scrapées
│   └── dvf/
│       └── valeursfoncieres-2023.csv # Données DVF téléchargées
├── scripts/
│   ├── fetch_prix_medians.py         # Script principal
│   ├── scrape_meilleursagents.py    # Scraper MeilleursAgents
│   ├── process_dvf.py               # Traiter données DVF
│   └── update_medians.py            # Mettre à jour les médians
└── criteria/
    └── prix.py                      # Utilise les médians (déjà mis à jour)
```

---

## 🔄 Mise à Jour des Médians

### Fréquence recommandée

- **MeilleursAgents** : Mensuel (données mises à jour régulièrement)
- **DVF** : Trimestriel ou annuel (données officielles, moins fréquentes)
- **Cache** : Conserver 30 jours minimum

### Script de mise à jour automatique

```python
# scripts/update_medians.py
import schedule
import time
from scripts.fetch_prix_medians import update_all_medians

def job():
    """Mise à jour mensuelle des prix médians"""
    print("🔄 Mise à jour des prix médians...")
    update_all_medians()
    print("✅ Mise à jour terminée")

# Planifier tous les 1er du mois
schedule.every().month.do(job)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Vérifier toutes les heures
```

---

## 🎯 Plan d'Action Immédiat

### Étape 1 : Scraper MeilleursAgents (1-2h)

1. Créer `scripts/scrape_meilleursagents.py`
2. Tester sur 2-3 arrondissements
3. Générer `data/prix_medians/arrondissements.json`
4. Intégrer dans `criteria/prix.py`

### Étape 2 : Traiter DVF (2-3h)

1. Télécharger données DVF 2023
2. Créer `scripts/process_dvf.py`
3. Calculer médians par arrondissement
4. Comparer avec MeilleursAgents (validation)

### Étape 3 : Quartiers (Optionnel, 3-4h)

1. Géocoder les adresses DVF
2. Mapper aux quartiers (via API géocodage inverse)
3. Calculer médians par quartier
4. Créer `data/prix_medians/quartiers.json`

### Étape 4 : Automatisation (1h)

1. Script de mise à jour automatique
2. Intégration dans le pipeline de scraping
3. Tests et validation

---

## 📊 Sources de Données par Quartier

Si besoin de données par quartier précis :

1. **Géocodage inverse** : Convertir adresses DVF → coordonnées → quartiers
   - API : Nominatim (OpenStreetMap), Google Geocoding API
   - Mapping : Utiliser `map_info.quartier` déjà disponible dans les données

2. **APUR** : Rapports détaillés par quartier
   - URL : `https://www.apur.org/fr/nos-travaux/observatoire-des-prix-immobiliers`

3. **Mairie de Paris** : Données officielles par quartier
   - URL : `https://opendata.paris.fr/`

---

## ⚠️ Points d'Attention

1. **Rate Limiting** : Respecter les limites des APIs/scraping
2. **Données à jour** : Les prix évoluent, mettre à jour régulièrement
3. **Précision** : DVF = données réelles, MeilleursAgents = estimations
4. **Quartiers** : Certains quartiers peuvent avoir peu de transactions → médian moins fiable
5. **Type de bien** : Filtrer par type (appartement vs maison) si nécessaire

---

## ✅ Checklist Implémentation

- [ ] Créer `scripts/scrape_meilleursagents.py`
- [ ] Tester scraping sur 2-3 arrondissements
- [ ] Générer `data/prix_medians/arrondissements.json`
- [ ] Mettre à jour `criteria/prix.py` pour utiliser les médians
- [ ] Tester avec quelques appartements
- [ ] (Optionnel) Traiter données DVF
- [ ] (Optionnel) Calculer médians par quartier
- [ ] Créer script de mise à jour automatique
- [ ] Documenter dans README

---

*Document créé le : 2025-01-XX*
*Version : 1.0*

