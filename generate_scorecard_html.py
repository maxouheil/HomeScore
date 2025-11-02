#!/usr/bin/env python3
"""
Génération du rapport HTML avec le design de scorecard
"""

import json
import os
import re
from datetime import datetime
from extract_baignoire import BaignoireExtractor

def load_scored_apartments():
    """Charge les appartements scorés et fusionne avec les données scrapées"""
    try:
        # Charger les scores
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            scored_apartments = json.load(f)
        
        # Charger les données scrapées pour fusionner style_analysis
        scraped_data = {}
        try:
            with open('data/scraped_apartments.json', 'r', encoding='utf-8') as f:
                scraped_list = json.load(f)
                # Convertir en dict par ID pour faciliter la fusion
                for apt in scraped_list:
                    apt_id = apt.get('id')
                    if apt_id:
                        scraped_data[apt_id] = apt
        except FileNotFoundError:
            print("⚠️  Fichier scraped_apartments.json non trouvé, certaines données peuvent manquer")
        
        # Fusionner les données scrapées (style_analysis, etc.) avec les scores
        for apartment in scored_apartments:
            apt_id = apartment.get('id')
            
            # Essayer d'abord depuis scraped_apartments.json
            if apt_id and apt_id in scraped_data:
                scraped_apt = scraped_data[apt_id]
                # Fusionner style_analysis et autres données importantes
                if 'style_analysis' in scraped_apt:
                    apartment['style_analysis'] = scraped_apt['style_analysis']
                # Fusionner d'autres données utiles si nécessaire
                if 'photos' in scraped_apt:
                    apartment['photos'] = scraped_apt['photos']
                if 'exposition' in scraped_apt:
                    apartment['exposition'] = scraped_apt['exposition']
                # Fusionner description et caractéristiques pour extraction de l'étage
                if 'description' in scraped_apt:
                    apartment['description'] = scraped_apt['description']
                if 'caracteristiques' in scraped_apt:
                    apartment['caracteristiques'] = scraped_apt['caracteristiques']
                if 'etage' in scraped_apt:
                    apartment['etage'] = scraped_apt['etage']
            
            # Si description/caracteristiques manquantes, essayer depuis les fichiers individuels
            if not apartment.get('description') or not apartment.get('caracteristiques'):
                apartment_file = f"data/appartements/{apt_id}.json"
                if os.path.exists(apartment_file):
                    try:
                        with open(apartment_file, 'r', encoding='utf-8') as f:
                            apt_data = json.load(f)
                            if 'description' in apt_data and not apartment.get('description'):
                                apartment['description'] = apt_data['description']
                            if 'caracteristiques' in apt_data and not apartment.get('caracteristiques'):
                                apartment['caracteristiques'] = apt_data['caracteristiques']
                            if 'etage' in apt_data and not apartment.get('etage'):
                                apartment['etage'] = apt_data['etage']
                    except:
                        pass
        
        return scored_apartments
    except FileNotFoundError:
        print("❌ Fichier de scores non trouvé")
        return []

def get_score_badge_color(score, max_score):
    """Détermine la couleur du mega score badge selon le design"""
    percentage = (score / max_score) * 100
    if percentage >= 80:
        return "#00966D"  # Vert selon design
    elif percentage >= 60:
        return "#F59E0B"  # Jaune selon design
    else:
        return "#F85457"  # Rouge selon design

def get_score_badge_class(score, max_score):
    """Détermine la classe du badge de score selon le design"""
    percentage = (score / max_score) * 100
    if percentage >= 80:
        return "green"
    elif percentage >= 60:
        return "yellow"
    else:
        return "red"

