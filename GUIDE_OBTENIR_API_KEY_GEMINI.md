# Guide : Obtenir une clé API Gemini

Ce guide vous explique étape par étape comment obtenir une clé API Gemini de Google.

## Prérequis

- Un compte Google (Gmail)
- Accès à Internet
- Environ 5 minutes

## Étapes détaillées

### Étape 1 : Accéder à Google AI Studio

1. Ouvrez votre navigateur web
2. Allez sur : **https://aistudio.google.com/**
3. Connectez-vous avec votre compte Google si ce n'est pas déjà fait

### Étape 2 : Créer une nouvelle clé API

1. Une fois connecté, cliquez sur **"Get API key"** dans le menu de gauche ou en haut à droite
2. Si vous avez plusieurs projets Google Cloud, sélectionnez le projet souhaité
3. Si vous n'avez pas de projet, Google créera automatiquement un nouveau projet pour vous

### Étape 3 : Générer la clé API

1. Cliquez sur **"Create API key in new project"** ou **"Create API key"**
2. La clé API sera générée automatiquement et affichée dans une popup
3. **IMPORTANT** : Copiez immédiatement la clé API et sauvegardez-la dans un endroit sûr
   - ⚠️ Vous ne pourrez plus voir la clé complète après avoir fermé cette fenêtre
   - La clé ressemble à : `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
4. Cliquez sur **"Close"** une fois la clé copiée

### Étape 4 : Trouver votre clé API dans Google Cloud Console

**⚠️ IMPORTANT :** Si vous avez créé la clé depuis Google AI Studio, elle peut être dans un projet différent !

1. Dans Google Cloud Console : **https://console.cloud.google.com/**
2. **Vérifiez le projet sélectionné** : En haut à gauche, cliquez sur le sélecteur de projet (à côté de "Google Cloud")
   - Vous verrez une liste de tous vos projets
   - Si vous avez créé la clé avec "Create API key in new project", Google a peut-être créé un projet avec un nom générique comme "My Project" ou "Project 12345"
   - Cherchez un projet récent ou avec un nom générique
3. Sélectionnez le bon projet dans la liste
4. Allez dans **"APIs & Services"** > **"Credentials"** (dans le menu de gauche)
5. Votre clé API Gemini devrait apparaître dans la section **"API Keys"**

**Si vous ne trouvez toujours pas la clé :**
- Retournez sur **https://aistudio.google.com/**
- Cliquez sur **"Get API key"** dans le menu
- Vous verrez la liste de toutes vos clés API créées depuis AI Studio
- Vous pouvez copier la clé directement depuis là, ou cliquer sur **"Manage API keys in Google Cloud Console"** pour être redirigé vers le bon projet

### Étape 5 : Configurer les restrictions (Recommandé)

1. Une fois que vous avez trouvé votre clé API dans la liste
2. Cliquez sur le nom de la clé (ou sur **"Show key"** puis **"Edit key"**)
3. Configurez les restrictions :
   - **Application restrictions** : Limitez à certaines applications/IP si nécessaire
   - **API restrictions** : Sélectionnez **"Restrict key"** et choisissez **"Generative Language API"** uniquement (recommandé)
4. Cliquez sur **"Save"**

### Étape 6 : Activer l'API Gemini (si nécessaire)

1. Assurez-vous d'être dans le **bon projet** (celui où se trouve votre clé API)
2. Dans Google Cloud Console, allez dans **"APIs & Services"** > **"Library"** (dans le menu de gauche)
3. Recherchez **"Generative Language API"** dans la barre de recherche
4. Cliquez sur **"Enable"** si ce n'est pas déjà activé

### Étape 7 : Utiliser votre clé API

Une fois la clé obtenue, vous pouvez l'utiliser dans votre code Python. Voici les conventions de nommage recommandées :

#### Option 1 : Variable directe (pour tests rapides)
```python
import google.generativeai as genai

# Nommez votre variable : GEMINI_API_KEY ou gemini_api_key
GEMINI_API_KEY = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-pro')
```

#### Option 2 : Variable d'environnement (recommandé pour production)
```python
import os
import google.generativeai as genai

# Récupérez la clé depuis une variable d'environnement
# Nom de la variable d'environnement : GEMINI_API_KEY
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

