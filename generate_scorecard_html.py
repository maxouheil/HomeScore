#!/usr/bin/env python3
"""
Génération du rapport HTML avec le design de scorecard
"""

import json
import os
import re
from datetime import datetime

def load_scored_apartments():
    """Charge les appartements scorés"""
    try:
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Fichier de scores non trouvé")
        return []

def get_score_color(score, max_score):
    """Détermine la couleur du score"""
    percentage = (score / max_score) * 100
    if percentage >= 80:
        return "#4CAF50"  # Vert
    elif percentage >= 60:
        return "#FFC107"  # Jaune
    else:
        return "#F44336"  # Rouge

def get_rating_badge(score, max_score):
    """Génère le badge de rating"""
    percentage = (score / max_score) * 100
    if percentage >= 60:
        return '<span class="rating-badge good">GOOD</span>'
    elif percentage >= 40:
        return '<span class="rating-badge moyen">MOYEN</span>'
    else:
        return '<span class="rating-badge faible">BAD</span>'

def get_quartier_name(apartment):
    """Extrait le nom du quartier depuis différentes sources"""
    # Priorité 1: map_info.quartier
    map_info = apartment.get('map_info', {})
    quartier = map_info.get('quartier', '')
    
    # Nettoyer si c'est pas "Quartier non identifié"
    if quartier and quartier != "Quartier non identifié":
        # Enlever "(score: XX)" si présent
        quartier = re.sub(r'\s*\(score:\s*\d+\)', '', quartier).strip()
        if quartier and quartier != "Non identifié":
            return quartier
    
    # Priorité 2: scores_detaille.localisation.justification (extrait par l'IA de scoring)
    scores_detaille = apartment.get('scores_detaille', {})
    localisation_score = scores_detaille.get('localisation', {})
    justification = localisation_score.get('justification', '')
    
    # Chercher "quartier XXX" dans la justification
    quartier_match = re.search(r'quartier\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:[,\.])', justification, re.IGNORECASE)
    if quartier_match:
        quartier = quartier_match.group(1).strip()
        # Vérifier que ce n'est pas un faux positif
        if quartier and len(quartier) > 3 and quartier not in ['Non identifié', 'Non identifiée', 'correcte', 'bonnes zones']:
            return quartier
    
    # Priorité 3: exposition.details.photo_details.quartier
    exposition = apartment.get('exposition', {})
    details = exposition.get('details', {})
    photo_details = details.get('photo_details', {})
    quartier_data = photo_details.get('quartier', {})
    
    if isinstance(quartier_data, dict):
        quartier = quartier_data.get('quartier', '')
        if quartier and quartier not in ['Non identifié', 'Non identifiée']:
            # Enlever les suffixes de proximité
            quartier = re.sub(r'\s*\(proximité\)', '', quartier).strip()
            return quartier
    
    # Fallback: utiliser la localisation si elle contient un quartier spécifique
    localisation = apartment.get('localisation', '')
    # Chercher des patterns de quartiers connus dans la localisation
    quartiers_patterns = [
        r'Buttes[- ]Chaumont', r'Place des Fêtes', r'Place de la Réunion',
        r'Jourdain', r'Pyrénées', r'Belleville', r'Ménilmontant', r'Canal de l\'Ourcq'
    ]
    
    for pattern in quartiers_patterns:
        match = re.search(pattern, localisation, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None

def format_prix_k(prix_str):
    """Convertit un prix en format k€ (ex: "775 000 €" -> "775k")"""
    try:
        # Extraire les chiffres
        prix_clean = re.sub(r'[^\d]', '', prix_str)
        if prix_clean:
            prix_int = int(prix_clean)
            # Convertir en k€
            prix_k = round(prix_int / 1000)
            return f"{prix_k}k"
        return None
    except:
        return None

def get_metro_name(apartment):
    """Extrait le nom du métro depuis différentes sources"""
    # Priorité 1: scores_detaille.localisation.justification (extrait par l'IA de scoring)
    scores_detaille = apartment.get('scores_detaille', {})
    localisation_score = scores_detaille.get('localisation', {})
    justification = localisation_score.get('justification', '')
    
    # Chercher "métro XXX" dans la justification
    # Patterns: "métro Ménilmontant", "métro Rue des Boulets", etc.
    metro_match = re.search(r'métro\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:[,\.]|\s+(?:zone|ligne|arrondissement)|\s*$)', justification, re.IGNORECASE)
    if metro_match:
        metro = metro_match.group(1).strip()
        # Vérifier que ce n'est pas un faux positif
        if metro and len(metro) > 2 and len(metro) < 50 and metro not in ['non trouvé', 'proximité', 'immédiate']:
            return metro
    
    # Chercher des noms de métros connus sans "métro" dans la justification
    # Stations de métro parisiennes communes
    known_metros = [
        'Philippe Auguste', 'Charonne', 'Pyrénées', 'Jourdain', 'Pelleport', 'Gambetta',
        'Ménilmontant', 'Alexandre Dumas', 'Rue des Boulets', 'Belleville', 'Couronnes',
        'Botzaris', 'Buttes-Chaumont', 'Place des Fêtes', 'Rébeval', 'Pyrénées',
        'Goncourt', 'République', 'Nation', 'Bastille', 'Gare de Lyon'
    ]
    for station in known_metros:
        if station in justification:
            return station
    
    # Priorité 2: map_info.metros (première station)
    map_info = apartment.get('map_info', {})
    metros = map_info.get('metros', [])
    if metros and len(metros) > 0:
        metro = metros[0].strip()
        # Nettoyer (enlever "métro " si présent)
        metro = re.sub(r'^métro\s+', '', metro, flags=re.IGNORECASE).strip()
        # Si trop long, extraire juste le nom de la station (avant le premier "-" ou ",")
        if len(metro) > 50:  # Si description longue
            metro = metro.split('-')[0].split(',')[0].strip()
        if metro and len(metro) > 2 and metro != "m" and len(metro) < 50:
            return metro
    
    # Priorité 3: transports (première station valide)
    transports = apartment.get('transports', [])
    for transport in transports:
        # Chercher une station de métro valide (nom + numéro de ligne potentiel)
        if re.search(r'^[A-Za-z\s\-éàèùîêôûçâë]+$', transport.strip()) and len(transport.strip()) > 2:
            # Vérifier que ce n'est pas un faux positif
            excluded = ['Paris', 'Entre', '€', 'm²', 'pièces', 'chambres']
            if not any(excl in transport for excl in excluded):
                return transport.strip()
    
    # Priorité 4: chercher dans la description (supporte "métro" et "métros")
    description = apartment.get('description', '')
    metro_match = re.search(r'métro\w*\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:,|\s+\(ligne|\s+[Ll]|\.|\s+et|\-)', description, re.IGNORECASE)
    if metro_match:
        metro = metro_match.group(1).strip()
        # Si trop long, extraire juste le nom de la station
        if len(metro) > 50:
            metro = metro.split('-')[0].split(',')[0].strip()
        if metro and len(metro) > 2 and len(metro) < 50:
            return metro
    
    return None

def get_style_name(apartment):
    """Extrait le nom du style depuis différentes sources"""
    # Priorité 1: style_analysis.style.type
    style_analysis = apartment.get('style_analysis', {})
    if style_analysis:
        style_data = style_analysis.get('style', {})
        style_type = style_data.get('type', '')
        if style_type and style_type != 'autre':
            # Capitaliser la première lettre et formater
            style_name = style_type.capitalize()
            # Gérer les cas spéciaux comme "70s" ou "Haussmannien"
            if '70' in style_type or 'seventies' in style_type.lower():
                style_name = "70s"
            elif 'haussmann' in style_type.lower():
                style_name = "Haussmannien"
            return f"Style {style_name}"
    
    # Priorité 2: scores_detaille.style.justification (chercher des indices de style)
    scores_detaille = apartment.get('scores_detaille', {})
    style_score = scores_detaille.get('style', {})
    justification = style_score.get('justification', '').lower()
    
    if 'haussmann' in justification or 'moulures' in justification or 'parquet' in justification:
        return "Style Haussmannien"
    elif '70' in justification or 'seventies' in justification:
        return "Style 70s"
    elif 'moderne' in justification or 'contemporain' in justification:
        return "Style Moderne"
    
    # Fallback: utiliser style_haussmannien si disponible
    style_haussmannien = apartment.get('style_haussmannien', {})
    if style_haussmannien.get('score', 0) > 20:
        return "Style Haussmannien"
    
    return None

def format_apartment_info(apartment):
    """Formate les informations de l'appartement"""
    localisation = apartment.get('localisation', 'Non spécifié')
    surface = apartment.get('surface', 'Non spécifié')
    pieces = apartment.get('pieces', 'Non spécifié')
    prix = apartment.get('prix', 'Non spécifié')
    prix_m2 = apartment.get('prix_m2', '')
    
    # Extraire les stations de métro
    transports = apartment.get('transports', [])
    stations_str = " · ".join(transports[:2]) if transports else ""
    
    # Extraire le quartier, le métro et formater le titre
    quartier = get_quartier_name(apartment)
    metro = get_metro_name(apartment)
    prix_k = format_prix_k(prix)
    
    # Formater le titre: "750k · Place de la Réunion" ou "750k · Ménilmontant" ou "750k · Paris 19e"
    if quartier and prix_k:
        title = f"{prix_k} · {quartier}"
    elif metro and prix_k:
        # Pas de quartier mais on a le métro, afficher "Prix · Métro"
        title = f"{prix_k} · {metro}"
    elif prix_k:
        # Pas de quartier ni de métro, afficher "Prix · Arrondissement"
        # Extraire l'arrondissement de la localisation
        arr_match = re.search(r'Paris (\d+e)', localisation)
        if arr_match:
            arrondissement = f"Paris {arr_match.group(1)}"
            title = f"{prix_k} · {arrondissement}"
        else:
            title = f"{prix_k} · {localisation}"
    elif quartier:
        title = quartier
    elif metro:
        title = metro
    else:
        title = localisation
    
    # Extraire la surface en nombre seulement (ex: "76 m²" -> "76 m²")
    surface_clean = ""
    if isinstance(surface, str):
        # Extraire juste "XX m²" de la surface
        surface_match = re.search(r'(\d+)\s*m²', surface)
        if surface_match:
            surface_clean = f"{surface_match.group(1)} m²"
    
    # Si surface_clean est vide, essayer depuis le titre
    if not surface_clean:
        titre = apartment.get('titre', '')
        if titre:
            titre_match = re.search(r'(\d+)\s*m²', titre)
            if titre_match:
                surface_clean = f"{titre_match.group(1)} m²"
    
    # Formater le prix/m² (ex: "11071 €/m²" -> "10 714 € / m²")
    prix_m2_formatted = ""
    if prix_m2 and prix_m2 != "Prix/m² non trouvé":
        # Extraire les chiffres et reformater
        prix_m2_match = re.search(r'(\d+)', prix_m2.replace(' ', ''))
        if prix_m2_match:
            prix_num = int(prix_m2_match.group(1))
            # Formater avec espaces de milliers
            prix_m2_formatted = f"{prix_num:,} € / m²".replace(',', ' ')
    else:
        # Calculer le prix/m² si disponible depuis prix et surface
        if surface_clean and prix:
            # Extraire le prix
            prix_match = re.search(r'([\d\s]+)', prix.replace(' ', ''))
            if prix_match:
                try:
                    prix_num = int(prix_match.group(1))
                    # Extraire la surface
                    surface_match = re.search(r'(\d+)', surface_clean)
                    if surface_match:
                        surface_num = int(surface_match.group(1))
                        if surface_num > 0:
                            prix_m2_calc = prix_num // surface_num
                            prix_m2_formatted = f"{prix_m2_calc:,} € / m²".replace(',', ' ')
                except:
                    pass
    
    # Extraire le style
    style_name = get_style_name(apartment)
    
    # Construire le subtitle: "76 m² · 10 714 € / m² · Style 70s"
    subtitle_parts = []
    if surface_clean:
        subtitle_parts.append(surface_clean)
    if prix_m2_formatted:
        subtitle_parts.append(prix_m2_formatted)
    if style_name:
        subtitle_parts.append(style_name)
    
    # Utiliser seulement les parties valides
    subtitle = " · ".join(subtitle_parts) if subtitle_parts else ""
    
    # Si subtitle est vide, créer un fallback simple
    if not subtitle:
        if surface_clean:
            subtitle = surface_clean
        else:
            subtitle = f"{surface} - {pieces}"
    
    return {
        'title': title,
        'subtitle': subtitle,
        'stations': stations_str,
        'prix': prix
    }

def get_all_apartment_photos(apartment):
    """Récupère toutes les photos d'appartement disponibles"""
    apartment_id = apartment.get('id', 'unknown')
    
    # Liste des URLs à exclure (logos, placeholders)
    excluded_patterns = [
        'AppStore.png',
        'GoogleStore.png',
        'Logo-Jinka',
        'logo-',
        'source_logos',
        'no-picture.png',
        'placeholder',
        'icon',
        'logo'
    ]
    
    photo_urls = []
    
    # Chercher d'abord dans photos_v2 (nouveau système), puis dans photos (ancien)
    photos_dir_v2 = f"data/photos_v2/{apartment_id}"
    photos_dir = f"data/photos/{apartment_id}"
    
    # Priorité 1: photos_v2 (nouveau système amélioré)
    if os.path.exists(photos_dir_v2):
        photo_files = []
        for filename in os.listdir(photos_dir_v2):
            if filename.endswith(('.jpg', '.jpeg', '.png')) and filename.startswith('photo_'):
                # Vérifier que ce n'est pas un logo
                is_excluded = any(pattern.lower() in filename.lower() for pattern in excluded_patterns)
                if not is_excluded:
                    file_path = os.path.join(photos_dir_v2, filename)
                    file_mtime = os.path.getmtime(file_path)
                    photo_files.append((filename, file_mtime))
        
        if photo_files:
            # Trier par date de modification décroissante (plus récent en premier)
            photo_files.sort(key=lambda x: x[1], reverse=True)
            for filename, _ in photo_files:
                photo_urls.append(f"../data/photos_v2/{apartment_id}/{filename}")
    
    # Priorité 2: photos (ancien système)
    if not photo_urls and os.path.exists(photos_dir):
        photo_files = []
        for filename in os.listdir(photos_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                # Vérifier que ce n'est pas un logo
                is_excluded = any(pattern.lower() in filename.lower() for pattern in excluded_patterns)
                if not is_excluded:
                    file_path = os.path.join(photos_dir, filename)
                    file_mtime = os.path.getmtime(file_path)
                    photo_files.append((filename, file_mtime))
        
        if photo_files:
            # Trier par date de modification décroissante (plus récent en premier)
            photo_files.sort(key=lambda x: x[1], reverse=True)
            for filename, _ in photo_files:
                photo_urls.append(f"../data/photos/{apartment_id}/{filename}")
    
    # Fallback: chercher dans les photos de l'appartement depuis les URLs distantes
    if not photo_urls:
        photos = apartment.get('photos', [])
        if photos and len(photos) > 0:
            # Trier par priorité: d'abord gallery_div, puis autres
            prioritized_photos = []
            other_photos = []
            
            for photo in photos:
                url = None
                alt = ''
                selector = ''
                
                if isinstance(photo, dict):
                    url = photo.get('url', '')
                    alt = photo.get('alt', '').lower() or ''
                    selector = photo.get('selector', '').lower() or ''
                elif isinstance(photo, str):
                    url = photo
                
                if not url:
                    continue
                
                # Exclure les logos et placeholders
                is_excluded = any(
                    pattern.lower() in url.lower() or pattern.lower() in alt
                    for pattern in excluded_patterns
                )
                
                if is_excluded:
                    continue
                
                # Accepter les URLs de vraies photos d'appartements
                if any(pattern in url for pattern in ['upload_pro_ad', 'upload_p', 'media.apimo.pro', 'studio-net.fr/biens']):
                    # Exclure si c'est un logo d'agence
                    if 'source_logos' in url or 'logo-' in url:
                        continue
                    
                    # Prioriser les photos de gallery_div (meilleure qualité)
                    if 'gallery_div' in selector:
                        prioritized_photos.append(url)
                    else:
                        other_photos.append(url)
            
            # Retourner toutes les photos prioritaires puis les autres
            photo_urls = prioritized_photos + other_photos
    
    return photo_urls if photo_urls else []

def get_apartment_photo(apartment):
    """Récupère la première photo d'appartement (pour compatibilité)"""
    photos = get_all_apartment_photos(apartment)
    return photos[0] if photos else None

def generate_scorecard_html(apartments):
    """Génère le HTML avec le design de scorecard EXACT"""
    
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HomeScore - Rapport des Appartements</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        @font-face {{
            font-family: 'Blacklist';
            src: url('https://www.dropbox.com/scl/fi/w3kbzil9txf14utsdwkpt/Great-Studio-Blacklist-Regular.otf?rlkey=ggixd3ig2524tzw9ph5qnx9r8&dl=1');
            font-weight: 400;
            font-style: normal;
        }}
        
        @font-face {{
            font-family: 'Blacklist';
            src: url('https://www.dropbox.com/scl/fi/w3kbzil9txf14utsdwkpt/Great-Studio-Blacklist-Regular.otf?rlkey=ggixd3ig2524tzw9ph5qnx9r8&dl=1');
            font-weight: 600;
            font-style: normal;
        }}
        
        @font-face {{
            font-family: 'Blacklist';
            src: url('https://www.dropbox.com/scl/fi/w3kbzil9txf14utsdwkpt/Great-Studio-Blacklist-Regular.otf?rlkey=ggixd3ig2524tzw9ph5qnx9r8&dl=1');
            font-weight: 700;
            font-style: normal;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8f9fa;
            color: #212529;
            line-height: 1.5;
            font-size: 14px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }}
        
        .header h1 {{
            font-size: 2em;
            margin-bottom: 5px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1em;
            opacity: 0.9;
        }}
        
        .apartments-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .scorecard {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            overflow: hidden;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .scorecard:hover {{
            box-shadow: 0 6px 16px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }}
        
        .apartment-image {{
            width: 100%;
            height: 286px;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 0.9em;
            position: relative;
            background-size: cover;
            background-position: center;
            border-radius: 8px 8px 0 0;
            overflow: hidden;
        }}
        
        .apartment-image-placeholder {{
            width: 100%;
            height: 286px;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 2rem;
            position: relative;
        }}
        
        .apartment-image-placeholder::before {{
            content: "📷";
        }}
        
        .apartment-image::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 40px;
            background: linear-gradient(transparent, rgba(0,0,0,0.3));
            pointer-events: none;
        }}
        
        .carousel-container {{
            position: relative;
            width: 100%;
            height: 286px;
            border-radius: 8px 8px 0 0;
            overflow: hidden;
        }}
        
        .carousel-track {{
            display: flex;
            transition: transform 0.3s ease;
            height: 100%;
        }}
        
        .carousel-slide {{
            min-width: 100%;
            height: 100%;
        }}
        
        .carousel-slide img {{
            width: 100%;
            height: 286px;
            object-fit: cover;
        }}
        
        .carousel-nav {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(255, 255, 255, 0.9);
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 10;
            transition: all 0.2s ease;
            font-size: 20px;
            color: #333;
        }}
        
        .carousel-nav:hover {{
            background: rgba(255, 255, 255, 1);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        
        .carousel-nav.prev {{
            left: 10px;
        }}
        
        .carousel-nav.next {{
            right: 10px;
        }}
        
        .carousel-nav:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}
        
        .carousel-dots {{
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 6px;
            z-index: 10;
        }}
        
        .carousel-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .carousel-dot.active {{
            background: white;
            width: 24px;
            border-radius: 4px;
        }}
        
        .photo-score-overlay {{
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 16px;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        
        .photo-score-number {{
            font-size: 20px;
            line-height: 1;
        }}
        
        .photo-score-label {{
            font-size: 11px;
            opacity: 0.9;
            margin-top: 2px;
        }}
        
        .apartment-info {{
            padding: 20px;
        }}
        
        .apartment-title {{
            font-family: 'Cera Pro', 'Inter', sans-serif;
            font-size: 18px;
            font-weight: 600;
            color: #212529;
            margin-bottom: 4px;
            line-height: 1.3;
        }}
        
        .apartment-location {{
            color: #6c757d;
            font-size: 14px;
            margin-bottom: 16px;
            font-weight: 400;
        }}
        
        .score-section {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .overall-score {{
            background: #28a745;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            text-align: center;
            min-width: 60px;
        }}
        
        .score-number {{
            font-size: 24px;
            font-weight: 700;
            line-height: 1;
        }}
        
        .score-label {{
            font-size: 12px;
            opacity: 0.9;
            margin-top: 2px;
            font-weight: 500;
        }}
        
        .criteria-section {{
            margin-bottom: 15px;
        }}
        
        .criterion {{
            margin-bottom: 8px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #dee2e6;
        }}
        
        .criterion-title {{
            font-family: 'Cera Pro', 'Inter', sans-serif;
            font-weight: 600;
            color: #212529;
            margin-bottom: 4px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .criterion-score {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2px;
        }}
        
        .score-value {{
            font-weight: 600;
            font-size: 14px;
        }}
        
        .rating-badge {{
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .rating-badge.good {{
            background: #27ae60;
            color: white;
        }}
        
        .rating-badge.moyen {{
            background: #ff9800;
            color: white;
        }}
        
        .rating-badge.faible {{
            background: #e74c3c;
            color: white;
        }}
        
        .criterion-details {{
            color: #6c757d;
            font-size: 12px;
            line-height: 1.4;
            font-weight: 400;
        }}
        
        .summary-stats {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        
        .stat-number {{
            font-size: 1.5em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 3px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.8em;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        @media (max-width: 768px) {{
            .apartments-grid {{
                grid-template-columns: 1fr;
            }}
            
            .apartment-title {{
                font-size: 1.1em;
            }}
            
            .score-number {{
                font-size: 1.5em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 HomeScore</h1>
            <p>Rapport d'évaluation des appartements - {len(apartments)} appartements analysés</p>
            <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
        </div>
        
        <div class="summary-stats">
            <h2 style="text-align: center; margin-bottom: 20px; color: #333;">📊 Statistiques Globales</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">{len(apartments)}</div>
                    <div class="stat-label">Appartements analysés</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{sum(1 for apt in apartments if apt.get('score_total', 0) >= 80)}</div>
                    <div class="stat-label">Scores ≥ 80/100</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{sum(1 for apt in apartments if apt.get('score_total', 0) >= 70)}</div>
                    <div class="stat-label">Scores ≥ 70/100</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{round(sum(apt.get('score_total', 0) for apt in apartments) / len(apartments), 1) if apartments else 0}</div>
                    <div class="stat-label">Score moyen</div>
                </div>
            </div>
        </div>
        
        <div class="apartments-grid">
"""
    
    # Trier les appartements par score décroissant
    sorted_apartments = sorted(apartments, key=lambda x: x.get('score_total', 0), reverse=True)
    
    for i, apartment in enumerate(sorted_apartments, 1):
        score_total = apartment.get('score_total', 0)
        apartment_info = format_apartment_info(apartment)
        scores_detaille = apartment.get('scores_detaille', {})
        
        # Récupérer toutes les photos de l'appartement
        all_photos = get_all_apartment_photos(apartment)
        
        # Couleur du score global
        score_color = get_score_color(score_total, 100)
        
        # URL de l'appartement
        apartment_url = apartment.get('url', '#')
        carousel_id = f"carousel-{i}"
        
        # Générer le HTML du carousel si plusieurs photos
        if len(all_photos) > 1:
            slides_html = ""
            for photo_idx, photo_url in enumerate(all_photos):
                if photo_url.startswith('http://') or photo_url.startswith('https://'):
                    slides_html += f'<div class="carousel-slide"><img src="{photo_url}" alt="Photo {photo_idx + 1}" style="width:100%;height:286px;object-fit:cover;" onerror="this.style.display=\'none\'"></div>'
                else:
                    slides_html += f'<div class="carousel-slide"><img src="{photo_url}" alt="Photo {photo_idx + 1}" style="width:100%;height:286px;object-fit:cover;" onerror="this.style.display=\'none\'"></div>'
            
            dots_html = ""
            for dot_idx in range(len(all_photos)):
                dots_html += f'<div class="carousel-dot {"active" if dot_idx == 0 else ""}" onclick="event.stopPropagation(); goToSlide(\'{carousel_id}\', {dot_idx})"></div>'
            
            photo_html = f"""
                <div class="carousel-container" data-carousel-id="{carousel_id}" data-total-slides="{len(all_photos)}">
                    <button class="carousel-nav prev" onclick="event.stopPropagation(); prevSlide('{carousel_id}')">‹</button>
                    <div class="carousel-track" id="{carousel_id}-track">
                        {slides_html}
                    </div>
                    <button class="carousel-nav next" onclick="event.stopPropagation(); nextSlide('{carousel_id}')">›</button>
                    <div class="carousel-dots">
                        {dots_html}
                    </div>
                </div>
            """
        elif len(all_photos) == 1:
            # Une seule photo, pas de carousel
            photo_url = all_photos[0]
            if photo_url.startswith('http://') or photo_url.startswith('https://'):
                photo_style = f"background-image: url('{photo_url}');"
            else:
                photo_style = f"background-image: url('{photo_url}');"
            photo_html = f'<div class="apartment-image" style="{photo_style}"></div>'
        else:
            # Aucune photo
            photo_html = '<div class="apartment-image-placeholder"></div>'
        
        html += f"""
            <div class="scorecard" onclick="window.open('{apartment_url}', '_blank')">
                {photo_html}
                <div class="apartment-info">
                    <div class="apartment-title">{apartment_info['title']}</div>
                    <div class="apartment-location">{apartment_info['subtitle']}</div>
                    <div class="apartment-location">{apartment_info['stations']}</div>
                    
                    <div class="score-section">
                        <div class="overall-score" style="background: {score_color};">
                            <div class="score-number">{score_total}</div>
                            <div class="score-label">/100</div>
                        </div>
                    </div>
                    
                    <div class="criteria-section">
"""
        
        # Afficher les critères de scoring
        criteria_mapping = {
            'localisation': {'name': 'LOCALISATION', 'max': 20},
            'prix': {'name': 'PRIX', 'max': 20},
            'style': {'name': 'STYLE', 'max': 20},
            'ensoleillement': {'name': 'EXPOSITION', 'max': 10},
            'cuisine': {'name': 'CUISINE OUVERTE', 'max': 10},
            'etage': {'name': 'ÉTAGE', 'max': 10}
        }
        
        for key, info in criteria_mapping.items():
            if key in scores_detaille:
                criterion = scores_detaille[key]
                score = criterion.get('score', 0)
                justification = criterion.get('justification', 'Non spécifié')
                
                # Couleur et badge
                color = get_score_color(score, info['max'])
                badge = get_rating_badge(score, info['max'])
                
                html += f"""
                        <div class="criterion">
                            <div class="criterion-title">{info['name']}</div>
                            <div class="criterion-score">
                                <span class="score-value" style="color: {color};">{score}/{info['max']}</span>
                                {badge}
                            </div>
                            <div class="criterion-details">{justification}</div>
                        </div>
"""
        
        html += """
                    </div>
                </div>
            </div>
"""
    
    html += """
        </div>
        
        <div class="footer">
            <p>🏠 HomeScore - Système d'évaluation d'appartements</p>
            <p>Généré automatiquement avec analyse IA et critères personnalisés</p>
        </div>
    </div>
    
    <script>
        // Carousel functions
        const carouselStates = {};
        
        function initCarousel(carouselId, totalSlides) {
            carouselStates[carouselId] = { current: 0, total: totalSlides };
        }
        
        function updateCarousel(carouselId) {
            const track = document.getElementById(carouselId + '-track');
            const state = carouselStates[carouselId];
            
            if (!track || !state) return;
            
            const translateX = -state.current * 100;
            track.style.transform = `translateX(${translateX}%)`;
            
            // Update dots
            const dots = track.parentElement.querySelectorAll('.carousel-dot');
            dots.forEach((dot, idx) => {
                if (idx === state.current) {
                    dot.classList.add('active');
                } else {
                    dot.classList.remove('active');
                }
            });
        }
        
        function prevSlide(carouselId) {
            const state = carouselStates[carouselId];
            if (!state) return;
            
            if (state.current > 0) {
                state.current--;
            } else {
                state.current = state.total - 1;
            }
            updateCarousel(carouselId);
        }
        
        function nextSlide(carouselId) {
            const state = carouselStates[carouselId];
            if (!state) return;
            
            if (state.current < state.total - 1) {
                state.current++;
            } else {
                state.current = 0;
            }
            updateCarousel(carouselId);
        }
        
        function goToSlide(carouselId, index) {
            const state = carouselStates[carouselId];
            if (!state) return;
            
            state.current = index;
            updateCarousel(carouselId);
        }
        
        // Initialize all carousels on page load
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.carousel-container').forEach(function(container) {
                const carouselId = container.getAttribute('data-carousel-id');
                const totalSlides = parseInt(container.getAttribute('data-total-slides'));
                if (carouselId && totalSlides) {
                    initCarousel(carouselId, totalSlides);
                }
            });
        });
    </script>
</body>
</html>
"""
    
    return html

def main():
    """Fonction principale"""
    print("🏠 GÉNÉRATION DU RAPPORT HTML")
    print("=" * 50)
    
    # Charger les appartements scorés
    apartments = load_scored_apartments()
    if not apartments:
        print("❌ Aucun appartement scoré trouvé")
        return
    
    print(f"📋 {len(apartments)} appartements trouvés")
    
    # Créer le répertoire de sortie
    os.makedirs("output", exist_ok=True)
    
    # Générer le HTML
    html_content = generate_scorecard_html(apartments)
    
    # Sauvegarder le fichier
    output_file = "output/scorecard_rapport.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Rapport généré: {output_file}")
    print(f"🌐 Ouvrez le fichier dans votre navigateur pour voir le rapport")

if __name__ == "__main__":
    main()
