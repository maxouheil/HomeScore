#!/usr/bin/env python3
"""
Exemple complet d'utilisation de Gemini pour l'analyse visuelle d'appartements
"""

import os
import json
from pathlib import Path
from gemini_analyzer import (
    GeminiAnalyzer,
    analyze_apartment_style,
    detect_bathtub,
    detect_open_kitchen,
    estimate_ceiling_height,
    analyze_living_room_size,
    estimate_distance_vis_a_vis
)

def exemple_analyse_complete():
    """Exemple d'analyse complète d'un appartement"""
    
    print("=" * 60)
    print("🏠 EXEMPLE D'ANALYSE COMPLÈTE D'APPARTEMENT")
    print("=" * 60)
    
    # Initialiser l'analyseur
    analyzer = GeminiAnalyzer('gemini-1.5-flash')
    print(f"\n✅ Analyseur initialisé: {analyzer.model_name}")
    print(f"💰 Coût par image: ${analyzer.cost_per_image:.6f}")
    
    # Exemple avec des chemins d'images (à adapter selon vos données)
    # Remplacez par de vrais chemins d'images de votre projet
    exemple_images = [
        "data/calme/example1.jpg",  # À remplacer
        "data/calme/example2.jpg",  # À remplacer
    ]
    
    # Filtrer les images qui existent vraiment
    images_existantes = [img for img in exemple_images if Path(img).exists()]
    
    if not images_existantes:
        print("\n⚠️  Aucune image d'exemple trouvée")
        print("💡 Modifiez les chemins dans le script pour tester avec de vraies images")
        print("\n📋 Voici les fonctions disponibles:\n")
        afficher_fonctions_disponibles()
        return
    
    print(f"\n📸 Images trouvées: {len(images_existantes)}")
    
    # 1. Analyse du style
    print("\n" + "-" * 60)
    print("1️⃣  ANALYSE DU STYLE")
    print("-" * 60)
    try:
        style_result = analyze_apartment_style(images_existantes[:3])  # Max 3 images
        print(json.dumps(style_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 2. Détection baignoire (si image de salle de bain disponible)
    print("\n" + "-" * 60)
    print("2️⃣  DÉTECTION BAIGNOIRE")
    print("-" * 60)
    # Exemple avec la première image (à adapter)
    try:
        baignoire_result = detect_bathtub(images_existantes[0])
        print(json.dumps(baignoire_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 3. Détection cuisine ouverte
    print("\n" + "-" * 60)
    print("3️⃣  DÉTECTION CUISINE OUVERTE")
    print("-" * 60)
    try:
        cuisine_result = detect_open_kitchen(images_existantes[0])
        print(json.dumps(cuisine_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 4. Estimation hauteur plafond
    print("\n" + "-" * 60)
    print("4️⃣  ESTIMATION HAUTEUR PLAFOND")
    print("-" * 60)
    try:
        hauteur_result = estimate_ceiling_height(images_existantes[0])
        print(json.dumps(hauteur_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # 5. Analyse taille pièce de vie
    print("\n" + "-" * 60)
    print("5️⃣  ANALYSE TAILLE PIÈCE DE VIE")
    print("-" * 60)
    try:
        piece_result = analyze_living_room_size(images_existantes[0])
        print(json.dumps(piece_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Résumé des coûts
    print("\n" + "=" * 60)
    print("💰 RÉSUMÉ DES COÛTS")
    print("=" * 60)
    num_analyses = 5  # Nombre d'analyses effectuées
    total_cost = analyzer.estimate_cost(num_analyses)
    print(f"Nombre d'analyses: {num_analyses}")
    print(f"Coût total estimé: ${total_cost:.6f}")
    print(f"Coût par analyse: ${analyzer.cost_per_image:.6f}")


def exemple_analyse_custom():
    """Exemple d'analyse personnalisée"""
    
    print("\n" + "=" * 60)
    print("🎨 EXEMPLE D'ANALYSE PERSONNALISÉE")
    print("=" * 60)
    
    analyzer = GeminiAnalyzer('gemini-1.5-flash')
    
    # Exemple d'image (à remplacer)
    image_path = "data/calme/example.jpg"
    
    if not Path(image_path).exists():
        print(f"\n⚠️  Image non trouvée: {image_path}")
        print("💡 Créez votre propre prompt personnalisé:")
        print("""
analyzer = GeminiAnalyzer('gemini-1.5-flash')
result = analyzer.analyze_image(
    image_path="votre_image.jpg",
    prompt="Votre question ou instruction ici",
    return_json=True  # ou False pour texte libre
)
        """)
        return
    
    # Prompt personnalisé
    custom_prompt = """
    Analyse cette photo d'appartement et réponds en JSON avec:
    - nombre_pieces_visibles (nombre)
    - presence_balcon (oui/non)
    - etat_general (excellent, bon, moyen, à rénover)
    - points_positifs (liste)
    - points_negatifs (liste)
    """
    
    try:
        result = analyzer.analyze_image(image_path, custom_prompt, return_json=True)
        print("\n✅ Résultat:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ Erreur: {e}")


def afficher_fonctions_disponibles():
    """Affiche la liste des fonctions disponibles"""
    
    fonctions = [
        ("analyze_apartment_style", "Analyse le style d'un appartement (plusieurs photos)"),
        ("detect_bathtub", "Détecte la présence d'une baignoire"),
        ("detect_open_kitchen", "Détecte si la cuisine est ouverte"),
        ("estimate_ceiling_height", "Estime la hauteur sous plafond"),
        ("analyze_living_room_size", "Analyse la taille de la pièce de vie"),
        ("estimate_distance_vis_a_vis", "Estime la distance vis-à-vis"),
    ]
    
    print("📚 Fonctions disponibles dans gemini_analyzer:\n")
    for func_name, description in fonctions:
        print(f"  • {func_name}")
        print(f"    {description}\n")
    
    print("\n💡 Utilisation:")
    print("""
from gemini_analyzer import detect_bathtub

result = detect_bathtub("chemin/vers/image.jpg")
print(result)
    """)


def exemple_batch_analysis():
    """Exemple d'analyse en batch de plusieurs appartements"""
    
    print("\n" + "=" * 60)
    print("📦 EXEMPLE D'ANALYSE EN BATCH")
    print("=" * 60)
    
    analyzer = GeminiAnalyzer('gemini-1.5-flash')
    
    # Exemple: analyser plusieurs appartements
    # Dans votre cas réel, vous itéreriez sur vos données
    appartements = [
        {"id": "apt1", "images": ["img1.jpg", "img2.jpg"]},
        {"id": "apt2", "images": ["img3.jpg", "img4.jpg"]},
    ]
    
    print("\n💡 Structure pour analyse en batch:\n")
    print("""
analyzer = GeminiAnalyzer('gemini-1.5-flash')
results = []

for apt in appartements:
    try:
        # Analyser le style
        style = analyze_apartment_style(apt['images'])
        
        # Détecter baignoire (si salle de bain disponible)
        baignoire = detect_bathtub(apt['images'][0])
        
        results.append({
            'apartment_id': apt['id'],
            'style': style,
            'bathtub': baignoire
        })
    except Exception as e:
        print(f"Erreur pour {apt['id']}: {e}")

# Sauvegarder les résultats
with open('results.json', 'w') as f:
    json.dump(results, f, indent=2)
    """)
    
    # Estimation des coûts
    num_apartments = 100
    images_per_apt = 3
    total_images = num_apartments * images_per_apt
    
    print(f"\n💰 Estimation pour {num_apartments} appartements:")
    print(f"   Images par appartement: {images_per_apt}")
    print(f"   Total images: {total_images}")
    print(f"   Coût estimé: ${analyzer.estimate_cost(total_images):.4f}")


if __name__ == "__main__":
    print("\n🚀 EXEMPLES D'UTILISATION GEMINI ANALYZER\n")
    
    # Vérifier la clé API
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY non trouvée")
        print("   Créez un fichier .env avec GEMINI_API_KEY=votre_cle")
        exit(1)
    
    # Exécuter les exemples
    try:
        exemple_analyse_complete()
        exemple_analyse_custom()
        exemple_batch_analysis()
        
        print("\n" + "=" * 60)
        print("✅ EXEMPLES TERMINÉS")
        print("=" * 60)
        print("\n💡 Prochaines étapes:")
        print("   1. Adaptez les chemins d'images à vos données")
        print("   2. Intégrez Gemini dans votre code existant")
        print("   3. Remplacez progressivement OpenAI par Gemini")
        print("   4. Économisez 96% sur vos coûts d'analyse ! 🎉")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

