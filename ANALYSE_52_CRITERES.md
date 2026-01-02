# 🚀 Analyse Ultra-Rapide des 10 Critères - 52 Appartements

## Vue d'ensemble

Ce système permet d'analyser les **10 critères** des **52 appartements** avec **Gemini Flash** optimisé pour la vitesse et affichage instantané dans le frontend.

## 📋 Les 10 Critères

1. **Haussmanien** 🔑 - Style haussmannien détecté
2. **Quartier** 📍 - Zone Tier 1 (Belleville, Ménilmontant, etc.)
3. **Prix** 💰 - Prix/m² < 9.5k€
4. **Luminosité** ☀️ - Lumineux (Sud/Ouest, vue dégagée)
5. **Cuisine ouverte** 👨‍🍳 - Cuisine ouverte sur salon
6. **Ascenseur** 🛗 - Présence d'ascenseur
7. **Large pièce de vie** 🛋️ - Salon > 35% surface totale
8. **Hauteur plafond** 📏 - ≥ 2.80m
9. **Rénové** 🔨 - Mentionné comme rénové
10. **Calme** 🔇 - Quartier calme

## 🎯 Fonctionnalités

### Backend

- **Script d'analyse** : `analyze_52_apartments_criteria.py`
  - Analyse unifiée en UNE SEULE requête Gemini Flash par appartement
  - Utilise seulement 2 photos (optimisation vitesse)
  - Rate limiting : 2 secondes entre chaque appartement (30 RPM)
  - Cache intelligent pour éviter les re-analyses

- **API Endpoints** : `backend/api/criteria_analysis.py`
  - `POST /api/criteria/analyze-all` : Démarre l'analyse
  - `GET /api/criteria/status` : Statut de l'analyse en cours
  - `GET /api/criteria/results` : Tous les résultats
  - `GET /api/criteria/results/{apartment_id}` : Résultats d'un appartement
  - `GET /api/criteria/latest` : Derniers résultats

### Frontend

- **Composant React** : `frontend/src/components/CriteriaAnalysis.jsx`
  - Interface pour démarrer l'analyse
  - Affichage en temps réel de la progression
  - Tableau récapitulatif avec tous les critères
  - Statistiques par critère
  - Mise à jour automatique toutes les secondes

## 🚀 Utilisation

### 1. Démarrer le backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Démarrer le frontend

```bash
cd frontend
npm start
```

### 3. Accéder à l'interface

1. Ouvrir `http://localhost:3000`
2. Cliquer sur le bouton **"📊 Analyse Critères"** dans la navigation
3. Cliquer sur **"🚀 Démarrer l'analyse"**

### 4. Suivre la progression

- La barre de progression affiche l'avancement en temps réel
- Le tableau se met à jour automatiquement au fur et à mesure
- Les statistiques sont calculées en temps réel

## ⚡ Optimisations

### Vitesse

- **2 photos seulement** par appartement (au lieu de 3-5)
- **UNE SEULE requête** Gemini Flash pour analyser tous les critères
- **Rate limiting optimisé** : 2 secondes entre chaque appartement
- **Cache intelligent** : évite les re-analyses

### Coûts

- **Gemini Flash** : ~$0.000075 par image
- **2 images** × **52 appartements** = **104 images**
- **Coût total estimé** : ~$0.008 (moins de 1 centime)

### Temps

- **~2-3 secondes** par appartement (analyse + rate limiting)
- **Total estimé** : ~2-3 minutes pour 52 appartements

## 📊 Format des Résultats

Les résultats sont sauvegardés dans `data/criteria_analysis/{apartment_id}.json` :

```json
{
  "apartment_id": "92336388",
  "analyzed_at": "2025-12-08T10:30:00",
  "criteria": {
    "haussmanien": {
      "detected": true,
      "confidence": 0.85,
      "indices": "moulures, parquet, cheminée"
    },
    "quartier": {
      "tier1": true,
      "zone": "Belleville",
      "confidence": 0.90
    },
    ...
  }
}
```

## 🔧 Configuration

### Modifier le nombre d'appartements

Dans `analyze_52_apartments_criteria.py`, modifier :

```python
apartment_ids = [apt_id for apt_id, _ in apartment_files_with_time[:52]]  # Changer 52
```

### Modifier le nombre de photos

Dans `analyze_criteria_unified()`, modifier :

```python
for photo in photos[:2]:  # Changer 2 pour plus/moins de photos
```

### Modifier le rate limiting

Dans `analyze_all_52()`, modifier :

```python
time.sleep(2)  # Changer 2 pour plus/moins de délai
```

## 🐛 Dépannage

### L'analyse ne démarre pas

- Vérifier que le backend est démarré sur le port 8000
- Vérifier les logs du backend pour les erreurs
- Vérifier que `GEMINI_API_KEY` est défini dans `.env`

### Les résultats ne s'affichent pas

- Vérifier la console du navigateur pour les erreurs
- Vérifier que les endpoints API répondent correctement
- Vérifier que `data/criteria_analysis/` existe et contient des fichiers

### L'analyse est trop lente

- Réduire le nombre de photos analysées (de 2 à 1)
- Réduire le rate limiting (de 2s à 1s)
- Vérifier la connexion internet

## 📝 Notes

- Les résultats sont mis en cache pour éviter les re-analyses
- L'analyse peut être interrompue et reprise (les résultats partiels sont sauvegardés)
- Le frontend met à jour automatiquement toutes les secondes pendant l'analyse


