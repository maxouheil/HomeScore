# 📍 Géocodage Inverse - Localisation Précise

## ✅ Fonctionnalité Ajoutée

Récupération automatique de la **localisation précise** (adresse complète) depuis les coordonnées GPS disponibles dans l'API.

## 🔧 Implémentation

### Module `geocoding.py`

**Fonction principale** : `reverse_geocode(lat, lng)`
- Utilise **Nominatim** (OpenStreetMap) - gratuit, pas besoin d'API key
- Convertit coordonnées GPS → Adresse précise
- Format : `"35 Rue Mélingue, 75019 Paris 19e"`

**Fonction utilitaire** : `get_precise_location(apartment)`
- Extrait automatiquement les coordonnées depuis un appartement
- Retourne l'adresse précise ou `None` si indisponible

### Intégration dans `api_data_adapter.py`

L'adaptateur API ajoute automatiquement le champ `localisation_precise` :

```python
{
    'localisation': 'Paris 19e (75019)',           # Format existant
    'localisation_precise': '35 Rue Mélingue, 75019 Paris 19e',  # Nouveau : adresse complète
    'coordinates': {
        'latitude': 48.8767,
        'longitude': 2.38578
    }
}
```

## 📊 Format de l'Adresse

**Format complet** : `"{numéro} {rue}, {code_postal} {ville}"`

Exemples :
- `"35 Rue Mélingue, 75019 Paris 19e"`
- `"12 Avenue de la République, 75011 Paris 11e"`
- `"8 Rue des Boulets, 75011 Paris 11e"`

## 🎯 Utilisation

### Automatique
Lors de l'adaptation des données API, la localisation précise est automatiquement ajoutée si les coordonnées GPS sont disponibles.

### Manuel
```python
from geocoding import get_precise_location

precise_address = get_precise_location(apartment)
if precise_address:
    print(f"Adresse précise: {precise_address}")
```

## ⚠️ Limitations

1. **Rate limiting** : Nominatim limite à 1 requête/seconde (gratuit)
   - Solution : Ajouter un délai si beaucoup d'appartements
   
2. **Disponibilité** : Nécessite des coordonnées GPS valides
   - Si `lat` ou `lng` manquants → `localisation_precise = None`

3. **Précision** : Dépend de la qualité des données OpenStreetMap
   - Généralement très bon pour Paris

## 🚀 Prochaines Étapes

- [ ] Ajouter cache pour éviter les requêtes répétées
- [ ] Gérer le rate limiting si beaucoup d'appartements
- [ ] Optionnel : Utiliser Google Geocoding API pour plus de précision (nécessite API key)

---

**Date** : 2025-01-XX  
**Statut** : ✅ Fonctionnel et intégré




