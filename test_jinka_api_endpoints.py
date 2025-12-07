#!/usr/bin/env python3
"""
Script pour tester les endpoints API Jinka et capturer les vraies structures JSON
"""

import json
import asyncio
import aiohttp
from pathlib import Path

# Charger les cookies depuis l'exploration
def load_cookies():
    """Charge les cookies depuis la dernière exploration"""
    exploration_dir = Path('data/api_exploration')
    
    # Trouver le dernier fichier de cookies
    cookie_files = list(exploration_dir.glob('cookies_*.json'))
    if not cookie_files:
        print("❌ Aucun fichier de cookies trouvé")
        return None
    
    latest = max(cookie_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Chargement des cookies depuis: {latest}")
    
    with open(latest, 'r') as f:
        cookies = json.load(f)
    
    return cookies

def get_api_token(cookies):
    """Extrait le token API depuis les cookies"""
    for cookie in cookies:
        if cookie['name'] == 'LA_API_TOKEN':
            return cookie['value']
    return None

async def test_endpoint(session, url, headers, name):
    """Teste un endpoint et retourne la réponse JSON"""
    print(f"\n🔍 Test de {name}")
    print(f"   URL: {url}")
    
    try:
        async with session.get(url, headers=headers) as response:
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    data = await response.json()
                    print(f"   ✅ JSON reçu ({len(str(data))} caractères)")
                    return {
                        'endpoint': name,
                        'url': url,
                        'status': response.status,
                        'data': data
                    }
                else:
                    text = await response.text()
                    print(f"   ⚠️  Réponse non-JSON: {content_type}")
                    print(f"   Preview: {text[:200]}")
            else:
                text = await response.text()
                print(f"   ❌ Erreur {response.status}")
                print(f"   Réponse: {text[:200]}")
                
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return None

async def main():
    """Fonction principale"""
    print("🚀 TEST DES ENDPOINTS API JINKA")
    print("="*60)
    
    # Charger les cookies
    cookies = load_cookies()
    if not cookies:
        return
    
    # Extraire le token API
    api_token = get_api_token(cookies)
    if not api_token:
        print("❌ Token API non trouvé dans les cookies")
        return
    
    print(f"✅ Token API trouvé: {api_token[:50]}...")
    
    # Créer les headers avec le token dans Authorization ET dans les cookies
    cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
    
    headers = {
        'Cookie': cookie_str,
        'Authorization': f'Bearer {api_token}',  # Token dans le header Authorization
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Origin': 'https://www.jinka.fr',
        'Referer': 'https://www.jinka.fr/',
        'Accept': 'application/json',
    }
    
    # Token d'alerte connu
    alert_token = "26c2ec3064303aa68ffa43f7c6518733"
    
    # Endpoints à tester
    endpoints = [
        {
            'name': 'Config',
            'url': 'https://api.jinka.fr/apiv2/config'
        },
        {
            'name': 'User Authenticated',
            'url': 'https://api.jinka.fr/apiv2/user/authenticated'
        },
        {
            'name': 'Alert List',
            'url': 'https://api.jinka.fr/apiv2/alert'
        },
        {
            'name': 'Alert Dashboard',
            'url': f'https://api.jinka.fr/apiv2/alert/{alert_token}/dashboard?filter=all&page=1&rrkey='
        },
        {
            'name': 'Property Details',
            'url': f'https://api.jinka.fr/apiv2/alert/{alert_token}/ad/90931157'
        },
        {
            'name': 'Contact Info',
            'url': 'https://api.jinka.fr/apiv2/ad/90931157/contact_info'
        },
    ]
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            result = await test_endpoint(session, endpoint['url'], headers, endpoint['name'])
            if result:
                results.append(result)
            await asyncio.sleep(0.5)  # Délai entre les requêtes
    
    # Sauvegarder les résultats
    if results:
        output_file = Path('data/api_exploration/api_responses_detailed.json')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ {len(results)} réponses sauvegardées dans {output_file}")
        
        # Générer un rapport
        report_file = Path('data/api_exploration/api_structures_report.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Structures de Données API Jinka\n\n")
            f.write("**Généré automatiquement depuis les réponses API réelles**\n\n")
            
            for result in results:
                f.write(f"## {result['endpoint']}\n\n")
                f.write(f"**URL:** `{result['url']}`\n\n")
                f.write(f"**Status:** {result['status']}\n\n")
                
                data = result['data']
                
                # Analyser la structure
                if isinstance(data, dict):
                    f.write("### Structure\n\n")
                    f.write("```json\n")
                    f.write(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
                    if len(str(data)) > 2000:
                        f.write("\n... [TRUNCATED]")
                    f.write("\n```\n\n")
                    
                    f.write("### Clés principales\n\n")
                    for key in list(data.keys())[:20]:
                        value = data[key]
                        if isinstance(value, list):
                            f.write(f"- `{key}`: array[{len(value)}]\n")
                        elif isinstance(value, dict):
                            f.write(f"- `{key}`: object\n")
                        else:
                            f.write(f"- `{key}`: {type(value).__name__}\n")
                    f.write("\n")
                    
                elif isinstance(data, list):
                    f.write("### Structure\n\n")
                    f.write(f"Array avec {len(data)} éléments\n\n")
                    if data:
                        f.write("```json\n")
                        f.write(json.dumps(data[0], ensure_ascii=False, indent=2)[:2000])
                        if len(str(data[0])) > 2000:
                            f.write("\n... [TRUNCATED]")
                        f.write("\n```\n\n")
                
                f.write("---\n\n")
        
        print(f"✅ Rapport généré: {report_file}")
    else:
        print("\n❌ Aucune réponse JSON capturée")

if __name__ == "__main__":
    asyncio.run(main())

