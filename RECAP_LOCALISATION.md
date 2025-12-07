# 📍 Récapitulatif - Fonctionnement de la Localisation

## Vue d'ensemble

Le système de **Localisation** dans HomeScore gère l'extraction, le formatage et le scoring de la localisation des appartements. Il utilise principalement les données de l'API Jinka (plus fiable que le scraping HTML) et permet de classer les appartements selon des zones prioritaires définies.

---

## 🔄 1. Extraction de la Localisation

### Source de données : API Jinka (prioritaire)

La localisation est **récupérée directement depuis l'API** Jinka, sans scraping HTML :

```python
# Dans api_data_adapter.py (lignes 50-54)
city = ad.get('city', '')
postal_code = ad.get('postal_code', '')
localisation = f"{city} ({postal_code})" if postal_code else city
```

**Champs API utilisés :**
- `city` : Nom de la ville (ex: "Paris")
- `postal_code` : Code postal (ex: "75020")
- `quartier_name` : Nom du quartier officiel (optionnel)
- `lat` / `lng` : Coordonnées GPS

**Format résultant :**
- `"Paris (75020)"` si code postal disponible
- `"Paris"` sinon

### Fallback scraping HTML (si API indisponible)

Si l'API n'est pas disponible, le système utilise le scraping HTML avec plusieurs fallbacks :
1. Extraction depuis le texte de l'annonce
2. Utilisation des stations de métro comme localisation
3. "Localisation non trouvée" en dernier recours

---

## 🎯 2. Formatage de la Localisation

### Format d'affichage : "Metro · Quartier"

Le formatage est géré par `criteria/localisation.py` :

```python
def format_localisation(apartment):
    metro = get_metro_name(apartment)      # Meilleure station (tier 1 prioritaire)
    quartier = get_quartier_name(apartment) # Nom du quartier
    
    # Format: "Metro Ménilmontant · Sorbier"
    return " · ".join([f"Metro {metro}", quartier])
```

### Extraction du Métro

**Priorité d'extraction** (dans `get_all_metro_stations()` puis `get_metro_name()`) :

1. **`scores_detaille.localisation.justification`** : Extraction depuis la justification générée par l'IA
2. **`map_info.metros`** : Liste des stations depuis les données de carte
3. **`transports`** : Liste des transports publics
4. **`description`** : Recherche regex dans la description

**Sélection de la meilleure station** :
- Le système classe les stations par **tier** (tier1 > tier2 > tier3)
- Retourne la première station du meilleur tier disponible
- Exemple : Si "Ménilmontant" (tier1) et "Goncourt" (tier2) sont disponibles → retourne "Ménilmontant"

### Extraction du Quartier

**Priorité d'extraction** (dans `get_quartier_name()`) :

1. **`map_info.quartier`** : Quartier depuis les données de carte
2. **`scores_detaille.localisation.justification`** : Extraction depuis la justification IA
3. **`exposition.details.photo_details.quartier`** : Quartier détecté depuis les photos
4. **Fallback** : Recherche de patterns connus dans `localisation` (ex: "Buttes-Chaumont", "Place de la Réunion")

---

## 📊 3. Scoring de la Localisation

### Configuration (scoring_config.json)

**Poids** : 20 points (max)

**Tiers définis** :

#### **TIER 1 - Premium (20 pts)**
- **Zones** : Place de la Réunion, Tronçon ligne 2 Belleville-Avron (Alexandre Dumas, Philippe Auguste, Belleville, Ménilmontant, Avron)
- **Bonus** : +5 points pour Place de la Réunion (score max: 25 pts)

#### **TIER 2 - Bonnes zones (10 pts)**
- **Zones** : Goncourt, 11e arrondissement, 20e arrondissement, 19e proche des Buttes-Chaumont, Pyrénées, Jourdain, Rue des Boulets, Nation

#### **TIER 3 - Zones correctes (0 pts)**
- **Zones** : Reste du 10e, reste du 20e, reste du 19e

### Algorithme de scoring (scoring.py)

