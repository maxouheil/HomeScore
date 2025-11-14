# Guide : Récupération des Nouveaux Appartements Jinka

## 📋 Vue d'ensemble

Ce document décrit la méthode qui fonctionne pour récupérer et scraper les nouveaux appartements depuis le dashboard Jinka, en évitant les problèmes de connexion et de détection des liens.

## 🎯 Problèmes résolus

### 1. **Problème de connexion automatique**
- **Avant** : Le script essayait de se connecter automatiquement avec les identifiants depuis `.env`, mais échouait souvent
- **Problème** : La connexion automatique ne fonctionnait pas de manière fiable, surtout avec l'authentification Google/2FA
- **Solution** : Passage à une connexion **100% manuelle** avec détection automatique de la connexion

### 2. **Rafraîchissement continu de la page**
- **Avant** : Le script rafraîchissait la page en boucle pour vérifier la connexion, empêchant l'utilisateur de se connecter
- **Problème** : `page.goto()` était appelé dans une boucle, ce qui relançait la page de cookies à chaque fois
- **Solution** : Vérification de l'URL **SANS navigation** pendant l'attente de connexion

### 3. **Page de cookies qui s'ouvre en boucle**
- **Avant** : Navigation répétée vers le dashboard déclenchait les popups de cookies
- **Problème** : `page.goto(dashboard_url)` était appelé plusieurs fois
- **Solution** : Navigation vers le dashboard **UNE SEULE FOIS** après détection de la connexion, avec fermeture automatique des popups

## 🔧 Changements techniques principaux

### Méthode de connexion

#### **AVANT** (ne fonctionnait pas)
```python
# Tentative de connexion automatique
login_success = await scraper.login()

# Vérification en naviguant vers le dashboard
await scraper.page.goto(dashboard_url)  # ❌ Déclenche les cookies
if "sign/in" in current_url:
    # Boucle qui rafraîchit la page...
    while True:
        await scraper.page.goto(dashboard_url)  # ❌ Rafraîchit en boucle
        current_url = scraper.page.url
        # ...
```

#### **APRÈS** (fonctionne)
```python
# 1. Aller directement à la page de login
await scraper.page.goto('https://www.jinka.fr/sign/in')
await scraper.page.wait_for_load_state('networkidle')

# 2. Cliquer sur Google pour faciliter (optionnel)
google_button = scraper.page.locator('button:has-text("Continuer avec Google")').first
if await google_button.count() > 0:
    await google_button.click()

# 3. Attendre la connexion SANS rafraîchir
while wait_time < max_wait:
    # ✅ Vérifier l'URL SANS changer de page
    current_url = scraper.page.url  # Pas de page.goto() !
    
    if "jinka.fr" in current_url and "sign/in" not in current_url:
        login_success = True
        break
    
    await asyncio.sleep(2)  # Attendre 2 secondes

# 4. Aller au dashboard UNE SEULE FOIS après connexion
await scraper.page.goto(dashboard_url)
# Fermer les popups de cookies
```

### Points clés de la solution

1. **Pas de navigation pendant l'attente**
   - Utiliser `page.url` pour vérifier l'URL actuelle
   - Ne JAMAIS appeler `page.goto()` dans la boucle d'attente
   - Laisser l'utilisateur compléter sa connexion tranquillement

2. **Navigation unique vers le dashboard**
   - Aller au dashboard **UNE SEULE FOIS** après détection de la connexion
   - Éviter les multiples navigations qui déclenchent les popups

3. **Fermeture automatique des popups de cookies**
   - Après la navigation unique, chercher et fermer les popups de cookies
   - Utiliser plusieurs sélecteurs pour être robuste :
     ```python
     cookie_selectors = [
         'button:has-text("Accepter")',
         'button:has-text("Accept")',
         '[id*="cookie"] button',
         '[class*="cookie"] button',
         '.cookie-consent button',
         '#cookieConsent button'
     ]
     ```

4. **Détection de connexion robuste**
   - Vérifier que l'URL contient `jinka.fr`
   - Vérifier que l'URL ne contient PAS `sign/in`
   - Vérifier que l'URL ne contient PAS `accounts.google.com` (on n'est plus sur Google)

## 📝 Fonctionnement du script complet

### Étape 1 : Initialisation
```python
scraper = JinkaScraper()
await scraper.setup()  # Ouvre Chrome en mode visible
```

### Étape 2 : Page de login
```python
await scraper.page.goto('https://www.jinka.fr/sign/in')
# Clique sur "Continuer avec Google" pour faciliter
```

### Étape 3 : Attente de connexion manuelle
```python
# Boucle qui vérifie l'URL SANS rafraîchir
while wait_time < max_wait:
    current_url = scraper.page.url  # ✅ Pas de navigation
    if est_connecte(current_url):
        break
    await asyncio.sleep(2)
```

