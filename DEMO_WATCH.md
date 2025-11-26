# 🎬 Démonstration : Test du Watch en Action

## 🚀 Test rapide (2 minutes)

### Étape 1 : Ouvrir un terminal et lancer le watch

```bash
cd /Users/sou/Desktop/HomeScore
python watch_scorecard.py
```

**Vous verrez :**
```
👀 SURVEILLANCE DU SCORECARD HTML
============================================================
📁 Fichiers surveillés:
   ✓ analyze_apartment_style.py
   ✓ analyze_photos.py
   ✓ criteria/baignoire.py
   ✓ criteria/cuisine.py
   ✓ criteria/exposition.py
   ✓ criteria/localisation.py
   ✓ criteria/prix.py
   ✓ criteria/style.py
   ✓ data/scores/all_apartments_scores.json
   ✓ data/scraped_apartments.json
   ✓ extract_baignoire.py
   ✓ generate_scorecard_html.py
   ✓ analyze_apartment_style.py

⏱️  Intervalle de vérification: 1 seconde(s)
⏳ Debounce: 2 seconde(s)

💡 Le HTML sera régénéré automatiquement lors des modifications
   Appuyez sur Ctrl+C pour arrêter
```

**Laissez ce terminal ouvert !**

### Étape 2 : Ouvrir un AUTRE terminal et modifier un fichier

```bash
cd /Users/sou/Desktop/HomeScore

# Option 1: Ajouter un commentaire de test
echo "# Test modification" >> generate_scorecard_html.py

# Option 2: Ou modifier avec votre éditeur préféré
# code generate_scorecard_html.py
# ou
# nano generate_scorecard_html.py
```

### Étape 3 : Retourner au premier terminal (celui avec le watch)

**Vous verrez automatiquement (après 1-2 secondes) :**

```
📝 Fichiers modifiés:
   • generate_scorecard_html.py

============================================================
🔄 [14:32:15] Régénération du scorecard HTML...
============================================================
✅ HTML régénéré avec succès!
   ✅ Rapport généré: output/homepage.html
   📋 42 appartements trouvés
🌐 Ouvrez le fichier dans votre navigateur pour voir le rapport
```

### Étape 4 : Vérifier le résultat

```bash
open output/homepage.html
```

Ou simplement rafraîchir la page si elle est déjà ouverte !

---

## 🎨 Test avec modification réelle

### Modifier le CSS dans `generate_scorecard_html.py`

1. **Terminal 1** : `python watch_scorecard.py` (laissé ouvert)

2. **Éditeur** : Ouvrez `generate_scorecard_html.py`
   - Cherchez la ligne avec `.score-badge-top`
   - Changez la couleur par exemple :
   ```python
   # AVANT
   .score-badge-top {
       background: #667eea;
   }
   
   # APRÈS
   .score-badge-top {
       background: #FF5733;  # Nouvelle couleur orange
   }
   ```
   - Sauvegardez (Cmd+S)

3. **Terminal 1** : Observez la régénération automatique !

4. **Navigateur** : Ouvrez `output/homepage.html` → Les badges ont la nouvelle couleur !

---

## 🧪 Test avec modification de données JSON

1. **Terminal 1** : `python watch_scorecard.py`

2. **Éditeur** : Ouvrez `data/scores/all_apartments_scores.json`
   - Modifiez un score (ex: changez un `score_total` de 80 à 90)
   - Sauvegardez

3. **Terminal 1** : Le HTML se régénère automatiquement avec le nouveau score !

---

## ✅ Vérification que ça marche

**Signes que le watch fonctionne :**

1. ✅ Le terminal affiche "👀 SURVEILLANCE DU SCORECARD HTML"
2. ✅ Liste des fichiers surveillés affichée
3. ✅ Pas d'erreur au démarrage
4. ✅ Quand vous modifiez un fichier, vous voyez "📝 Fichiers modifiés:"
5. ✅ Puis "🔄 Régénération..." suivi de "✅ HTML régénéré"

**Si ça ne marche pas :**

- Vérifiez que le fichier modifié est dans la liste des fichiers surveillés
- Vérifiez les permissions d'écriture dans `output/`
- Regardez les messages d'erreur dans le terminal

---

## 🛑 Arrêter le watch

Dans le terminal où le watch tourne, appuyez sur :
```
Ctrl+C
```

Le cache sera nettoyé automatiquement.

---

## 💡 Astuce : Deux terminaux côte à côte

Pour un workflow optimal :
- **Terminal gauche** : `python watch_scorecard.py` (watch actif)
- **Terminal droit** : Vos commandes et modifications

Comme ça vous voyez la régénération en temps réel ! 🎉










