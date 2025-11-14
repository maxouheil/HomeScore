# Plan pour récupérer toutes les URLs d'appartements depuis l'alerte Jinka

## 🎯 Objectif
Récupérer **toutes** les URLs d'appartements de l'alerte Jinka (pas seulement les 17 premiers visibles).

## 📋 Stratégies possibles

### Option 1: Scroll infini (Lazy Loading) ⭐ RECOMMANDÉE
Le dashboard Jinka charge probablement les appartements au fur et à mesure du scroll (lazy loading).

**Étapes:**
1. Se connecter à Jinka
2. Aller au dashboard de l'alerte
3. Scroller progressivement jusqu'en bas de la page
4. Attendre le chargement des nouveaux appartements
5. Répéter jusqu'à ce qu'il n'y ait plus de nouveaux appartements
6. Extraire toutes les URLs une fois tout chargé

**Avantages:**
- Simple à implémenter
- Fonctionne avec la plupart des sites modernes
- Pas besoin de gérer la pagination

**Code à implémenter:**
```python
async def scroll_to_load_all_apartments(page):
    """Scroll progressivement pour charger tous les appartements"""
    last_count = 0
    stable_count = 0
    max_stable = 3  # Si le nombre ne change pas 3 fois, on arrête
    
    while stable_count < max_stable:
        # Scroller progressivement
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)  # Attendre le chargement
        
        # Compter les appartements actuels
        current_count = await page.locator('a[href*="ad="]').count()
        
        if current_count == last_count:
            stable_count += 1
        else:
            stable_count = 0
            print(f"   📊 {current_count} appartements chargés...")
        
        last_count = current_count
        
        # Sécurité: limite max (ex: 500 appartements)
        if current_count > 500:
            break
    
    return last_count
```

---

### Option 2: Pagination par paramètre URL
Si Jinka utilise des pages avec paramètre `?page=2`, `?page=3`, etc.

**Étapes:**
1. Essayer d'accéder à `dashboard_url?page=1`, `?page=2`, etc.
2. Pour chaque page, extraire les URLs
3. Arrêter quand une page est vide

**Code à implémenter:**
```python
async def extract_urls_from_all_pages(scraper, dashboard_url):
    """Extrait les URLs de toutes les pages"""
    all_urls = []
    page = 1
    
    while True:
        # Construire l'URL de la page
        if '?' in dashboard_url:
            page_url = f"{dashboard_url}&page={page}"
        else:
            page_url = f"{dashboard_url}?page={page}"
        
        await scraper.page.goto(page_url)
        await scraper.page.wait_for_timeout(3000)
        
        # Extraire les URLs de cette page
        page_urls = await extract_urls_from_page(scraper.page)
        
        if not page_urls:
            break  # Plus d'appartements
        
        all_urls.extend(page_urls)
        print(f"   Page {page}: {len(page_urls)} appartements")
        
        page += 1
        
        # Sécurité: limite max de pages
        if page > 50:
            break
    
    return all_urls
```

---

### Option 3: Bouton "Voir plus" / "Charger plus"
Si Jinka a un bouton pour charger plus d'appartements.

**Étapes:**
1. Chercher le bouton "Voir plus", "Charger plus", "Load more", etc.
2. Cliquer dessus jusqu'à ce qu'il disparaisse
3. Extraire toutes les URLs

**Code à implémenter:**
```python
async def click_load_more_until_done(page):
    """Clique sur 'Voir plus' jusqu'à ce qu'il n'y en ait plus"""
    max_clicks = 100
    click_count = 0
    
    while click_count < max_clicks:
        # Chercher le bouton
        load_more_selectors = [
            'button:has-text("Voir plus")',
            'button:has-text("Charger plus")',
            'button:has-text("Load more")',
            'a:has-text("Voir plus")',
            '[data-testid="load-more"]',
            '.load-more',
            'button[class*="load"]'
        ]
        
        button_found = False
        for selector in load_more_selectors:
            button = page.locator(selector).first
            if await button.count() > 0:
                # Vérifier si visible
                is_visible = await button.is_visible()
                if is_visible:
                    await button.click()
                    await asyncio.sleep(2)
                    click_count += 1
                    button_found = True
                    print(f"   🔘 Clic {click_count} sur 'Voir plus'")
                    break
        
        if not button_found:
            break  # Plus de bouton
    
    return click_count
```

---

## 🛠️ Implémentation recommandée

### Nouveau script: `extract_all_apartment_urls.py`

**Fonctionnalités:**
1. **Méthode hybride** : Combine scroll + recherche de bouton + pagination
2. **Extraction robuste** : Plusieurs méthodes pour trouver les URLs
3. **Sauvegarde** : Sauvegarde toutes les URLs dans `data/all_apartment_urls.json`
4. **Rapport** : Affiche le nombre total d'appartements trouvés

**Structure:**
```python
async def extract_all_apartment_urls():
    """
    Extrait TOUTES les URLs d'appartements depuis le dashboard Jinka
    """
    # 1. Setup + Login
    # 2. Aller au dashboard
    # 3. Essayer scroll infini
    # 4. Essayer bouton "Voir plus"
    # 5. Essayer pagination
    # 6. Extraire toutes les URLs (dédupliquer)
    # 7. Sauvegarder dans JSON
    # 8. Retourner la liste
```

---

## 📝 Checklist d'implémentation

- [ ] Créer `extract_all_apartment_urls.py`
- [ ] Implémenter la méthode de scroll infini
- [ ] Implémenter la détection de bouton "Voir plus"
- [ ] Implémenter la pagination par URL
- [ ] Ajouter la déduplication des URLs
- [ ] Sauvegarder dans `data/all_apartment_urls.json`
- [ ] Ajouter des logs détaillés
- [ ] Gérer les erreurs et timeouts
- [ ] Tester avec l'alerte réelle

---

## 🔍 Méthodes d'extraction des URLs

### Méthode 1: Regex sur le HTML
```python
import re
page_content = await page.content()
url_pattern = r'href="(/alert_result\?token=[^&]+&ad=\d+[^"]*)"'
urls = re.findall(url_pattern, page_content)
```

### Méthode 2: Sélecteurs Playwright
```python
links = page.locator('a[href*="alert_result"][href*="ad="]')
count = await links.count()
urls = []
for i in range(count):
    href = await links.nth(i).get_attribute('href')
    if href:
        urls.append(href)
```

### Méthode 3: JavaScript injection
```python
urls = await page.evaluate('''
    () => {
        const links = Array.from(document.querySelectorAll('a[href*="ad="]'));
        return links.map(link => link.href).filter(href => href.includes('alert_result'));
    }
''')
```

---

## 🎯 Résultat attendu

Un fichier `data/all_apartment_urls.json` contenant toutes les URLs:
```json
[
  "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90129925&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
  "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=78267327&from=dashboard_card&from_alert_filter=all&from_alert_page=1",
  ...
]
```

---

## 🚀 Prochaines étapes

1. **Créer le script** `extract_all_apartment_urls.py`
2. **Tester** avec ton alerte Jinka
3. **Vérifier** le nombre d'appartements trouvés
4. **Utiliser** ces URLs pour le scraping complet

---

## ⚠️ Notes importantes

- **Rate limiting** : Ajouter des pauses entre les actions pour éviter de surcharger le serveur
- **Timeouts** : Configurer des timeouts appropriés pour le chargement
- **Déduplication** : Toujours dédupliquer les URLs avant de sauvegarder
- **Erreurs** : Gérer les cas où le chargement échoue ou prend trop de temps






