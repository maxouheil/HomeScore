# Guide : Récupération régulière des annonces manquantes

Ce guide explique comment utiliser le script `fetch_missing_from_dashboard.py` pour récupérer régulièrement les nouvelles annonces depuis votre dashboard Jinka.

## 📋 Fonctionnalités

Le script `fetch_missing_from_dashboard.py` :
- ✅ Se connecte automatiquement au dashboard Jinka
- ✅ Extrait toutes les URLs d'appartements disponibles (gère le scroll infini et les boutons "Voir plus")
- ✅ Compare avec les appartements déjà scrapés dans `data/appartements/`
- ✅ Scrape uniquement les appartements manquants
- ✅ Sauvegarde un log de chaque exécution
- ✅ Évite de scraper les appartements déjà existants

## 🚀 Utilisation

### Exécution simple

```bash
python fetch_missing_from_dashboard.py
```

Scrape tous les appartements manquants depuis le dashboard.

### Limiter le nombre d'appartements

```bash
python fetch_missing_from_dashboard.py 10
```

Scrape maximum 10 appartements manquants.

### Spécifier une URL de dashboard personnalisée

```bash
python fetch_missing_from_dashboard.py "https://www.jinka.fr/asrenter/alert/dashboard/MON_TOKEN"
```

## ⏰ Exécution régulière

### Option 1 : Cron Job (Linux/Mac)

Ajoutez cette ligne à votre crontab pour exécuter le script tous les jours à 9h00 :

```bash
crontab -e
```

Ajoutez :
```
0 9 * * * cd /Users/sou/Desktop/HomeScore && /usr/bin/python3 fetch_missing_from_dashboard.py >> logs/fetch_missing_cron.log 2>&1
```

### Option 2 : Exécution manuelle quotidienne

Lancez simplement le script chaque jour :

```bash
python fetch_missing_from_dashboard.py
```

### Option 3 : Script wrapper avec notifications

Créez un script `run_fetch_missing.sh` :

```bash
#!/bin/bash
cd /Users/sou/Desktop/HomeScore
python3 fetch_missing_from_dashboard.py

# Optionnel : envoyer une notification
# osascript -e 'display notification "Récupération terminée" with title "HomeScore"'
```

Puis exécutez-le via cron ou manuellement.

## 📊 Résultats

### Fichiers générés

- **Nouveaux appartements** : Sauvegardés dans `data/appartements/{id}.json`
- **Photos** : Téléchargées dans `data/photos/{id}/`
- **Logs** : Sauvegardés dans `data/logs/fetch_missing_{timestamp}.json`

### Format du log

Chaque exécution génère un fichier JSON avec :
```json
{
  "timestamp": "2024-01-15T09:00:00",
  "total_dashboard": 150,
  "existing": 145,
  "missing": 5,
  "scraped": 5,
  "skipped": 0,
  "errors": 0
}
```

## 🔧 Configuration

Le script utilise automatiquement :
1. L'URL du dashboard depuis `config.json` (clé `dashboard_url` ou `alert_url`)
2. Si non trouvé, utilise l'URL par défaut du dashboard

Pour personnaliser, créez/modifiez `config.json` :

```json
{
  "dashboard_url": "https://www.jinka.fr/asrenter/alert/dashboard/MON_TOKEN",
  "alert_url": "..."
}
```

## 📝 Exemple de sortie

```
🔍 RÉCUPÉRATION DES ANNONCES MANQUANTES
============================================================
⏰ Début: 2024-01-15 09:00:00

📋 PHASE 1: Analyse des appartements existants
------------------------------------------------------------
✅ 145 appartements déjà scrapés

🌐 PHASE 2: Extraction des URLs depuis le dashboard
------------------------------------------------------------
✅ Scraper initialisé
🔐 Connexion à Jinka...
✅ Connexion réussie
🌐 Navigation vers le dashboard...
✅ Accès au dashboard réussi !
📜 Chargement de tous les appartements (scroll)...
✅ Scroll terminé: 150 appartements chargés
🔍 Extraction des URLs...
✅ 150 URLs trouvées sur le dashboard

🔍 PHASE 3: Identification des appartements manquants
------------------------------------------------------------
📊 Statistiques:
   Total sur le dashboard: 150
   Déjà scrapés: 145
   Manquants: 5

🏠 PHASE 4: Scraping des appartements manquants
------------------------------------------------------------
✅ Appartement 123456 scrapé et sauvegardé
...

============================================================
📊 RÉSUMÉ FINAL
============================================================
✅ Appartements scrapés: 5
⏭️  Appartements déjà existants (skip): 0
❌ Erreurs: 0
📈 Total manquants traités: 5

🎉 Récupération terminée avec succès !
   ✅ 5 nouveaux appartements ajoutés
```

## ⚠️ Notes importantes

1. **Connexion automatique** : Le script se connecte automatiquement avec les identifiants dans `.env` (`JINKA_EMAIL` et `JINKA_PASSWORD`)

2. **Performance** : Le script peut prendre plusieurs minutes selon le nombre d'appartements manquants

3. **Pause entre requêtes** : Le script attend 1 seconde entre chaque appartement pour éviter la surcharge

4. **Gestion des erreurs** : Les erreurs sont comptabilisées mais n'arrêtent pas le processus

5. **Skip automatique** : Les appartements déjà existants sont automatiquement ignorés (pas d'écrasement)

## 🐛 Dépannage

### Problème de connexion

Vérifiez que `.env` contient :
```
JINKA_EMAIL=votre@email.com
JINKA_PASSWORD=votre_mot_de_passe
```

### Aucun appartement trouvé

- Vérifiez que vous êtes bien connecté au dashboard
- Vérifiez que l'URL du dashboard est correcte
- Le dashboard peut mettre du temps à charger, le script attend automatiquement

### Trop d'appartements manquants

Limitez le nombre avec :
```bash
python fetch_missing_from_dashboard.py 20
```

## 📞 Support

Pour toute question ou problème, consultez les autres scripts similaires :
- `extract_all_apartment_urls.py` : Extraction complète des URLs
- `scrape_from_urls.py` : Scraping depuis une liste d'URLs
- `run_daily_scrape.py` : Script de scraping quotidien complet

