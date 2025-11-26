# 🚨 RÈGLE IMPORTANTE: Fichier HTML unique

## ⚠️ ON TRAVAILLE UNIQUEMENT SUR `output/homepage.html`

### ✅ Fichier principal
- **Fichier HTML:** `output/homepage.html` (UNIQUEMENT)
- **Script générateur:** `generate_scorecard_html.py`
- **Commande:** `python3 generate_scorecard_html.py`

### ❌ NE JAMAIS créer d'autres fichiers HTML

**Interdits:**
- ❌ `output/scorecard_fitscore_style.html`
- ❌ `output/scorecard_rapport.html`
- ❌ `output/rapport_appartements.html`
- ❌ Tout autre fichier HTML dans `output/`

### 📝 Workflow correct

1. **Modifier le code:** Éditer `generate_scorecard_html.py`
2. **Régénérer:** `python3 generate_scorecard_html.py`
3. **Tester:** Ouvrir `output/homepage.html` dans le navigateur

### 🔧 Si vous voyez d'autres fichiers HTML

- Ils sont obsolètes ou générés par erreur
- **IGNOREZ-LES**
- Ne les utilisez pas comme référence
- Le seul fichier valide est `output/homepage.html`

### 📋 Checklist avant commit

- [ ] Seul `output/homepage.html` a été modifié/généré
- [ ] Aucun autre fichier HTML créé dans `output/`
- [ ] Les modifications sont dans `generate_scorecard_html.py`
- [ ] Le HTML a été régénéré avec la commande correcte










