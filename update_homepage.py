#!/usr/bin/env python3
"""
Script rapide pour mettre à jour homepage.html avec la nouvelle structure
"""

import json
import os
from generate_html import generate_html

def main():
    print("🔄 Mise à jour de homepage.html...")
    
    # Charger les scores existants
    try:
        with open('data/scores.json', 'r', encoding='utf-8') as f:
            apartments = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier data/scores.json non trouvé")
        print("💡 Lancez d'abord: python homescore.py")
        return
    
    print(f"✅ {len(apartments)} appartements chargés")
    
    # Générer le HTML
    print("📄 Génération du HTML...")
    html = generate_html(apartments)
    
    # Sauvegarder
    os.makedirs('output', exist_ok=True)
    output_file = 'output/homepage.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ homepage.html mis à jour: {output_file}")
    print(f"   {len(apartments)} appartements affichés")

if __name__ == "__main__":
    main()

