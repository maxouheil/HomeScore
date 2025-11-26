# 🐛 Problème de Scoring Localisation - Analyse et Solution

## 🔍 Problème Identifié

**Symptôme** : Des appartements avec "Pyrénées" (Tier 2 = 10 pts) reçoivent 20 points (Tier 1) au lieu de 10 points.

**Exemple réel** : Appartement `93083514.json`
- Quartier : **Combat**
- Stations : **Pyrénées, Jourdain** (Tier 2)
- Description : "...typique du quartier de **Belleville**..."
- **Score reçu** : 20 points (Tier 1) ❌
- **Score attendu** : 10 points (Tier 2) ✅

## 🔎 Cause Racine

Le problème vient de la **logique de matching trop large** dans `scoring.py` :

```python
# Ligne 86 - PROBLÈME ICI
if zone in localisation or zone in text_combined:
    zone_matched = True
```

**Problèmes** :

1. **Vérification Tier 1 AVANT Tier 2** : Si une zone Tier 1 est mentionnée dans la description (même juste comme référence), elle prend le dessus sur les stations Tier 2 réelles.

2. **Matching trop large** : "Belleville" mentionné dans la description d'un appartement à Pyrénées fait matcher Tier 1, même si l'appartement n'est pas vraiment à Belleville.

3. **Zone "Tronçon ligne 2 Belleville-Avron" trop large** : Cette zone Tier 1 peut matcher avec n'importe quelle mention de "Belleville" dans la description.

## 📊 Exemples de Cas Problématiques

### Cas 1 : Mention dans description
- **Appartement réel** : Quartier Combat, Station Pyrénées
- **Description** : "...typique du quartier de Belleville..."
- **Résultat** : 20 pts (Tier 1) au lieu de 10 pts (Tier 2)
- **Raison** : "Belleville" trouvé dans description → match Tier 1

### Cas 2 : Zone large "Tronçon ligne 2 Belleville-Avron"
- Si cette zone est mentionnée quelque part, elle matche avec n'importe quelle mention de "Belleville", "Ménilmontant", etc.

## ✅ Solutions Proposées

### Solution 1 : Prioriser les Stations Réelles (RECOMMANDÉE)

**Principe** : Les stations de métro réelles sont plus fiables que les mentions dans la description.

**Modification** :
- Vérifier d'abord les **stations de métro réelles** (depuis `map_info.metros` ou `transports`)
- Ne vérifier la description que si aucune station ne matche
- Ou : vérifier Tier 2 d'abord si une station Tier 2 est présente

### Solution 2 : Matching Plus Strict pour Tier 1

**Principe** : Tier 1 ne devrait matcher que si :
- La zone est dans la **localisation** (ville/arrondissement)
- La zone est dans le **quartier**
- La zone correspond à une **station de métro réelle**

**Ne PAS matcher** si la zone est seulement mentionnée dans la description.

### Solution 3 : Vérifier Tier 2 en Premier si Station Tier 2 Présente

**Principe** : Si une station Tier 2 est présente (ex: Pyrénées), vérifier Tier 2 d'abord avant Tier 1.

## 🛠️ Correction Proposée

Modifier `scoring.py` pour prioriser les stations réelles :

```python
def score_localisation(apartment, config):
    """Score localisation selon zones définies dans config - utilise TOUTES les stations et rues"""
    tier_config = config['axes']['localisation']['tiers']
    
    # Récupérer localisation, quartier, description, toutes les stations de métro
    localisation = apartment.get('localisation', '').lower()
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    text_combined = f"{localisation} {description} {caracteristiques}"
    
    quartier = get_quartier_name(apartment)
    if quartier:
        quartier = quartier.lower()
    
    # Récupérer TOUTES les stations de métro (pas seulement la meilleure pour l'affichage)
    all_stations = get_all_metro_stations(apartment)
    all_stations_lower = [s.lower() for s in all_stations] if all_stations else []
    
    # NOUVELLE LOGIQUE : Vérifier d'abord les stations réelles, puis le texte
    
    # 1. Vérifier Tier 1 dans les STATIONS RÉELLES d'abord
    tier1_zones = [z.lower() for z in tier_config['tier1']['zones']]
    tier1_station_match = None
    
    for zone in tier1_zones:
        for station in all_stations_lower:
            if zone in station or station in zone:
                tier1_station_match = (zone, station)
                break
        if tier1_station_match:
            break
    
    # Si match Tier 1 dans station réelle → Tier 1
    if tier1_station_match:
        zone, station = tier1_station_match
        score = tier_config['tier1']['score']
        if 'place de la réunion' in zone:
            score += config['bonus']['place_reunion']
        return {
            'score': score,
            'tier': 'tier1',
            'justification': f"Zone premium: {zone} (métro {station})"
        }
    
    # 2. Vérifier Tier 2 dans les STATIONS RÉELLES
    tier2_zones = [z.lower() for z in tier_config['tier2']['zones']]
    tier2_station_match = None
    
    for zone in tier2_zones:
        for station in all_stations_lower:
            if zone in station or station in zone:
                tier2_station_match = (zone, station)
                break
        if tier2_station_match:
            break
    
    # Si match Tier 2 dans station réelle → Tier 2
    if tier2_station_match:
        zone, station = tier2_station_match
        return {
            'score': tier_config['tier2']['score'],
            'tier': 'tier2',
            'justification': f"Bonne zone: {zone} (métro {station})"
        }
    
    # 3. Fallback : Vérifier dans localisation/quartier/description (moins fiable)
    # Tier 1 dans localisation/quartier
    for zone in tier1_zones:
        if zone in localisation or (quartier and zone in quartier):
            score = tier_config['tier1']['score']
            if 'place de la réunion' in zone:
                score += config['bonus']['place_reunion']
            return {
                'score': score,
                'tier': 'tier1',
                'justification': f"Zone premium: {zone}"
            }
    
    # Tier 2 dans localisation/quartier
    for zone in tier2_zones:
        if zone in localisation or (quartier and zone in quartier):
            return {
                'score': tier_config['tier2']['score'],
                'tier': 'tier2',
                'justification': f"Bonne zone: {zone}"
            }
    
    # Par défaut tier3
    return {
        'score': tier_config['tier3']['score'],
        'tier': 'tier3',
        'justification': "Zone correcte"
    }
```

## 📝 Changements Clés

1. ✅ **Priorité aux stations réelles** : Vérifie d'abord les stations de métro réelles avant la description
2. ✅ **Tier 2 vérifié avant Tier 1 dans description** : Si aucune station ne matche, vérifie Tier 2 avant Tier 1 dans le texte
3. ✅ **Matching plus strict** : Ne matche Tier 1 dans description que si c'est dans localisation/quartier, pas juste mentionné

## 🧪 Tests à Effectuer

Après correction, tester :
- ✅ Appartement Pyrénées + Combat → 10 pts (Tier 2)
- ✅ Appartement Ménilmontant → 20 pts (Tier 1)
- ✅ Appartement avec mention "Belleville" dans description mais station Pyrénées → 10 pts (Tier 2)

---

**Date** : 2025-01-XX
**Statut** : 🔴 Problème identifié, correction à appliquer




