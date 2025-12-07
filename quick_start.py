#!/usr/bin/env python3
"""
Script de démarrage rapide pour HomeScore
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def check_requirements():
    """Vérifie que les prérequis sont installés"""
    print("🔍 Vérification des prérequis...")
    
    try:
        import playwright
        import openai
        import requests
        from dotenv import load_dotenv
        print("✅ Modules Python installés")
    except ImportError as e:
        print(f"❌ Module manquant: {e}")
        print("💡 Exécutez: pip install -r requirements.txt")
        return False
    
    return True

def check_environment():
    """Vérifie les variables d'environnement"""
    print("🔍 Vérification de l'environnement...")
    
    load_dotenv()
    
    if not os.getenv('JINKA_EMAIL'):
        print("❌ JINKA_EMAIL non défini")
        return False
    
    if not os.getenv('JINKA_PASSWORD'):
        print("❌ JINKA_PASSWORD non défini")
        return False
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY non défini")
        return False
    
    print("✅ Variables d'environnement OK")
    return True

def install_playwright():
    """Installe Playwright si nécessaire"""
    print("🔍 Vérification de Playwright...")
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print("✅ Playwright OK")
        return True
    except:
        print("📦 Installation de Playwright...")
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            print("✅ Playwright installé")
            return True
        except:
            print("❌ Erreur installation Playwright")
            return False

def run_test():
    """Exécute les tests"""
    print("🧪 Exécution des tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_homescore.py"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tests réussis")
            return True
        else:
            print("❌ Tests échoués")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Erreur tests: {e}")
        return False

def show_usage():
    """Affiche les instructions d'utilisation"""
    print("\n" + "="*60)
    print("🏠 HomeScore - Prêt à l'emploi!")
    print("="*60)
    print("\n📋 Commandes disponibles:")
    print("  python test_homescore.py          # Tester le système")
    print("  python explore_jinka_api.py       # Explorer les APIs Jinka")
    print("  python scrape_jinka.py <URL>      # Scraper une alerte")
    print("  python score_appartement.py       # Scorer les appartements")
    print("  python generate_html_report.py    # Générer le rapport")
    print("  python run_daily_scrape.py        # Automatisation quotidienne")
    print("\n🚀 Démarrage rapide:")
    print("  1. Modifiez l'URL dans config.json avec votre alerte Jinka")
    print("  2. python scrape_jinka.py 'VOTRE_URL_ALERTE'")
    print("  3. python score_appartement.py")
    print("  4. python generate_html_report.py")
    print("  5. Ouvrez output/rapport_appartements.html")
    print("\n📁 Fichiers importants:")
    print("  .env                    # Vos identifiants (à créer)")
    print("  config.json            # Configuration")
    print("  output/rapport_appartements.html  # Rapport final")

def main():
    """Fonction principale"""
    print("🏠 HomeScore - Configuration initiale")
    print("="*50)
    
    # Vérifier les prérequis
    if not check_requirements():
        print("\n❌ Prérequis manquants. Installez-les avec:")
        print("   pip install -r requirements.txt")
        return False
    
    # Vérifier l'environnement
    if not check_environment():
        print("\n❌ Variables d'environnement manquantes.")
        print("💡 Créez un fichier .env avec:")
        print("   JINKA_EMAIL=votre_email@gmail.com")
        print("   JINKA_PASSWORD=votre_mot_de_passe")
        print("   OPENAI_API_KEY=votre_cle_openai")
        return False
    
    # Installer Playwright si nécessaire
    if not install_playwright():
        return False
    
    # Exécuter les tests
    if not run_test():
        print("\n⚠️ Certains tests ont échoué, mais HomeScore peut fonctionner")
    
    # Afficher les instructions
    show_usage()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
