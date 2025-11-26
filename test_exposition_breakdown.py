#!/usr/bin/env python3
"""
Script de test pour analyser le breakdown d'exposition de 3 appartements spécifiques
"""

import json
import sys
sys.path.append('.')

from extract_exposition import ExpositionExtractor

def test_exposition_breakdown():
    """Test le breakdown d'exposition pour 3 appartements"""
    
    # Charger les données
    with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # IDs trouvés
    apt_ids = {
        '749k_belleville': '85653922',
        '750k_belleville': '89529151',
        '754k_roquette': '92274287'
    }
    
    extractor = ExpositionExtractor()
    
    for key, apt_id in apt_ids.items():
        apt = next((a for a in data if a.get('id') == apt_id), None)
        if not apt:
            print(f"❌ Appartement {apt_id} non trouvé")
            continue
        
        print(f"\n{'='*80}")
        print(f"🏠 APPARTEMENT: {key.upper()}")
        print(f"{'='*80}")
        print(f"ID: {apt.get('id')}")
        print(f"Prix: {apt.get('prix')}")
        print(f"Quartier: {apt.get('map_info', {}).get('quartier', 'N/A')}")
        print(f"{'-'*80}\n")
        
        description = apt.get('description', '')
        caracteristiques = apt.get('caracteristiques', '')
        etage = apt.get('etage', '')
        photos = apt.get('photos', [])
        photos_urls = [p.get('url') if isinstance(p, dict) else p for p in photos[:5]]
        
        print(f"📝 Description (extrait): {description[:200]}...")
        print(f"📋 Caractéristiques: {caracteristiques}")
        print(f"🏢 Étage: {etage if etage else 'Non spécifié'}")
        print(f"📸 Photos disponibles: {len(photos_urls)}\n")
        
        # Analyser l'exposition
        try:
            result = extractor.extract_exposition_complete(description, caracteristiques, photos_urls, etage)
            
            if not result:
                print("❌ Aucun résultat d'exposition")
                continue
            
            print(f"📊 RÉSULTAT EXPOSITION:")
            print(f"   ✅ Exposition: {result.get('exposition', 'N/A')}")
            print(f"   ✅ Score: {result.get('score', 0)}/10")
            print(f"   ✅ Tier: {result.get('tier', 'N/A')}")
            print(f"   ✅ Justification: {result.get('justification', 'N/A')}")
            
            details = result.get('details', {})
            print(f"\n🔍 BREAKDOWN DÉTAILLÉ DU CALCUL:")
            print(f"   📍 Score exposition (orientation): {details.get('exposition_score', 0)}/10")
            print(f"   💡 Score luminosité: {details.get('luminosite_score', 0)}/10")
            print(f"   👁️  Score vue: {details.get('vue_score', 0)}/10")
            print(f"   🎯 Score base (MAX des 3): {details.get('score_base', 0)}/10")
            print(f"   🏢 Bonus étage >=4: +{details.get('bonus_etage', 0)}")
            print(f"   📊 Score total final: {result.get('score', 0)}/10")
            
            ai_analysis = details.get('ai_analysis', {})
            if ai_analysis:
                print(f"\n🤖 ANALYSE IA TEXTUELLE:")
                print(f"   - Confiance globale: {ai_analysis.get('confiance_globale', 0):.0%}")
                print(f"   - Confiance exposition: {ai_analysis.get('confiance_exposition', 0):.0%}")
                print(f"   - Exposition explicite: {result.get('exposition_explicite', False)}")
                
                etage_info = ai_analysis.get('etage_analyse', {})
                if etage_info.get('etage_trouve'):
                    print(f"   - Étage détecté: {etage_info.get('etage_trouve')}")
                    print(f"     → Impact luminosité: {etage_info.get('impact_luminosite', 'N/A')}")
                
                vue_info = ai_analysis.get('vue_mentionnee', {})
                if vue_info.get('vue_trouvee'):
                    print(f"   - Vue mentionnée: {vue_info.get('type_vue', 'N/A')}")
                    print(f"     → Impact luminosité: {vue_info.get('impact_luminosite', 'N/A')}")
                
                indices = ai_analysis.get('indices_trouves', [])
                if indices:
                    print(f"   - Indices trouvés: {', '.join(indices[:5])}")
            
            # Vérifier si analyse visuelle a été faite
            photo_validation = details.get('photo_validation')
            indices_precis = result.get('indices_precis', {})
            if photo_validation or indices_precis:
                print(f"\n📸 ANALYSE VISUELLE:")
                print(f"   - Photos analysées: {result.get('photos_analyzed', 0)}")
                if indices_precis:
                    print(f"   - Indices visuels détectés:")
                    for indice_name, indice_data in indices_precis.items():
                        if isinstance(indice_data, dict) and indice_data.get('present'):
                            conf = indice_data.get('confiance', 0)
                            if indice_name == 'exposition_image':
                                print(f"     • Exposition dans image: {indice_data.get('orientation', 'N/A')} ({conf:.0%})")
                            elif indice_name == 'grandes_fenetres':
                                print(f"     • Grandes fenêtres: Oui ({conf:.0%})")
                            elif indice_name == 'pas_vis_a_vis':
                                print(f"     • Pas de vis-à-vis: Oui ({conf:.0%})")
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n{'='*80}\n")

if __name__ == "__main__":
    test_exposition_breakdown()









