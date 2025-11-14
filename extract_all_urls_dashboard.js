// Script JavaScript amélioré pour extraire TOUTES les URLs depuis le dashboard
// Gère le scroll infini et la pagination pour récupérer tous les appartements
// Copie-colle ce code dans la console du navigateur quand tu es sur le dashboard

(function() {
    console.log("🔍 EXTRACTION DE TOUTES LES URLs DU DASHBOARD");
    console.log("=" .repeat(60));
    
    const urls = new Set();
    const JINKA_TOKEN = "26c2ec3064303aa68ffa43f7c6518733";
    
    // Fonction pour construire une URL complète
    function buildUrl(aptId) {
        return `https://www.jinka.fr/alert_result?token=${JINKA_TOKEN}&ad=${aptId}&from=dashboard_card&from_alert_filter=all&from_alert_page=1`;
    }
    
    // Fonction pour extraire les IDs depuis la page actuelle
    function extractIdsFromPage() {
        const ids = new Set();
        
        // Méthode 1: Chercher tous les liens avec ad=
        const links = document.querySelectorAll('a[href*="ad="]');
        links.forEach(link => {
            const href = link.href || link.getAttribute('href');
            if (href) {
                const match = href.match(/ad=(\d+)/);
                if (match) {
                    ids.add(match[1]);
                }
            }
        });
        
        // Méthode 2: Chercher dans le HTML
        const html = document.documentElement.outerHTML;
        const idMatches = html.match(/ad=(\d{6,})/g);
        if (idMatches) {
            idMatches.forEach(match => {
                const id = match.match(/\d+/)[0];
                ids.add(id);
            });
        }
        
        return ids;
    }
    
    // Fonction pour scroller progressivement
    async function scrollToLoadAll() {
        console.log("\n📜 Début du scroll pour charger tous les appartements...");
        
        let lastCount = 0;
        let stableCount = 0;
        const maxStable = 3; // Si le nombre ne change pas 3 fois, on arrête
        let scrollCount = 0;
        const maxScrolls = 50;
        
        while (scrollCount < maxScrolls && stableCount < maxStable) {
            // Compter avant le scroll
            const beforeIds = extractIdsFromPage();
            const beforeCount = beforeIds.size;
            
            // Scroller vers le bas
            window.scrollTo(0, document.body.scrollHeight);
            
            // Attendre le chargement lazy
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Petit scroll supplémentaire pour déclencher le chargement
            window.scrollBy(0, -100);
            await new Promise(resolve => setTimeout(resolve, 500));
            window.scrollTo(0, document.body.scrollHeight);
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Compter après le scroll
            const afterIds = extractIdsFromPage();
            const afterCount = afterIds.size;
            
            scrollCount++;
            
            if (afterCount === beforeCount) {
                stableCount++;
                console.log(`   ⏸️  Scroll ${scrollCount}: ${afterCount} appartements (stable ${stableCount}/${maxStable})`);
            } else {
                stableCount = 0;
                console.log(`   📊 Scroll ${scrollCount}: ${beforeCount} → ${afterCount} appartements (+${afterCount - beforeCount})`);
            }
            
            lastCount = afterCount;
            
            // Sécurité: limite max
            if (afterCount > 500) {
                console.log(`   🛑 Limite de sécurité atteinte (${afterCount} appartements)`);
                break;
            }
        }
        
        console.log(`   ✅ Scroll terminé: ${lastCount} appartements chargés après ${scrollCount} scrolls`);
        return lastCount;
    }
    
    // Fonction pour cliquer sur "Voir plus" si présent
    async function clickLoadMore() {
        console.log("\n🔘 Recherche de bouton 'Voir plus'...");
        
        const loadMoreSelectors = [
            'button:has-text("Voir plus")',
            'button:has-text("Charger plus")',
            'button:has-text("Load more")',
            'a:has-text("Voir plus")',
            '[data-testid="load-more"]',
            '.load-more',
            'button[class*="load"]',
            'button[class*="more"]'
        ];
        
        let clickCount = 0;
        const maxClicks = 100;
        
        while (clickCount < maxClicks) {
            let buttonFound = false;
            
            for (const selector of loadMoreSelectors) {
                try {
                    const button = document.querySelector(selector);
                    if (button && button.offsetParent !== null) { // Vérifier si visible
                        const beforeCount = extractIdsFromPage().size;
                        button.click();
                        await new Promise(resolve => setTimeout(resolve, 3000));
                        const afterCount = extractIdsFromPage().size;
                        
                        clickCount++;
                        buttonFound = true;
                        console.log(`   🔘 Clic ${clickCount}: ${beforeCount} → ${afterCount} appartements (+${afterCount - beforeCount})`);
                        break;
                    }
                } catch (e) {
                    continue;
                }
            }
            
            if (!buttonFound) {
                console.log(`   ✅ Plus de bouton 'Voir plus' trouvé après ${clickCount} clics`);
                break;
            }
        }
        
        return clickCount;
    }
    
    // Fonction principale
    async function extractAll() {
        console.log("\n📍 URL actuelle:", window.location.href);
        
        // Vérifier qu'on est sur le dashboard
        if (!window.location.href.includes('dashboard')) {
            console.log("⚠️  Tu n'es pas sur le dashboard!");
            console.log("   Va sur: https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733");
            return;
        }
        
        // Étape 1: Scroll infini
        await scrollToLoadAll();
        
        // Étape 2: Bouton "Voir plus"
        await clickLoadMore();
        
        // Étape 3: Attendre un peu pour le chargement final
        console.log("\n⏳ Attente du chargement final...");
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Étape 4: Extraire toutes les URLs
        console.log("\n🔍 Extraction finale des URLs...");
        const allIds = extractIdsFromPage();
        
        allIds.forEach(id => {
            urls.add(buildUrl(id));
        });
    
        // Résultats
        const allUrls = Array.from(urls).sort();
        
        console.log("\n" + "=".repeat(60));
        console.log(`📊 TOTAL: ${allUrls.length} URLs trouvées`);
        console.log("=".repeat(60));
        
        console.log("\n📋 Liste complète:");
        allUrls.forEach((url, i) => {
            const id = url.match(/ad=(\d+)/)[1];
            console.log(`${i+1}. ID: ${id} - ${url}`);
        });
        
        // Copier dans le presse-papier
        const jsonOutput = JSON.stringify(allUrls, null, 2);
        navigator.clipboard.writeText(jsonOutput).then(() => {
            console.log("\n✅ JSON copié dans le presse-papier!");
            console.log("   Colle-le dans un fichier all_apartment_urls_dashboard.json");
        }).catch(err => {
            console.log("\n⚠️ Impossible de copier automatiquement");
            console.log("   Copie manuellement le JSON ci-dessous:");
        });
        
        // Afficher le JSON
        console.log("\n📄 JSON à sauvegarder:");
        console.log(jsonOutput);
        
        return allUrls;
    }
    
    // Lancer l'extraction
    return extractAll();
})();






