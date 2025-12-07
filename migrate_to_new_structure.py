#!/usr/bin/env python3
"""
Script de migration vers la nouvelle structure
Convertit les anciennes données vers le nouveau format
"""

import json
import os
from datetime import datetime


def load_old_scores():
    """Charge les scores depuis l'ancienne structure"""
    try:
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  Fichier data/scores/all_apartments_scores.json non trouvé")
        return []


def load_scraped_apartments():
    """Charge les données scrapées"""
    try:
        with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  Fichier data/scraped_apartments.json non trouvé")
        return []


def merge_apartment_data(scored_apartments, scraped_apartments):
    """
    Fusionne les données scorées avec les données scrapées
    Crée un dict par ID pour faciliter la fusion
    """
    # Convertir scraped_apartments en dict par ID
    scraped_dict = {}
    for apt in scraped_apartments:
        apt_id = apt.get('id')
        if apt_id:
            scraped_dict[apt_id] = apt
    
    # Fusionner les données
    merged = []
    for scored_apt in scored_apartments:
        apt_id = scored_apt.get('id')
        if apt_id and apt_id in scraped_dict:
            scraped_apt_data = scraped_dict[apt_id]
            # Fusionner en gardant les scores mais en ajoutant les données scrapées
            merged_apt = scored_apt.copy()
            # Ajouter style_analysis si présent
            if 'style_analysis' in scraped_apt_data:
                merged_apt['style_analysis'] = scraped_apt_data['style_analysis']
            # Ajouter exposition si présent
            if 'exposition' in scraped_apt_data:
                merged_apt['exposition'] = scraped_apt_data['exposition']
            # Ajouter photos si présentes
            if 'photos' in scraped_apt_data:
                merged_apt['photos'] = scraped_apt_data['photos']
            # Ajouter autres données importantes
            if 'style_haussmannien' in scraped_apt_data:
                merged_apt['style_haussmannien'] = scraped_apt_data['style_haussmannien']
            merged.append(merged_apt)
        else:
            # Si pas dans scraped, garder tel quel
            merged.append(scored_apt)
    
    return merged


def migrate_scores():
    """Migre les scores vers le nouveau format"""
    print("🔄 Migration vers la nouvelle structure...")
    print("=" * 50)
    
    # Phase 1: Charger les anciennes données
    print("\n📥 Phase 1: Chargement des anciennes données...")
    old_scores = load_old_scores()
    scraped_apartments = load_scraped_apartments()
    
    if not old_scores:
        print("❌ Aucun score trouvé. Utilisez scoring.py pour calculer les scores.")
        return False
    
    print(f"✅ {len(old_scores)} scores chargés")
    print(f"✅ {len(scraped_apartments)} appartements scrapés chargés")
    
    # Phase 2: Fusionner les données
    print("\n🔗 Phase 2: Fusion des données...")
    merged_apartments = merge_apartment_data(old_scores, scraped_apartments)
    print(f"✅ {len(merged_apartments)} appartements fusionnés")
    
    # Phase 3: Sauvegarder dans le nouveau format
    print("\n💾 Phase 3: Sauvegarde dans le nouveau format...")
    
    # Sauvegarder scores.json (nouveau format)
    os.makedirs('data', exist_ok=True)
    with open('data/scores.json', 'w', encoding='utf-8') as f:
        json.dump(merged_apartments, f, indent=2, ensure_ascii=False)
    print(f"✅ Scores sauvegardés: data/scores.json")
    
    # Sauvegarder scraped_apartments.json (s'assurer qu'il est à jour)
    if scraped_apartments:
        with open('data/scraped_apartments.json', 'w', encoding='utf-8') as f:
            json.dump(scraped_apartments, f, indent=2, ensure_ascii=False)
        print(f"✅ Données scrapées sauvegardées: data/scraped_apartments.json")
    
    print("\n🎉 Migration terminée!")
    print(f"   - {len(merged_apartments)} appartements migrés")
    print(f"   - Fichiers créés:")
    print(f"     • data/scores.json")
    print(f"     • data/scraped_apartments.json")
    print("\n💡 Vous pouvez maintenant utiliser:")
    print("   python homescore.py  # Pour générer le HTML")
    
    return True


def check_compatibility():
    """Vérifie la compatibilité des données existantes"""
    print("🔍 Vérification de la compatibilité...")
    
    issues = []
    
    # Vérifier si all_apartments_scores.json existe
    if not os.path.exists('data/scores/all_apartments_scores.json'):
        issues.append("⚠️  data/scores/all_apartments_scores.json non trouvé")
    
    # Vérifier si scraped_apartments.json existe
    if not os.path.exists('data/scraped_apartments.json'):
        issues.append("⚠️  data/scraped_apartments.json non trouvé")
    
    # Vérifier si scores.json existe déjà
    if os.path.exists('data/scores.json'):
        issues.append("ℹ️  data/scores.json existe déjà (sera écrasé)")
    
    if issues:
        print("\nPoints d'attention:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ Tous les fichiers nécessaires sont présents")
    
    return len(issues) == 0


def main():
    """Fonction principale"""
    print("🏠 Migration vers la nouvelle structure HomeScore")
    print("=" * 50)
    
    # Vérifier la compatibilité
    if not check_compatibility():
        print("\n❓ Voulez-vous continuer? (les fichiers manquants seront ignorés)")
        response = input("   Tapez 'oui' pour continuer: ")
        if response.lower() != 'oui':
            print("❌ Migration annulée")
            return
    
    # Migrer
    success = migrate_scores()
    
    if success:
        print("\n✅ Migration réussie!")
        print("\n📋 Prochaines étapes:")
        print("   1. Vérifiez data/scores.json")
        print("   2. Vérifiez data/scraped_apartments.json")
        print("   3. Lancez: python homescore.py")
    else:
        print("\n❌ Migration échouée")
        print("   Assurez-vous d'avoir les fichiers nécessaires")


if __name__ == "__main__":
    main()