def get_tier_badge_class(tier):
    """Détermine la classe du badge selon le tier (Good/Moyen/Bad)"""
    if tier == 'tier1':
        return "green"
    elif tier == 'tier2':
        return "yellow"
    else:  # tier3 ou défaut
        return "red"

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
    
    # Formater l'étage (ex: "4e étage" ou "RDC")
    etage_formatted = ""
    etage = apartment.get('etage', '')
    
    # Si l'étage n'est pas directement disponible, chercher dans la description et les caractéristiques
    if not etage:
        description = apartment.get('description', '')
        caracteristiques = apartment.get('caracteristiques', '')
        text_to_search = f"{description} {caracteristiques}"
        
        # Patterns pour trouver l'étage
        etage_patterns = [
            r'(\d+)(?:er?|e|ème?)\s*étage',
            r'au\s+(\d+)(?:er?|e|ème?)',
            r'(\d+)(?:er?|e|ème?)\s*ét\.',
            r'étage\s*(\d+)',
        ]
        
        for pattern in etage_patterns:
            match = re.search(pattern, text_to_search, re.IGNORECASE)
            if match:
                num = match.group(1)
                if num == '1':
                    etage = "1er étage"
                else:
                    etage = f"{num}e étage"
                break
        
        # Chercher RDC si pas d'étage numérique trouvé
        if not etage:
            if re.search(r'\bRDC\b|rez-de-chaussée|rez de chaussée|rez\s*de\s*chaussée', text_to_search, re.IGNORECASE):
                etage = "RDC"
    
    # Formater l'étage trouvé
    if etage:
        etage_match = re.search(r'(\d+(?:er?|e|ème?))\s*étage|RDC|rez-de-chaussée|rez de chaussée', str(etage), re.IGNORECASE)
        if etage_match:
            etage_text = etage_match.group(0)
            if 'rdc' in etage_text.lower() or 'rez' in etage_text.lower():
                etage_formatted = "RDC"
            else:
                num_match = re.search(r'(\d+)', etage_text)
                if num_match:
                    num = num_match.group(1)
                    if num == '1':
                        etage_formatted = "1er étage"
                    else:
                        etage_formatted = f"{num}e étage"
    
    # Extraire le style
    style_name = get_style_name(apartment)
    
    # Construire le subtitle: "76 m² · 4e étage · Style 70s"
    subtitle_parts = []
    if surface_clean:
        subtitle_parts.append(surface_clean)
    if etage_formatted:
        subtitle_parts.append(etage_formatted)
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

def get_criterion_confidence(apartment, criterion_key):
    """Récupère la confiance pour un critère donné depuis style_analysis ou autres sources"""
    style_analysis = apartment.get('style_analysis', {})
    
    # Mapping des critères aux données de style_analysis
    confidence_mapping = {
        'style': style_analysis.get('style', {}).get('confidence'),
        'cuisine': style_analysis.get('cuisine', {}).get('confidence'),
        'ensoleillement': style_analysis.get('luminosite', {}).get('confidence'),
        'baignoire': None,  # Sera calculé via extract_baignoire
    }
    
    confidence = confidence_mapping.get(criterion_key)
    
    # Pour baignoire, utiliser extract_baignoire_textuelle uniquement (TEXT ONLY pour éviter les blocages)
    if criterion_key == 'baignoire':
        try:
            extractor = BaignoireExtractor()
            description = apartment.get('description', '')
            caracteristiques = apartment.get('caracteristiques', '')
            baignoire_data = extractor.extract_baignoire_textuelle(description, caracteristiques)
            confidence = baignoire_data.get('confidence', 0)
        except:
            confidence = None
    
    # Convertir en pourcentage si c'est un float entre 0 et 1
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            return int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            return int(confidence)
    
    return None

def format_localisation_criterion(apartment):
    """Formate le critère Localisation: "Metro · Quartier" """
    metro = get_metro_name(apartment)
    quartier = get_quartier_name(apartment)
    
    parts = []
    if metro:
        parts.append(f"Metro {metro}")
    if quartier:
        parts.append(quartier)
    
    if parts:
        return {
            'main_value': " · ".join(parts),
            'confidence': None,  # Données factuelles, pas de confiance
            'indices': None
        }
    else:
        return {
            'main_value': "Non spécifié",
            'confidence': None,
            'indices': None
        }

