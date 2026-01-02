# 💳 Activer la Facturation pour Gemini Pro

## 📊 Situation Actuelle

D'après votre écran, vous avez :
- ✅ **Fincalert** : Compte de facturation activé ("My Billing Account")
- ✅ **Tidbit** : Compte de facturation activé
- ❌ **Default Gemini Project** : Facturation désactivée (c'est là que votre clé Gemini est créée)
- ❌ **CURSOR** : Facturation désactivée

## 🎯 Solution : Lier le Projet Gemini à un Compte de Facturation

### Option 1 : Utiliser le Compte de Facturation Existant (Recommandé)

1. Dans la page "Your projects", trouvez **"Default Gemini Project"**
2. Cliquez sur les **3 points verticaux** (Actions) à droite du projet
3. Sélectionnez **"Change billing account"** ou **"Link billing account"**
4. Choisissez **"My Billing Account"** (celui déjà utilisé pour Fincalert)
5. Confirmez

### Option 2 : Créer une Nouvelle Clé dans le Projet Fincalert

Si vous préférez utiliser le projet qui a déjà la facturation :

1. Allez dans le projet **"Fincalert"**
2. Allez dans **"APIs & Services"** > **"Credentials"**
3. Cliquez sur **"+ Create credentials"** > **"API key"**
4. Une nouvelle clé sera créée dans le projet Fincalert
5. Mettez à jour votre fichier `.env` avec cette nouvelle clé

### Option 3 : Créer un Nouveau Compte de Facturation

Si vous voulez un compte séparé pour Gemini :

1. Allez dans **"Billing"** > **"Your billing accounts"**
2. Cliquez sur **"Create account"** ou **"Link billing account"**
3. Suivez les instructions pour ajouter une carte de crédit
4. Retournez dans "Your projects" et liez "Default Gemini Project" à ce nouveau compte

## ⚠️ Important : Comprendre la Popup

La popup "No available billing accounts" apparaît quand :
- Vous essayez de lier un projet à un compte de facturation
- Mais tous vos comptes de facturation sont déjà liés à d'autres projets
- OU vous n'avez pas les droits administrateur

**Solution** : Utilisez le compte "My Billing Account" existant qui est déjà lié à Fincalert et Tidbit.

## ✅ Après Activation

Une fois la facturation liée au projet Gemini :

1. Les quotas augmentent automatiquement
2. Vous pouvez utiliser `gemini-pro-latest` et `gemini-2.5-pro`
3. Les limites gratuites sont plus élevées
4. Vous payez seulement si vous dépassez les quotas gratuits

## 💰 Coûts Gemini

- **Quota gratuit** : Généreux même avec facturation activée
- **Gemini Flash** : $0.000075 par image (très économique)
- **Gemini Pro** : $0.001315 par image
- **Crédits Google** : Souvent $300 offerts pour nouveaux comptes

## 🔗 Liens Directs

- **Gestion des projets** : https://console.cloud.google.com/cloud-resource-manager
- **Facturation** : https://console.cloud.google.com/billing
- **Credentials** : https://console.cloud.google.com/apis/credentials

---

**Recommandation** : Liez "Default Gemini Project" à "My Billing Account" existant pour activer immédiatement les quotas Pro ! 🚀

