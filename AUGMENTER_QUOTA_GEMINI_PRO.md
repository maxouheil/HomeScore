# 💳 Comment Augmenter le Quota Gemini Pro

## 🎯 Solution : Activer la Facturation

Pour utiliser Gemini Pro au-delà du quota gratuit, vous devez activer la facturation dans Google Cloud Console.

### Étape 1 : Accéder à la Facturation

1. Allez sur : **https://console.cloud.google.com/**
2. Assurez-vous d'être dans le **bon projet** (celui avec votre clé Gemini)
3. Dans le menu de gauche, cliquez sur **"Billing"** (Facturation)

### Étape 2 : Activer un Compte de Facturation

1. Si vous n'avez pas encore de compte de facturation :
   - Cliquez sur **"Link a billing account"** ou **"Create billing account"**
   - Suivez les instructions pour ajouter une carte de crédit
   - Google offre souvent des crédits gratuits ($300) pour nouveaux comptes

2. Si vous avez déjà un compte de facturation :
   - Assurez-vous qu'il est lié à votre projet
   - Sélectionnez-le dans la liste

### Étape 3 : Vérifier les Quotas

1. Allez dans **"APIs & Services"** > **"Quotas"**
2. Recherchez **"Generative Language API"**
3. Vous verrez les quotas actuels et pourrez les augmenter si nécessaire

### Étape 4 : Utiliser Gemini Pro

Une fois la facturation activée, vous pouvez utiliser :

- **`gemini-pro-latest`** : Modèle texte Pro
- **`gemini-2.5-pro`** : Modèle vision Pro

## 💰 Coûts Gemini Pro

- **Gemini 2.5 Pro** : ~$0.001315 par image
- **Gemini Pro (texte)** : Variable selon l'usage

## 💡 Alternative : Utiliser Gemini Flash (Gratuit)

En attendant d'activer la facturation, vous pouvez utiliser **Gemini Flash** qui a un quota gratuit généreux :

- **15 requêtes/minute** gratuitement
- **Coût** : $0.000075 par image (très économique)
- **Qualité** : Bonne pour la plupart des cas d'usage

```python
from gemini_analyzer import GeminiAnalyzer

# Utiliser Flash (gratuit jusqu'à 15 req/min)
analyzer = GeminiAnalyzer('gemini-2.5-flash')
```

## 🔗 Liens Utiles

- **Google Cloud Console** : https://console.cloud.google.com/
- **Facturation** : https://console.cloud.google.com/billing
- **Quotas** : https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
- **Pricing Gemini** : https://ai.google.dev/pricing

---

**Une fois la facturation activée, vous pourrez utiliser Gemini Pro sans limite de quota gratuit !** 🚀

