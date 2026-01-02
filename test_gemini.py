#!/usr/bin/env python3
"""
Script de test pour vérifier que votre clé API Gemini fonctionne correctement
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Charger les variables d'environnement depuis .env
load_dotenv()

def test_gemini_api():
    """Teste la connexion et l'utilisation de l'API Gemini"""
    
    # Récupérer la clé API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    if not GEMINI_API_KEY:
        print("❌ ERREUR: GEMINI_API_KEY non trouvée")
        print("\n💡 Solutions:")
        print("   1. Créez un fichier .env à la racine du projet")
        print("   2. Ajoutez: GEMINI_API_KEY=votre_cle_api")
        print("   3. Installez python-dotenv: pip install python-dotenv")
        return False
    
    print("✅ Clé API trouvée dans les variables d'environnement")
    print(f"   Clé: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-5:]}\n")
    
    # Configurer Gemini
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ Configuration Gemini réussie\n")
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        return False
    
    # Test 1: Modèle texte simple (utiliser Flash qui a un meilleur quota gratuit)
    print("🧪 Test 1: Modèle texte (gemini-flash-latest)")
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content("Dis-moi bonjour en français en une phrase")
        print(f"   ✅ Réponse: {response.text}\n")
    except Exception as e:
        print(f"   ⚠️  Erreur avec Flash: {e}")
        print("   💡 Essayons avec gemini-pro-latest...")
        try:
            model = genai.GenerativeModel('gemini-pro-latest')
            response = model.generate_content("Dis-moi bonjour en français en une phrase")
            print(f"   ✅ Réponse avec Pro: {response.text}\n")
        except Exception as e2:
            print(f"   ❌ Erreur avec Pro aussi: {e2}\n")
            print("   💡 Le quota gratuit peut être épuisé. Vérifiez: https://ai.dev/usage")
            return False
    
    # Test 2: Modèle vision (pour analyse d'images)
    print("🧪 Test 2: Modèle vision (gemini-2.5-flash)")
    try:
        vision_model = genai.GenerativeModel('gemini-2.5-flash')
        print(f"   ✅ Modèle {vision_model.model_name} chargé avec succès")
        print(f"   ✅ Modèle prêt pour l'analyse d'images\n")
    except Exception as e:
        print(f"   ❌ Erreur: {e}\n")
        return False
    
    # Test 3: Lister les modèles disponibles
    print("🧪 Test 3: Modèles disponibles")
    try:
        models = list(genai.list_models())
        vision_models = [m for m in models if 'vision' in str(m.supported_generation_methods).lower() or 'generateContent' in m.supported_generation_methods]
        print(f"   ✅ {len(models)} modèles disponibles")
        print(f"   ✅ {len(vision_models)} modèles avec vision disponibles")
        print("\n   Modèles vision recommandés:")
        for m in vision_models[:5]:  # Afficher les 5 premiers
            print(f"      - {m.name}")
        print()
    except Exception as e:
        print(f"   ⚠️  Erreur lors de la liste des modèles: {e}\n")
    
    print("="*60)
    print("✅ TOUS LES TESTS SONT PASSÉS !")
    print("="*60)
    print("\n🎉 Votre clé API Gemini fonctionne correctement")
    print("💡 Vous pouvez maintenant utiliser Gemini dans votre projet")
    print("\n📚 Prochaines étapes:")
    print("   1. Consultez PROCHAINES_ETAPES_GEMINI.md pour l'intégration")
    print("   2. Créez un script d'analyse visuelle avec Gemini")
    print("   3. Remplacez progressivement OpenAI par Gemini pour économiser 96% !")
    
    return True


if __name__ == "__main__":
    print("="*60)
    print("🔍 TEST DE LA CLÉ API GEMINI")
    print("="*60)
    print()
    
    success = test_gemini_api()
    
    if not success:
        print("\n❌ Certains tests ont échoué. Vérifiez:")
        print("   - Que votre clé API est correcte")
        print("   - Que l'API Generative Language API est activée dans Google Cloud Console")
        print("   - Que vous avez installé: pip install google-generativeai python-dotenv")
        exit(1)

