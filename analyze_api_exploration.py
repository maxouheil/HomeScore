#!/usr/bin/env python3
"""
Script pour analyser les résultats de l'exploration API Jinka
Aide à identifier les endpoints, l'authentification, et les patterns
"""

import json
import os
from collections import defaultdict
from urllib.parse import urlparse, parse_qs
import re

def load_latest_exploration():
    """Charge la dernière exploration depuis data/api_exploration/"""
    if not os.path.exists('data/api_exploration'):
        print("❌ Dossier data/api_exploration/ non trouvé")
        print("   Exécutez d'abord explore_jinka_api_advanced.py")
        return None
    
    # Trouver les fichiers les plus récents
    files = {}
    for filename in os.listdir('data/api_exploration'):
        if filename.startswith('summary_'):
            timestamp = filename.replace('summary_', '').replace('.json', '')
            files[timestamp] = filename
    
    if not files:
        print("❌ Aucun fichier d'exploration trouvé")
        return None
    
    latest_timestamp = max(files.keys())
    base_name = latest_timestamp
    
    print(f"📂 Chargement de l'exploration du {latest_timestamp}")
    
    results = {}
    
    # Charger les fichiers
    for file_type in ['summary', 'requests', 'responses', 'endpoints', 'cookies', 'tokens']:
        filepath = f'data/api_exploration/{file_type}_{latest_timestamp}.json'
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                results[file_type] = json.load(f)
        else:
            results[file_type] = None
    
    return results, base_name

def analyze_endpoints(responses):
    """Analyse les endpoints API identifiés"""
    print("\n" + "="*60)
    print("🔍 ANALYSE DES ENDPOINTS API")
    print("="*60)
    
    # Grouper par pattern d'URL
    endpoint_patterns = defaultdict(list)
    
    for resp in responses:
        if not resp.get('is_api'):
            continue
        
        url = resp['url']
        method = resp.get('request_url', 'UNKNOWN')
        if method == 'UNKNOWN' and resp.get('request_url'):
            # Essayer d'extraire depuis les requêtes
            pass
        
        # Extraire le chemin de base
        parsed = urlparse(url)
        base_path = parsed.path
        
        # Identifier le pattern
        pattern = base_path
        # Remplacer les IDs numériques par {id}
        pattern = re.sub(r'/\d+', '/{id}', pattern)
        pattern = re.sub(r'/[a-f0-9]{32}', '/{token}', pattern)  # Tokens hex
        
        endpoint_patterns[pattern].append({
            'url': url,
            'method': resp.get('request_url', 'GET'),
            'status': resp['status'],
            'has_json': resp.get('json') is not None,
        })
    
    print(f"\n📊 {len(endpoint_patterns)} patterns d'endpoints uniques identifiés:\n")
    
    for pattern, requests in sorted(endpoint_patterns.items()):
        print(f"🔹 {pattern}")
        print(f"   Appels: {len(requests)}")
        
        # Méthodes HTTP utilisées
        methods = set(r['method'] for r in requests)
        print(f"   Méthodes: {', '.join(methods)}")
        
        # Statuts de réponse
        statuses = set(r['status'] for r in requests)
        print(f"   Statuts: {', '.join(map(str, statuses))}")
        
        # Avoir du JSON
        has_json = any(r['has_json'] for r in requests)
        print(f"   JSON: {'✅' if has_json else '❌'}")
        
        # Exemple d'URL
        if requests:
            print(f"   Exemple: {requests[0]['url'][:100]}")
        print()

def analyze_authentication(requests, responses, cookies, tokens):
    """Analyse le mécanisme d'authentification"""
    print("\n" + "="*60)
    print("🔐 ANALYSE DE L'AUTHENTIFICATION")
    print("="*60)
    
    # Chercher les endpoints d'authentification
    auth_endpoints = []
    for resp in responses:
        url = resp['url'].lower()
        if any(keyword in url for keyword in ['auth', 'login', 'sign/in', 'oauth', 'google']):
            auth_endpoints.append({
                'url': resp['url'],
                'status': resp['status'],
                'method': resp.get('request_url', 'UNKNOWN'),
            })
    
    if auth_endpoints:
        print("\n📋 Endpoints d'authentification identifiés:")
        for endpoint in auth_endpoints:
            print(f"   {endpoint['method']} {endpoint['url']}")
            print(f"      Status: {endpoint['status']}")
    
    # Analyser les cookies
    if cookies:
        print(f"\n🍪 {len(cookies)} cookies capturés:")
        important_cookies = [c for c in cookies if any(
            key in c['name'].lower() for key in ['session', 'token', 'auth', 'jwt', 'access', 'refresh']
        )]
        
        if important_cookies:
            print("\n   Cookies importants pour l'authentification:")
            for cookie in important_cookies:
                print(f"   🔑 {cookie['name']}")
                print(f"      Value: {cookie['value'][:50]}...")
                print(f"      Domain: {cookie.get('domain', 'N/A')}")
                print(f"      HttpOnly: {cookie.get('httpOnly', False)}")
                print(f"      Secure: {cookie.get('secure', False)}")
                print()
    
    # Analyser les tokens
    if tokens:
        print(f"\n🎫 {len(tokens)} tokens d'authentification trouvés:")
        for key, value in tokens.items():
            print(f"   {key}: {value[:50]}...")

