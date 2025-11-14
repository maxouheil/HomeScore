# Guide : Extraction des URLs depuis les emails Jinka

## Avantages de l'extraction par email

✅ **Plus robuste** : Pas de problème de 403 ou de détection de bot  
✅ **Format stable** : Les emails ont toujours le même format  
✅ **Complet** : Contient généralement toutes les URLs des nouveaux appartements  
✅ **Automatisable** : Peut être lancé en cron/tâche planifiée  

## Configuration

### 1. Configurer Gmail avec App Password

1. Va sur https://myaccount.google.com/apppasswords
2. Sélectionne "Mail" et "Autre (nom personnalisé)"
3. Donne un nom (ex: "HomeScore")
4. Gmail génère un mot de passe de 16 caractères
5. **Copie ce mot de passe** (tu ne pourras plus le voir après)

### 2. Configurer le fichier .env

Ajoute ces lignes dans ton fichier `.env` :

```bash
JINKA_EMAIL=ton_email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Le App Password de 16 caractères (sans espaces)
```

**Important** : Utilise l'App Password, pas ton mot de passe Gmail normal !

### 3. Installer les dépendances (si nécessaire)

Les bibliothèques standard de Python suffisent (imaplib est inclus).

## Utilisation

### Basique

```bash
python extract_urls_from_email.py
```

Le script va :
1. Se connecter à ta boîte email via IMAP
2. Chercher les emails de Jinka des 30 derniers jours
3. Extraire toutes les URLs d'appartements
4. Sauvegarder dans `data/apartment_urls_from_email.json`

### Options

Tu peux modifier dans le code :
- `days_back=30` : Nombre de jours en arrière pour chercher
- `sender_filter='jinka'` : Filtre pour l'expéditeur

## Résultat

Le fichier `data/apartment_urls_from_email.json` contiendra toutes les URLs trouvées, par exemple :

```json
[
  "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=75507606&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
  "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=75578302&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
  ...
]
```

## Automatisation

Tu peux lancer ce script :
- **Manuellement** quand tu veux récupérer les nouvelles URLs
- **Automatiquement** avec un cron job (ex: tous les jours à 8h)
- **Dans un pipeline** avant le scraping

## Comparaison avec le scraping web

| Méthode | Avantages | Inconvénients |
|---------|-----------|---------------|
| **Email** ✅ | Stable, pas de 403, complet | Nécessite config email |
| **Web scraping** | Pas de config email | 403, détection bot, instable |

## Dépannage

### Erreur "IMAP4.error"
- Vérifie que tu utilises bien un **App Password**, pas ton mot de passe normal
- Active l'accès IMAP dans les paramètres Gmail

### Aucune URL trouvée
- Vérifie que tu as bien reçu des emails d'alerte Jinka
- Augmente `days_back` pour chercher plus loin dans le temps
- Vérifie le `sender_filter` (peut être 'noreply@jinka.fr' au lieu de 'jinka')

### Erreur de connexion
- Vérifie que les identifiants dans `.env` sont corrects
- Pour Gmail, utilise `imap.gmail.com` (défaut)
- Pour autres providers, modifie `imap_server` dans le code






