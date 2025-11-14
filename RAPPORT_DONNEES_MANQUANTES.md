# 📊 Rapport Complet des Données Manquantes

**Date**: 2025-11-03  
**Total d'appartements vérifiés**: 34

---

## 📈 Statistiques Globales

| Catégorie | Nombre | Pourcentage |
|-----------|--------|------------|
| **Total** | 34 | 100% |
| ✅ **Complets** | 0 | 0% |
| ⚠️ **Incomplets** | 34 | 100% |
| 📁 **Manquants fichiers** | 0 | 0% |
| 📸 **Manquantes photos** | 11 | 32.4% |
| 🔬 **Manquantes analyses** | 18 | 52.9% |
| 📊 **Manquants scores** | 5 | 14.7% |

---

## 📋 Résumé des Données Manquantes

### 🔹 Données de Base (BASIC)
- **prix_m2**: 33 appartements (97.1%)
  - ❌ **PROBLÈME MAJEUR**: Presque tous les appartements n'ont pas le prix au m² calculé

### 🔹 Informations Carte (MAP_INFO)
- **metros (vide)**: 15 appartements (44.1%)
  - 15 appartements n'ont pas de métros identifiés dans map_info

### 🔹 Photos (PHOTOS)
- **photos_dir (vide)**: 3 appartements (8.8%)
  - `87336337`, `91652882`, `93005222`
- **photos (aucune photo)**: 2 appartements (5.9%)
  - `91153576`, `92913102` - Pas de photos dans les données
- **photos_dir (partiel)**: 7 appartements (20.6%)
  - Photos téléchargées partiellement pour plusieurs appartements

### 🔹 Analyses (ANALYSIS)
- **baignoire**: 18 appartements (52.9%)
  - ❌ **PROBLÈME MAJEUR**: Plus de la moitié n'ont pas d'analyse baignoire
- **exposition.exposition**: 12 appartements (35.3%)
  - 12 appartements n'ont pas d'exposition spécifiée
- **style_analysis**: 5 appartements (14.7%)
  - `91153576`, `91644200`, `92724395`, `92732956`, `92913102`

### 🔹 Scores (SCORING)
- **scores_detaille**: 5 appartements (14.7%)
- **score_total**: 5 appartements (14.7%)
- **tier**: 5 appartements (14.7%)
  - ❌ **CRITIQUE**: 5 appartements n'ont pas de scores calculés
  - `91153576`, `91644200`, `92724395`, `92732956`, `92913102`

---

## 🔴 Appartements Critiques (Manque photos ou scoring)

### Top 5 Appartements avec le plus de problèmes:

1. **91153576** - 9 problèmes
   - ❌ Pas de photos
   - ❌ Pas de scoring
   - ❌ Pas d'analyse baignoire
   - ❌ Pas d'analyse style
   - ❌ Pas d'exposition spécifiée
   - ❌ Pas de prix_m2
   - ❌ Pas de métros

2. **91644200** - 9 problèmes
   - ❌ Pas de scoring
   - ❌ Photos partiellement téléchargées (2/3)
   - ❌ Pas d'analyse baignoire
   - ❌ Pas d'analyse style
   - ❌ Pas d'exposition spécifiée
   - ❌ Pas de prix_m2
   - ❌ Pas de métros

3. **92913102** - 9 problèmes
   - ❌ Pas de photos
   - ❌ Pas de scoring
   - ❌ Pas d'analyse baignoire
   - ❌ Pas d'analyse style
   - ❌ Pas d'exposition spécifiée
   - ❌ Pas de prix_m2
   - ❌ Pas de métros

4. **92732956** - 8 problèmes
   - ❌ Pas de scoring
   - ❌ Pas d'analyse baignoire
   - ❌ Pas d'analyse style
   - ❌ Pas d'exposition spécifiée
   - ❌ Pas de prix_m2
   - ❌ Pas de métros

5. **92724395** - 7 problèmes
   - ❌ Pas de scoring
   - ❌ Pas d'analyse baignoire
   - ❌ Pas d'analyse style
   - ❌ Pas de prix_m2
   - ❌ Pas de métros

---

## 🟡 Appartements avec Analyses Manquantes (Priorité Élevée)

- `88305405`: Exposition + Baignoire manquantes
- `90931157`: Baignoire manquante
- `91419570`: Exposition + Baignoire manquantes
- `92656309`: Exposition + Baignoire manquantes
- `92656320`: Exposition + Baignoire manquantes

---

## 📊 Actions Recommandées par Priorité

### 🔴 PRIORITÉ CRITIQUE

1. **Calculer les scores pour 5 appartements**
   - `91153576`, `91644200`, `92724395`, `92732956`, `92913102`
   - Action: Exécuter `regenerate_all_scores.py` ou `rescore_all_apartments.py`

2. **Télécharger/Re-télécharger les photos**
   - 2 appartements sans photos: `91153576`, `92913102`
   - 3 appartements avec dossier vide: `87336337`, `91652882`, `93005222`
   - 7 appartements avec photos partielles
   - Action: Exécuter `batch_download_all_photos.py` ou `rescrape_missing_photos.py`

### 🟡 PRIORITÉ ÉLEVÉE

3. **Analyser les baignoires** (18 appartements)
   - Action: Exécuter analyse baignoire pour ces appartements

4. **Déterminer l'exposition** (12 appartements)
   - Action: Améliorer l'extraction d'exposition ou ré-analyser

5. **Analyser le style** (5 appartements)
   - Action: Exécuter analyse de style pour ces appartements

### 🟢 PRIORITÉ MOYENNE

6. **Calculer prix_m2** (33 appartements - 97%)
   - Action: Ajouter calcul automatique dans le scraping

7. **Identifier les métros** (15 appartements)
   - Action: Améliorer l'extraction des métros depuis map_info

---

## 📝 Liste Complète des Appartements par Problème

### Appartements sans photos
- `91153576`
- `92913102`

### Appartements sans scoring
- `91153576`
- `91644200`
- `92724395`
- `92732956`
- `92913102`

### Appartements sans analyse baignoire (18)
- `85467731`, `87336337`, `88305405`, `90931157`, `91153576`, `91419570`, `91644200`, `91652882`, `91673409`, `91901126`, `92385257`, `92656309`, `92656320`, `92708756`, `92724395`, `92732956`, `92913102`, `93005222`

### Appartements sans exposition spécifiée (12)
- `87336337`, `88305405`, `91153576`, `91419570`, `91644200`, `91652882`, `91673409`, `91901126`, `92656309`, `92656320`, `92732956`, `92913102`

### Appartements sans analyse style (5)
- `91153576`, `91644200`, `92724395`, `92732956`, `92913102`

### Appartements avec photos partielles
- `85467731`: 9/14 photos
- `91644200`: 2/3 photos
- `91673409`: 10/11 photos
- `91901126`: 1/10 photos
- `92385257`: 14/15 photos
- `92708756`: 5/11 photos

---

## ✅ Conclusion

**Statut Global**: ❌ **Aucun appartement n'est complet** (0/34)

**Problèmes principaux**:
1. **Prix au m²**: 97% des appartements (33/34)
2. **Analyse baignoire**: 53% des appartements (18/34)
3. **Exposition**: 35% des appartements (12/34)
4. **Métros**: 44% des appartements (15/34)
5. **Scoring**: 15% des appartements (5/34) - **CRITIQUE**

**Prochaines étapes prioritaires**:
1. Calculer les scores pour les 5 appartements critiques
2. Télécharger les photos manquantes
3. Exécuter les analyses manquantes (baignoire, style, exposition)