def analyze_data_structures(responses):
    """Analyse les structures de données JSON"""
    print("\n" + "="*60)
    print("📊 ANALYSE DES STRUCTURES DE DONNÉES")
    print("="*60)
    
    json_responses = [r for r in responses if r.get('json') is not None]
    
    if not json_responses:
        print("⚠️  Aucune réponse JSON trouvée")
        return
    
    print(f"\n📋 {len(json_responses)} réponses JSON trouvées\n")
    
    # Analyser les structures
    structures = defaultdict(int)
    
    for resp in json_responses:
        json_data = resp['json']
        url = resp['url']
        
        if isinstance(json_data, dict):
            # Analyser les clés principales
            main_keys = list(json_data.keys())[:5]
            structure_key = ', '.join(main_keys)
            structures[structure_key] += 1
            
            # Afficher quelques exemples intéressants
            if any(key in url.lower() for key in ['property', 'ad', 'alert']):
                print(f"🔹 {url[:80]}")
                print(f"   Structure: {structure_key}")
                if 'data' in json_data:
                    print(f"   Contient 'data': ✅")
                if 'results' in json_data:
                    print(f"   Contient 'results': ✅")
                if 'properties' in json_data:
                    print(f"   Contient 'properties': ✅")
                print()
        elif isinstance(json_data, list):
            structures['array'] += 1
            if json_data:
                print(f"🔹 {url[:80]}")
                print(f"   Type: Array avec {len(json_data)} éléments")
                if json_data and isinstance(json_data[0], dict):
                    print(f"   Clés du premier élément: {', '.join(list(json_data[0].keys())[:5])}")
                print()
    
    print("\n📊 Structures les plus communes:")
    for structure, count in sorted(structures.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {structure}: {count} occurrences")

def generate_api_documentation(results, base_name):
    """Génère une documentation API basique"""
    print("\n" + "="*60)
    print("📝 GÉNÉRATION DE LA DOCUMENTATION API")
    print("="*60)
    
    doc_path = f'data/api_exploration/api_documentation_{base_name}.md'
    
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write("# Documentation API Jinka (Générée automatiquement)\n\n")
        f.write(f"**Date:** {base_name}\n\n")
        
        # Résumé
        summary = results.get('summary', {})
        f.write("## Résumé\n\n")
        f.write(f"- Total requêtes: {summary.get('total_requests', 'N/A')}\n")
        f.write(f"- Requêtes API: {summary.get('api_requests', 'N/A')}\n")
        f.write(f"- Endpoints identifiés: {summary.get('api_endpoints', 'N/A')}\n\n")
        
        # Endpoints
        endpoints = results.get('endpoints', [])
        if endpoints:
            f.write("## Endpoints Identifiés\n\n")
            for endpoint in endpoints:
                f.write(f"### {endpoint['method']} {endpoint['url']}\n\n")
                f.write(f"- **Status:** {endpoint['status']}\n")
                f.write(f"- **JSON:** {'✅' if endpoint.get('has_json') else '❌'}\n\n")
        
        # Authentification
        cookies = results.get('cookies', [])
        tokens = results.get('tokens', {})
        if cookies or tokens:
            f.write("## Authentification\n\n")
            if tokens:
                f.write("### Tokens\n\n")
                for key, value in tokens.items():
                    f.write(f"- **{key}:** `{value[:50]}...`\n\n")
            if cookies:
                important_cookies = [c for c in cookies if any(
                    key in c['name'].lower() for key in ['session', 'token', 'auth']
                )]
                if important_cookies:
                    f.write("### Cookies Importants\n\n")
                    for cookie in important_cookies:
                        f.write(f"- **{cookie['name']}**\n")
                        f.write(f"  - Domain: {cookie.get('domain', 'N/A')}\n")
                        f.write(f"  - HttpOnly: {cookie.get('httpOnly', False)}\n")
                        f.write(f"  - Secure: {cookie.get('secure', False)}\n\n")
    
    print(f"✅ Documentation générée: {doc_path}")

def main():
    """Fonction principale"""
    print("🔍 ANALYSE DES RÉSULTATS D'EXPLORATION API JINKA")
    print("="*60)
    
    # Charger les résultats
    result = load_latest_exploration()
    if not result:
        return
    
    results, base_name = result
    
    # Analyser les endpoints
    if results.get('responses'):
        analyze_endpoints(results['responses'])
    
    # Analyser l'authentification
    if results.get('requests') and results.get('responses'):
        analyze_authentication(
            results.get('requests', []),
            results.get('responses', []),
            results.get('cookies', []),
            results.get('tokens', {})
        )
    
    # Analyser les structures de données
    if results.get('responses'):
        analyze_data_structures(results['responses'])
    
    # Générer la documentation
    generate_api_documentation(results, base_name)
    
    print("\n✅ Analyse terminée!")

if __name__ == "__main__":
    main()