def format_prix_criterion(apartment):
    """Formate le critère Prix: "X/m² · Moyen/Bad/Good" """
    scores_detaille = apartment.get('scores_detaille', {})
    prix_score = scores_detaille.get('prix', {})
    tier = prix_score.get('tier', 'tier3')
    
    # Calculer prix/m²
    prix = apartment.get('prix', '')
    surface = apartment.get('surface', '')
    prix_m2 = None
    
    # Extraire le prix en nombre
    prix_match = re.search(r'([\d\s]+)', prix.replace(' ', '')) if prix else None
    if prix_match:
        try:
            prix_num = int(prix_match.group(1))
            # Extraire la surface
            surface_match = re.search(r'(\d+)', surface) if surface else None
            if surface_match:
                surface_num = int(surface_match.group(1))
                if surface_num > 0:
                    prix_m2 = prix_num // surface_num
        except:
            pass
    
    # Si pas calculé, essayer depuis prix_m2 directement
    if prix_m2 is None:
        prix_m2_str = apartment.get('prix_m2', '')
        if prix_m2_str:
            prix_m2_match = re.search(r'(\d+)', prix_m2_str.replace(' ', ''))
            if prix_m2_match:
                try:
                    prix_m2 = int(prix_m2_match.group(1))
                except:
                    pass
    
    # Formater avec virgule comme séparateur de milliers et m² avec superscript
    if prix_m2:
        prix_formatted = f"{prix_m2:,}".replace(',', ' ')
        main_value = f"{prix_formatted} / m<sup>2</sup>"
    else:
        main_value = "Prix/m<sup>2</sup> non disponible"
    
    # Mapping tiers avec couleurs
    tier_mapping = {
        'tier1': ('Good', 'good'),
        'tier2': ('Moyen', 'moyen'),
        'tier3': ('Bad', 'bad')
    }
    tier_label, tier_class = tier_mapping.get(tier, ('Bad', 'bad'))
    
    return {
        'main_value': f"{main_value} · <span class=\"tier-label {tier_class}\">{tier_label}</span>",
        'confidence': None,  # Données factuelles
        'indices': None
    }

def format_style_criterion(apartment):
    """Formate le critère Style: "70's/Haussmanien/Moderne (X% confiance) + indices" """
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    
    style_type = style_data.get('type', '')
    confidence = style_data.get('confidence')
    
    # Formater le nom du style
    if not style_type or style_type == 'autre' or style_type == 'inconnu':
        # Fallback: chercher dans scores_detaille
        scores_detaille = apartment.get('scores_detaille', {})
        style_score = scores_detaille.get('style', {})
        justification = style_score.get('justification', '').lower()
        
        if 'haussmann' in justification or 'moulures' in justification:
            style_type = 'haussmannien'
        elif '70' in justification or 'seventies' in justification:
            style_type = '70s'
        elif 'moderne' in justification or 'contemporain' in justification:
            style_type = 'moderne'
        else:
            style_type = 'Non spécifié'
    
    # Capitaliser et formater
    if '70' in style_type.lower() or 'seventies' in style_type.lower():
        style_name = "70's"
    elif 'haussmann' in style_type.lower():
        style_name = "Haussmannien"
    elif 'moderne' in style_type.lower():
        style_name = "Moderne"
    else:
        style_name = style_type.capitalize()
    
    # Convertir confiance en pourcentage
    confidence_pct = None
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # Extraire les indices
    indices = []
    details = style_data.get('details', '')
    if details:
        # Chercher des mots-clés dans les détails
        keywords = ['moulures', 'cheminée', 'parquet', 'hauteur sous plafond', 'moldings', 'fireplace']
        found_keywords = [kw for kw in keywords if kw.lower() in details.lower()]
        if found_keywords:
            indices = found_keywords[:3]  # Limiter à 3 indices
    
    # Si pas d'indices dans details, chercher dans style_haussmannien
    if not indices:
        style_haussmannien = apartment.get('style_haussmannien', {})
        if isinstance(style_haussmannien, dict):
            elements = style_haussmannien.get('elements', {})
            if isinstance(elements, dict):
                architectural = elements.get('architectural', [])
                if isinstance(architectural, list) and architectural:
                    indices = architectural[:3]
    
    indices_str = None
    if indices:
        indices_str = "Indices: " + " · ".join(indices)
    
    return {
        'main_value': style_name,
        'confidence': confidence_pct,
        'indices': indices_str
    }

