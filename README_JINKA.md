# Récupération automatique des appartements Jinka

Ce système permet de récupérer automatiquement les nouveaux appartements correspondant à votre alerte Jinka, avec téléchargement des photos et stockage local.

## Installation

1. Installer les dépendances:
```bash
pip install -r requirements.txt
```

2. **Sauvegarder vos cookies Jinka** (une seule fois):
```bash
python save_jinka_cookies.py
```
Ce script ouvre un navigateur, vous vous connectez à Jinka manuellement, puis les cookies sont sauvegardés automatiquement. Vous n'aurez plus besoin de vous reconnecter ensuite !

## Configuration

Le token de l'alerte est configuré dans `config_jinka.py`. Par défaut, il utilise le token:
`26c2ec3064303aa68ffa43f7c6518733`

Pour modifier le token, éditez `config_jinka.py`:
```python
JINKA_ALERT_TOKEN = "votre_token_ici"
```

## Utilisation

### Exécution manuelle

Récupérer les nouveaux appartements une fois:
```bash
python fetch_jinka_apartments.py
```

Sans télécharger les photos:
```bash
python fetch_jinka_apartments.py --no-photos
```

Mode test (affiche les informations sans sauvegarder):
```bash
python fetch_jinka_apartments.py --test
```

### Planification quotidienne

#### Option 1: Avec cron (recommandé)

Créer une tâche cron pour exécuter le script une fois par jour à 9h00:
```bash
crontab -e
```

Ajouter la ligne:
```
0 9 * * * cd /Users/sou/Desktop/HomeScore && /usr/bin/python3 fetch_jinka_apartments.py --once
```

Ou utiliser le script wrapper:
```
0 9 * * * cd /Users/sou/Desktop/HomeScore && /usr/bin/python3 schedule_jinka_fetch.py --once
```

#### Option 2: Avec schedule Python (mode daemon)

Exécuter en mode daemon qui vérifie et exécute le script quotidiennement:
```bash
python schedule_jinka_fetch.py --daemon --time 09:00
```

#### Option 3: Avec launchd (macOS)

Créer un fichier `~/Library/LaunchAgents/com.homescore.jinka.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.homescore.jinka</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/sou/Desktop/HomeScore/fetch_jinka_apartments.py</string>
        <string>--once</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/sou/Desktop/HomeScore/logs/jinka_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/sou/Desktop/HomeScore/logs/jinka_stderr.log</string>
</dict>
</plist>
```

Charger le service:
```bash
launchctl load ~/Library/LaunchAgents/com.homescore.jinka.plist
```

## Structure des fichiers

- `config_jinka.py` - Configuration (token, chemins)
- `jinka_api.py` - Client API pour Jinka
- `jinka_scraper.py` - Extraction des données des appartements
- `photo_downloader.py` - Téléchargement des photos
- `fetch_jinka_apartments.py` - Script principal
- `schedule_jinka_fetch.py` - Script de planification

## Fichiers de données

- `data/jinka_apartments.json` - Tous les appartements Jinka récupérés
- `data/scores/all_apartments_scores.json` - Fichier principal (mis à jour avec les nouveaux)
- `data/photos/{apartment_id}/` - Photos téléchargées pour chaque appartement

## Format des données

Les appartements sont stockés au format JSON avec la structure suivante:
```json
{
  "id": "93828578",
  "titre": "Paris 11e - 39 m² - 2 pièces - 1 chambres",
  "url": "https://www.jinka.fr/alert_result?token=...&ad=93828578",
  "prix": "770 000 €",
  "surface": "39 m²",
  "localisation": "Paris 11e",
  "photos": [
    {
      "url": "https://...",
      "local_path": "data/photos/93828578/93828578_0.jpg"
    }
  ],
  "date_ajout": "2025-12-08T10:00:00",
  "source": "jinka_alert"
}
```

## Authentification avec cookies

Le système utilise des **cookies de session persistants** pour éviter de devoir se reconnecter à chaque fois :

1. **Première utilisation** : Exécutez `python save_jinka_cookies.py`
   - Le navigateur s'ouvre
   - Connectez-vous à Jinka manuellement
   - Les cookies sont sauvegardés automatiquement

2. **Utilisations suivantes** : Les cookies sont automatiquement réutilisés
   - Pas besoin de se reconnecter
   - Les cookies sont valides pendant 30 jours
   - Si les cookies expirent, le script vous demandera de les renouveler

## Notes

- Le système utilise l'API Jinka avec les cookies de session sauvegardés
- Les nouveaux appartements sont détectés par comparaison des IDs
- Les photos sont téléchargées uniquement pour les nouveaux appartements
- Le système évite les doublons automatiquement
- Les cookies sont sauvegardés dans `data/cookies/jinka_cookies.json`

