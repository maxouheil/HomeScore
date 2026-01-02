#!/usr/bin/env python3
"""
Script de test pour vérifier la mise à jour automatique des alertes
"""
import json
import os
import requests
import time

def test_mise_a_jour():
    """Test complet de la mise à jour des alertes"""
    
    print("🧪 TEST: Mise à jour automatique des alertes")
    print("=" * 60)
    
    # 1. État initial
    print("\n1️⃣ État initial")
    if os.path.exists('data/scraped_apartments.json'):
        with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
            initial_data = json.load(f)
        initial_count = len(initial_data)
        print(f"   ✅ {initial_count} appartements dans scraped_apartments.json")
    else:
        initial_count = 0
        print("   ⚠️  scraped_apartments.json n'existe pas")
    
    # 2. Vérifier l'API
    print("\n2️⃣ Vérification de l'API")
    try:
        response = requests.get('http://localhost:8000/api/apartments', timeout=5)
        if response.status_code == 200:
            api_apartments = response.json()
            api_count = len(api_apartments)
            print(f"   ✅ API retourne {api_count} appartements")
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur connexion API: {e}")
        print("   💡 Assurez-vous que le backend est démarré: python start_backend.py")
        return False
    
    # 3. Vérifier le chargement depuis data/appartements/
    print("\n3️⃣ Vérification du chargement depuis data/appartements/")
    if os.path.exists('data/appartements'):
        files = [f for f in os.listdir('data/appartements') 
                if f.endswith('.json') and not f.startswith('test_')]
        print(f"   ✅ {len(files)} fichiers dans data/appartements/")
        
        # Vérifier que load_apartments_data() charge bien depuis ces fichiers
        print("   🔍 Vérification que l'API charge depuis data/appartements/...")
        # Prendre un ID d'appartement depuis un fichier individuel
        if files:
            sample_file = files[0]
            with open(f'data/appartements/{sample_file}', 'r', encoding='utf-8') as f:
                sample_apt = json.load(f)
                sample_id = sample_apt.get('id')
                if sample_id:
                    # Vérifier que cet appartement est dans l'API
                    found = any(apt.get('id') == sample_id for apt in api_apartments)
                    if found:
                        print(f"   ✅ Appartement {sample_id} trouvé dans l'API (chargé depuis data/appartements/)")
                    else:
                        print(f"   ⚠️  Appartement {sample_id} non trouvé dans l'API")
    else:
        print("   ⚠️  Dossier data/appartements/ n'existe pas")
    
    # 4. Test d'invalidation du cache
    print("\n4️⃣ Test d'invalidation du cache")
    try:
        response = requests.post('http://localhost:8000/api/apartments/invalidate-cache', timeout=5)
        if response.status_code == 200:
            print("   ✅ Cache invalidé avec succès")
            # Vérifier que le cache est bien invalidé en rechargeant
            time.sleep(0.5)
            response2 = requests.get('http://localhost:8000/api/apartments', timeout=5)
            if response2.status_code == 200:
                print("   ✅ API recharge correctement après invalidation")
        else:
            print(f"   ⚠️  Erreur invalidation: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Erreur invalidation: {e}")
    
    # 5. Vérifier qu'un appartement sans scores est géré
    print("\n5️⃣ Test des placeholders")
    try:
        # Chercher un appartement sans scores_detaille
        apartments = api_apartments
        apts_without_scores = [apt for apt in apartments if not apt.get('scores_detaille')]
        if apts_without_scores:
            print(f"   ✅ {len(apts_without_scores)} appartements sans scores détectés (seront affichés avec placeholders)")
            # Vérifier qu'ils ont au moins les champs de base
            sample = apts_without_scores[0]
            if sample.get('id') and sample.get('prix'):
                print(f"   ✅ Exemple: Appartement {sample.get('id')} a les données de base")
        else:
            print("   ℹ️  Tous les appartements ont des scores")
    except Exception as e:
        print(f"   ⚠️  Erreur: {e}")
    
    # 6. Test des stats
    print("\n6️⃣ Test des statistiques")
    try:
        response = requests.get('http://localhost:8000/api/apartments/stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Total: {stats.get('total_apartments')} appartements")
            print(f"   ✅ Avec calme: {stats.get('apartments_with_calme')} ({stats.get('percentage_with_calme')}%)")
            print(f"   ✅ Avec pièce de vie: {stats.get('apartments_with_piece_vie')} ({stats.get('percentage_with_piece_vie')}%)")
        else:
            print(f"   ⚠️  Erreur stats: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Erreur stats: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés")
    print("\n💡 Pour tester le scraping complet:")
    print("   python scrape_new_apartments.py")
    print("\n💡 Pour tester une alerte spécifique:")
    print("   1. Démarrer le backend: python start_backend.py")
    print("   2. Ouvrir le frontend")
    print("   3. Aller sur une alerte et vérifier que les nouveaux appartements apparaissent")
    
    return True

if __name__ == '__main__':
    test_mise_a_jour()