def format_exposition_criterion(apartment):
    """Formate le critère Exposition: "Lumineux / Luminosité moyenne / Sombre (X% confiance) + indices" """
    style_analysis = apartment.get('style_analysis', {})
    luminosite_data = style_analysis.get('luminosite', {})
    
    luminosite_type = luminosite_data.get('type', '')
    confidence = luminosite_data.get('confidence')
    
    # Mapping luminosité
    if 'excellente' in luminosite_type.lower():
        main_value = "Lumineux"
    elif 'bonne' in luminosite_type.lower() or 'moyenne' in luminosite_type.lower():
        main_value = "Luminosité moyenne"
    else:
        main_value = "Sombre"
    
    # Convertir confiance en pourcentage
    confidence_pct = None
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # Extraire les indices depuis exposition
    indices_parts = []
    exposition = apartment.get('exposition', {})
    
    # Étage
    etage = apartment.get('etage', '')
    if etage:
        etage_match = re.search(r'(\d+(?:er?|e|ème?))\s*étage|RDC|rez-de-chaussée|rez de chaussée', str(etage), re.IGNORECASE)
        if etage_match:
            etage_text = etage_match.group(0)
            if 'rdc' in etage_text.lower() or 'rez' in etage_text.lower():
                indices_parts.append("RDC")
            else:
                num_match = re.search(r'(\d+)', etage_text)
                if num_match:
                    num = num_match.group(1)
                    if num == '1':
                        indices_parts.append("1er étage")
                    else:
                        indices_parts.append(f"{num}e étage")
    
    # Vis-à-vis depuis description ou exposition
    description = apartment.get('description', '').lower()
    if 'vis-à-vis' in description or 'vis à vis' in description or 'pas de vis' in description:
        if 'pas de vis' in description:
            indices_parts.append("pas de vis à vis")
        else:
            indices_parts.append("vis à vis")
    
    # Exposition directionnelle
    exposition_dir = exposition.get('exposition', '')
    if exposition_dir and exposition_dir.lower() not in ['inconnue', 'inconnu', 'non spécifiée']:
        indices_parts.append(f"Exposition {exposition_dir} détectée")
    
    indices_str = " · ".join(indices_parts) if indices_parts else None
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str
    }

def format_cuisine_criterion(apartment):
    """Formate le critère Cuisine: "Ouverte / Fermée (X% confiance) + indices" """
    style_analysis = apartment.get('style_analysis', {})
    cuisine_data = style_analysis.get('cuisine', {})
    
    cuisine_ouverte = cuisine_data.get('ouverte', False)
    confidence = cuisine_data.get('confidence')
    details = cuisine_data.get('details', '')
    
    # Simplifié: seulement Ouverte ou Fermée (plus de Semi Ouverte)
    if cuisine_ouverte:
        main_value = "Ouverte"
    else:
        main_value = "Fermée"
    
    # Convertir confiance en pourcentage
    confidence_pct = None
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # Extraire les indices
    indices = None
    if details:
        # Chercher des mots-clés dans les détails pour les indices
        if 'analyse photo' in details.lower() or 'photo' in details.lower():
            indices = f"Analyse photo : Cuisine {main_value.lower()} détectée"
        else:
            # Extraire des indices pertinents depuis details
            keywords_found = []
            if 'bar' in details.lower() or 'comptoir' in details.lower():
                keywords_found.append('bar détecté')
            if 'ouverte' in details.lower() and main_value == "Ouverte":
                keywords_found.append('cuisine intégrée')
            
            if keywords_found:
                indices = " · ".join(keywords_found[:3])
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices
    }

