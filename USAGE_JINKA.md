# Guide d'utilisation - Récupération automatique Jinka

## 🚀 Démarrage rapide

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Configuration initiale (une seule fois)

#### Sauvegarder vos cookies Jinka
```bash
python save_jinka_cookies.py
```

**Ce que fait ce script :**
1. Ouvre un navigateur Chrome
2. Va sur le dashboard Jinka
3. **Vous vous connectez manuellement** (Gmail, email, etc.)
4. Une fois connecté, appuyez sur Entrée dans le terminal
5. Les cookies sont sauvegardés automatiquement

**Important :** Vous n'aurez plus besoin de vous reconnecter ensuite ! Les cookies sont réutilisés automatiquement.

### 3. Utilisation quotidienne

#### Récupérer les nouveaux appartements
```bash
python fetch_jinka_apartments.py
```

#### Mode test (sans sauvegarder)
```bash
python fetch_jinka_apartments.py --test
```

#### Sans télécharger les photos
```bash
python fetch_jinka_apartments.py --no-photos
```

## 📋 Planification automatique

### Option 1 : Cron (recommandé)
```bash
crontab -e
```

Ajouter :
```
0 9 * * * cd /Users/sou/Desktop/HomeScore && /usr/bin/python3 fetch_jinka_apartments.py
```

### Option 2 : Script de planification Python
```bash
python schedule_jinka_fetch.py --daemon --time 09:00
```

## 🔧 Dépannage

### Les cookies ont expiré
Si vous voyez un message indiquant que les cookies sont expirés :
```bash
python save_jinka_cookies.py
```
Réconnectez-vous et les nouveaux cookies seront sauvegardés.

### Aucun appartement trouvé
1. Vérifiez que vous êtes bien connecté : `python save_jinka_cookies.py`
2. Vérifiez que votre alerte Jinka a bien des résultats
3. Testez en mode debug : `python fetch_jinka_apartments.py --test`

### Supprimer les cookies sauvegardés
```python
from cookie_manager import CookieManager
manager = CookieManager()
manager.clear_cookies()
```

## 📁 Fichiers créés

- `data/cookies/jinka_cookies.json` - Cookies de session sauvegardés
- `data/jinka_apartments.json` - Tous les appartements récupérés
- `data/photos/{apartment_id}/` - Photos téléchargées
- `data/scores/all_apartments_scores.json` - Fichier principal (mis à jour)

## 💡 Astuces

- Les cookies sont valides pendant ~30 jours
- Vous pouvez avoir plusieurs alertes Jinka, le système récupère toutes les alertes
- Les photos sont téléchargées uniquement pour les nouveaux appartements
- Le système détecte automatiquement les doublons par ID