model = genai.GenerativeModel('gemini-pro')
```

#### Option 3 : Fichier .env (meilleure pratique)
```python
# Dans un fichier .env (à ne jamais commiter dans git)
# GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()  # Charge les variables du fichier .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-pro')
```

**Conventions de nommage recommandées :**
- `GEMINI_API_KEY` (en majuscules pour les constantes)
- `gemini_api_key` (en minuscules avec underscores)
- `GOOGLE_GEMINI_API_KEY` (si vous utilisez plusieurs APIs Google)

## Notes importantes

- **Gratuit** : Google offre un quota gratuit généreux pour Gemini API
- **Sécurité** : Ne partagez jamais votre clé API publiquement
- **Quota** : Vérifiez votre quota dans Google Cloud Console
- **Limites** : Respectez les limites de taux (rate limits) de l'API

## Vérification de votre clé API

Pour tester si votre clé fonctionne :

```python
import google.generativeai as genai

# Remplacez par votre vraie clé API
GEMINI_API_KEY = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Bonjour, test de l'API")
print(response.text)
```

## Liens utiles (en anglais)

- **Google AI Studio** : https://aistudio.google.com/
- **Gemini API Documentation** : https://ai.google.dev/docs
- **Google Cloud Console** : https://console.cloud.google.com/
- **API Pricing** : https://ai.google.dev/pricing
- **Quickstart Guide** : https://ai.google.dev/quickstart
- **Python SDK Reference** : https://ai.google.dev/api/python

## Terminologie anglaise de l'interface

Pour vous aider à naviguer dans l'interface anglaise :

- **"Get API key"** = Obtenir une clé API
- **"Create API key"** = Créer une clé API
- **"Create API key in new project"** = Créer une clé API dans un nouveau projet
- **"Manage API keys in Google Cloud Console"** = Gérer les clés API dans Google Cloud Console
- **"APIs & Services"** = APIs et Services
- **"Credentials"** = Identifiants
- **"Library"** = Bibliothèque
- **"Enable"** = Activer
- **"Restrict key"** = Restreindre la clé
- **"Application restrictions"** = Restrictions d'application
- **"API restrictions"** = Restrictions d'API
- **"Save"** = Enregistrer
- **"Close"** = Fermer
- **"Project selector"** = Sélecteur de projet (en haut à gauche, à côté de "Google Cloud")
- **"Show key"** = Afficher la clé
- **"Edit key"** = Modifier la clé

## Dépannage

### Problème : "Je ne vois pas ma clé API Gemini dans la liste des credentials"

**Solution 1 : Vérifier le projet sélectionné**
1. En haut à gauche de Google Cloud Console, cliquez sur le **sélecteur de projet** (à côté de "Google Cloud")
2. Vous verrez tous vos projets Google Cloud
3. Si vous avez créé la clé avec "Create API key in new project", cherchez :
   - Un projet récent (créé aujourd'hui)
   - Un projet avec un nom générique comme "My Project", "Project 12345", ou "Project-XXXXX"
   - Un projet que vous n'avez pas créé manuellement
4. Sélectionnez ce projet et retournez dans **"APIs & Services"** > **"Credentials"**

**Solution 2 : Retrouver la clé depuis Google AI Studio**
1. Allez sur **https://aistudio.google.com/**
2. Cliquez sur **"Get API key"** dans le menu
3. Vous verrez toutes vos clés API créées depuis AI Studio
4. Vous pouvez :
   - Copier la clé directement depuis cette page
   - Cliquer sur **"Manage API keys in Google Cloud Console"** pour être redirigé vers le bon projet

**Solution 3 : Créer une nouvelle clé dans le projet actuel**
1. Dans Google Cloud Console, assurez-vous d'être dans le projet souhaité (ex: "Fincalert")
2. Allez dans **"APIs & Services"** > **"Credentials"**
3. Cliquez sur **"+ Create credentials"** > **"API key"**
4. La nouvelle clé sera créée dans ce projet et apparaîtra dans la liste

### Problème : "API key not valid"
- Vérifiez que vous avez copié la clé complète
- Vérifiez que l'API Gemini est activée dans votre projet
- Assurez-vous d'utiliser la clé du bon projet

### Problème : "Quota exceeded"
- Vérifiez votre quota dans Google Cloud Console
- Attendez la réinitialisation du quota ou passez à un plan payant

### Problème : "Permission denied"
- Vérifiez les restrictions de votre clé API dans Google Cloud Console
- Assurez-vous que l'API Gemini est activée pour votre projet
- Vérifiez que vous êtes dans le bon projet Google Cloud

