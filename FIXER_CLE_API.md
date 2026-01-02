# 🔧 Guide pour Corriger la Clé API Gemini

## ⚠️ Problème Détecté

Votre clé API commence par "Alza" au lieu de "AIza". Les clés Gemini doivent commencer par "AIza" (avec un I majuscule).

## ✅ Solution : Recopier la Clé Correctement

### Étape 1 : Accéder à Google Cloud Console

1. Allez sur : **https://console.cloud.google.com/**
2. Assurez-vous d'être dans le **bon projet** (celui où vous avez créé la clé "GEMINI KEY")

### Étape 2 : Afficher la Clé API

1. Dans le menu de gauche, cliquez sur **"APIs & Services"** > **"Credentials"**
2. Trouvez votre clé **"GEMINI KEY"** dans la liste
3. Cliquez sur **"Show key"** (ou sur le nom de la clé)
4. Une popup s'ouvre avec votre clé complète
5. **Copiez TOUTE la clé** (elle doit commencer par "AIza" et faire ~39 caractères)

### Étape 3 : Vérifier que l'API est Activée

1. Dans le menu de gauche, cliquez sur **"APIs & Services"** > **"Library"**
2. Recherchez **"Generative Language API"** dans la barre de recherche
3. Si vous voyez **"Enable"**, cliquez dessus pour activer l'API
4. Si vous voyez **"Manage"**, l'API est déjà activée ✅

### Étape 4 : Vérifier les Restrictions (Optionnel)

1. Retournez dans **"Credentials"**
2. Cliquez sur votre clé **"GEMINI KEY"**
3. Vérifiez la section **"API restrictions"** :
   - Si c'est **"Don't restrict key"**, c'est bon ✅
   - Si c'est **"Restrict key"**, assurez-vous que **"Generative Language API"** est dans la liste

### Étape 5 : Mettre à Jour le Fichier .env

Une fois que vous avez la bonne clé (commençant par "AIza") :

```bash
# Remplacez VOTRE_CLE_ICI par la vraie clé
echo "GEMINI_API_KEY=VOTRE_CLE_ICI" > .env
```

Ou éditez manuellement le fichier `.env` et remplacez la valeur de `GEMINI_API_KEY`.

### Étape 6 : Tester

```bash
python3 test_gemini.py
```

Ou :

```bash
python3 diagnostic_gemini.py
```

## 🔍 Format d'une Clé API Gemini Valide

- ✅ Commence par : **AIza** (A-I-Z-a)
- ✅ Longueur : ~39 caractères
- ✅ Exemple : `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

## ❌ Erreurs Communes

- ❌ "Alza" au lieu de "AIza" (erreur de copie)
- ❌ Clé tronquée (manque des caractères)
- ❌ Espaces avant/après la clé
- ❌ Guillemets autour de la clé dans .env

## 💡 Astuce

Pour éviter les erreurs de copie, utilisez le bouton **"Copy"** (icône de copie) dans la popup Google Cloud Console plutôt que de sélectionner manuellement.

---

**Une fois la clé corrigée, relancez `python3 test_gemini.py` pour vérifier !** 🚀

