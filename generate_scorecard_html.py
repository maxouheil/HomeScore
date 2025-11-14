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
        
        # Charger les données scrapées pour fusionner style_analysis, baignoire, etc.
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
        
        # Charger aussi depuis les fichiers individuels si disponibles (pour les données les plus récentes)
        from pathlib import Path
        appartements_dir = Path('data/appartements')
        if appartements_dir.exists():
            for apt_file in appartements_dir.glob('*.json'):
                if apt_file.stem in ['test_001', 'test_no_photo', 'unknown']:
                    continue
                try:
                    with open(apt_file, 'r', encoding='utf-8') as f:
                        apt_data = json.load(f)
                        apt_id = apt_data.get('id')
                        if apt_id:
                            # Les fichiers individuels ont priorité sur scraped_apartments.json
                            scraped_data[apt_id] = apt_data
                except Exception as e:
                    # Ignorer les erreurs de lecture de fichiers individuels
                    pass
        
        # Fusionner les données scrapées (style_analysis, baignoire, etc.) avec les scores
        for apartment in scored_apartments:
            apt_id = apartment.get('id')
            if apt_id and apt_id in scraped_data:
                scraped_apt = scraped_data[apt_id]
                # Fusionner style_analysis et autres données importantes
                if 'style_analysis' in scraped_apt:
                    apartment['style_analysis'] = scraped_apt['style_analysis']
                # Fusionner d'autres données utiles si nécessaire
                if 'photos' in scraped_apt:
                    apartment['photos'] = scraped_apt['photos']
                # Fusionner l'exposition depuis scraped_apt pour avoir brightness_value
                if 'exposition' in scraped_apt:
                    scraped_expo = scraped_apt['exposition']
                    # Si l'appartement a déjà une exposition, fusionner les détails
                    if 'exposition' in apartment:
                        # Fusionner les détails pour avoir brightness_value
                        if 'details' in scraped_expo:
                            if 'details' not in apartment['exposition']:
                                apartment['exposition']['details'] = {}
                            apartment['exposition']['details'].update(scraped_expo['details'])
                        # Mettre à jour l'exposition principale si elle existe dans scraped
                        if scraped_expo.get('exposition'):
                            apartment['exposition']['exposition'] = scraped_expo['exposition']
                        # Mettre à jour exposition_explicite si présent
                        if 'exposition_explicite' in scraped_expo:
                            apartment['exposition']['exposition_explicite'] = scraped_expo['exposition_explicite']
                    else:
                        # Sinon, utiliser directement l'exposition scrapée
                        apartment['exposition'] = scraped_expo
                
                # Si pas d'exposition ou pas d'exposition_explicite, essayer d'extraire depuis la description
                if 'exposition' not in apartment or not apartment.get('exposition', {}).get('exposition_explicite'):
                    description = scraped_apt.get('description', '') or apartment.get('description', '')
                    caracteristiques = scraped_apt.get('caracteristiques', '') or apartment.get('caracteristiques', '')
                    if description:
                        import re
                        text_lower = description.lower()
                        # Patterns pour exposition explicite (même logique que api_data_adapter.py)
                        expo_patterns = [
                            (r'exposition\s+(sud|nord|est|ouest|sud-ouest|nord-est|sud-est|nord-ouest)', 'exposition'),
                            (r'orienté\s+(sud|nord|est|ouest|sud-ouest|nord-est|sud-est|nord-ouest)', 'orienté'),
                            (r'plein\s+(sud|nord|est|ouest)', 'plein'),
                            (r'(sud|nord|est|ouest|sud-ouest|nord-est|sud-est|nord-ouest)\s+exposé', 'exposé'),
                            (r'\b(sud-ouest|nord-est|sud-est|nord-ouest)\b', 'simple'),
                            (r'\b(nord|sud|est|ouest)\b', 'simple'),
                        ]
                        
                        for pattern, context in expo_patterns:
                            match = re.search(pattern, text_lower)
                            if match:
                                expo_found = match.group(1) if match.lastindex else match.group(0)
                                expo_found = expo_found.replace('-', '_').replace(' ', '_')
                                
                                # Créer ou mettre à jour l'objet exposition
                                if 'exposition' not in apartment:
                                    apartment['exposition'] = {}
                                apartment['exposition']['exposition'] = expo_found
                                apartment['exposition']['exposition_explicite'] = True
                                
                                # Ajouter etage_num si disponible
                                if 'details' not in apartment['exposition']:
                                    apartment['exposition']['details'] = {}
                                etage_field = scraped_apt.get('etage', '') or apartment.get('etage', '')
                                if etage_field:
                                    etage_match = re.search(r'(\d+)[èe]?r?me?\s*étage|RDC|rez[\s-]de[\s-]chaussée', etage_field, re.IGNORECASE)
                                    if etage_match:
                                        if 'rdc' in etage_match.group(0).lower() or 'rez' in etage_match.group(0).lower():
                                            apartment['exposition']['details']['etage_num'] = 0
                                        else:
                                            num_match = re.search(r'(\d+)', etage_match.group(0))
                                            if num_match:
                                                apartment['exposition']['details']['etage_num'] = int(num_match.group(1))
                                break
                # Fusionner la baignoire depuis scraped_apt (PRIORITÉ sur scores_detaille)
                if 'baignoire' in scraped_apt:
                    apartment['baignoire'] = scraped_apt['baignoire']
        
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
    # PRIORITÉ 1: Utiliser scores_detaille.style.tier pour déterminer Ancien/Neuf
    scores_detaille = apartment.get('scores_detaille', {})
    style_score = scores_detaille.get('style', {})
    style_tier = style_score.get('tier', '')
    
    if style_tier == 'tier1':
        return "Style Haussmannien"  # Ancien
    elif style_tier == 'tier2':
        return "Style Atypique"  # Atypique
    elif style_tier == 'tier3':
        return "Style Moderne"  # Neuf
    
    # PRIORITÉ 2: style_analysis.style.type (si tier non disponible)
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
            elif 'moderne' in style_type.lower() or 'contemporain' in style_type.lower():
                style_name = "Moderne"
            return f"Style {style_name}"
    
    # PRIORITÉ 3: scores_detaille.style.justification (mais seulement si tier non disponible)
    justification = style_score.get('justification', '').lower()
    
    # Vérifier d'abord les mots-clés "neuf" ou "moderne" avant "ancien"
    if 'moderne' in justification or 'contemporain' in justification or 'neuf' in justification or 'design épuré' in justification:
        return "Style Moderne"
    elif 'haussmann' in justification:
        return "Style Haussmannien"
    elif '70' in justification or 'seventies' in justification:
        return "Style 70s"
    # Ne pas utiliser "moulures" ou "parquet" seuls car ils peuvent être dans du moderne
    
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

