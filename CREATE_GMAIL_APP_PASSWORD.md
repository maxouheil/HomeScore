# Guide : Créer un mot de passe d'application Gmail

Gmail nécessite un **mot de passe d'application** pour l'accès IMAP (pas votre mot de passe normal).

## 🔧 Étapes pour créer un mot de passe d'application

### Option 1 : Via le site Google (Recommandé)

1. **Allez sur** : https://myaccount.google.com/apppasswords
   - Ou : Google Account → Sécurité → Mots de passe des applications

2. **Si vous avez la 2FA activée** :
   - Vous verrez directement la page "Mots de passe des applications"
   - Sélectionnez "Mail" et "Autre (nom personnalisé)"
   - Entrez "HomeScore" comme nom
   - Cliquez sur "Générer"
   - **Copiez le mot de passe généré** (16 caractères, espaces ou sans espaces)

3. **Si vous n'avez PAS la 2FA activée** :
   - Vous devez d'abord activer la validation en deux étapes
   - Allez sur : https://myaccount.google.com/security
   - Activez "Validation en deux étapes"
   - Puis revenez sur la page des mots de passe d'application

### Option 2 : Via les paramètres Gmail

1. Allez sur : https://myaccount.google.com/security
2. Sous "Connexion à Google", cliquez sur "Validation en deux étapes"
3. Si pas activée, activez-la
4. Retournez sur la page de sécurité
5. Cliquez sur "Mots de passe des applications"
6. Suivez les étapes ci-dessus

## 📝 Mise à jour du .env

Une fois le mot de passe d'application généré, mettez à jour votre `.env` :

```env
GMAIL_EMAIL=souheil.medaghri@gmail.com
GMAIL_PASSWORD=xxxx xxxx xxxx xxxx
```

**Important** : 
- Le mot de passe d'application fait 16 caractères
- Vous pouvez le copier avec ou sans espaces (les deux fonctionnent)
- Ne partagez JAMAIS ce mot de passe

## ✅ Vérification

Une fois configuré, testez avec :

```bash
python3 test_gmail_code.py
```

Le script devrait maintenant pouvoir se connecter à Gmail et récupérer les codes d'activation.

## 🔒 Sécurité

- Les mots de passe d'application sont plus sécurisés que votre mot de passe principal
- Vous pouvez en créer plusieurs (un par application)
- Vous pouvez les révoquer à tout moment depuis votre compte Google






