# 🏠 HomeScore - Système de Scoring d'Appartements

Un système intelligent pour scraper, analyser et scorer des appartements sur Jinka selon des critères personnalisés.

## 📋 Vue d'ensemble

HomeScore est un système automatisé qui :
- **Scrape** les offres d'appartements depuis vos alertes Jinka
- **Extrait** automatiquement les données clés (prix, surface, localisation, etc.)
- **Score** chaque appartement sur 100 points selon vos critères
- **Génère** des rapports HTML visuels
- **Identifie** automatiquement le quartier via analyse de carte

## 🎯 Critères de Scoring

| Critère | Points | Description |
|---------|--------|-------------|
| **Localisation** | 20pts | Arrondissement, quartier, proximité transports |
| **Style** | 20pts | Éléments haussmanniens, caractère architectural |
| **Prix** | 20pts | Prix total et prix au m² |
| **Ensoleillement** | 10pts | Luminosité, orientation |
| **Cuisine ouverte** | 10pts | Type de cuisine (américaine, ouverte, fermée) |
| **Étage** | 10pts | Étage, ascenseur, vue |
| **Vue** | 5pts | Vue dégagée, balcon, terrasse |
| **Surface** | 5pts | Surface habitable, pièces |

## 🚀 Fonctionnalités

### ✅ Scraping Automatique
- **Connexion Jinka** via Google OAuth
- **Extraction des URLs** d'appartements depuis les alertes
- **Scraping des données** détaillées de chaque appartement
- **Mode headless** pour l'efficacité

### ✅ Extraction de Données Avancée
- **Prix et prix/m²** : Extraction automatique
- **Surface et pièces** : Détection via regex
- **Étage** : Identification automatique
- **Localisation** : Arrondissement + analyse de carte
- **Description complète** : Texte intégral
- **Caractéristiques** : Parking, ascenseur, balcon, etc.
- **Photos** : URLs des images
- **Agence** : Nom de l'agence

### ✅ Analyse de Carte Intelligente
- **Screenshots automatiques** de la carte Jinka
- **Identification du quartier** basée sur les rues visibles
- **Coordonnées GPS** (en développement)
- **Proximité des transports** et points d'intérêt

### ✅ Scoring Haussmannien
- **Détection automatique** des éléments architecturaux
- **Mots-clés étendus** : moulures, parquet, cheminée, etc.
- **Scoring par catégorie** : architectural, caractère, matériaux, détails
- **Score final** calculé automatiquement

### ✅ Rapports Visuels
- **Génération HTML** avec cartes d'appartements
- **Scores détaillés** par critère
- **Photos et descriptions** intégrées
- **Interface moderne** et responsive

## 📁 Structure du Projet

```
HomeScore/
├── README.md                    # Documentation
├── requirements.txt             # Dépendances Python
├── .env                        # Variables d'environnement
├── config.json                 # Configuration générale
├── scoring_config.json         # Critères de scoring
├── scoring_prompt.txt          # Prompt OpenAI
├── scrape_jinka.py             # Scraper principal
├── score_appartement.py        # Module de scoring
├── generate_html_report.py     # Générateur de rapports
├── run_daily_scrape.py         # Automatisation quotidienne
├── test_homescore.py           # Tests du système
├── quick_start.py              # Démarrage rapide
├── data/
│   ├── appartements/           # Données scrapées (JSON)
│   └── screenshots/            # Screenshots de cartes
└── output/
    └── rapport_appartements.html  # Rapport final
```

## 🛠️ Installation

### 1. Cloner le projet
```bash
git clone <repository>
cd HomeScore
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configuration
```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer les variables
nano .env
```

### 4. Variables d'environnement
```env
JINKA_EMAIL=votre_email@gmail.com
JINKA_PASSWORD=votre_mot_de_passe
OPENAI_API_KEY=votre_cle_openai
```

## 🚀 Utilisation

### Démarrage rapide
```bash
python quick_start.py
```

### Scraping manuel
```bash
python scrape_jinka.py "URL_DE_VOTRE_ALERTE_JINKA"
```

### Scoring des appartements
```bash
python score_appartement.py
```

### Génération de rapport
```bash
python generate_html_report.py
```

### Test complet
```bash
python test_homescore.py
```

## 📊 Exemple de Résultats

### Données Extraites
```json
{
  "id": "90931157",
  "prix": "775 000 €",
  "surface": "70 m²",
  "pieces": "3 pièces - 2 chambres",
  "etage": "4e étage",
  "localisation": "Paris 19e (75019)",
  "quartier": "Place des Fêtes (score: 8)",
  "description": "Magnifique duplex...",
  "style_haussmannien": {
    "score": 30,
    "elements": {
      "caractère": ["restauré"]
    }
  }
}
```

### Score Final
- **Prix** : 15/20
- **Localisation** : 15/20
- **Surface** : 15/20
- **Style** : 6/20
- **Total** : 51/100

## 🔧 Configuration Avancée

### Critères de Scoring
Éditez `scoring_config.json` pour personnaliser :
- Poids des critères
- Descriptions détaillées
- Niveaux de scoring (excellent, bon, moyen)
- Bonus et malus

### Prompt OpenAI
Modifiez `scoring_prompt.txt` pour ajuster :
- Instructions de scoring
- Contexte et critères
- Format de réponse

## 📈 Améliorations Futures

### 🎯 Court terme
- [ ] Correction des coordonnées GPS
- [ ] Extraction d'adresses exactes
- [ ] Amélioration de l'OCR sur les cartes
- [ ] Interface web pour visualisation

### 🚀 Long terme
- [ ] Machine Learning pour scoring automatique
- [ ] Intégration d'autres sites immobiliers
- [ ] Notifications push pour nouvelles offres
- [ ] API REST pour intégration externe

## 🐛 Dépannage

### Problèmes courants

**Erreur de connexion Jinka**
```bash
# Vérifier les credentials
cat .env
# Relancer le scraping
python scrape_jinka.py
```

**Screenshots non générés**
```bash
# Vérifier les permissions
ls -la data/screenshots/
# Relancer avec debug
python scrape_jinka.py --debug
```

**Scoring OpenAI échoue**
```bash
# Vérifier la clé API
echo $OPENAI_API_KEY
# Tester la connexion
python score_appartement.py --test
```

## 📝 Logs et Debug

### Niveaux de log
- `INFO` : Informations générales
- `DEBUG` : Détails techniques
- `ERROR` : Erreurs critiques

### Fichiers de log
```bash
tail -f logs/homescore.log
```

## 🤝 Contribution

### Ajouter de nouveaux critères
1. Modifier `scoring_config.json`
2. Mettre à jour `scoring_prompt.txt`
3. Tester avec `python test_homescore.py`

### Améliorer l'extraction
1. Identifier les nouveaux sélecteurs CSS
2. Modifier `scrape_jinka.py`
3. Ajouter des tests unitaires

## 📄 Licence

MIT License - Voir `LICENSE` pour plus de détails.

## 🙏 Remerciements

- **Jinka** pour la plateforme immobilière
- **Playwright** pour l'automatisation web
- **OpenAI** pour l'IA de scoring
- **CandidaturesPlum** pour l'inspiration du système de scoring

---

## 📞 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Consulter la documentation
- Vérifier les logs d'erreur

**HomeScore - Trouvez votre appartement idéal ! 🏠✨**