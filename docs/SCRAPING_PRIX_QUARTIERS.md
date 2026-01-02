# 🔍 Guide : Scraper les Prix depuis PAP.fr et MeilleursAgents

## 📋 Vue d'ensemble

Ce guide explique comment récupérer automatiquement les prix médians par quartier depuis PAP.fr et MeilleursAgents.

---

## 🎯 Complexité : **MOYENNE** ⚠️

### Pourquoi c'est compliqué ?

1. **Anti-scraping** : Les sites protègent leurs données
   - Rate limiting (limite de requêtes)
   - Vérification User-Agent
   - CAPTCHA possible
   - Blocage IP si trop de requêtes

2. **Structure HTML variable** : 
   - Les sites changent leur structure régulièrement
   - Sélecteurs CSS à adapter
   - Données dans JavaScript (nécessite parfois Selenium)

3. **Codes quartiers** :
   - PAP.fr utilise des codes (ex: `g439`)
   - MeilleursAgents utilise des URLs avec noms de quartiers
   - Mapping à créer manuellement

---

## 🛠️ Solutions

### Option 1 : Scraping Simple (Recommandé pour débuter)

**Script créé** : `scripts/scrape_prix_pap_meilleursagents.py`

**Avantages** :
- ✅ Simple à utiliser
- ✅ Pas besoin de Selenium
- ✅ Rapide

**Inconvénients** :
- ⚠️ Peut nécessiter ajustements selon structure HTML
- ⚠️ Rate limiting à respecter

**Utilisation** :
```bash
python scripts/scrape_prix_pap_meilleursagents.py
```

---

### Option 2 : Scraping avec Selenium (Si données dans JavaScript)

**Quand l'utiliser** :
- Si les prix sont chargés dynamiquement en JavaScript
- Si le scraping simple ne fonctionne pas

**Complexité** : **ÉLEVÉE** ⚠️⚠️

**Avantages** :
- ✅ Peut gérer JavaScript
- ✅ Plus robuste

**Inconvénients** :
- ❌ Plus lent
- ❌ Nécessite Chrome/Firefox installé
- ❌ Plus complexe à maintenir

---

### Option 3 : API Officielle (Si disponible)

**MeilleursAgents** :
- Vérifier si API disponible : `https://www.meilleursagents.com/api/`
- Peut nécessiter clé API
- Documentation à consulter

**PAP.fr** :
- Pas d'API publique connue
- Scraping nécessaire

---

## 📊 Structure des URLs

### PAP.fr

**Format** : `https://www.pap.fr/vendeur/prix-m2/paris-75-{code}`

**Exemples** :
- Sainte-Marguerite : `https://www.pap.fr/vendeur/prix-m2/paris-75-g439`
- Hôpital Saint-Louis : `https://www.pap.fr/vendeur/prix-m2/paris-75-gXXX` (code à trouver)

**Comment trouver les codes** :
1. Aller sur PAP.fr
2. Naviguer vers le quartier
3. Regarder l'URL dans le navigateur
4. Extraire le code (ex: `g439`)

---

### MeilleursAgents

**Format** : `https://www.meilleursagents.com/prix-immobilier/paris-{arrondissement}/{quartier}/`

**Exemples** :
- Sainte-Marguerite : `https://www.meilleursagents.com/prix-immobilier/paris-75011/sainte-marguerite/`
- Hôpital Saint-Louis : `https://www.meilleursagents.com/prix-immobilier/paris-75010/hopital-saint-louis/`

**Normalisation** :
- Minuscules
- Espaces → tirets (`-`)
- Accents conservés mais URL-encodés

---

## 🔧 Implémentation

### Étape 1 : Tester sur un quartier

```python
from scripts.scrape_prix_pap_meilleursagents import scrape_pap_quartier, scrape_meilleursagents_quartier

# Tester PAP.fr
result = scrape_pap_quartier("g439", "Sainte-Marguerite")
print(result)

# Tester MeilleursAgents
result = scrape_meilleursagents_quartier("Sainte-Marguerite", "75011")
print(result)
```

