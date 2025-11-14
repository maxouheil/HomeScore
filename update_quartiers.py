#!/usr/bin/env python3
"""
Script pour mettre à jour les quartiers de tous les appartements existants
Utilise la nouvelle fonction identify_quartier() améliorée
"""

import json
import os
from scrape_jinka import JinkaScraper
from datetime import datetime

def update_apartment_quartier(apartment_file):
    """Met à jour le quartier d'un appartement"""
    try:
        with open(apartment_file, 'r', encoding='utf-8') as f:
            apartment = json.load(f)
        
        apartment_id = apartment.get('id', 'unknown')
        current_quartier = apartment.get('map_info', {}).get('quartier', '')
        
        # Nettoyer le quartier actuel pour vérifier s'il est identifié
        clean_quartier = current_quartier.replace('(score:', '').strip()
        is_identified = (current_quartier and 
                        current_quartier != "Quartier non identifié" and 
                        current_quartier != "Non identifié" and
                        len(clean_quartier) > 5)
        
        # Si déjà identifié, passer
        if is_identified:
            return {'status': 'skipped', 'reason': 'already_identified', 'quartier': current_quartier}
        
        # Récupérer les données pour identifier le quartier
        streets = apartment.get('map_info', {}).get('streets', [])
        metros = apartment.get('map_info', {}).get('metros', [])
        
        # Ajouter les transports comme métros si disponibles
        transports = apartment.get('transports', [])
        for transport in transports:
            if isinstance(transport, str) and transport not in metros:
                # Nettoyer le transport (enlever numéros de ligne)
                transport_clean = transport.strip()
                if len(transport_clean) > 2 and len(transport_clean) < 50:
                    metros.append(transport_clean)
        
        # Si pas de données, essayer d'extraire depuis la description
        if not streets and not metros:
            description = apartment.get('description', '').lower()
            localisation = apartment.get('localisation', '').lower()
            
            # Chercher des indices de quartiers dans la description
            quartier_keywords = {
                'ménilmontant': 'Ménilmontant',
                'menilmontant': 'Ménilmontant',
                'père-lachaise': 'Père-Lachaise',
                'pere-lachaise': 'Père-Lachaise',
                'belleville': 'Belleville',
                'buttes-chaumont': 'Buttes-Chaumont',
                'buttes chaumont': 'Buttes-Chaumont',
                'pyrenees': 'Pyrénées',
                'pyrénées': 'Pyrénées',
                'jourdain': 'Jourdain',
                'goncourt': 'Goncourt',
                'nation': 'Nation',
                'république': 'République',
                'republique': 'République',
                'bastille': 'Bastille',
                'rue des boulets': 'Rue des Boulets',
            }
            
            for keyword, quartier_name in quartier_keywords.items():
                if keyword in description or keyword in localisation:
                    apartment['map_info']['quartier'] = f"{quartier_name} (détecté depuis description)"
                    apartment['map_info']['updated_at'] = datetime.now().isoformat()
                    
                    # Sauvegarder
                    with open(apartment_file, 'w', encoding='utf-8') as f:
                        json.dump(apartment, f, indent=2, ensure_ascii=False)
                    
                    return {'status': 'updated', 'quartier': quartier_name, 'method': 'description'}
            
            return {'status': 'skipped', 'reason': 'no_data', 'quartier': None}
        
        # Utiliser identify_quartier() pour identifier le quartier
        scraper = JinkaScraper()
        new_quartier = scraper.identify_quartier(streets, metros)
        
        if new_quartier and new_quartier != "Quartier non identifié":
            # Mettre à jour le quartier
            apartment['map_info']['quartier'] = new_quartier
            apartment['map_info']['updated_at'] = datetime.now().isoformat()
            
            # Sauvegarder
            with open(apartment_file, 'w', encoding='utf-8') as f:
                json.dump(apartment, f, indent=2, ensure_ascii=False)
            
            return {'status': 'updated', 'quartier': new_quartier, 'method': 'identify_quartier'}
        else:
            return {'status': 'skipped', 'reason': 'not_identifiable', 'quartier': None}
            
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def main():
    """Met à jour tous les appartements"""
    print("🔄 MISE À JOUR DES QUARTIERS")
    print("=" * 60)
    
    appartements_dir = "data/appartements"
    if not os.path.exists(appartements_dir):
        print(f"❌ Dossier {appartements_dir} non trouvé")
        return
    
    # Lister tous les fichiers JSON
    apartment_files = [f for f in os.listdir(appartements_dir) if f.endswith('.json')]
    
    if not apartment_files:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"📋 {len(apartment_files)} appartements à vérifier\n")
    
    stats = {
        'total': len(apartment_files),
        'updated': 0,
        'skipped_already': 0,
        'skipped_no_data': 0,
        'skipped_not_identifiable': 0,
        'errors': 0
    }
    
    updated_apartments = []
    
    for i, filename in enumerate(apartment_files, 1):
        apartment_file = os.path.join(appartements_dir, filename)
        apartment_id = filename.replace('.json', '')
        
        print(f"[{i}/{len(apartment_files)}] Appartement {apartment_id}...", end=' ')
        
        result = update_apartment_quartier(apartment_file)
        
        if result['status'] == 'updated':
            stats['updated'] += 1
            updated_apartments.append({
                'id': apartment_id,
                'quartier': result.get('quartier', 'N/A'),
                'method': result.get('method', 'N/A')
            })
            print(f"✅ {result.get('quartier', 'N/A')}")
        elif result['status'] == 'skipped':
            reason = result.get('reason', 'unknown')
            if reason == 'already_identified':
                stats['skipped_already'] += 1
                print(f"⏭️  Déjà identifié: {result.get('quartier', 'N/A')}")
            elif reason == 'no_data':
                stats['skipped_no_data'] += 1
                print("⏭️  Pas de données")
            elif reason == 'not_identifiable':
                stats['skipped_not_identifiable'] += 1
                print("⏭️  Non identifiable")
        elif result['status'] == 'error':
            stats['errors'] += 1
            print(f"❌ Erreur: {result.get('error', 'Unknown')}")
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"Total: {stats['total']}")
    print(f"✅ Mis à jour: {stats['updated']}")
    print(f"⏭️  Déjà identifiés: {stats['skipped_already']}")
    print(f"⏭️  Pas de données: {stats['skipped_no_data']}")
    print(f"⏭️  Non identifiables: {stats['skipped_not_identifiable']}")
    print(f"❌ Erreurs: {stats['errors']}")
    
    if updated_apartments:
        print("\n✅ APPARTEMENTS MIS À JOUR:")
        for apt in updated_apartments:
            print(f"   - {apt['id']}: {apt['quartier']} ({apt['method']})")

if __name__ == "__main__":
    main()