def format_baignoire_criterion(apartment):
    """Formate le critère Baignoire: "Oui / Non (confiance) + indices" """
    try:
        extractor = BaignoireExtractor()
        # Utiliser extract_baignoire_textuelle uniquement pour éviter les blocages avec analyse photo
        description = apartment.get('description', '')
        caracteristiques = apartment.get('caracteristiques', '')
        baignoire_data = extractor.extract_baignoire_textuelle(description, caracteristiques)
        
        has_baignoire = baignoire_data.get('has_baignoire', False)
        has_douche = baignoire_data.get('has_douche', False)
        confidence = baignoire_data.get('confidence', 0)
        justification = baignoire_data.get('justification', '')
        
        # Déterminer la valeur principale
        if has_baignoire:
            main_value = "Oui"
        else:
            main_value = "Non"
        
        # Convertir confiance en pourcentage
        confidence_pct = None
        if confidence is not None:
            if isinstance(confidence, float) and 0 <= confidence <= 1:
                confidence_pct = int(confidence * 100)
            elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
                confidence_pct = int(confidence)
        
        # Extraire les indices depuis justification
        indices = None
        if justification:
            if 'photo' in justification.lower() or 'détectée' in justification.lower() or 'analysée' in justification.lower():
                if has_baignoire:
                    indices = "Analyse photo : Baignoire détectée"
                elif has_douche:
                    indices = "Analyse photo : Douche détectée"
            elif 'description' in justification.lower() or 'caractéristiques' in justification.lower():
                # Détecté depuis texte
                if has_baignoire:
                    indices = "Baignoire mentionnée dans le texte"
                elif has_douche:
                    indices = "Douche mentionnée dans le texte"
            else:
                # Utiliser la justification comme indices si elle est courte
                if len(justification) < 100:
                    indices = justification
        
        return {
            'main_value': main_value,
            'confidence': confidence_pct,
            'indices': indices
        }
    except Exception as e:
        # Fallback si erreur
        return {
            'main_value': "Non",
            'confidence': None,
            'indices': None
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
                    # Extraire le numéro de la photo pour trier correctement
                    match = re.search(r'photo_(\d+)', filename)
                    photo_num = int(match.group(1)) if match else 999999
                    photo_files.append((filename, photo_num))
        
        if photo_files:
            # Trier par numéro de photo (photo_1.jpg, photo_2.jpg, etc.)
            photo_files.sort(key=lambda x: x[1])
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
                    # Extraire le numéro de la photo pour trier correctement
                    match = re.search(r'photo_(\d+)', filename)
                    if match:
                        photo_num = int(match.group(1))
                    else:
                        # Fallback: utiliser la date de modification pour les anciens fichiers
                        file_path = os.path.join(photos_dir, filename)
                        file_mtime = os.path.getmtime(file_path)
                        photo_num = int(file_mtime)  # Utiliser timestamp comme numéro
                    photo_files.append((filename, photo_num))
        
        if photo_files:
            # Trier par numéro de photo (photo_1.jpg, photo_2.jpg, etc.)
            photo_files.sort(key=lambda x: x[1])
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
    <link rel="preconnect" href="https://fonts.cdnfonts.com" crossorigin>
    <link href="https://fonts.cdnfonts.com/css/cera-pro" rel="stylesheet">
    <style>
        /* Cera Pro - Design System Standard - Chargement via CDN */
        @import url('https://fonts.cdnfonts.com/css/cera-pro');
        
        /* Fallback: Si CDN ne fonctionne pas, utiliser les variantes système */
        @font-face {{
            font-family: 'Cera Pro Fallback';
            src: local('Cera Pro'), local('CeraPro-Regular'), local('CeraPro');
            font-weight: 400;
            font-style: normal;
            font-display: swap;
        }}
        
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
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }}
        
        body {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
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
            grid-template-columns: repeat(3, 1fr);
            gap: 30px;
            margin: 20px 0;
        }}
        
        @media (max-width: 1400px) {{
            .apartments-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 900px) {{
            .apartments-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media (max-width: 768px) {{
            .apartments-grid {{
                gap: 20px;
            }}
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
        
        .apartment-image-container {{
            position: relative;
            height: 280px;
            border-radius: 16px 16px 0 0;
            background: #f0f0f0;
            overflow: hidden;
        }}
        
        .score-badge-top {{
            position: absolute;
            top: 15px;
            right: 15px;
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            font-size: 20px;
            font-weight: 500;
            color: white !important;
            padding: 8px 16px;
            border-radius: 12px;
            display: inline-block;
            z-index: 10;
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
            padding: 24px;
        }}
        
        .apartment-title {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            font-size: 20px;
            font-weight: 500;
            color: #212529;
            margin-bottom: 4px;
            line-height: 1.2;
        }}
        
        .apartment-subtitle {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            font-size: 14px;
            font-weight: 400;
            color: #6c757d;
            margin-bottom: 24px;
        }}
        
        .criterion {{
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        }}
        
        .criterion:last-child {{
            border-bottom: none;
            padding-bottom: 0;
            margin-bottom: 0;
        }}
        
        .criterion-details {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            font-size: 13px;
            font-weight: 400;
            color: #212529;
            margin-top: 4px;
        }}
        
        .criterion-details .tier-label {{
            font-weight: 600;
        }}
        
        .criterion-details .tier-label.good {{
            color: #00966D !important;
        }}
        
        .criterion-details .tier-label.moyen {{
            color: #F59E0B !important;
        }}
        
        .criterion-details .tier-label.bad {{
            color: #F85457 !important;
        }}
        
        .criterion-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0;
            gap: 12px;
        }}
        
        .criterion-name {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            font-size: 16px;
            font-weight: 500;
            color: #212529;
            text-transform: none !important;
            flex: 1;
            min-width: 0;
        }}
        
        .criterion-score-badge {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 500;
            padding: 4px 12px;
            border-radius: 9999px;
            text-align: center;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            height: fit-content;
            line-height: 1.2;
        }}
        
        .criterion-score-badge.green {{
            color: #00966D;
            background: rgba(0, 150, 109, 0.1);
        }}
        
        .criterion-score-badge.yellow {{
            color: #F59E0B;
            background: rgba(245, 158, 11, 0.1);
        }}
        
        .criterion-score-badge.red {{
            color: #F85457;
            background: rgba(248, 84, 87, 0.1);
        }}
        
        .tier-label {{
            font-weight: 600;
        }}
        
        .tier-label.good {{
            color: #00966D;
        }}
        
        .tier-label.moyen {{
            color: #F59E0B !important;
        }}
        
        .criterion-details .tier-label.moyen {{
            color: #F59E0B !important;
        }}
        
        .tier-label.bad {{
            color: #F85457;
        }}
        
        .criterion-sub-details {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            font-size: 12px;
            color: #999;
            margin-top: 2px;
        }}
        
        .confidence-badge {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            font-size: 10px;
            font-weight: 500;
            color: rgba(0, 0, 0, 0.3);
            background: rgba(0, 0, 0, 0.06);
            padding: 0 8px;
            height: 18px;
            line-height: 18px;
            border-radius: 9999px;
            margin-left: 4px;
            display: inline-block;
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
                gap: 20px;
            }}
            
            .apartment-title {{
                font-size: 1.1em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="apartments-grid">
"""
    
    # Trier les appartements par score décroissant
    sorted_apartments = sorted(apartments, key=lambda x: x.get('score_total', 0), reverse=True)
    
    for i, apartment in enumerate(sorted_apartments, 1):
        apartment_info = format_apartment_info(apartment)
        scores_detaille = apartment.get('scores_detaille', {})
        
        # Afficher les critères de scoring avec formatage structuré
        criteria_mapping = {
            'localisation': {'name': 'Localisation', 'max': 20, 'formatter': format_localisation_criterion},
            'prix': {'name': 'Prix', 'max': 20, 'formatter': format_prix_criterion},
            'style': {'name': 'Style', 'max': 20, 'formatter': format_style_criterion},
            'ensoleillement': {'name': 'Exposition', 'max': 10, 'formatter': format_exposition_criterion},
            'cuisine': {'name': 'Cuisine ouverte', 'max': 10, 'formatter': format_cuisine_criterion},
            'baignoire': {'name': 'Baignoire', 'max': 10, 'formatter': format_baignoire_criterion}
        }
        
        # Calculer le mega score : SEULEMENT les 6 critères de scoring (pas etage, surface, vue qui sont des indices)
        # Les 6 critères sont : localisation, prix, style, ensoleillement, cuisine, baignoire
        mega_score = 0
        
        # Liste des critères qui comptent pour le score (exclure etage, surface, vue qui sont des indices)
        scored_criteria = ['localisation', 'prix', 'style', 'ensoleillement', 'cuisine', 'baignoire']
        
        # Calculer depuis scores_detaille uniquement pour les critères de scoring
        for key in scored_criteria:
            if key in scores_detaille:
                criterion = scores_detaille[key]
                if isinstance(criterion, dict):
                    mega_score += criterion.get('score', 0)
            elif key == 'baignoire':
                # Pour baignoire, si pas dans scores_detaille, utiliser extract_baignoire_textuelle (TEXT ONLY)
                try:
                    extractor = BaignoireExtractor()
                    description = apartment.get('description', '')
                    caracteristiques = apartment.get('caracteristiques', '')
                    baignoire_data = extractor.extract_baignoire_textuelle(description, caracteristiques)
                    mega_score += baignoire_data.get('score', 0)
                except:
                    pass
        
        # Ajouter les bonus/malus si disponibles dans l'appartement
        bonus = apartment.get('bonus', 0)
        malus = apartment.get('malus', 0)
        mega_score += bonus - malus
        
        # Arrondir le mega score à 1 décimale si nécessaire
        mega_score = round(mega_score, 1)
        # Formater pour l'affichage (enlever .0 si entier)
        mega_score_display = int(mega_score) if mega_score == int(mega_score) else mega_score
        
        # Récupérer toutes les photos de l'appartement
        all_photos = get_all_apartment_photos(apartment)
        
        # Couleur du mega score badge (basée sur 90 pts max + bonus possibles)
        # Max théorique: 20+20+20+10+10+10 = 90 (6 critères seulement) + bonus (max ~17) = ~107
        # On utilise 90 comme référence standard pour le pourcentage de couleur (les 6 critères de scoring)
        max_score_for_color = 90
        score_badge_color = get_score_badge_color(mega_score, max_score_for_color)
        
        # URL de l'appartement
        apartment_url = apartment.get('url', '#')
        carousel_id = f"carousel-{i}"
        
        # Générer le HTML du carousel si plusieurs photos
        if len(all_photos) > 1:
            slides_html = ""
            for photo_idx, photo_url in enumerate(all_photos):
                if photo_url.startswith('http://') or photo_url.startswith('https://'):
                    slides_html += f'<div class="carousel-slide"><img src="{photo_url}" alt="Photo {photo_idx + 1}" style="width:100%;height:280px;object-fit:cover;" onerror="console.error(\'Erreur chargement image:\', this.src); this.parentElement.style.display=\'none\'"></div>'
                else:
                    slides_html += f'<div class="carousel-slide"><img src="{photo_url}" alt="Photo {photo_idx + 1}" style="width:100%;height:280px;object-fit:cover;" onerror="console.error(\'Erreur chargement image:\', this.src); this.parentElement.style.display=\'none\'"></div>'
            
            dots_html = ""
            for dot_idx in range(len(all_photos)):
                dots_html += f'<div class="carousel-dot {"active" if dot_idx == 0 else ""}" onclick="event.stopPropagation(); goToSlide(\'{carousel_id}\', {dot_idx})"></div>'
            
            photo_html = f"""
                <div class="apartment-image-container">
                    <div class="score-badge-top" style="background: {score_badge_color};">{mega_score_display}</div>
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
                </div>
            """
        elif len(all_photos) == 1:
            # Une seule photo, pas de carousel
            photo_url = all_photos[0]
            if photo_url.startswith('http://') or photo_url.startswith('https://'):
                photo_style = f"background-image: url('{photo_url}');"
            else:
                photo_style = f"background-image: url('{photo_url}');"
            photo_html = f'<div class="apartment-image-container"><div class="score-badge-top" style="background: {score_badge_color};">{mega_score_display}</div><div class="apartment-image" style="{photo_style}"></div></div>'
        else:
            # Aucune photo
            photo_html = f'<div class="apartment-image-container"><div class="score-badge-top" style="background: {score_badge_color};">{mega_score_display}</div><div class="apartment-image-placeholder"></div></div>'
        
        html += f"""
            <div class="scorecard" onclick="window.open('{apartment_url}', '_blank')">
                {photo_html}
                <div class="apartment-info">
                    <div class="apartment-title">{apartment_info['title']}</div>
                    <div class="apartment-subtitle">{apartment_info['subtitle']}</div>
"""
        
        for key, info in criteria_mapping.items():
            # Pour baignoire, ne pas vérifier scores_detaille car il n'y est peut-être pas
            if key == 'baignoire' or key in scores_detaille:
                # Obtenir le score et le tier depuis scores_detaille si disponible
                score = 0
                tier = 'tier3'  # Défaut
                if key in scores_detaille:
                    criterion = scores_detaille[key]
                    score = criterion.get('score', 0)
                    tier = criterion.get('tier', 'tier3')
                elif key == 'baignoire':
                    # Pour baignoire, utiliser extract_baignoire_textuelle pour obtenir le score (TEXT ONLY pour éviter les blocages)
                    try:
                        extractor = BaignoireExtractor()
                        description = apartment.get('description', '')
                        caracteristiques = apartment.get('caracteristiques', '')
                        baignoire_data = extractor.extract_baignoire_textuelle(description, caracteristiques)
                        score = baignoire_data.get('score', 0)
                        tier = baignoire_data.get('tier', 'tier3')
                    except:
                        score = 0
                        tier = 'tier3'
                
                # Classe du badge de score basée sur le tier, pas le pourcentage
                badge_class = get_tier_badge_class(tier)
                
                # Utiliser la fonction de formatage spécifique
                formatted = info['formatter'](apartment)
                main_value = formatted.get('main_value', 'Non spécifié')
                confidence = formatted.get('confidence')
                indices = formatted.get('indices')
                
                # Construire le badge de confiance
                confidence_html = ""
                if confidence is not None:
                    confidence_html = f'<span class="confidence-badge">{confidence}% confiance</span>'
                
                # Construire le HTML selon le design
                details_html = f'{main_value}{confidence_html}'
                if indices:
                    # Les indices sont déjà formatés par les fonctions (peuvent contenir "Indices:" ou "Analyse photo:")
                    details_html += f'<div class="criterion-sub-details">{indices}</div>'
                
                html += f"""
                        <div class="criterion">
                            <div class="criterion-header">
                                <span class="criterion-name">{info['name']}</span>
                                <span class="criterion-score-badge {badge_class}">{score} pts</span>
                            </div>
                            <div class="criterion-details">{details_html}</div>
                        </div>
"""
        
        html += """
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
            // Positionner immédiatement le carousel à la première slide
            updateCarousel(carouselId);
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
    output_file = "output/homepage.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Rapport généré: {output_file}")
    print(f"🌐 Ouvrez le fichier dans votre navigateur pour voir le rapport")

if __name__ == "__main__":
    main()
