// Script à copier-coller dans la console du navigateur quand tu es sur le dashboard
// Copie tout ce code et colle-le dans la console (F12 > Console)

(function() {
    console.log("🔍 EXTRACTION DES URLs D'APPARTEMENTS");
    console.log("=" .repeat(60));
    
    const urls = new Set();
    
    // Méthode 1: Chercher tous les liens avec ad=
    console.log("\n📋 Méthode 1: Liens avec ad=");
    const links = document.querySelectorAll('a[href*="ad="]');
    console.log(`   Trouvé ${links.length} liens`);
    
    links.forEach((link, i) => {
        let href = link.href || link.getAttribute('href');
        if (href) {
            if (href.startsWith('/')) {
                href = 'https://www.jinka.fr' + href;
            }
            if (href.includes('ad=') || href.includes('alert_result')) {
                urls.add(href);
                if (i < 5) {
                    console.log(`   ${i+1}. ${href}`);
                }
            }
        }
    });
    
    // Méthode 2: Chercher dans le HTML
    console.log("\n📋 Méthode 2: Regex sur le HTML");
    const html = document.documentElement.outerHTML;
    const idMatches = html.match(/ad=(\d+)/g);
    if (idMatches) {
        const uniqueIds = [...new Set(idMatches.map(m => m.match(/\d+/)[0]))];
        console.log(`   Trouvé ${uniqueIds.length} IDs uniques`);
        
        uniqueIds.forEach(id => {
            const url = `https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=${id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1`;
            urls.add(url);
        });
    }
    
    // Résultats
    const allUrls = Array.from(urls).sort();
    
    console.log("\n" + "=".repeat(60));
    console.log(`📊 TOTAL: ${allUrls.length} URLs trouvées`);
    console.log("=".repeat(60));
    
    console.log("\n📋 Liste complète:");
    allUrls.forEach((url, i) => {
        console.log(`${i+1}. ${url}`);
    });
    
    // Copier dans le presse-papier
    const jsonOutput = JSON.stringify(allUrls, null, 2);
    navigator.clipboard.writeText(jsonOutput).then(() => {
        console.log("\n✅ JSON copié dans le presse-papier!");
        console.log("   Colle-le dans un fichier apartment_urls_page1.json");
    }).catch(err => {
        console.log("\n⚠️ Impossible de copier automatiquement");
        console.log("   Copie manuellement le JSON ci-dessous:");
        console.log(jsonOutput);
    });
    
    // Afficher le JSON
    console.log("\n📄 JSON à sauvegarder:");
    console.log(jsonOutput);
    
    return allUrls;
})();