def get_criterion_confidence(apartment, criterion_key, baignoire_extractor=None):
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
    
    # Pour baignoire, utiliser extract_baignoire (réutiliser l'instance si fournie)
    if criterion_key == 'baignoire':
        try:
            if baignoire_extractor is None:
                baignoire_extractor = BaignoireExtractor()
            baignoire_data = baignoire_extractor.extract_baignoire_ultimate(apartment)
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
    """Formate le critère Style: "Ancien/Neuf/Atypique (X% confiance) + indices" """
    # PRIORITÉ 1: Utiliser scores_detaille.style.tier pour déterminer Ancien/Neuf/Atypique
    scores_detaille = apartment.get('scores_detaille', {})
    style_score = scores_detaille.get('style', {})
    style_tier = style_score.get('tier', '')
    
    # Déterminer le nom du style selon le tier
    if style_tier == 'tier1':
        style_name = "Ancien"  # Haussmannien
    elif style_tier == 'tier2':
        style_name = "Atypique"  # Loft, atypique
    elif style_tier == 'tier3':
        style_name = "Neuf"  # Moderne, contemporain
    else:
        # Fallback: utiliser style_analysis
        style_analysis = apartment.get('style_analysis', {})
        style_data = style_analysis.get('style', {})
        style_type = style_data.get('type', '')
        
        if 'haussmann' in style_type.lower():
            style_name = "Ancien"
        elif 'atypique' in style_type.lower() or 'loft' in style_type.lower():
            style_name = "Atypique"
        elif 'moderne' in style_type.lower() or 'contemporain' in style_type.lower():
            style_name = "Neuf"
        else:
            style_name = "Non spécifié"
    
    # Récupérer la confiance depuis style_analysis
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    confidence = style_data.get('confidence')
    
    # Convertir confiance en pourcentage
    confidence_pct = None
    if confidence is not None:
        if isinstance(confidence, float) and 0 <= confidence <= 1:
            confidence_pct = int(confidence * 100)
        elif isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
            confidence_pct = int(confidence)
    
    # PRIORITÉ: Extraire la justification depuis scores_detaille.style.justification (comme cuisine/baignoire)
    scores_detaille = apartment.get('scores_detaille', {})
    style_score = scores_detaille.get('style', {})
    justification = style_score.get('justification', '')
    
    # Extraire les indices depuis justification - systématiquement ajoutés
    indices_str = None
    if justification:
        # Utiliser la justification comme indices si elle est disponible
        # La justification contient déjà une phrase qui justifie le côté ancien ou neuf
        indices_str = f"Style Indice: {justification}"
    else:
        # Fallback: chercher dans style_data.justification
        style_justification = style_data.get('justification', '')
        if style_justification:
            indices_str = f"Style Indice: {style_justification}"
        else:
            # Fallback 2: extraire depuis details ou style_haussmannien
            indices = []
            details = style_data.get('details', '')
            if details:
                # Vérifier que details est une string avant d'appeler .lower()
                if isinstance(details, str):
                    # Chercher des mots-clés dans les détails
                    keywords = ['moulures', 'cheminée', 'parquet', 'hauteur sous plafond', 'moldings', 'fireplace']
                    found_keywords = [kw for kw in keywords if kw.lower() in details.lower()]
                    if found_keywords:
                        indices = found_keywords[:3]  # Limiter à 3 indices
            
            # Si pas d'indices dans details, chercher dans style_haussmannien
            if not indices:
                style_haussmannien = apartment.get('style_haussmannien', {})
                elements = style_haussmannien.get('elements', {})
                # Vérifier que elements est un dict avant d'appeler .get()
                if isinstance(elements, dict):
                    architectural = elements.get('architectural', [])
                    if architectural:
                        indices = architectural[:3]
                elif isinstance(elements, list):
                    # Si elements est directement une liste, l'utiliser
                    if elements:
                        indices = elements[:3]
            
            if indices:
                indices_str = "Style Indice: " + " · ".join(indices)
            else:
                # Dernier fallback: créer une phrase basée sur le style détecté
                if 'haussmann' in style_type.lower():
                    indices_str = "Style Indice: Style ancien détecté (moulures, parquet, hauteur sous plafond)"
                elif 'moderne' in style_type.lower() or 'contemporain' in style_type.lower():
                    indices_str = "Style Indice: Style neuf détecté (design épuré, matériaux modernes)"
                else:
                    indices_str = "Style Indice: Style non spécifié"
    
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
    
    # Extraire les indices depuis exposition - même format que criteria/exposition.py
    indices_parts = []
    exposition = apartment.get('exposition', {})
    description = apartment.get('description', '').lower()
    caracteristiques = apartment.get('caracteristiques', '').lower()
    text = f"{description} {caracteristiques}"
    
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
    
    # Exposition directionnelle - chercher dans le texte d'abord
    exposition_dir = exposition.get('exposition', '')
    if exposition_dir and exposition_dir.lower() not in ['inconnue', 'inconnu', 'non spécifiée']:
        # Vérifier si mentionné dans le texte
        expo_lower = exposition_dir.lower()
        if expo_lower in text:
            indices_parts.append(f"{exposition_dir} mentionné")
        else:
            indices_parts.append(f"{exposition_dir} détecté")
    
    # Chercher aussi dans le texte pour des expositions non détectées par l'extracteur
    expo_keywords = {
        'nord': 'Nord',
        'nord-est': 'Nord Est',
        'nord est': 'Nord Est',
        'nord-ouest': 'Nord Ouest',
        'nord ouest': 'Nord Ouest',
        'sud': 'Sud',
        'sud-est': 'Sud Est',
        'sud est': 'Sud Est',
        'sud-ouest': 'Sud Ouest',
        'sud ouest': 'Sud Ouest',
        'est': 'Est',
        'ouest': 'Ouest'
    }
    for keyword, label in expo_keywords.items():
        if keyword in text and not any(label.lower() in part.lower() for part in indices_parts):
            indices_parts.append(f"{label} mentionné")
            break
    
    # Vis-à-vis depuis description ou exposition
    if 'vis-à-vis' in text or 'vis à vis' in text or 'pas de vis' in text:
        if 'pas de vis' in text:
            indices_parts.append("Pas de vis à vis")
        else:
            indices_parts.append("Vis à vis")
    
    # Terrasse/Balcon - chercher dans le texte
    if 'grande terrasse' in text or 'grand terrasse' in text:
        indices_parts.append("Grande terrasse")
    elif 'terrasse' in text:
        indices_parts.append("Terrasse mentionnée")
    elif 'balcon' in text:
        indices_parts.append("Balcon mentionné")
    
    # Formater avec le préfixe "Expo Indice:"
    indices_str = None
    if indices_parts:
        indices_str = "Expo Indice: " + " · ".join(indices_parts)
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str
    }

