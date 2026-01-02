#!/usr/bin/env python3
"""
Test direct de l'API Jinka pour voir ce qu'elle retourne vraiment
"""

import requests
import json
from cookie_manager import CookieManager
from config_jinka import JINKA_ALERT_TOKEN, JINKA_API_BASE_URL

print("=" * 80)
print("🔍 TEST DIRECT DE L'API JINKA")
print("=" * 80)
print()

manager = CookieManager()
saved_cookies = manager.load_cookies()

if not saved_cookies:
    print("❌ Pas de cookies sauvegardés")
    exit(1)

print(f"✅ {len(saved_cookies)} cookie(s) chargé(s)")
print()

# Créer une session avec les cookies
session = requests.Session()
cookie_dict = manager.cookies_to_requests_format(saved_cookies)
session.cookies.update(cookie_dict)
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.jinka.fr/asrenter/alert/dashboard/26c2ec3064303aa68ffa43f7c6518733'
})

# Test 1: Endpoint de l'alerte
print("1️⃣  Test: GET /alert/{token}")
print("-" * 80)
url = f"{JINKA_API_BASE_URL}/alert/{JINKA_ALERT_TOKEN}"
response = session.get(url)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Clés dans la réponse: {list(data.keys())[:20]}")
    print(f"has_unread_result: {data.get('has_unread_result')}")
    print()
    
    # Sauvegarder pour inspection
    with open('data/api_alert_response.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("💾 Réponse sauvegardée dans data/api_alert_response.json")
else:
    print(f"Erreur: {response.text[:200]}")
print()

# Test 2: Chercher des endpoints pour les résultats
endpoints_to_try = [
    f"/alert/{JINKA_ALERT_TOKEN}/results",
    f"/alert/{JINKA_ALERT_TOKEN}/ads",
    f"/alert/{JINKA_ALERT_TOKEN}/matches",
    f"/alert/{JINKA_ALERT_TOKEN}/listings",
    f"/alert/{JINKA_ALERT_TOKEN}/apartments",
    f"/alert/{JINKA_ALERT_TOKEN}/properties",
    f"/results?alert_token={JINKA_ALERT_TOKEN}",
    f"/ads?alert_token={JINKA_ALERT_TOKEN}",
    f"/search?alert_id={JINKA_ALERT_TOKEN}",
]

print("2️⃣  Test de différents endpoints pour les résultats")
print("-" * 80)
for endpoint in endpoints_to_try:
    url = f"{JINKA_API_BASE_URL}{endpoint}"
    try:
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {endpoint}")
            print(f"   Type: {type(data)}")
            if isinstance(data, dict):
                print(f"   Clés: {list(data.keys())[:10]}")
            elif isinstance(data, list):
                print(f"   Nombre d'éléments: {len(data)}")
                if len(data) > 0:
                    print(f"   Premier élément: {list(data[0].keys())[:5] if isinstance(data[0], dict) else type(data[0])}")
            print()
        elif response.status_code != 404:
            print(f"⚠️  {endpoint} - Status: {response.status_code}")
    except Exception as e:
        pass

print()
print("3️⃣  Inspection détaillée de la réponse de l'alerte")
print("-" * 80)
if response.status_code == 200:
    data = response.json()
    
    # Chercher récursivement des IDs d'appartements
    def find_apartment_ids(obj, path=""):
        ids = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ['id', 'ad_id', 'apartment_id', 'property_id'] and isinstance(value, (str, int)):
                    if str(value).isdigit() and len(str(value)) >= 6:
                        ids.append((path + key, value))
                ids.extend(find_apartment_ids(value, path + key + "."))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                ids.extend(find_apartment_ids(item, path + f"[{i}]."))
        return ids
    
    apartment_ids = find_apartment_ids(data)
    if apartment_ids:
        print(f"✅ IDs d'appartements trouvés dans la réponse:")
        for path, apt_id in apartment_ids[:10]:
            print(f"   {path}: {apt_id}")
    else:
        print("⚠️  Aucun ID d'appartement trouvé dans la réponse directe")
    
    # Chercher des listes qui pourraient contenir des appartements
    def find_lists_with_apartments(obj, path=""):
        lists = []
        if isinstance(obj, list) and len(obj) > 0:
            first_item = obj[0]
            if isinstance(first_item, dict):
                keys = list(first_item.keys())
                if any(k in keys for k in ['id', 'ad_id', 'apartment_id', 'titre', 'title', 'price', 'prix']):
                    lists.append((path, len(obj), keys[:5]))
        elif isinstance(obj, dict):
            for key, value in obj.items():
                lists.extend(find_lists_with_apartments(value, path + "." + key if path else key))
        return lists
    
    apartment_lists = find_lists_with_apartments(data)
    if apartment_lists:
        print(f"\n✅ Listes qui pourraient contenir des appartements:")
        for path, length, sample_keys in apartment_lists:
            print(f"   {path}: {length} éléments, clés: {sample_keys}")
    else:
        print("\n⚠️  Aucune liste d'appartements trouvée dans la réponse")

print()
print("=" * 80)
print("✅ Test terminé")
print("=" * 80)

