#!/usr/bin/env python3
"""
Test direct de l'API pour vérifier les scores renvoyés
"""

import requests
import json

def test_alert_api():
    """Test l'API d'alertes pour voir les scores renvoyés"""
    print("🧪 Test de l'API d'alertes")
    print("=" * 60)
    
    # Récupérer la liste des alertes
    try:
        response = requests.get("http://localhost:8000/api/alerts")
        if response.status_code != 200:
            print(f"❌ Erreur récupération alertes: {response.status_code}")
            return
        
        alerts = response.json()
        if not alerts:
            print("⚠️ Aucune alerte trouvée")
            return
        
        # Prendre la première alerte
        alert = alerts[0]
        alert_id = alert['id']
        print(f"📋 Alerte test: {alert.get('name', 'N/A')} (ID: {alert_id})")
        
        # Récupérer les appartements de cette alerte
        response = requests.get(f"http://localhost:8000/api/alerts/{alert_id}/apartments")
        if response.status_code != 200:
            print(f"❌ Erreur récupération appartements: {response.status_code}")
            return
        
        apartments = response.json()
        print(f"\n📊 {len(apartments)} appartements trouvés")
        
        # Afficher les 5 premiers avec leurs scores
        print("\n🔍 Scores des 5 premiers appartements:")
        for i, apt in enumerate(apartments[:5]):
            alert_score = apt.get('alert_score', 'N/A')
            alert_tier = apt.get('alert_tier', 'N/A')
            criteria_scores = apt.get('alert_criteria_scores', {})
            
            print(f"\n{i+1}. Appartement {apt.get('id', 'N/A')}:")
            print(f"   alert_score: {alert_score}")
            print(f"   alert_tier: {alert_tier}")
            print(f"   max_score attendu: 5")
            
            if alert_score > 5:
                print(f"   ⚠️ PROBLÈME: Score {alert_score} > 5!")
            
            # Afficher les scores individuels
            if criteria_scores:
                print(f"   Scores individuels:")
                for crit_name, crit_data in criteria_scores.items():
                    crit_score = crit_data.get('score', 'N/A')
                    crit_tier = crit_data.get('tier', 'N/A')
                    print(f"     {crit_name}: {crit_score}pt (tier: {crit_tier})")
        
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au backend sur http://localhost:8000")
        print("   Assurez-vous que le backend est démarré")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_alert_api()


