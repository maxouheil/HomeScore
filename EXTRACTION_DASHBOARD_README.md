# Guide : Extraction de toutes les URLs depuis le dashboard

## Vue d'ensemble

Le script JavaScript `extract_all_urls_dashboard.js` permet d'extraire **TOUTES** les URLs d'appartements depuis le dashboard Jinka, en gérant le scroll infini et les boutons "Voir plus".

## Utilisation

### Méthode recommandée

1. **Ouvre le dashboard** dans ton navigateur :
   ```
   https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733
   ```

2. **Ouvre la console** du navigateur :
   - Chrome/Edge : `F12` ou `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - Safari : `Cmd+Option+C` (Mac)

3. **Copie-colle** tout le contenu du fichier `extract_all_urls_dashboard.js` dans la console

4. **Appuie sur Entrée**

5. Le script va automatiquement :
   - Scroller progressivement pour charger tous les appartements
   - Cliquer sur "Voir plus" s'il existe
   - Extraire toutes les URLs
   - Les copier dans le presse-papier au format JSON

6. **Sauvegarde** le JSON dans `data/all_apartment_urls_dashboard.json`

## Fonctionnalités

- ✅ **Scroll infini** : Scroll progressif pour charger tous les appartements (lazy loading)
- ✅ **Bouton "Voir plus"** : Détection et clic automatique
- ✅ **Déduplication** : Évite les doublons
- ✅ **Extraction robuste** : Plusieurs méthodes pour trouver les IDs
- ✅ **Copie automatique** : JSON copié dans le presse-papier

## Résultat

Le script génère un fichier JSON avec toutes les URLs :

```json
[
  "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=75507606&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
  "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=75578302&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
  ...
]
```

## Comparaison avec la version simple

| Fonctionnalité | Version simple | Version complète |
|----------------|----------------|------------------|
| Page 1 seulement | ✅ | ❌ |
| Scroll infini | ❌ | ✅ |
| Bouton "Voir plus" | ❌ | ✅ |
| Toutes les pages | ❌ | ✅ |

## Dépannage

### Le script ne trouve pas tous les appartements
- Attends que le scroll soit terminé (peut prendre 1-2 minutes)
- Vérifie qu'il n'y a pas d'erreurs dans la console
- Essaie de scroller manuellement puis relance l'extraction

### Le script ne détecte pas le bouton "Voir plus"
- C'est normal si le dashboard utilise le scroll infini
- Le script fonctionnera quand même avec le scroll

### Erreur "Tu n'es pas sur le dashboard"
- Assure-toi d'être sur la bonne URL du dashboard
- Recharge la page et réessaie

## Prochaines étapes

Une fois les URLs extraites :

1. Sauvegarde dans `data/all_apartment_urls_dashboard.json`
2. Lance `python merge_all_urls.py` pour fusionner avec d'autres sources
3. Lance `python scrape_from_urls.py` pour scraper les appartements