```python
def score_localisation(apartment, config):
    # 1. Récupérer toutes les données disponibles
    localisation = apartment.get('localisation', '').lower()
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    text_combined = f"{localisation} {description} {caracteristiques}"
    
    quartier = get_quartier_name(apartment)
    all_stations = get_all_metro_stations(apartment)  # TOUTES les stations
    
    # 2. Vérifier tier1 (zones premium)
    #    - Cherche dans localisation, quartier, description, caractéristiques
    #    - Vérifie TOUTES les stations de métro
    #    - Si match → score 20 pts (+5 bonus Place de la Réunion si applicable)
    
    # 3. Vérifier tier2 (bonnes zones)
    #    - Même logique que tier1
    #    - Si match → score 10 pts
    
    # 4. Par défaut → tier3 (0 pts)
```

**Points clés** :
- ✅ Utilise **TOUTES les stations** de métro (pas seulement la meilleure)
- ✅ Recherche dans **localisation, quartier, description, caractéristiques**
- ✅ Matching flexible (zone contenue dans station ou vice versa)
- ✅ Bonus Place de la Réunion intégré dans le score (20 → 25 pts max)

---

## 🔍 4. Détection des Stations de Métro

### Mapping explicite des stations par tier

Le système utilise un **mapping explicite** pour une meilleure précision :

**Tier 1 stations** :
- Alexandre Dumas, Philippe Auguste, Belleville, Ménilmontant, Avron, Place de la Réunion

**Tier 2 stations** :
- Goncourt, Pyrénées, Jourdain, Rue des Boulets, Nation

### Classification automatique

Si une station n'est pas dans le mapping explicite, le système :
1. Compare avec les zones définies dans `scoring_config.json`
2. Utilise un matching flexible (mots-clés communs)
3. Classe la station dans le tier correspondant

---

## 📋 5. Structure des Données

### Format dans `apartment` :

```json
{
  "localisation": "Paris (75020)",
  "map_info": {
    "metros": ["Ménilmontant", "Goncourt"],
    "quartier": "Sorbier"
  },
  "transports": ["Métro Ménilmontant", "Métro Goncourt"],
  "scores_detaille": {
    "localisation": {
      "score": 20,
      "tier": "tier1",
      "justification": "Zone premium: Place de la Réunion (métro Ménilmontant)"
    }
  }
}
```

### Format d'affichage :

```
Metro Ménilmontant · Sorbier
```

---

## 🎨 6. Utilisation dans le Frontend

### Formatage dans `ApartmentCard.jsx` :

```javascript
function formatLocalisation(apartment) {
  const metro = getMetroName(apartment)      // Meilleure station
  const quartier = getQuartierName(apartment) // Quartier
  
  const parts = []
  if (metro) parts.push(`Metro ${metro}`)
  if (quartier) parts.push(quartier)
  
  return parts.join(" · ") || "Non spécifié"
}
```

### Affichage du score :

- **Score** : 0-25 pts (20 pts base + 5 pts bonus Place de la Réunion)
- **Tier** : tier1 / tier2 / tier3
- **Justification** : Texte explicatif (ex: "Zone premium: Place de la Réunion")

---

## ✅ 7. Avantages du Système Actuel

1. **✅ Données structurées** : Utilise l'API Jinka (plus fiable que scraping HTML)
2. **✅ Matching flexible** : Recherche dans plusieurs sources (localisation, quartier, description, stations)
3. **✅ Utilise toutes les stations** : Ne se limite pas à une seule station pour le scoring
4. **✅ Classification intelligente** : Mapping explicite + matching flexible pour meilleure précision
5. **✅ Bonus intégré** : Place de la Réunion avec bonus +5 points

---

## 🔧 8. Fichiers Clés

- **`api_data_adapter.py`** : Extraction depuis l'API (lignes 50-54)
- **`criteria/localisation.py`** : Formatage et extraction métro/quartier
- **`scoring.py`** : Algorithme de scoring (fonction `score_localisation()`)
- **`scoring_config.json`** : Configuration des tiers et zones
- **`test_localisation_api.py`** : Tests de vérification de l'extraction API

---

## 📝 Notes Techniques

- **Case-insensitive** : Toutes les comparaisons sont en lowercase
- **Déduplication** : Les stations sont dédupliquées avant utilisation
- **Fallback** : Plusieurs niveaux de fallback si données manquantes
- **Performance** : Utilise toutes les stations disponibles pour scoring mais affiche seulement la meilleure

---

**Dernière mise à jour** : 2025-01-XX




