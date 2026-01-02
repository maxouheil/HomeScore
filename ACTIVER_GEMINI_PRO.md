# 🔧 Comment Activer Gemini Pro

## 📋 Étapes pour Activer l'API Generative Language

Pour utiliser tous les modèles Gemini (y compris Gemini Pro), vous devez activer l'API Generative Language dans Google Cloud Console.

### Étape 1 : Accéder à Google Cloud Console

1. Allez sur : **https://console.cloud.google.com/**
2. Assurez-vous d'être dans le **bon projet** (celui où se trouve votre clé "GEMINI KEY")

### Étape 2 : Activer l'API Generative Language

1. Dans le menu de gauche, cliquez sur **"APIs & Services"** > **"Library"**
2. Dans la barre de recherche en haut, tapez : **"Generative Language API"**
3. Cliquez sur le résultat **"Generative Language API"**
4. Si vous voyez un bouton **"Enable"**, cliquez dessus
5. Attendez quelques secondes que l'activation se termine

### Étape 3 : Vérifier l'Activation

1. Retournez dans **"APIs & Services"** > **"Enabled APIs & services"**
2. Vous devriez voir **"Generative Language API"** dans la liste avec le statut **"Enabled"** ✅

### Étape 4 : Vérifier les Restrictions de votre Clé API

1. Allez dans **"APIs & Services"** > **"Credentials"**
2. Cliquez sur votre clé **"GEMINI KEY"**
3. Vérifiez la section **"API restrictions"** :
   - Si c'est **"Don't restrict key"** → ✅ C'est bon
   - Si c'est **"Restrict key"** → Assurez-vous que **"Generative Language API"** est dans la liste des APIs autorisées

### Étape 5 : Tester les Modèles

Une fois l'API activée, testez avec :

```bash
python3 test_gemini.py
```

## 📚 Modèles Disponibles

Après activation, vous devriez avoir accès à :

- **`gemini-pro-latest`** : Modèle texte Pro (équivalent à l'ancien gemini-pro)
- **`gemini-2.5-flash`** : Modèle vision rapide et économique
- **`gemini-2.5-pro`** : Modèle vision Pro pour analyses complexes
- **`gemini-flash-latest`** : Dernière version Flash

## 🔍 Vérifier les Modèles Disponibles

Pour voir tous les modèles disponibles avec votre clé :

```python
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

models = list(genai.list_models())
for m in models:
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")
```

## ⚠️ Si l'API est Déjà Activée

Si l'API est déjà activée mais que certains modèles ne fonctionnent pas :

1. **Vérifiez votre projet** : Assurez-vous d'utiliser le bon projet Google Cloud
2. **Vérifiez les quotas** : Certains modèles peuvent avoir des quotas limités
3. **Utilisez les alias "latest"** : 
   - `gemini-pro-latest` au lieu de `gemini-pro`
   - `gemini-flash-latest` au lieu de `gemini-1.5-flash`

## 💡 Code d'Exemple

```python
from gemini_analyzer import GeminiAnalyzer

# Utiliser Gemini Pro pour texte
analyzer_pro = GeminiAnalyzer('gemini-pro-latest')

# Utiliser Gemini Flash pour vision (économique)
analyzer_flash = GeminiAnalyzer('gemini-2.5-flash')

# Utiliser Gemini Pro pour vision (qualité)
analyzer_pro_vision = GeminiAnalyzer('gemini-2.5-pro')
```

---

**Une fois l'API activée, relancez `python3 test_gemini.py` !** 🚀

