# 🚀 Intégration Gemini dans HomeScore

Ce guide explique comment utiliser Gemini pour l'analyse visuelle dans votre projet HomeScore, réduisant les coûts de **96%** par rapport à OpenAI.

## 📋 Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Configuration

Créez un fichier `.env` à la racine du projet :

```env
GEMINI_API_KEY=votre_cle_api_gemini
```

### 3. Test de la clé API

```bash
python test_gemini.py
```

### 4. Exemple d'utilisation

```bash
python exemple_analyse_gemini.py
```

## 📚 Modules Disponibles

### `gemini_analyzer.py`

Module principal pour l'analyse visuelle avec Gemini.

**Fonctions principales :**

- `GeminiAnalyzer` : Classe principale pour analyser des images
- `analyze_apartment_style()` : Analyse le style d'un appartement
- `detect_bathtub()` : Détecte la présence d'une baignoire
- `detect_open_kitchen()` : Détecte si la cuisine est ouverte
- `estimate_ceiling_height()` : Estime la hauteur sous plafond
- `analyze_living_room_size()` : Analyse la taille de la pièce de vie
- `estimate_distance_vis_a_vis()` : Estime la distance vis-à-vis

**Exemple d'utilisation :**

```python
from gemini_analyzer import GeminiAnalyzer, detect_bathtub

# Analyse simple
analyzer = GeminiAnalyzer('gemini-1.5-flash')
result = analyzer.analyze_image(
    "photo.jpg",
    "Décris cette photo en détail",
    return_json=True
)

# Fonction spécialisée
bathtub_result = detect_bathtub("salle_de_bain.jpg")
print(bathtub_result)
```

### `vision_analyzer.py`

Wrapper unifié supportant OpenAI ET Gemini. Permet de basculer facilement entre les deux.

**Exemple d'utilisation :**

```python
from vision_analyzer import VisionAnalyzer, Provider

# Utiliser Gemini (recommandé)
analyzer = VisionAnalyzer(Provider.GEMINI, model='gemini-1.5-flash')
result = analyzer.analyze_image("photo.jpg", "Analyse cette image")

# Utiliser OpenAI (si nécessaire)
analyzer_openai = VisionAnalyzer(Provider.OPENAI, model='gpt-4o-mini')
result = analyzer_openai.analyze_image("photo.jpg", "Analyse cette image")

# Comparer les coûts
from vision_analyzer import compare_providers
comparison = compare_providers(1000)
print(comparison)
```

## 💰 Comparaison des Coûts

| Modèle | Coût/Image | Coût pour 10K images | Économies |
|--------|-----------|---------------------|----------|
| GPT-4o-mini (actuel) | $0.0003 | $20.76 | - |
| **Gemini 1.5 Flash** ⭐ | **$0.000075** | **$0.77** | **96.3%** |
| Gemini 1.5 Pro | $0.001315 | $13.54 | 34.8% |

## 🎯 Cas d'Usage Recommandés

### Analyse Simple (Détection présence/absence)
**Modèle :** `gemini-1.5-flash`
- Détection baignoire
- Détection cuisine ouverte/fermée
- Détection présence fenêtres

### Analyse Modérée (Style, caractéristiques)
**Modèle :** `gemini-1.5-pro`
- Analyse du style (moderne, haussmannien, etc.)
- Estimation hauteur plafond
- Analyse taille pièce de vie

## 📝 Migration depuis OpenAI

### Avant (OpenAI)
```python
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    }]
)
```

### Après (Gemini)
```python
from gemini_analyzer import GeminiAnalyzer
analyzer = GeminiAnalyzer('gemini-1.5-flash')
result = analyzer.analyze_image(image_path, prompt, return_json=True)
```

## 🔧 Configuration Avancée

### Rate Limiting

Gemini 1.5 Flash offre 15 requêtes/minute gratuitement. Le module gère automatiquement le rate limiting.

### Modèles Disponibles

- `gemini-1.5-flash` : Rapide et économique (recommandé)
- `gemini-1.5-pro` : Meilleure qualité pour analyses complexes

### Gestion des Erreurs

Le module inclut :
- Retry automatique avec backoff exponentiel
- Gestion des erreurs de rate limiting
- Support des URLs et fichiers locaux

## 📊 Exemples Complets

Voir `exemple_analyse_gemini.py` pour des exemples complets d'utilisation.

## 🆘 Dépannage

### Erreur : "GEMINI_API_KEY non trouvée"
- Vérifiez que le fichier `.env` existe
- Vérifiez que la clé est correctement formatée

### Erreur : "Rate limit exceeded"
- Le module gère automatiquement le rate limiting
- Attendez quelques secondes entre les requêtes

### Erreur : "Image non trouvée"
- Vérifiez le chemin de l'image
- Les URLs HTTP/HTTPS sont supportées

## 📚 Documentation

- [Guide d'obtention de la clé API](GUIDE_OBTENIR_API_KEY_GEMINI.md)
- [Prochaines étapes](PROCHAINES_ETAPES_GEMINI.md)
- [Documentation Gemini](https://ai.google.dev/docs)

## 🎉 Résultats Attendus

Avec Gemini 1.5 Flash :
- ✅ **96% d'économies** sur les coûts d'analyse
- ✅ **Gratuit** jusqu'à 15 requêtes/minute
- ✅ **Rapide** : réponses en quelques secondes
- ✅ **Qualité** : suffisante pour la plupart des cas d'usage

---

**Prêt à économiser ?** Commencez par tester votre clé avec `python test_gemini.py` ! 🚀