### Étape 4 : Navigation vers le dashboard
```python
# UNE SEULE FOIS après connexion détectée
await scraper.page.goto(dashboard_url)
# Fermer les popups de cookies
```

### Étape 5 : Extraction des URLs
```python
# Scroll pour charger tous les appartements (lazy loading)
await scroll_to_load_all_apartments(scraper.page)

# Cliquer sur "Voir plus" si disponible
await click_load_more_until_done(scraper.page)

# Extraire toutes les URLs
all_urls = await extract_urls_from_page(scraper.page)
```

### Étape 6 : Filtrage des nouveaux appartements
```python
# Charger les IDs déjà scrapés
existing_ids = load_existing_apartment_ids()

# Filtrer pour ne garder que les nouveaux
new_urls = filter_new_apartments(all_urls, existing_ids)
```

### Étape 7 : Scraping des nouveaux appartements
```python
for url in new_urls:
    apartment_data = await scraper.scrape_apartment(url)
    # Sauvegarde automatique dans data/appartements/
```

## 🔍 Méthode d'extraction des URLs

La fonction `extract_urls_from_page()` utilise **3 méthodes combinées** pour être robuste :

### Méthode 1 : Sélecteurs Playwright
```python
links = page.locator('a[href*="alert_result"][href*="ad="], a[href*="ad="]')
count = await links.count()
for i in range(count):
    href = await links.nth(i).get_attribute('href')
    # Construire l'URL complète si nécessaire
```

### Méthode 2 : Regex sur le HTML
```python
page_content = await page.content()
url_patterns = [
    r'href="(/alert_result\?token=[^&]+&ad=\d+[^"]*)"',
    r'href="(https://www\.jinka\.fr/alert_result\?token=[^&]+&ad=\d+[^"]*)"',
    r'ad=(\d+)',
]
```

### Méthode 3 : JavaScript injection
```javascript
const links = Array.from(document.querySelectorAll('a[href*="ad="]'));
return links.map(link => {
    let href = link.href || link.getAttribute('href');
    if (href && !href.startsWith('http') && href.startsWith('/')) {
        href = 'https://www.jinka.fr' + href;
    }
    return href;
}).filter(href => href && href.includes('alert_result') && href.includes('ad='));
```

## ✅ Checklist pour que ça fonctionne

- [x] Connexion 100% manuelle (pas d'authentification automatique)
- [x] Pas de `page.goto()` dans la boucle d'attente
- [x] Navigation vers le dashboard UNE SEULE FOIS après connexion
- [x] Fermeture automatique des popups de cookies
- [x] Scroll infini pour charger tous les appartements
- [x] Cliquer sur "Voir plus" si disponible
- [x] Extraction des URLs avec 3 méthodes combinées
- [x] Filtrage pour ne scraper que les nouveaux appartements

## 🚀 Utilisation

```bash
python scrape_new_apartments.py
```

Le script va :
1. Ouvrir Chrome
2. Aller à la page de login Jinka
3. Cliquer sur "Continuer avec Google"
4. **Attendre que tu te connectes manuellement** (sans rafraîchir)
5. Détecter automatiquement la connexion
6. Aller au dashboard une seule fois
7. Fermer les popups de cookies
8. Extraire tous les nouveaux appartements
9. Les scraper automatiquement

## 📊 Résultats

Les nouveaux appartements sont sauvegardés dans :
- `data/appartements/{id}.json` - Données complètes de l'appartement
- `data/photos/{id}/` - Photos téléchargées localement

## 🔄 Comparaison avec l'ancienne méthode

| Aspect | Ancienne méthode | Nouvelle méthode |
|--------|------------------|------------------|
| Connexion | Automatique (échouait souvent) | Manuelle (100% fiable) |
| Rafraîchissement | En boucle (bloquait la connexion) | Aucun (attente passive) |
| Navigation dashboard | Plusieurs fois (popups cookies) | Une seule fois |
| Popups cookies | Non gérées | Fermeture automatique |
| Extraction URLs | 1 méthode | 3 méthodes combinées |
| Détection connexion | Tentative de navigation | Vérification URL sans navigation |

## 💡 Leçons apprises

1. **Ne jamais rafraîchir pendant une action utilisateur** : Si l'utilisateur doit faire quelque chose manuellement, ne pas interférer avec la page

2. **Une seule navigation après connexion** : Éviter les multiples navigations qui déclenchent des popups

3. **Vérification passive de l'URL** : Utiliser `page.url` au lieu de `page.goto()` pour vérifier l'état

4. **Gestion des popups** : Toujours prévoir de fermer les popups après une navigation

5. **Méthodes multiples pour extraction** : Combiner plusieurs méthodes (sélecteurs, regex, JS) pour être robuste

## 📅 Date de création

2024-11-01 - Documentation des changements qui ont permis au scraping de fonctionner correctement






