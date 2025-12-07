#!/usr/bin/env python3
"""
Script de test pour HomeScore
"""

import os
import sys
import json
from datetime import datetime

def test_environment():
    """Teste l'environnement"""
    print("🔍 Test de l'environnement...")
    
    # Vérifier les variables d'environnement
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['JINKA_EMAIL', 'JINKA_PASSWORD', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables manquantes: {', '.join(missing_vars)}")
        print("💡 Créez un fichier .env avec vos identifiants")
        return False
    
    print("✅ Variables d'environnement OK")
    return True

def test_config_files():
    """Teste les fichiers de configuration"""
    print("🔍 Test des fichiers de configuration...")
    
    required_files = [
        'scoring_config.json',
        'scoring_prompt.txt',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Fichiers manquants: {', '.join(missing_files)}")
        return False
    
    print("✅ Fichiers de configuration OK")
    return True

def test_directories():
    """Teste la création des répertoires"""
    print("🔍 Test des répertoires...")
    
    required_dirs = [
        'data',
        'data/appartements',
        'data/scores',
        'output',
        'logs'
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"📁 Répertoire créé: {dir_path}")
    
    print("✅ Répertoires OK")
    return True

def test_scoring_config():
    """Teste la configuration de scoring"""
    print("🔍 Test de la configuration de scoring...")
    
    try:
        with open('scoring_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'axes' not in config:
            print("❌ Configuration invalide: pas d'axes")
            return False
        
        axes = config['axes']
        if len(axes) != 8:
            print(f"❌ Configuration invalide: {len(axes)} axes au lieu de 8")
            return False
        
        total_weight = sum(axe.get('poids', 0) for axe in axes)
        if total_weight != 100:
            print(f"❌ Configuration invalide: poids total {total_weight} au lieu de 100")
            return False
        
        print(f"✅ Configuration de scoring OK: {len(axes)} axes, poids total {total_weight}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return False

def test_openai_connection():
    """Teste la connexion OpenAI"""
    print("🔍 Test de la connexion OpenAI...")
    
    try:
        import openai
        from dotenv import load_dotenv
        load_dotenv()
        
        client = openai.OpenAI()
        
        # Test simple
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test de connexion"}],
            max_tokens=10
        )
        
        print("✅ Connexion OpenAI OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur OpenAI: {e}")
        return False

def test_playwright():
    """Teste Playwright"""
    print("🔍 Test de Playwright...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://www.google.com')
            title = page.title()
            browser.close()
            
            if 'Google' in title:
                print("✅ Playwright OK")
                return True
            else:
                print("❌ Playwright: page non chargée correctement")
                return False
                
    except Exception as e:
        print(f"❌ Erreur Playwright: {e}")
        return False

def create_sample_apartment():
    """Crée un appartement d'exemple pour les tests"""
    print("🔍 Création d'un appartement d'exemple...")
    
    sample_apartment = {
        "id": "test_001",
        "url": "https://www.jinka.fr/alert_result?ad=test_001",
        "scraped_at": datetime.now().isoformat(),
        "titre": "Paris 19e - 70m² - 3p - Magnifique duplex haussmannien",
        "prix": "775 000 €",
        "prix_m2": "11071 €/m²",
        "localisation": "Paris 19e (75019)",
        "surface": "70 m²",
        "pieces": "3 pièces - 2 chambres",
        "date": "Appartement, le 29 oct. à 16:28, par une agence",
        "transports": ["Pyrénées 11", "Jourdain 11", "Botzaris 7 bis"],
        "description": "Globalstone vous propose en exclusivité ce magnifique duplex situé dans le XIXe arrondissement de Paris, à seulement 350 m des Buttes-Chaumont. Lumineux et spacieux de 69,96 m², situé dans un immeuble entièrement restauré sur le 4e étage. Il dispose d'une cuisine américaine ouverte connectée à un grand salon et une salle à manger. À l'étage, deux chambres, dont l'une de plus de 15 m², une salle d'eau et un WC indépendant.",
        "photos": ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],
        "caracteristiques": "Caractéristiques: Duplex, Cuisine américaine, Parquet, Moulures, Cheminée",
        "agence": "GLOBALSTONE"
    }
    
    os.makedirs('data/appartements', exist_ok=True)
    with open('data/appartements/test_001.json', 'w', encoding='utf-8') as f:
        json.dump(sample_apartment, f, ensure_ascii=False, indent=2)
    
    print("✅ Appartement d'exemple créé")
    return True

def test_scoring():
    """Teste le scoring avec l'appartement d'exemple"""
    print("🔍 Test du scoring...")
    
    try:
        from score_appartement import score_apartment_with_openai, load_scoring_config
        
        # Charger la configuration
        scoring_config = load_scoring_config()
        if not scoring_config:
            print("❌ Impossible de charger la configuration de scoring")
            return False
        
        # Charger l'appartement d'exemple
        with open('data/appartements/test_001.json', 'r', encoding='utf-8') as f:
            apartment_data = json.load(f)
        
        # Scorer l'appartement
        score_result = score_apartment_with_openai(apartment_data, scoring_config)
        
        if score_result and score_result.get('score_global', 0) > 0:
            print(f"✅ Scoring OK: {score_result['score_global']}/100")
            return True
        else:
            print("❌ Scoring échoué")
            return False
            
    except Exception as e:
        print(f"❌ Erreur scoring: {e}")
        return False

def test_html_report():
    """Teste la génération du rapport HTML"""
    print("🔍 Test du rapport HTML...")
    
    try:
        from generate_html_report import generate_html_report
        
        if generate_html_report():
            if os.path.exists('output/rapport_appartements.html'):
                print("✅ Rapport HTML généré")
                return True
            else:
                print("❌ Fichier rapport non trouvé")
                return False
        else:
            print("❌ Génération rapport échouée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur rapport: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test de HomeScore")
    print("=" * 50)
    
    tests = [
        ("Environnement", test_environment),
        ("Fichiers de configuration", test_config_files),
        ("Répertoires", test_directories),
        ("Configuration de scoring", test_scoring_config),
        ("Connexion OpenAI", test_openai_connection),
        ("Playwright", test_playwright),
        ("Appartement d'exemple", create_sample_apartment),
        ("Scoring", test_scoring),
        ("Rapport HTML", test_html_report)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} échoué")
        except Exception as e:
            print(f"❌ {test_name} erreur: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("✅ Tous les tests sont passés! HomeScore est prêt à l'emploi.")
        return True
    else:
        print("❌ Certains tests ont échoué. Vérifiez la configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