def format_cuisine_criterion(apartment):
    """Formate le critère Cuisine: "Ouverte / Fermée (X% confiance) + indices" """
    # PRIORITÉ: Utiliser le résultat final depuis scores_detaille (après validation croisée texte + photos)
    scores_detaille = apartment.get('scores_detaille', {})
    cuisine_score = scores_detaille.get('cuisine', {})
    cuisine_details = cuisine_score.get('details', {})
    photo_validation = cuisine_details.get('photo_validation', {})
    
    # Chercher la valeur depuis photo_result (résultat final après validation)
    cuisine_ouverte = None
    confidence = cuisine_details.get('confidence')
    
    if isinstance(photo_validation, dict):
        photo_result = photo_validation.get('photo_result', {})
        # Le résultat final est dans photo_result après validation croisée
        cuisine_ouverte = photo_result.get('ouverte')
    
    # Fallback: utiliser style_analysis si pas trouvé
    style_analysis = apartment.get('style_analysis', {})
    cuisine_data = style_analysis.get('cuisine', {}) if style_analysis else {}
    details = cuisine_data.get('details', '') if cuisine_data else ''
    
    if cuisine_ouverte is None:
        cuisine_ouverte = cuisine_data.get('ouverte', False) if cuisine_data else False
        if confidence is None:
            confidence = cuisine_data.get('confidence') if cuisine_data else None
    
    # Si toujours None, vérifier le tier pour déduire
    if cuisine_ouverte is None:
        tier = cuisine_score.get('tier', 'tier3')
        # tier2 = cuisine non trouvée (5pts) → afficher "Non spécifié"
        if tier == 'tier2':
            main_value = "Non spécifié"
            return {
                'main_value': main_value,
                'confidence': None,
                'indices': "Cuisine Indice: Non spécifié"
            }
        # tier1 = ouverte (10pts), tier3 = fermée (0pts)
        cuisine_ouverte = (tier == 'tier1')
    
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
    
    # Chercher les numéros d'images détectées depuis différentes sources
    detected_photos = []
    
    # Source 1: Depuis photo_validation (déjà récupéré plus haut)
    if isinstance(photo_validation, dict):
        photo_result = photo_validation.get('photo_result', {})
        detected_photos = photo_result.get('detected_photos', [])
    
    # Source 2: Si pas trouvé, chercher dans style_analysis directement (via photo_validation)
    if not detected_photos:
        photo_validation_cuisine = cuisine_data.get('photo_validation', {}) if cuisine_data else {}
        if isinstance(photo_validation_cuisine, dict):
            photo_result = photo_validation_cuisine.get('photo_result', {})
            detected_photos = photo_result.get('detected_photos', [])
    
    # Source 3: Chercher dans les détails du style_analysis
    if not detected_photos and details:
        # Essayer d'extraire depuis details si formaté différemment
        import re
        photo_matches = re.findall(r'photo\s*(\d+)', details.lower())
        if photo_matches:
            detected_photos = [int(p) for p in photo_matches]
    
    # Formater les indices avec les numéros d'images
    indices_parts = []
    
    # Vérifier le statut de validation pour savoir si on peut utiliser detected_photos
    validation_status = cuisine_details.get('validation_status', '')
    
    # Récupérer photo_result.ouverte pour vérifier la cohérence
    photo_ouverte_result = None
    if isinstance(photo_validation, dict):
        photo_result_for_check = photo_validation.get('photo_result', {})
        photo_ouverte_result = photo_result_for_check.get('ouverte')
    
    # Si détecté par photos ET que le résultat photo correspond au résultat final
    # (pas de conflit ou photos confirment le résultat final)
    if detected_photos and validation_status != 'conflict':
        # Pas de conflit → utiliser detected_photos avec main_value
        photos_str = ", ".join([f"image {p}" for p in detected_photos])
        if main_value == "Ouverte":
            indices_parts.append(f"Cuisine ouverte détectée {photos_str}")
        else:
            indices_parts.append(f"Cuisine fermée détectée {photos_str}")
    elif detected_photos and validation_status == 'conflict':
        # Conflit détecté → vérifier si photo_result correspond au résultat final
        # Si photo_result.ouverte correspond à main_value, on peut utiliser detected_photos
        # Sinon, ne pas utiliser detected_photos car elles contredisent le résultat final
        if (photo_ouverte_result is True and main_value == "Ouverte") or \
           (photo_ouverte_result is False and main_value == "Fermée"):
            # Les photos confirment le résultat final → utiliser detected_photos
            photos_str = ", ".join([f"image {p}" for p in detected_photos])
            if main_value == "Ouverte":
                indices_parts.append(f"Cuisine ouverte détectée {photos_str}")
            else:
                indices_parts.append(f"Cuisine fermée détectée {photos_str}")
        else:
            # Les photos contredisent le résultat final → ne pas afficher detected_photos
            # Afficher seulement que c'est détecté sans numéros d'images
            if main_value == "Ouverte":
                indices_parts.append("Cuisine ouverte détectée")
            else:
                indices_parts.append("Cuisine fermée détectée")
    elif details and ('analyse photo' in details.lower() or 'photo' in details.lower()):
        # Fallback: utiliser les détails existants
        indices_parts.append(f"Analyse photo : Cuisine {main_value.lower()} détectée")
    else:
        # Si aucune détection photo, dire qu'on a analysé les 5 premières images
        indices_parts.append(f"Cuisine {main_value.lower()} - 5 premières images analysées")
    
    # Formater avec le préfixe "Cuisine Indice:"
    indices_str = "Cuisine Indice: " + " · ".join(indices_parts)
    
    return {
        'main_value': main_value,
        'confidence': confidence_pct,
        'indices': indices_str
    }

