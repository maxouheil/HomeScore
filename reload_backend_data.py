#!/usr/bin/env python3
"""
Script pour recharger les données dans le backend et les envoyer au frontend
"""

import requests
import time
import subprocess
import os

def invalidate_backend_cache():
    """Invalide le cache du backend via l'API"""
    try:
        response = requests.post("http://localhost:8000/api/apartments/invalidate-cache", timeout=5)
        if response.status_code == 200:
            print("✅ Cache invalidé via API")
            return True
        else:
            print(f"⚠️  Erreur invalidation cache: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  Backend non accessible - il faut le redémarrer")
        return False
    except Exception as e:
        print(f"⚠️  Erreur: {e}")
        return False

def restart_backend():
    """Redémarre le backend"""
    print("🛑 Arrêt du backend...")
    try:
        subprocess.run(["pkill", "-9", "-f", "uvicorn.*backend.main"], check=False)
        subprocess.run(["pkill", "-9", "-f", "python.*start_backend"], check=False)
        time.sleep(2)
    except:
        pass
    
    print("🚀 Démarrage du backend...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_script = os.path.join(script_dir, "start_backend.py")
    
    # Démarrer en arrière-plan
    subprocess.Popen(
        ["python3", backend_script],
        cwd=script_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Attendre que le backend démarre
    print("⏳ Attente du démarrage du backend...")
    for i in range(10):
        time.sleep(1)
        try:
            response = requests.get("http://localhost:8000/api/apartments", timeout=2)
            if response.status_code == 200:
                print("✅ Backend démarré et accessible")
                return True
        except:
            pass
    
    print("⚠️  Backend démarré mais pas encore accessible (peut prendre quelques secondes)")
    return False

def verify_data_loaded():
    """Vérifie que les nouvelles données sont chargées"""
    try:
        response = requests.get("http://localhost:8000/api/apartments", timeout=10)
        if response.status_code == 200:
            apartments = response.json()
            print(f"✅ {len(apartments)} appartements chargés dans le backend")
            
            # Vérifier qu'il y a des appartements avec style_analysis
            with_style = sum(1 for apt in apartments if apt.get('style_analysis'))
            print(f"✅ {with_style} appartements avec style_analysis")
            
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

def main():
    print("🔄 RECHARGEMENT DES DONNÉES DANS LE BACKEND")
    print("=" * 60)
    
    # Essayer d'invalider le cache d'abord
    if invalidate_backend_cache():
        print("\n✅ Cache invalidé - les nouvelles données seront chargées à la prochaine requête")
        time.sleep(1)
        if verify_data_loaded():
            print("\n✅ Données rechargées avec succès!")
            return
    
    # Si l'invalidation ne fonctionne pas, redémarrer le backend
    print("\n🔄 Redémarrage du backend...")
    if restart_backend():
        time.sleep(3)
        if verify_data_loaded():
            print("\n✅ Backend redémarré et données chargées avec succès!")
        else:
            print("\n⚠️  Backend redémarré mais vérification des données échouée")
    else:
        print("\n⚠️  Redémarrage du backend - vérifiez manuellement")

if __name__ == "__main__":
    main()


