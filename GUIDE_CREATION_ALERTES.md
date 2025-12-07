# Guide : Création des Alertes Jinka pour Scraping Paris Complet

## Objectif

Créer 10 alertes Jinka couvrant tous les arrondissements de Paris pour pouvoir scraper tous les appartements disponibles.

## Étapes de Création

### 1. Aller sur Jinka

1. Connectez-vous sur https://www.jinka.fr
2. Allez dans "Mes alertes" ou "Créer une alerte"

### 2. Créer les 10 Alertes

Pour chaque alerte, utilisez ces critères :

#### Alerte 1 : Paris 1e-2e (Centre)
- **Localisation** : Paris 1e, Paris 2e
- **Prix** : 0€ - 2,000,000€ (large pour tout capturer)
- **Surface** : 0m² - 200m² (large)
- **Type** : Appartement
- **Note** : Token après création

#### Alerte 2 : Paris 3e-4e (Marais)
- **Localisation** : Paris 3e, Paris 4e
- **Prix** : 0€ - 2,000,000€
- **Surface** : 0m² - 200m²
- **Type** : Appartement

#### Alerte 3 : Paris 5e-6e (Latin)
- **Localisation** : Paris 5e, Paris 6e
- **Prix** : 0€ - 2,000,000€
- **Surface** : 0m² - 200m²
- **Type** : Appartement

#### Alerte 4 : Paris 7e-8e (Champs-Élysées)
- **Localisation** : Paris 7e, Paris 8e
- **Prix** : 0€ - 2,000,000€
- **Surface** : 0m² - 200m²
- **Type** : Appartement

#### Alerte 5 : Paris 9e-10e (Opéra)
- **Localisation** : Paris 9e, Paris 10e
- **Prix** : 0€ - 2,000,000€
- **Surface** : 0m² - 200m²
- **Type** : Appartement

#### Alerte 6 : Paris 11e-12e (Bastille)
- **Localisation** : Paris 11e, Paris 12e
- **Prix** : 0€ - 2,000,000€
- **Surface** : 0m² - 200m²
- **Type** : Appartement

#### Alerte 7 : Paris 13e-14e (Montparnasse)
- **Localisation** : Paris 13e, Paris 14e
- **Prix** : 0€ - 2,000,000€
- **Surface** : 0m² - 200m²
- **Type** : Appartement

#### Alerte 8 : Paris 15e-16e (Auteuil)
- **Localisation** : Paris 15e, Paris 16e
- **Prix** : 0€ - 2,000,000€
- **Surface** : 0m² - 200m²
- **Type** : Appartement

#### Alerte 9 : Paris 17e-18e (Montmartre)
- **Localisation** : Paris 17e, Paris 18e
- **Prix** : 0€ - 2,000,000€
- **Surface** : 0m² - 200m²
- **Type** : Appartement

#### Alerte 10 : Paris 19e-20e (Belleville)
- **Localisation** : Paris 19e, Paris 20e
- **Prix** : 0€ - 2,000,000€
- **Surface** : 0m² - 200m²
- **Type** : Appartement

### 3. Récupérer les Tokens

Pour chaque alerte créée :

1. Allez sur la page de l'alerte (dashboard)
2. L'URL ressemble à : `https://www.jinka.fr/asrenter/alert/dashboard/TOKEN_ICI`
3. Le **TOKEN** est la chaîne de 32 caractères après `/dashboard/`
4. Notez chaque token dans un fichier ou directement dans le script

**Exemple** :
- URL : `https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733`
- Token : `26c2ec3064303aa68ffa43f7c6518733`

### 4. Format pour le Script

Une fois tous les tokens récupérés, créez un fichier `data/alert_tokens.json` :

```json
{
  "paris_alerts": [
    {
      "name": "Paris 1e-2e",
      "token": "TOKEN_ICI_1"
    },
    {
      "name": "Paris 3e-4e",
      "token": "TOKEN_ICI_2"
    },
    {
      "name": "Paris 5e-6e",
      "token": "TOKEN_ICI_3"
    },
    {
      "name": "Paris 7e-8e",
      "token": "TOKEN_ICI_4"
    },
    {
      "name": "Paris 9e-10e",
      "token": "TOKEN_ICI_5"
    },
    {
      "name": "Paris 11e-12e",
      "token": "TOKEN_ICI_6"
    },
    {
      "name": "Paris 13e-14e",
      "token": "TOKEN_ICI_7"
    },
    {
      "name": "Paris 15e-16e",
      "token": "TOKEN_ICI_8"
    },
    {
      "name": "Paris 17e-18e",
      "token": "TOKEN_ICI_9"
    },
    {
      "name": "Paris 19e-20e",
      "token": "TOKEN_ICI_10"
    }
  ]
}
```

**OU** directement dans le script Python (je vais modifier le script pour accepter une liste).

## Temps Estimé

- Création d'une alerte : ~2-3 minutes
- Total pour 10 alertes : **20-30 minutes**

## Astuce

Si Jinka permet de créer une alerte "Paris" globale (tous arrondissements), c'est encore plus rapide ! Vérifiez si c'est possible.

## Après Création

Une fois les tokens récupérés, je modifierai le script pour :
1. Charger tous les tokens depuis un fichier ou directement dans le code
2. Scraper chaque alerte automatiquement
3. Fusionner tous les résultats
4. Filtrer les doublons
5. Sauvegarder dans `data/paris_apartments.json`



