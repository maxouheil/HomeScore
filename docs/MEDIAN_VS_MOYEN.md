# 📊 Médian vs Moyen : Quelle Différence pour l'Immobilier ?

## 🎯 Différence Conceptuelle

### **Médian** (valeur médiane)
- Valeur qui sépare les données en deux moitiés égales
- 50% des biens sont **en dessous**, 50% sont **au-dessus**
- **Résistant aux valeurs extrêmes** (outliers)

### **Moyen** (moyenne arithmétique)
- Somme de toutes les valeurs divisée par le nombre
- **Sensible aux valeurs extrêmes**
- Peut être tiré vers le haut par quelques biens très chers

---

## 📈 Exemple Concret : Station Belleville

Supposons 10 appartements vendus à Belleville :

```
Prix/m² : 8 000, 9 000, 9 500, 10 000, 10 500, 10 800, 11 000, 11 500, 12 000, 25 000
                                                                              ↑
                                                                        Appartement de luxe
```

### **Médian** = 10 650 €/m²
- Valeur centrale (entre 10 500 et 10 800)
- **Représente le marché "typique"**
- L'appartement à 25 000€/m² ne l'affecte pas

### **Moyen** = 11 730 €/m²
- (8 000 + 9 000 + ... + 25 000) / 10
- **Tiré vers le haut** par l'appartement de luxe
- Ne représente pas le marché "typique"

**Différence** : +1 080 €/m² (+10%) avec le moyen !

---

## 🏠 Impact sur le Scoring

### Avec **Médian** (10 650 €/m²)
- Appartement à **10 200 €/m²** → **Good** ✅ (en dessous du médian)
- Appartement à **11 000 €/m²** → **Moyen** (≈ médian)
- Appartement à **12 500 €/m²** → **Bad** ❌ (au-dessus)

### Avec **Moyen** (11 730 €/m²)
- Appartement à **10 200 €/m²** → **Good** ✅ (en dessous)
- Appartement à **11 000 €/m²** → **Good** ✅ (en dessous aussi !)
- Appartement à **12 500 €/m²** → **Moyen** (≈ moyen)

**Résultat** : Le moyen rend le scoring **plus généreux** car la barre est plus haute !

---

## ✅ Pourquoi le Médian est Meilleur pour l'Immobilier

### 1. **Résistant aux valeurs extrêmes**
- Quelques appartements de luxe ne faussent pas le marché
- Représente mieux le marché "accessible"

### 2. **Plus représentatif**
- 50% des biens sont en dessous, 50% au-dessus
- Meilleur indicateur pour un acheteur "moyen"

### 3. **Moins de volatilité**
- Moins sensible aux ventes exceptionnelles
- Plus stable dans le temps

### 4. **Standard de l'industrie**
- Utilisé par MeilleursAgents, SeLoger, etc.
- Facilite les comparaisons

---

## 🔄 Si on Utilisait le Moyen

### Avantages
- ✅ Plus facile à calculer (somme / nombre)
- ✅ Peut capturer les tendances de marché (hausse générale)

### Inconvénients
- ❌ Faussé par quelques biens très chers
- ❌ Scoring trop généreux (plus d'appartements classés "Good")
- ❌ Ne représente pas le marché accessible
- ❌ Peut masquer les vraies opportunités

---

## 💡 Recommandation

**Garder le MÉDIAN** pour :
- ✅ Scoring plus précis et équitable
- ✅ Meilleure représentation du marché accessible
- ✅ Cohérence avec les standards de l'industrie
- ✅ Résistance aux valeurs extrêmes

**Utiliser le MOYEN** seulement si :
- On veut analyser les tendances de marché (hausse/baisse)
- On cherche à identifier les zones en gentrification
- On veut comparer avec d'autres indicateurs qui utilisent le moyen

---

## 📊 Comparaison Visuelle

```
Prix/m² à Belleville (hypothétique)

Médian (10 650€) ←─── 50% en dessous ──── 50% au-dessus ───→
Moyen (11 730€) ←─── Tiré vers le haut par les biens de luxe ───→

Appartements "normaux" : 8 000 - 12 000 €/m²
Appartement de luxe : 25 000 €/m² (affecte seulement le moyen)
```

---

## 🎯 Conclusion

**Le médian est meilleur pour le scoring** car il :
- Représente mieux le marché accessible
- Donne un scoring plus équitable
- Est moins sensible aux valeurs extrêmes
- Est le standard de l'industrie immobilière

Le moyen pourrait être utilisé comme **indicateur complémentaire** pour analyser les tendances, mais pas pour le scoring principal.

---

*Document créé le : 2025-01-XX*

