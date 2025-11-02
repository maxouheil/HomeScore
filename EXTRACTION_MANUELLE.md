# Extraction manuelle des URLs

Comme le script automatique rencontre des erreurs 403, voici comment extraire les URLs manuellement :

## Méthode rapide (recommandée)

1. **Ouvre le dashboard** dans ton navigateur : https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733

2. **Ouvre la console** du navigateur :
   - Chrome/Edge : `F12` ou `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - Safari : `Cmd+Option+C` (Mac)

3. **Copie-colle** le contenu du fichier `extract_urls_console.js` dans la console

4. **Appuie sur Entrée**

5. Les URLs seront affichées dans la console et copiées dans le presse-papier

6. **Sauvegarde** le JSON dans `data/apartment_urls_page1.json`

## Alternative : Extraction manuelle simple

Si la console ne fonctionne pas, tu peux aussi :

1. Sur le dashboard, fais un clic droit > "Inspecter"
2. Dans l'onglet Elements, cherche tous les liens avec `href` contenant `ad=`
3. Note les URLs manuellement

Le script JavaScript devrait automatiquement trouver toutes les URLs et les formater en JSON.

