# Guide : Connexion Jinka par Email avec Code d'Activation

Le script utilise maintenant la connexion par email au lieu de Google OAuth, et récupère automatiquement le code d'activation depuis Gmail.

## 🔧 Configuration Gmail

Pour que le script puisse lire vos emails Gmail, vous devez :

### Option 1 : Mot de passe d'application (Recommandé si 2FA activé)

1. Allez sur https://myaccount.google.com/apppasswords
2. Sélectionnez "Mail" et "Autre (nom personnalisé)"
3. Entrez "HomeScore" comme nom
4. Générez le mot de passe
5. Copiez le mot de passe généré (16 caractères)

### Option 2 : Autoriser les applications moins sécurisées (Si 2FA désactivé)

1. Allez sur https://myaccount.google.com/lesssecureapps
2. Activez "Autoriser les applications moins sécurisées"

## 📝 Configuration .env

Ajoutez ces variables dans votre fichier `.env` :

```env
# Email Jinka (celui utilisé pour se connecter à Jinka)
JINKA_EMAIL=votre@email.com

# Identifiants Gmail pour récupérer le code d'activation
GMAIL_EMAIL=votre@gmail.com
GMAIL_PASSWORD=votre_mot_de_passe_application

# Ou utilisez les mêmes identifiants si c'est le même compte
# GMAIL_EMAIL=${JINKA_EMAIL}
# GMAIL_PASSWORD=${JINKA_PASSWORD}
```

**Note :** Si `GMAIL_EMAIL` et `GMAIL_PASSWORD` ne sont pas définis, le script utilisera `JINKA_EMAIL` et `JINKA_PASSWORD` par défaut.

## 🚀 Utilisation

Le script fonctionne automatiquement :

1. Va sur la page de connexion Jinka
2. Clique sur "Continuer avec mon e-mail"
3. Saisit votre email
4. Attend le code d'activation
5. Récupère automatiquement le code depuis Gmail
6. Saisit le code et se connecte

## ⚠️ Notes importantes

- Le script cherche les emails de Jinka des **10 dernières minutes**
- Il cherche les emails de `noreply@jinka.fr` ou contenant "code" dans le sujet
- Le code doit être à **6 chiffres**
- Si le code n'est pas trouvé automatiquement, vous avez 60 secondes pour l'entrer manuellement

## 🐛 Dépannage

### Erreur "Identifiants Gmail non trouvés"
→ Vérifiez que `GMAIL_EMAIL` et `GMAIL_PASSWORD` sont dans votre `.env`

### Erreur "Aucun code d'activation trouvé"
→ Vérifiez votre boîte mail Gmail
→ Le script cherche dans les 10 dernières minutes
→ Assurez-vous que l'email de Jinka est bien arrivé

### Erreur de connexion IMAP
→ Vérifiez que vous utilisez un mot de passe d'application (pas votre mot de passe normal)
→ Vérifiez que l'accès IMAP est activé dans Gmail

### Le code n'est pas détecté
→ Le script cherche un code à 6 chiffres
→ Vérifiez le format de l'email de Jinka
→ Vous pouvez entrer le code manuellement (60 secondes de timeout)

