# HomeScore

Système d'analyse d'appartements utilisant l'IA pour évaluer les caractéristiques visuelles des biens immobiliers.

## 📋 Description

HomeScore est un projet d'analyse visuelle d'appartements qui utilise Google Gemini API pour analyser les photos et extraire des informations clés sur les caractéristiques des biens immobiliers.

## 🚀 Fonctionnalités

### Analyse visuelle avec Gemini AI
- **Module d'analyse** (`gemini_analyzer.py`) : Intégration avec Google Gemini API pour réduire les coûts de 96% par rapport à OpenAI
- **Analyse complète d'appartement** (`analyser_appartement.py`) : Script pour analyser un appartement spécifique avec plusieurs métriques
- **Recherche d'appartements** (`trouver_appartement.py`) : Script pour rechercher des appartements dans les données JSON

### Analyses disponibles

1. **Style architectural**
   - Classification : haussmannien, décennies jusqu'à 80, moderne
   - Indice de style (0-100)
   - Hauteur de plafond estimée
   - Ambiance et matériaux dominants

2. **Équipements**
   - Détection de baignoire (type, confiance)
   - Détection de cuisine ouverte/fermée
   - Présence d'îlot central

3. **Caractéristiques spatiales**
   - Estimation de la hauteur sous plafond
   - Analyse de la taille de la pièce de vie
   - Calcul du pourcentage de surface totale

4. **Luminosité**
   - Estimation de la distance vis-à-vis
   - Impact sur la luminosité
   - Type de vis-à-vis (immeuble, mur, espace vert)

## 📦 Installation

```bash
pip install google-generativeai pillow python-dotenv requests
```

## 🔧 Configuration

Créez un fichier `.env` avec votre clé API Gemini :

```
GEMINI_API_KEY=votre_cle_api
```

## 💻 Utilisation

### Analyser un appartement

```bash
python analyser_appartement.py 'titre ou ID' [url_photo1] [url_photo2] ...
```

Exemple :
```bash
python analyser_appartement.py '770k · Goncourt'
```

### Rechercher un appartement

```bash
python trouver_appartement.py
```

## 💰 Coûts

- **Gemini 2.5 Flash** : $0.000075 par image (gratuit jusqu'à 15 requêtes/minute)
- **Gemini 2.5 Pro** : $0.001315 par image (pour analyses plus précises)

Le système inclut un rate limiting automatique pour respecter les quotas gratuits.

## 📊 Progrès d'aujourd'hui

### ✅ Réalisations

- **Migration vers Gemini API** : Remplacement d'OpenAI par Google Gemini pour réduire les coûts de 96%
- **Module d'analyse complet** : Création du module `gemini_analyzer.py` avec :
  - Support de plusieurs modèles (Flash et Pro)
  - Rate limiting automatique
  - Gestion des images (URLs, fichiers locaux)
  - Parsing JSON automatique
  - Retry logic avec backoff exponentiel

- **Script d'analyse d'appartement** : Développement de `analyser_appartement.py` avec :
  - Recherche d'appartement par titre/ID
  - Analyse complète en 6 étapes :
    1. Analyse du style architectural
    2. Détection de baignoire
    3. Détection de cuisine ouverte
    4. Estimation de la luminosité et vis-à-vis
    5. Estimation de la hauteur de plafond
    6. Analyse de la pièce de vie avec pourcentage
  - Calcul automatique des coûts
  - Sauvegarde des résultats en JSON

- **Script de recherche** : Création de `trouver_appartement.py` pour rechercher des appartements avec système de scoring multi-critères

### 🔄 Améliorations techniques

- Gestion intelligente des chemins de photos (locaux et URLs)
- Support de multiples sources de données JSON
- Calcul précis du nombre d'images analysées pour l'estimation des coûts
- Gestion d'erreurs robuste avec retry automatique

## 📁 Structure du projet

```
HomeScore/
├── gemini_analyzer.py          # Module d'analyse avec Gemini API
├── analyser_appartement.py     # Script d'analyse complète d'appartement
├── trouver_appartement.py      # Script de recherche d'appartements
└── README.md                   # Documentation du projet
```

## 🔮 Prochaines étapes

- [ ] Intégration avec la base de données complète
- [ ] Interface web pour visualiser les analyses
- [ ] Export des résultats en différents formats
- [ ] Optimisation des prompts pour améliorer la précision
- [ ] Ajout de nouvelles métriques d'analyse

## 📝 Notes

- Le projet utilise Gemini 2.5 Flash par défaut pour réduire les coûts
- Gemini 2.5 Pro est utilisé uniquement pour l'estimation de hauteur de plafond (meilleure précision)
- Les analyses sont sauvegardées automatiquement en JSON

