# 💳 Activer la Facturation pour le Projet CURSOR

## 🎯 Objectif

Lier le projet **CURSOR** au même compte de facturation que **Fincalert** ("My Billing Account").

## 📋 Étapes Détaillées

### Étape 1 : Accéder à la Gestion des Projets

1. Allez sur : **https://console.cloud.google.com/**
2. Assurez-vous d'être connecté avec le bon compte Google
3. Dans le menu de gauche, cliquez sur **"Billing"** > **"Your projects"**
   - OU allez directement sur : **https://console.cloud.google.com/billing/projects**

### Étape 2 : Trouver le Projet CURSOR

1. Dans la liste des projets, trouvez **"CURSOR"**
2. Vous devriez voir **"Billing is disabled"** dans la colonne "Billing account"

### Étape 3 : Lier le Compte de Facturation

1. Cliquez sur les **3 points verticaux** (⋮) dans la colonne "Actions" à droite de "CURSOR"
2. Sélectionnez **"Change billing account"** ou **"Link billing account"**
3. Dans la popup qui s'ouvre :
   - Sélectionnez **"My Billing Account"** (le même que Fincalert)
   - Cliquez sur **"Set account"** ou **"Link"**

### Étape 4 : Vérifier

1. Après quelques secondes, rafraîchissez la page
2. Vous devriez voir **"My Billing Account"** dans la colonne "Billing account" pour CURSOR
3. Le statut devrait être identique à Fincalert ✅

## ⚠️ Si la Popup Dit "No available billing accounts"

Si vous voyez "There are no available billing accounts to link to this project" :

### Solution 1 : Vérifier les Permissions

1. Assurez-vous d'être **administrateur** du compte de facturation
2. Allez dans **"Billing"** > **"Your billing accounts"**
3. Vérifiez que vous voyez "My Billing Account" dans la liste
4. Si vous ne le voyez pas, vous n'avez peut-être pas les droits

### Solution 2 : Utiliser un Autre Compte

1. Si vous avez plusieurs comptes Google, assurez-vous d'être connecté avec le bon
2. Le compte qui a créé "My Billing Account" doit être celui utilisé

### Solution 3 : Créer un Nouveau Compte de Facturation

Si nécessaire :

1. Allez dans **"Billing"** > **"Your billing accounts"**
2. Cliquez sur **"Create account"** ou **"Link billing account"**
3. Suivez les instructions pour ajouter une carte de crédit
4. Retournez dans "Your projects" et liez CURSOR à ce nouveau compte

## 🔗 Lien Direct

Pour accéder directement à la gestion des projets :
**https://console.cloud.google.com/billing/projects**

## ✅ Résultat Attendu

Après activation, votre projet CURSOR devrait avoir :
- ✅ **Billing account** : My Billing Account
- ✅ **Billing account ID** : 01F9B6-3E581A-63B116 (même que Fincalert)
- ✅ **Statut** : Identique à Fincalert

## 💡 Note Importante

- Lier un compte de facturation ne signifie pas que vous payez automatiquement
- Google offre des quotas gratuits généreux même avec facturation activée
- Vous ne payez que si vous dépassez les quotas gratuits
- Google offre souvent $300 de crédits gratuits pour nouveaux comptes

---

**Une fois lié, votre projet CURSOR aura les mêmes quotas que Fincalert !** 🚀