def format_baignoire_criterion(apartment, baignoire_extractor=None):
    """Formate le critère Baignoire: "Oui / Non / Non spécifié (confiance) + indices" """
    # PRIORITÉ: Utiliser le résultat final depuis scores_detaille
    scores_detaille = apartment.get('scores_detaille', {})
    baignoire_score = scores_detaille.get('baignoire', {})
    baignoire_details = baignoire_score.get('details', {})
    tier = baignoire_score.get('tier', 'tier3')
    
    # tier2 = salle de bain non trouvée (5pts) → afficher "Non spécifié"
    if tier == 'tier2':
        return {
            'main_value': "Non spécifié",
            'confidence': None,
            'indices': "Baignoire Indice: Non spécifié"
        }
    
    try:
        if baignoire_extractor is None:
            baignoire_extractor = BaignoireExtractor()
        baignoire_data = baignoire_extractor.extract_baignoire_ultimate(apartment)
        
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
        
        # Extraire les indices depuis justification - systématiquement ajoutés
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
        
        # Formater avec le préfixe "Baignoire:"
        indices_str = None
        if indices:
            indices_str = "Baignoire: " + indices
        else:
            # Fallback si aucun indice trouvé
            indices_str = "Baignoire: Non spécifié"
        
        return {
            'main_value': main_value,
            'confidence': confidence_pct,
            'indices': indices_str
        }
    except Exception as e:
        # Fallback si erreur - toujours ajouter la phrase indice
        return {
            'main_value': "Non",
            'confidence': None,
            'indices': "Baignoire: Non spécifié"
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
    
    # Priorité 2: photos (nouveau système avec photo1.jpg, photo2.jpg, etc.)
    if not photo_urls and os.path.exists(photos_dir):
        photo_files = []
        for filename in os.listdir(photos_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                # Vérifier que ce n'est pas un logo
                is_excluded = any(pattern.lower() in filename.lower() for pattern in excluded_patterns)
                if not is_excluded:
                    file_path = os.path.join(photos_dir, filename)
                    file_mtime = os.path.getmtime(file_path)
                    # Extraire le numéro pour trier (photo1.jpg -> 1, photo2.jpg -> 2, etc.)
                    try:
                        # Si le nom commence par "photo" suivi d'un chiffre
                        if filename.startswith('photo') and filename[5:].replace('.jpg', '').replace('.jpeg', '').replace('.png', '').isdigit():
                            photo_num = int(filename[5:].replace('.jpg', '').replace('.jpeg', '').replace('.png', ''))
                            photo_files.append((filename, photo_num, file_mtime))
                        else:
                            # Sinon utiliser la date de modification
                            photo_files.append((filename, 9999, file_mtime))
                    except:
                        photo_files.append((filename, 9999, file_mtime))
        
        if photo_files:
            # Trier d'abord par numéro (photo1, photo2, etc.), puis par date
            photo_files.sort(key=lambda x: (x[1], x[2]))
            for filename, _, _ in photo_files:
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
    
    # Créer une seule instance de BaignoireExtractor pour tous les appartements (évite réinitialisations lourdes)
    baignoire_extractor = BaignoireExtractor()
    
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
            margin: 0;
            padding: 0;
        }}
        
        .container {{
            width: 100%;
            margin: 0 auto;
            padding: 30px;
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
            margin: 0;
            padding: 0;
            width: 100%;
            grid-auto-flow: row;
        }}
        
        .scorecard {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            overflow: hidden;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 100%;
            max-width: 100%;
            margin: 0;
            display: flex;
            flex-direction: column;
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
            isolation: isolate;
            width: 100%;
            flex-shrink: 0;
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
            white-space: nowrap;
            min-width: fit-content;
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
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
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
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        }}
        
        .criterion:last-child {{
            border-bottom: none;
            padding-bottom: 0;
            margin-bottom: 0;
        }}
        
        .criterion-content {{
            display: flex;
            flex-direction: column;
            min-width: 0;
        }}
        
        .criterion-name {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            font-size: 16px;
            font-weight: 500;
            color: #212529;
            margin-bottom: 0;
            word-wrap: break-word;
            overflow-wrap: break-word;
            text-transform: none !important;
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
        
        .criterion-score-badge {{
            font-family: 'Cera Pro', 'CeraPro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
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
            align-self: center;
            white-space: nowrap;
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
        
        @media (max-width: 1000px) {{
            .apartments-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 600px) {{
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
            'cuisine': {'name': 'Cuisine', 'max': 10, 'formatter': format_cuisine_criterion},
            'baignoire': {'name': 'Baignoire', 'max': 10, 'formatter': format_baignoire_criterion}
        }
        
        # Calculer le mega score comme la somme des scores affichés seulement
        # Mettre en cache le résultat baignoire pour éviter de recalculer plusieurs fois
        baignoire_data_cache = None
        mega_score = 0
        for key, info in criteria_mapping.items():
            if key == 'baignoire':
                # Pour baignoire, utiliser extract_baignoire (réutiliser l'instance unique et mettre en cache)
                if baignoire_data_cache is None:
                    try:
                        baignoire_data_cache = baignoire_extractor.extract_baignoire_ultimate(apartment)
                    except:
                        baignoire_data_cache = {'score': 0}
                mega_score += baignoire_data_cache.get('score', 0)
            elif key in scores_detaille:
                criterion = scores_detaille[key]
                mega_score += criterion.get('score', 0)
        
        # Arrondir le mega score à 1 décimale si nécessaire
        mega_score = round(mega_score, 1)
        # Formater pour l'affichage (enlever .0 si entier, s'assurer que c'est toujours un nombre valide)
        if mega_score == int(mega_score):
            mega_score_display = int(mega_score)
        else:
            mega_score_display = mega_score
        # S'assurer que le score est toujours un nombre valide (pas None, pas "00")
        if mega_score_display is None or (isinstance(mega_score_display, str) and mega_score_display.strip() == ""):
            mega_score_display = 0
        # Convertir en string pour l'affichage (pour éviter les problèmes de formatage)
        mega_score_display = str(mega_score_display)
        # Correction: si le score affiche "00", le remplacer par "0"
        if mega_score_display == "00":
            mega_score_display = "0"
        
        # Récupérer toutes les photos de l'appartement
        all_photos = get_all_apartment_photos(apartment)
        
        # Couleur du mega score badge (basée sur les 90 pts max des critères affichés)
        score_badge_color = get_score_badge_color(mega_score, 90)
        
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
            # Générer un dot pour chaque photo (le JavaScript s'occupera de cacher ceux qui correspondent à des slides invalides)
            for dot_idx in range(len(all_photos)):
                dots_html += f'<div class="carousel-dot {"active" if dot_idx == 0 else ""}" data-slide-index="{dot_idx}" onclick="event.stopPropagation(); goToSlide(\'{carousel_id}\', {dot_idx})"></div>'
            
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
                    # Pour baignoire, réutiliser les données en cache (évite recalcul)
                    if baignoire_data_cache is None:
                        try:
                            baignoire_data_cache = baignoire_extractor.extract_baignoire_ultimate(apartment)
                        except:
                            baignoire_data_cache = {'score': 0, 'tier': 'tier3'}
                    score = baignoire_data_cache.get('score', 0)
                    tier = baignoire_data_cache.get('tier', 'tier3')
                
                # Classe du badge de score basée sur le tier, pas le pourcentage
                badge_class = get_tier_badge_class(tier)
                
                # Utiliser la fonction de formatage spécifique (passer baignoire_extractor si nécessaire)
                if key == 'baignoire':
                    formatted = format_baignoire_criterion(apartment, baignoire_extractor)
                else:
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
                            <div class="criterion-content">
                                <div class="criterion-name">{info['name']}</div>
                                <div class="criterion-details">{details_html}</div>
                            </div>
                            <span class="criterion-score-badge {badge_class}">{score} pts</span>
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
            // Créer un mapping entre les indices de dots et les indices réels de slides visibles
            const track = document.getElementById(carouselId + '-track');
            const dotToSlideMap = [];
            let actualTotal = totalSlides;
            
            if (track) {
                const slides = track.querySelectorAll('.carousel-slide');
                // Créer le mapping : pour chaque slide, si elle est visible, ajouter son index réel
                slides.forEach((slide, realIndex) => {
                    const style = window.getComputedStyle(slide);
                    if (style.display !== 'none' && style.visibility !== 'hidden') {
                        dotToSlideMap.push(realIndex);
                    }
                });
                actualTotal = dotToSlideMap.length;
            } else {
                // Fallback : créer un mapping linéaire si pas de track trouvé
                for (let i = 0; i < totalSlides; i++) {
                    dotToSlideMap.push(i);
                }
            }
            
            carouselStates[carouselId] = { 
                current: 0, 
                total: actualTotal,
                dotToSlideMap: dotToSlideMap  // Mapping dot index -> slide index réel
            };
            
            // Cacher les dots au-delà du nombre réel de slides visibles
            const container = document.querySelector(`[data-carousel-id="${carouselId}"]`);
            if (container) {
                const dots = container.querySelectorAll('.carousel-dot');
                dots.forEach((dot, dotIndex) => {
                    if (dotIndex >= actualTotal) {
                        dot.style.display = 'none';
                    }
                });
            }
            
            // Positionner immédiatement le carousel à la première slide
            updateCarousel(carouselId);
        }
        
        function updateCarousel(carouselId) {
            const track = document.getElementById(carouselId + '-track');
            const state = carouselStates[carouselId];
            
            if (!track || !state) return;
            
            // Valider que current est dans les limites
            if (state.current < 0) {
                state.current = 0;
            } else if (state.current >= state.total) {
                state.current = state.total - 1;
            }
            
            // Utiliser le mapping pour obtenir l'index réel de la slide
            const realSlideIndex = state.dotToSlideMap && state.dotToSlideMap[state.current] !== undefined 
                ? state.dotToSlideMap[state.current] 
                : state.current;
            
            const translateX = -realSlideIndex * 100;
            track.style.transform = `translateX(${translateX}%)`;
            
            // Update dots (ne mettre actif que si le dot correspond à une slide valide)
            const dots = track.parentElement.querySelectorAll('.carousel-dot');
            dots.forEach((dot, dotIdx) => {
                if (dotIdx === state.current && dotIdx < state.total) {
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
            
            // Valider que l'index est dans les limites
            if (index < 0 || index >= state.total) {
                console.warn(`Index ${index} hors limites pour carousel ${carouselId} (total: ${state.total})`);
                return;
            }
            
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
