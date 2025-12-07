#!/usr/bin/env python3
"""
Test rapide de homescore_v2 avec seulement 3 appartements
"""

import json
from pathlib import Path
from data_loader import load_apartments
from scoring import score_all_apartments
from generate_html import generate_html

def test_v2_quick():
    """Test rapide avec 3 appartements"""
    print("🧪 TEST RAPIDE HOMESCORE V2")
    print("=" * 60)
    
    # Charger les données
    print("\n1️⃣ Chargement des données...")
    apartments = load_apartments(prefer_api=True)
    
    if not apartments:
        print("❌ Aucune donnée trouvée")
        return False
    
    print(f"✅ {len(apartments)} appartements disponibles")
    
    # Tester avec seulement 3 appartements
    test_apartments = apartments[:3]
    print(f"\n2️⃣ Test du scoring avec {len(test_apartments)} appartements...")
    
    scored = score_all_apartments(test_apartments)
    
    if not scored:
        print("❌ Erreur lors du scoring")
        return False
    
    print(f"✅ {len(scored)} appartements scorés")
    
    # Tester la génération HTML
    print(f"\n3️⃣ Test de la génération HTML...")
    html = generate_html(scored)
    
    if not html:
        print("❌ Erreur lors de la génération HTML")
        return False
    
    print(f"✅ HTML généré ({len(html)} caractères)")
    
    # Vérifier les scores
    print(f"\n4️⃣ Vérification des scores...")
    for apt in scored:
        score = apt.get('score_total', 0)
        print(f"   {apt.get('id')}: {score}/100")
    
    print("\n✅ TEST RÉUSSI - HomeScore v2 fonctionne correctement!")
    return True

if __name__ == "__main__":
    test_v2_quick()




