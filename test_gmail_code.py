#!/usr/bin/env python3
"""
Script de test pour vérifier la récupération du code d'activation depuis Gmail
"""

from dotenv import load_dotenv
from scrape_jinka import JinkaScraper

load_dotenv()

def get_activation_code_from_gmail():
    """Récupère le code d'activation depuis Gmail en utilisant la fonction de scrape_jinka.py"""
    print("📧 TEST : Récupération du code d'activation depuis Gmail")
    print("=" * 60)
    print()
    
    # Utiliser la fonction de JinkaScraper
    scraper = JinkaScraper()
    code = scraper.get_activation_code_from_gmail()
    
    return code

if __name__ == "__main__":
    code = get_activation_code_from_gmail()
    if code:
        print(f"\n🎉 SUCCÈS: Code trouvé = {code}")
    else:
        print("\n❌ Aucun code trouvé")

