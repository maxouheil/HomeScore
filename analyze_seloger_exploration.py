#!/usr/bin/env python3
"""
Analyse les résultats de l'exploration SeLoger pour identifier les endpoints API réels
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def find_latest_exploration():
    """Trouve la dernière exploration"""
    exploration_dir = Path('data/api_exploration/seloger')
    if not exploration_dir.exists():
        return None
    
    summaries = list(exploration_dir.glob('summary_*.json'))
    if not summaries:
        return None
    
    # Trier par nom de fichier (qui contient le timestamp)
    latest = max(summaries, key=lambda p: p.name)
    timestamp = latest.stem.replace('summary_', '')
    return timestamp

def analyze_endpoints(timestamp):
    """Analyse les endpoints capturés"""
    endpoints_file = Path(f'data/api_exploration/seloger/endpoints_{timestamp}.json')
    if not endpoints_file.exists():
        print(f"❌ Fichier endpoints non trouvé: {endpoints_file}")
        return
    
    with open(endpoints_file, 'r', encoding='utf-8') as f:
        endpoints = json.load(f)
    
    print("\n" + "="*60)
    print("📊 ANALYSE DES ENDPOINTS")
    print("="*60)
    
    # Filtrer les endpoints SeLoger uniquement
    seloger_endpoints = [e for e in endpoints if 'seloger.com' in e['url']]
    
    # Grouper par domaine/path
    by_domain = defaultdict(list)
    for ep in seloger_endpoints:
        url = ep['url']
        if 'api' in url.lower():
            by_domain['API'].append(ep)
        elif 'assets' in url:
            by_domain['Assets'].append(ep)
        else:
            by_domain['Other'].append(ep)
    
    print(f"\n✅ Endpoints SeLoger trouvés: {len(seloger_endpoints)}")
    print(f"   - API: {len(by_domain['API'])}")
    print(f"   - Assets: {len(by_domain['Assets'])}")
    print(f"   - Other: {len(by_domain['Other'])}")
    
    # Afficher les endpoints API
    if by_domain['API']:
        print("\n🔍 ENDPOINTS API IDENTIFIÉS:")
        for ep in by_domain['API']:
            print(f"   {ep['method']} {ep['url']}")
            print(f"      Status: {ep['status']}, JSON: {ep['has_json']}")

def analyze_responses(timestamp):
    """Analyse les réponses pour trouver des données JSON"""
    responses_file = Path(f'data/api_exploration/seloger/responses_{timestamp}.json')
    if not responses_file.exists():
        print(f"❌ Fichier responses non trouvé: {responses_file}")
        return
    
    with open(responses_file, 'r', encoding='utf-8') as f:
        responses = json.load(f)
    
    print("\n" + "="*60)
    print("📦 ANALYSE DES RÉPONSES JSON")
    print("="*60)
    
    json_responses = [r for r in responses if r.get('json') is not None]
    seloger_json = [r for r in json_responses if 'seloger.com' in r['url']]
    
    print(f"\n✅ Réponses JSON SeLoger: {len(seloger_json)}")
    
    for resp in seloger_json:
        print(f"\n🌐 {resp['url']}")
        print(f"   Status: {resp['status']}")
        json_data = resp.get('json')
        if isinstance(json_data, dict):
            print(f"   Keys: {list(json_data.keys())[:10]}")
        elif isinstance(json_data, list):
            print(f"   Array length: {len(json_data)}")
            if len(json_data) > 0:
                print(f"   First item keys: {list(json_data[0].keys())[:10] if isinstance(json_data[0], dict) else 'N/A'}")

def analyze_requests(timestamp):
    """Analyse les requêtes pour trouver des patterns"""
    requests_file = Path(f'data/api_exploration/seloger/requests_{timestamp}.json')
    if not requests_file.exists():
        print(f"❌ Fichier requests non trouvé: {requests_file}")
        return
    
    with open(requests_file, 'r', encoding='utf-8') as f:
        requests = json.load(f)
    
    print("\n" + "="*60)
    print("🌐 ANALYSE DES REQUÊTES")
    print("="*60)
    
    # Chercher les requêtes POST avec body
    post_requests = [r for r in requests if r.get('method') == 'POST' and r.get('post_data')]
    seloger_post = [r for r in post_requests if 'seloger.com' in r['url']]
    
    print(f"\n✅ Requêtes POST SeLoger avec body: {len(seloger_post)}")
    
    for req in seloger_post[:5]:  # Limiter à 5
        print(f"\n📤 POST {req['url']}")
        post_data = req.get('post_data', '')
        if post_data:
            print(f"   Body preview: {post_data[:200]}...")
        
        # Chercher GraphQL
        if 'graphql' in req['url'].lower() or 'query' in post_data.lower():
            print("   ⚠️  Possible requête GraphQL détectée!")

def main():
    """Fonction principale"""
    print("🔍 ANALYSE DE L'EXPLORATION SELOGER")
    print("="*60)
    
    timestamp = find_latest_exploration()
    if not timestamp:
        print("❌ Aucune exploration trouvée")
        print("   Exécutez d'abord: python explore_seloger_api.py")
        return
    
    print(f"✅ Exploration trouvée: {timestamp}")
    
    analyze_endpoints(timestamp)
    analyze_responses(timestamp)
    analyze_requests(timestamp)
    
    print("\n" + "="*60)
    print("💡 RECOMMANDATIONS")
    print("="*60)
    print("""
1. Si aucun endpoint API n'a été trouvé pour les annonces :
   - SeLoger utilise probablement du Server-Side Rendering (SSR)
   - Les données sont dans le HTML initial
   - Ou bien les requêtes sont bloquées par CAPTCHA/anti-bot

2. Pour améliorer l'exploration :
   - Attendre plus longtemps que le JavaScript charge
   - Interagir avec la page (cliquer sur des filtres)
   - Désactiver le CAPTCHA si possible
   - Chercher des requêtes GraphQL ou WebSocket

3. Alternative :
   - Utiliser le scraping HTML comme fallback
   - Les scrapers créés supportent déjà le fallback HTML
    """)

if __name__ == "__main__":
    main()



