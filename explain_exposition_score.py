#!/usr/bin/env python3
"""
Script pour expliquer le calcul de la note d'exposition
"""

import json
from extract_exposition import ExpositionExtractor

# Charger les données de l'appartement
with open('data/appartements/85653922.json', 'r') as f:
    apartment = json.load(f)

print("=" * 70)
print("🏠 EXPLICATION DE LA NOTE D'EXPOSITION")
print("=" * 70)
print(f"\n📍 Appartement: {apartment['titre']}")
print(f"💰 Prix: {apartment['prix']}")
print(f"📍 Localisation: {apartment['localisation']}")
print(f"🏘️ Quartier: {apartment['map_info']['quartier']}")
print(f"📐 Surface: {apartment['surface']}")
print(f"🏢 Étage: {apartment.get('etage', 'Non spécifié')}")
print(f"📝 Caractéristiques: {apartment['caracteristiques']}")
print(f"\n📄 Description (extrait): {apartment['description'][:200]}...")

print("\n" + "=" * 70)
print("🔍 ANALYSE D'EXPOSITION")
print("=" * 70)

# Analyser avec le nouveau système
extractor = ExpositionExtractor()

description = apartment.get('description', '')
caracteristiques = apartment.get('caracteristiques', '')
etage_text = apartment.get('etage', '')
photos = [p['url'] for p in apartment.get('photos', [])]

print("\n📝 PHASE 1 : Analyse Textuelle")
print("-" * 70)

text_result = extractor.extract_exposition_textuelle(description, caracteristiques, etage_text)

print(f"✅ Exposition trouvée dans le texte: {text_result.get('exposition')}")
print(f"✅ Exposition explicite: {text_result.get('exposition_explicite', False)}")
print(f"📊 Score base: {text_result.get('details', {}).get('exposition_score', 0)}")
print(f"📊 Luminosité score: {text_result.get('details', {}).get('luminosite_score', 0)}")
print(f"📊 Vue score: {text_result.get('details', {}).get('vue_score', 0)}")
print(f"📊 Score base (max): {text_result.get('details', {}).get('score_base', 0)}")
print(f"➕ Bonus étage: +{text_result.get('bonus_etage', 0)}")
print(f"📊 Score total: {text_result.get('score', 0)}/10")
print(f"🏆 Tier: {text_result.get('tier', 'tier3')}")
print(f"💬 Justification: {text_result.get('justification', '')}")

if text_result.get('exposition_explicite', False):
    print("\n✅ EXPOSITION EXPLICITE TROUVÉE → Retour direct (pas d'analyse photos/contextuel)")
else:
    print("\n⚠️ Pas d'exposition explicite → Analyse photos...")
    
    if photos:
        print(f"\n📸 PHASE 2 : Analyse Photos ({len(photos)} photos disponibles)")
        print("-" * 70)
        photo_result = extractor.extract_exposition_photos(photos[:3])
        
        if photo_result.get('photos_analyzed', 0) > 0:
            print(f"✅ Photos analysées: {photo_result.get('photos_analyzed', 0)}")
            print(f"📊 Exposition détectée: {photo_result.get('exposition')}")
            print(f"📊 Score: {photo_result.get('score', 0)}/10")
            print(f"🏆 Tier: {photo_result.get('tier', 'tier3')}")
            print(f"💬 Justification: {photo_result.get('justification', '')}")
            
            details = photo_result.get('details', {})
            if details:
                print(f"\n📊 Détails du score:")
                print(f"   - Exposition (30%): {details.get('exposition_score', 0)}")
                print(f"   - Luminosité (30%): {details.get('luminosite_score', 0):.1f}")
                print(f"   - Fenêtres (20%): {details.get('fenetres_score', 0):.1f}")
                print(f"   - Vue (20%): {details.get('vue_score', 0):.1f}")
                print(f"   - Bonus balcon: +{details.get('balcon_bonus', 0)}")
                print(f"   - Score pondéré: {photo_result.get('score', 0)}/10")
        else:
            print("❌ Aucune photo analysée avec succès")
            print("→ Passage à l'analyse contextuelle...")
    
    print("\n🏘️ PHASE 3 : Analyse Contextuelle (dernier recours)")
    print("-" * 70)
    contextual_result = extractor.extract_exposition_contextual(apartment)
    print(f"📊 Exposition estimée: {contextual_result.get('exposition')}")
    print(f"📊 Score: {contextual_result.get('score', 0)}/10")
    print(f"📊 Confiance: {contextual_result.get('confidence', 0):.2f}")
    print(f"💬 Justification: {contextual_result.get('justification', '')}")

print("\n" + "=" * 70)
print("📊 RÉSULTAT FINAL")
print("=" * 70)

final_result = extractor.extract_exposition_ultimate(apartment)

print(f"\n✅ Exposition finale: {final_result.get('exposition')}")
print(f"📊 Score final: {final_result.get('score', 0)}/10")
print(f"🏆 Tier: {final_result.get('tier', 'tier3')}")
print(f"💬 Justification: {final_result.get('justification', '')}")

if final_result.get('exposition_explicite'):
    print(f"\n✨ Cet appartement a une exposition EXPLICITE mentionnée dans le texte")
    print(f"   → Priorité absolue donnée à cette information")
    print(f"   → Les photos et l'analyse contextuelle n'ont PAS été utilisées")

print("\n" + "=" * 70)
print("💡 EXPLICATION DU CALCUL")
print("=" * 70)

if final_result.get('exposition_explicite'):
    print("""
1. ✅ EXPOSITION EXPLICITE DÉTECTÉE dans le texte
   → Le système a trouvé "est" (Est) dans la description/caractéristiques
   
2. 📊 SCORE BASE
   → Exposition Est = 7 points (tier2)
   
3. ➕ BONUS ÉTAGE
   → 4ème étage détecté
   → Bonus de +1 point (étage >= 4)
   
4. 📊 SCORE TOTAL
   → 7 (exposition) + 1 (bonus étage) = 8 points
   → Score limité à 10 max → 8 points
   → Tier: tier2 (score entre 7 et 9)
   
5. ✅ RÉSULTAT FINAL
   → Exposition: Est
   → Score: 8/10
   → Tier: tier2
    """)
else:
    print("""
Le calcul dépend de la méthode utilisée (photos ou contextuel).
Voir les détails ci-dessus pour comprendre le calcul exact.
    """)










