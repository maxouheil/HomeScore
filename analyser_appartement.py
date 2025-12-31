#!/usr/bin/env python3
"""
Script pour analyser un appartement spécifique avec Gemini
"""

import os
import json
import sys
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


def trouver_appartement_par_titre(titre_recherche: str, fichier_donnees: str = None):
    """
    Trouve un appartement par son titre dans les fichiers de données
    
    Args:
        titre_recherche: Titre ou partie du titre à rechercher
        fichier_donnees: Chemin vers le fichier JSON (optionnel)
    
    Returns:
        Dictionnaire avec les données de l'appartement ou None
    """
    from project_config import APARTMENTS_FILE
    
    # Chercher d'abord dans le fichier source standard depuis PROJECT_ROOT
    fichier_source = str(APARTMENTS_FILE)
    if os.path.exists(fichier_source):
        try:
            with open(fichier_source, 'r', encoding='utf-8') as f:
                data_source = json.load(f)
            
            # Chercher dans le fichier source
            if isinstance(data_source, list):
                appartements_source = data_source
            elif isinstance(data_source, dict):
                appartements_source = list(data_source.values())
            else:
                appartements_source = []
            
            titre_lower = titre_recherche.lower()
            for apt in appartements_source:
                titre = apt.get('titre', '').lower()
                apt_id = str(apt.get('id', ''))
                localisation = apt.get('localisation', '').lower()
                
                # Rechercher dans le titre, l'ID ou la localisation
                if (titre_lower in titre or titre_lower in apt_id or 
                    'goncourt' in titre or 'goncourt' in localisation or
                    'hôpital' in titre or 'hopital' in titre or 
                    'hôpital' in localisation or 'hopital' in localisation or
                    'saint-louis' in titre or 'saint-louis' in localisation):
                    return apt
        except Exception as e:
            print(f"⚠️ Erreur lors de la lecture du fichier source: {e}")
    
    # Si un fichier personnalisé est fourni, l'utiliser
    if fichier_donnees and os.path.exists(fichier_donnees):
        try:
            with open(fichier_donnees, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Chercher dans les détails par appartement
            if 'details_par_appartement' in data:
                appartements = data['details_par_appartement']
            elif isinstance(data, list):
                appartements = data
            else:
                return None
            
            titre_lower = titre_recherche.lower()
            for apt in appartements:
                titre = apt.get('titre', '').lower()
                apt_id = str(apt.get('id', ''))
                
                # Rechercher dans le titre ou l'ID
                if titre_lower in titre or titre_lower in apt_id or 'goncourt' in titre or 'hôpital' in titre or 'hopital' in titre:
                    return apt
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la lecture de {fichier_donnees}: {e}")
    
    return None


def analyser_appartement_complet(apt_data: dict, photos: list = None):
    """
    Lance une analyse complète d'un appartement
    
    Args:
        apt_data: Données de l'appartement
        photos: Liste des URLs ou chemins vers les photos (optionnel)
    """
    print("=" * 80)
    print(f"🏠 ANALYSE DE L'APPARTEMENT")
    print("=" * 80)
    print(f"ID: {apt_data.get('id', 'N/A')}")
    print(f"Titre: {apt_data.get('titre', 'N/A')}")
    print(f"URL: {apt_data.get('url', 'N/A')}")
    print()
    
    # Si pas de photos fournies, essayer de les récupérer depuis les données
    if not photos:
        photos_raw = apt_data.get('photos', [])
        if photos_raw:
            # Extraire les URLs ou chemins locaux depuis la structure des photos
            photos = []
            for photo in photos_raw:
                if isinstance(photo, dict):
                    # Priorité au chemin local s'il existe et que le fichier existe
                    local_path = photo.get('local_path', '')
                    if local_path:
                        # Essayer le chemin tel quel
                        if os.path.exists(local_path):
                            photos.append(local_path)
                        else:
                            # Essayer depuis PROJECT_ROOT
                            from project_config import PROJECT_ROOT
                            project_path = PROJECT_ROOT / local_path
                            if project_path.exists():
                                photos.append(str(project_path))
                            else:
                                # Sinon utiliser l'URL
                                photo_url = photo.get('url', '')
                                if photo_url:
                                    photos.append(photo_url)
                    else:
                        # Sinon utiliser l'URL
                        photo_url = photo.get('url', '')
                        if photo_url:
                            photos.append(photo_url)
                elif isinstance(photo, str):
                    # Si c'est directement une URL ou un chemin
                    photos.append(photo)
        
        if not photos:
            # Essayer de trouver les photos dans les analyses existantes
            analyses = apt_data.get('analyses', {})
            for analyse_type, analyse_data in analyses.items():
                if 'photos' in analyse_data:
                    photos_list = analyse_data['photos']
                    if isinstance(photos_list, list):
                        photos.extend(photos_list)
    
    if not photos:
        print("⚠️  Aucune photo trouvée pour cet appartement")
        print("💡 Vous pouvez fournir les URLs des photos en argument:")
        print("   python analyser_appartement.py 'titre' url1 url2 url3 ...")
        return
    
    print(f"📸 Photos trouvées: {len(photos)}")
    print()
    
    # Initialiser l'analyseur
    analyzer = GeminiAnalyzer('gemini-2.5-flash')
    print(f"✅ Analyseur initialisé: {analyzer.model_name}")
    print(f"💰 Coût par image: ${analyzer.cost_per_image:.6f}")
    print()
    
    # Extraire la surface totale depuis les données
    surface_totale = None
    surface_str = apt_data.get('surface', '')
    if surface_str:
        try:
            # Extraire le nombre depuis une chaîne comme "48 m²"
            import re
            match = re.search(r'(\d+(?:\.\d+)?)', str(surface_str))
            if match:
                surface_totale = float(match.group(1))
        except:
            pass
    
    results = {
        'apartment_id': apt_data.get('id'),
        'titre': apt_data.get('titre'),
        'url': apt_data.get('url'),
        'surface_totale_m2': surface_totale,
        'analyses': {}
    }
    
    # 1. Analyse du style (premières 3 photos)
    print("-" * 80)
    print("1️⃣  ANALYSE DU STYLE")
    print("-" * 80)
    try:
        style_photos = photos[:3]  # Limiter à 3 photos pour le style
        style_result = analyze_apartment_style(style_photos)
        results['analyses']['style'] = style_result
        
        # Afficher de manière lisible
        classification = style_result.get('classification_style', 'N/A')
        indice = style_result.get('indice_style', 'N/A')
        print(f"Classification: {classification}")
        print(f"Indice style: {indice}/100")
        print(f"Hauteur plafond estimée: {style_result.get('hauteur_plafond_estimee', 'N/A')} m")
        print(f"Ambiance: {style_result.get('ambiance', 'N/A')}")
        print(f"Matériau dominant: {style_result.get('materiau_dominant', 'N/A')}")
        print(f"Pièces visibles: {', '.join(style_result.get('type_pieces_visibles', []))}")
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse du style: {e}")
        results['analyses']['style'] = {'error': str(e)}
    
    print()
    
    # 2. Détection baignoire (analyser toutes les images pour trouver sur quelle image)
    print("-" * 80)
    print("2️⃣  DÉTECTION BAIGNOIRE")
    print("-" * 80)
    baignoire_trouvee = False
    try:
        for idx, photo in enumerate(photos, 1):
            baignoire_result = detect_bathtub(photo)
            if baignoire_result.get('presence_baignoire', '').lower() == 'oui':
                baignoire_trouvee = True
                baignoire_result['image_detectee'] = idx
                results['analyses']['baignoire'] = baignoire_result
                print(f"✅ Baignoire détectée sur l'image {idx}")
                print(f"   Type: {baignoire_result.get('type_baignoire', 'N/A')}")
                print(f"   Confiance: {baignoire_result.get('confiance', 'N/A')}%")
                break
        
        if not baignoire_trouvee:
            results['analyses']['baignoire'] = {'presence_baignoire': 'non', 'image_detectee': None}
            print("❌ Aucune baignoire détectée")
    except Exception as e:
        print(f"❌ Erreur lors de la détection de baignoire: {e}")
        results['analyses']['baignoire'] = {'error': str(e)}
    
    print()
    
    # 3. Détection cuisine ouverte (analyser toutes les images pour trouver sur quelle image)
    print("-" * 80)
    print("3️⃣  DÉTECTION CUISINE OUVERTE")
    print("-" * 80)
    cuisine_trouvee = False
    try:
        for idx, photo in enumerate(photos, 1):
            cuisine_result = detect_open_kitchen(photo)
            if cuisine_result.get('cuisine_ouverte', '').lower() == 'oui':
                cuisine_trouvee = True
                cuisine_result['image_detectee'] = idx
                results['analyses']['cuisine'] = cuisine_result
                print(f"✅ Cuisine ouverte détectée sur l'image {idx}")
                print(f"   Type: {cuisine_result.get('type_cuisine', 'N/A')}")
                print(f"   Confiance: {cuisine_result.get('confiance', 'N/A')}%")
                break
        
        if not cuisine_trouvee:
            results['analyses']['cuisine'] = {'cuisine_ouverte': 'non', 'image_detectee': None}
            print("❌ Cuisine ouverte non détectée")
    except Exception as e:
        print(f"❌ Erreur lors de la détection de cuisine: {e}")
        results['analyses']['cuisine'] = {'error': str(e)}
    
    print()
    
    # 4. Luminosité avec distance vis-à-vis (chercher une photo avec fenêtre)
    print("-" * 80)
    print("4️⃣  LUMINOSITÉ ET DISTANCE VIS-À-VIS")
    print("-" * 80)
    try:
        # Chercher une photo avec fenêtre (priorité aux premières photos)
        vis_a_vis_result = None
        for idx, photo in enumerate(photos[:5], 1):  # Limiter à 5 premières photos
            try:
                vis_a_vis_result = estimate_distance_vis_a_vis(photo)
                if vis_a_vis_result.get('distance_estimee_m'):
                    vis_a_vis_result['image_utilisee'] = idx
                    break
            except:
                continue
        
        if vis_a_vis_result and vis_a_vis_result.get('distance_estimee_m'):
            results['analyses']['luminosite'] = vis_a_vis_result
            print(f"Distance vis-à-vis: {vis_a_vis_result.get('distance_estimee_m', 'N/A')} m")
            print(f"Type vis-à-vis: {vis_a_vis_result.get('type_vis_a_vis', 'N/A')}")
            print(f"Luminosité impactée: {vis_a_vis_result.get('luminosite_impactee', 'N/A')}")
            print(f"Confiance: {vis_a_vis_result.get('confiance', 'N/A')}%")
            print(f"Image utilisée: {vis_a_vis_result.get('image_utilisee', 'N/A')}")
        else:
            results['analyses']['luminosite'] = {'error': 'Aucune fenêtre détectée pour estimer le vis-à-vis'}
            print("⚠️ Impossible d'estimer la distance vis-à-vis (aucune fenêtre détectée)")
    except Exception as e:
        print(f"❌ Erreur lors de l'estimation du vis-à-vis: {e}")
        results['analyses']['luminosite'] = {'error': str(e)}
    
    print()
    
    # 5. Estimation hauteur plafond
    print("-" * 80)
    print("5️⃣  ESTIMATION HAUTEUR PLAFOND")
    print("-" * 80)
    try:
        hauteur_result = estimate_ceiling_height(photos[0])
        results['analyses']['hauteur_plafond'] = hauteur_result
        print(f"Hauteur estimée: {hauteur_result.get('hauteur_estimee', 'N/A')} m")
        print(f"Confiance: {hauteur_result.get('confiance', 'N/A')}%")
    except Exception as e:
        print(f"❌ Erreur lors de l'estimation de la hauteur: {e}")
        results['analyses']['hauteur_plafond'] = {'error': str(e)}
    
    print()
    
    # 6. Analyse pièce de vie avec pourcentage
    print("-" * 80)
    print("6️⃣  ANALYSE PIÈCE DE VIE")
    print("-" * 80)
    try:
        # Chercher une photo de pièce de vie (salon/séjour)
        piece_vie_result = None
        for idx, photo in enumerate(photos[:5], 1):
            try:
                piece_vie_result = analyze_living_room_size(photo, surface_totale)
                if piece_vie_result.get('surface_estimee_m2'):
                    piece_vie_result['image_utilisee'] = idx
                    break
            except:
                continue
        
        if piece_vie_result:
            results['analyses']['piece_de_vie'] = piece_vie_result
            print(f"Surface estimée: {piece_vie_result.get('surface_estimee_m2', 'N/A')} m²")
            if surface_totale and piece_vie_result.get('pourcentage_surface_totale'):
                print(f"Pourcentage sur surface totale ({surface_totale} m²): {piece_vie_result.get('pourcentage_surface_totale')}%")
            print(f"Taille: {piece_vie_result.get('taille_estimee', 'N/A')}")
            print(f"Confiance: {piece_vie_result.get('confiance', 'N/A')}%")
            print(f"Image utilisée: {piece_vie_result.get('image_utilisee', 'N/A')}")
        else:
            results['analyses']['piece_de_vie'] = {'error': 'Impossible d\'estimer la surface'}
            print("⚠️ Impossible d'estimer la surface de la pièce de vie")
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse de la pièce de vie: {e}")
        results['analyses']['piece_de_vie'] = {'error': str(e)}
    
    print()
    
    # Compter le nombre réel d'images analysées (chaque image analysée compte)
    num_images_analyzed = 0
    if 'style' in results['analyses']:
        num_images_analyzed += min(3, len(photos))  # Style utilise 3 images max
    if 'baignoire' in results['analyses']:
        # Compter combien d'images ont été analysées pour trouver la baignoire
        baignoire_img = results['analyses']['baignoire'].get('image_detectee')
        if baignoire_img:
            num_images_analyzed += baignoire_img
        else:
            num_images_analyzed += len(photos)  # Toutes analysées si pas trouvée
    if 'cuisine' in results['analyses']:
        cuisine_img = results['analyses']['cuisine'].get('image_detectee')
        if cuisine_img:
            num_images_analyzed += cuisine_img
        else:
            num_images_analyzed += len(photos)
    if 'luminosite' in results['analyses']:
        num_images_analyzed += results['analyses']['luminosite'].get('image_utilisee', 1)
    if 'hauteur_plafond' in results['analyses']:
        num_images_analyzed += 1
    if 'piece_de_vie' in results['analyses']:
        num_images_analyzed += results['analyses']['piece_de_vie'].get('image_utilisee', 1)
    
    # Résumé des coûts
    print("=" * 80)
    print("💰 RÉSUMÉ DES COÛTS")
    print("=" * 80)
    total_cost = analyzer.estimate_cost(num_images_analyzed)
    print(f"Nombre d'images analysées: {num_images_analyzed}")
    print(f"Coût total estimé: ${total_cost:.6f}")
    print()
    
    # Sauvegarder les résultats
    output_file = f"analyse_{apt_data.get('id', 'unknown')}_{Path(__file__).stem}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"💾 Résultats sauvegardés dans: {output_file}")
    
    return results


def main():
    """Fonction principale"""
    
    # Vérifier la clé API
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY non trouvée")
        print("   Créez un fichier .env avec GEMINI_API_KEY=votre_cle")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python analyser_appartement.py 'titre ou ID' [url_photo1] [url_photo2] ...")
        print("\nExemple:")
        print("  python analyser_appartement.py '770k · Goncourt'")
        print("  python analyser_appartement.py '770k · Goncourt' https://photo1.jpg https://photo2.jpg")
        sys.exit(1)
    
    # Récupérer le titre/ID de recherche
    recherche = sys.argv[1]
    
    # Récupérer les URLs des photos si fournies
    photos = sys.argv[2:] if len(sys.argv) > 2 else None
    
    print(f"🔍 Recherche de l'appartement: '{recherche}'")
    print()
    
    # Chercher l'appartement
    apt_data = trouver_appartement_par_titre(recherche)
    
    if not apt_data:
        print(f"❌ Appartement non trouvé avec la recherche: '{recherche}'")
        print("\n💡 Essayez avec:")
        print("  - Un ID d'appartement")
        print("  - Une partie du titre")
        print("  - Ou fournissez directement les URLs des photos")
        
        if photos:
            print("\n📸 Analyse avec les photos fournies...")
            apt_data = {
                'id': 'custom',
                'titre': recherche,
                'url': '',
                'photos': photos
            }
            analyser_appartement_complet(apt_data, photos)
        else:
            sys.exit(1)
    else:
        print(f"✅ Appartement trouvé!")
        analyser_appartement_complet(apt_data, photos)


if __name__ == "__main__":
    main()

