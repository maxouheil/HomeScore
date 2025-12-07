#!/usr/bin/env python3
"""
Test de l'analyse de style sur 5 appartements
"""

import json
import os
from analyze_apartment_style import ApartmentStyleAnalyzer

def load_apartment(apartment_id):
    """Charge un appartement depuis data/appartements"""
    apartment_file = f"data/appartements/{apartment_id}.json"
    if os.path.exists(apartment_file):
        with open(apartment_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def test_style_analysis():
    """Test l'analyse de style sur 5 appartements"""
    print("=" * 80)
    print("🎨 TEST D'ANALYSE DE STYLE - 5 APPARTEMENTS")
    print("=" * 80)
    print()
    
    # Liste des appartements à tester (ceux qui ont des photos dans photos_v2)
    apartment_ids = [
        "90931157",
        "90129925",
        "85653922",
        "91005791",
        "90466722"
    ]
    
    # Vérifier quels appartements existent réellement
    available_apartments = []
    for apt_id in apartment_ids:
        apt_file = f"data/appartements/{apt_id}.json"
        if os.path.exists(apt_file):
            available_apartments.append(apt_id)
        else:
            # Chercher dans scraped_apartments.json
            print(f"   ⚠️ {apt_id}.json non trouvé, recherche alternative...")
    
    # Si pas assez dans data/appartements, charger depuis scraped_apartments.json
    if len(available_apartments) < 5:
        scraped_file = "data/scraped_apartments.json"
        if os.path.exists(scraped_file):
            with open(scraped_file, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
                # Prendre les 5 premiers qui ont des photos
                for apt in scraped_data:
                    apt_id = apt.get('id')
                    if apt_id and apt_id not in available_apartments:
                        photos = apt.get('photos', [])
                        if photos:
                            available_apartments.append(apt_id)
                            if len(available_apartments) >= 5:
                                break
    
    if len(available_apartments) == 0:
        print("❌ Aucun appartement trouvé pour tester")
        return
    
    # Limiter à 5
    apartment_ids = available_apartments[:5]
    
    print(f"📋 {len(apartment_ids)} appartements à analyser:")
    for apt_id in apartment_ids:
        print(f"   - {apt_id}")
    print()
    
    # Initialiser l'analyseur
    analyzer = ApartmentStyleAnalyzer()
    
    if not analyzer.openai_api_key or analyzer.openai_api_key == 'votre_clé_openai':
        print("❌ Clé API OpenAI non configurée")
        print("   Configurez OPENAI_API_KEY dans le fichier .env")
        return
    
    results = []
    
    # Analyser chaque appartement
    for i, apartment_id in enumerate(apartment_ids, 1):
        print("\n" + "=" * 80)
        print(f"🏠 APPARTEMENT {i}/{len(apartment_ids)}: {apartment_id}")
        print("=" * 80)
        
        # Charger les données de l'appartement
        apartment_data = load_apartment(apartment_id)
        if not apartment_data:
            # Essayer depuis scraped_apartments.json
            scraped_file = "data/scraped_apartments.json"
            if os.path.exists(scraped_file):
                with open(scraped_file, 'r', encoding='utf-8') as f:
                    scraped_data = json.load(f)
                    for apt in scraped_data:
                        if apt.get('id') == apartment_id:
                            apartment_data = apt
                            break
        
        if not apartment_data:
            print(f"   ❌ Appartement {apartment_id} non trouvé")
            continue
        
        print(f"   📍 Localisation: {apartment_data.get('localisation', 'N/A')}")
        print(f"   💰 Prix: {apartment_data.get('prix', 'N/A')}")
        print(f"   📐 Surface: {apartment_data.get('surface', 'N/A')}")
        
        # Vérifier les photos locales
        photos_dir_v2 = f"data/photos/{apartment_id}"
        photos_dir = f"data/photos/{apartment_id}"
        has_local_photos = os.path.exists(photos_dir_v2) or os.path.exists(photos_dir)
        
        if has_local_photos:
            print(f"   ✅ Photos locales trouvées")
        else:
            photos = apartment_data.get('photos', [])
            print(f"   📸 {len(photos)} photos dans les données (téléchargement nécessaire)")
        
        # Analyser le style
        try:
            style_analysis = analyzer.analyze_apartment_photos_from_data(apartment_data)
            
            if style_analysis:
                print(f"\n   🎯 RÉSULTATS:")
                style = style_analysis.get('style', {})
                cuisine = style_analysis.get('cuisine', {})
                luminosite = style_analysis.get('luminosite', {})
                
                print(f"      🏛️  STYLE: {style.get('type', 'N/A').upper()}")
                print(f"         Score: {style.get('score', 0)}/20")
                print(f"         Confiance: {style.get('confidence', 0):.2f}")
                print(f"         Détails: {style.get('details', 'N/A')}")
                
                print(f"      🍳 CUISINE: {'OUVERTE' if cuisine.get('ouverte', False) else 'FERMÉE'}")
                print(f"         Score: {cuisine.get('score', 0)}/10")
                print(f"         Confiance: {cuisine.get('confidence', 0):.2f}")
                
                print(f"      💡 LUMINOSITÉ: {luminosite.get('type', 'N/A').upper()}")
                print(f"         Score: {luminosite.get('score', 0)}/10")
                print(f"         Confiance: {luminosite.get('confidence', 0):.2f}")
                
                print(f"      📸 Photos analysées: {style_analysis.get('photos_analyzed', 0)}")
                
                results.append({
                    'apartment_id': apartment_id,
                    'style_analysis': style_analysis,
                    'success': True
                })
            else:
                print(f"   ❌ Aucune analyse de style retournée")
                results.append({
                    'apartment_id': apartment_id,
                    'style_analysis': None,
                    'success': False
                })
        
        except Exception as e:
            print(f"   ❌ Erreur lors de l'analyse: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'apartment_id': apartment_id,
                'style_analysis': None,
                'success': False,
                'error': str(e)
            })
    
    # Résumé final
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES RÉSULTATS")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r.get('success', False))
    print(f"\n✅ Réussis: {success_count}/{len(results)}")
    print(f"❌ Échecs: {len(results) - success_count}/{len(results)}")
    
    if success_count > 0:
        print(f"\n📈 STYLES DÉTECTÉS:")
        styles_detected = {}
        for r in results:
            if r.get('success'):
                style_type = r.get('style_analysis', {}).get('style', {}).get('type', 'inconnu')
                styles_detected[style_type] = styles_detected.get(style_type, 0) + 1
        
        for style_type, count in styles_detected.items():
            print(f"   - {style_type}: {count}")
        
        # Sauvegarder les résultats
        output_file = "data/test_style_analysis_results.json"
        os.makedirs("data", exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvegardés dans {output_file}")
    
    print("\n✅ Test terminé!")

if __name__ == "__main__":
    test_style_analysis()

