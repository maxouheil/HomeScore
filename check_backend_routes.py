#!/usr/bin/env python3
"""
Vérifie que le backend répond et liste les routes disponibles
"""

import requests
import json

def check_backend():
    """Vérifie le backend et liste les routes"""
    try:
        # Test de santé
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Backend répond sur http://localhost:8000")
        else:
            print(f"⚠️ Backend répond mais avec code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend non accessible sur http://localhost:8000")
        print("   Assurez-vous que le backend est démarré")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Tester l'endpoint de test
    try:
        response = requests.get("http://localhost:8000/api/alerts/test-scoring", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Endpoint test-scoring fonctionne!")
            print(f"   Score: {data.get('score')}")
            print(f"   Max score: {data.get('max_score')}")
            print(f"   Tier: {data.get('tier')}")
            print(f"   Criteria scores: {data.get('criteria_scores')}")
            
            if data.get('score', 0) > 5:
                print(f"\n⚠️ PROBLÈME: Score {data.get('score')} > 5!")
            else:
                print(f"\n✅ Score correct: {data.get('score')}/5")
        else:
            print(f"\n❌ Endpoint test-scoring retourne {response.status_code}")
            print(f"   Réponse: {response.text}")
    except Exception as e:
        print(f"\n❌ Erreur lors du test de l'endpoint: {e}")
        import traceback
        traceback.print_exc()
    
    return True

if __name__ == "__main__":
    check_backend()


