#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier la configuration Gemini
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("🔍 DIAGNOSTIC GEMINI API")
print("=" * 60)
print()

# 1. Vérifier le fichier .env
print("1️⃣  Vérification du fichier .env")
if os.path.exists(".env"):
    print("   ✅ Fichier .env trouvé")
    with open(".env", "r") as f:
        content = f.read()
        if "GEMINI_API_KEY" in content:
            print("   ✅ Variable GEMINI_API_KEY trouvée")
        else:
            print("   ❌ Variable GEMINI_API_KEY non trouvée dans .env")
else:
    print("   ❌ Fichier .env non trouvé")
print()

# 2. Vérifier la clé API
print("2️⃣  Vérification de la clé API")
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    print(f"   ✅ Clé API trouvée")
    print(f"   Longueur: {len(api_key)} caractères")
    print(f"   Début: {api_key[:10]}...")
    print(f"   Fin: ...{api_key[-5:]}")
    
    # Vérifier le format
    if api_key.startswith("AIza"):
        print("   ✅ Format de clé correct (commence par AIza)")
    else:
        print("   ⚠️  Format de clé suspect (devrait commencer par AIza)")
    
    if len(api_key) >= 35:
        print("   ✅ Longueur de clé correcte")
    else:
        print("   ⚠️  Longueur de clé suspecte (devrait être ~39 caractères)")
else:
    print("   ❌ Clé API non trouvée")
print()

# 3. Tester l'import de la bibliothèque
print("3️⃣  Vérification de la bibliothèque")
try:
    import google.generativeai as genai
    print("   ✅ google-generativeai importé avec succès")
except ImportError as e:
    print(f"   ❌ Erreur d'import: {e}")
    print("   💡 Installez avec: pip install google-generativeai")
    exit(1)
print()

# 4. Tester la configuration
print("4️⃣  Test de configuration")
if api_key:
    try:
        genai.configure(api_key=api_key)
        print("   ✅ Configuration réussie")
    except Exception as e:
        print(f"   ❌ Erreur de configuration: {e}")
else:
    print("   ⚠️  Impossible de tester (clé API manquante)")
print()

# 5. Tester une requête simple
print("5️⃣  Test de requête API")
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        print("   ⏳ Envoi d'une requête de test...")
        response = model.generate_content("Dis bonjour")
        print(f"   ✅ Requête réussie!")
        print(f"   Réponse: {response.text[:50]}...")
    except Exception as e:
        print(f"   ❌ Erreur lors de la requête: {e}")
        print()
        print("   🔧 SOLUTIONS POSSIBLES:")
        print("   1. Vérifiez que votre clé API est correcte dans Google Cloud Console")
        print("   2. Allez sur https://console.cloud.google.com/")
        print("   3. Sélectionnez le bon projet")
        print("   4. Allez dans 'APIs & Services' > 'Library'")
        print("   5. Recherchez 'Generative Language API' et cliquez sur 'Enable'")
        print("   6. Vérifiez les restrictions de votre clé dans 'Credentials'")
        print("   7. Recopiez la clé depuis Google Cloud Console")
else:
    print("   ⚠️  Impossible de tester (clé API manquante)")
print()

print("=" * 60)
print("✅ DIAGNOSTIC TERMINÉ")
print("=" * 60)