### Étape 2 : Créer la liste des quartiers

**Mapping quartiers → stations** :
```python
QUARTIERS = [
    {
        "nom": "Sainte-Marguerite",
        "code_pap": "g439",
        "arrondissement": "75011",
        "station_proche": "Alexandre Dumas"
    },
    {
        "nom": "Hôpital Saint-Louis",
        "code_pap": "gXXX",  # À trouver
        "arrondissement": "75010",
        "station_proche": "Goncourt"
    },
    # ... autres quartiers
]
```

### Étape 3 : Scraper tous les quartiers

```python
for quartier in QUARTIERS:
    # Essayer PAP.fr
    result = scrape_pap_quartier(quartier["code_pap"], quartier["nom"])
    
    # Si échec, essayer MeilleursAgents
    if not result:
        result = scrape_meilleursagents_quartier(quartier["nom"], quartier["arrondissement"])
    
    # Sauvegarder le résultat
    if result:
        save_result(result, quartier["station_proche"])
```

---

## ⚠️ Points d'Attention

### 1. Rate Limiting

**Respecter les délais** :
```python
time.sleep(2)  # Attendre 2 secondes entre chaque requête
```

**Pourquoi** :
- Éviter le blocage IP
- Respecter les conditions d'utilisation
- Ne pas surcharger les serveurs

### 2. User-Agent

**Toujours spécifier** :
```python
HEADERS = {
    'User-Agent': 'Mozilla/5.0 ...'  # Simuler un navigateur
}
```

### 3. Gestion d'erreurs

**Toujours gérer les exceptions** :
```python
try:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"Erreur: {e}")
    return None
```

### 4. Structure HTML changeante

**Problème** : Les sites changent leur HTML régulièrement

**Solution** :
- Tester régulièrement le script
- Avoir plusieurs méthodes de parsing (fallback)
- Documenter les sélecteurs CSS utilisés

---

## 🎯 Stratégie Recommandée

### Phase 1 : Scraping Manuel (Rapide)

1. **Identifier les quartiers importants** (ceux avec stations tier1/tier2)
2. **Scraper manuellement** quelques quartiers clés
3. **Mettre à jour le fichier JSON** directement

**Temps** : 30 minutes pour 10-15 quartiers

### Phase 2 : Automatisation (Si besoin)

1. **Créer la liste complète** des quartiers
2. **Tester le script** sur quelques quartiers
3. **Lancer le scraping complet** avec rate limiting
4. **Vérifier les résultats** manuellement

**Temps** : 2-3h pour tous les quartiers de Paris

---

## 📝 Checklist

- [ ] Identifier les quartiers importants (proches des stations tier1/tier2)
- [ ] Trouver les codes PAP.fr pour ces quartiers
- [ ] Tester le scraping sur 2-3 quartiers
- [ ] Vérifier que les prix sont cohérents
- [ ] Créer le mapping quartiers → stations
- [ ] Mettre à jour `stations_metro.json` avec les nouveaux prix
- [ ] Tester le scoring avec les nouveaux prix

---

## 🔄 Mise à Jour Régulière

**Fréquence recommandée** : **Mensuelle**

Les prix immobiliers évoluent, il faut mettre à jour régulièrement :
- Script de mise à jour automatique (optionnel)
- Vérification manuelle trimestrielle
- Alertes si changement significatif

---

## 💡 Alternative : Données Manuelles

**Si le scraping est trop compliqué** :

1. **Aller sur MeilleursAgents** manuellement
2. **Noter les prix** pour chaque quartier important
3. **Mettre à jour le JSON** directement

**Avantages** :
- ✅ Pas de problème de scraping
- ✅ Données garanties exactes
- ✅ Rapide pour quelques quartiers

**Inconvénients** :
- ❌ Pas automatisé
- ❌ Nécessite mise à jour manuelle

---

*Document créé le : 2025-01-XX*

