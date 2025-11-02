#!/usr/bin/env python3
"""
Génération HTML simplifiée - UN SEUL générateur pour homepage.html
Utilise les modules criteria/ pour le formatage
"""

import json
import os
from datetime import datetime
from criteria import (
    format_localisation,
    format_prix,
    format_style,
    format_exposition,
    format_cuisine,
    format_baignoire
)
# BaignoireExtractor n'est plus importé ici pour éviter les blocages
# L'extraction est faite dans criteria/baignoire.py avec fallback texte rapide


def load_scored_apartments():
    """Charge les appartements scorés depuis data/scores.json"""
    try:
        with open('data/scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Fichier data/scores.json non trouvé")
        return []


def get_all_apartment_photos(apartment):
    """Récupère toutes les photos d'un appartement (URLs ou fichiers locaux)"""
    photos = []
    
    # Priorité 1: photos depuis données scrapées
    scraped_photos = apartment.get('photos', [])
    for photo in scraped_photos:
        if isinstance(photo, dict):
            photo_url = photo.get('url')
        else:
            photo_url = photo
        
        if photo_url:
            photos.append(photo_url)
    
    # Priorité 2: photos depuis dossier local
    apartment_id = apartment.get('id')
    if apartment_id:
        photos_dir = f"data/photos/{apartment_id}"
        if os.path.exists(photos_dir):
            photo_files = sorted([f for f in os.listdir(photos_dir) if f.endswith(('.jpg', '.jpeg', '.png'))])
            for photo_file in photo_files[:5]:  # Limiter à 5 photos
                photos.append(f"{photos_dir}/{photo_file}")
    
    return photos[:5]  # Max 5 photos


def format_prix_k(prix_str):
    """Convertit un prix en format k€ (ex: "775 000 €" -> "775k")"""
    import re
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


def format_apartment_info(apartment):
    """Formate les infos principales de l'appartement
    
    Titre: "750k · Pyrénées" (prix en k + quartier)
    Subtitle: "67 m² · 1er étage · Moderne" (m² · étage · style)
    """
    import re
    from criteria.localisation import get_quartier_name
    
    # Titre: prix en k + quartier
    prix = apartment.get('prix', '')
    prix_k = format_prix_k(prix) if prix else None
    quartier = get_quartier_name(apartment)
    
    title_parts = []
    if prix_k:
        title_parts.append(prix_k)
    if quartier:
        title_parts.append(quartier)
    
    title = ' · '.join(title_parts) if title_parts else apartment.get('titre', 'Appartement')
    
    # Subtitle: m² · étage · style
    surface = apartment.get('surface', '')
    # Extraire juste le nombre de m²
    surface_match = re.search(r'(\d+)', surface) if surface else None
    surface_str = f"{surface_match.group(1)} m²" if surface_match else None
    
    # Extraire l'étage depuis plusieurs sources
    etage_str = None
    
    # Source 1: champ etage direct
    etage = apartment.get('etage', '')
    if etage:
        etage_match = re.search(r'(\d+)(?:er?|e|ème?)\s*étage', str(etage), re.IGNORECASE)
        if etage_match:
            num = etage_match.group(1)
            if num == '1':
                etage_str = "1er étage"
            else:
                etage_str = f"{num}e étage"
        elif 'rdc' in str(etage).lower() or 'rez' in str(etage).lower():
            etage_str = "RDC"
    
    # Source 2: description si pas trouvé
    if not etage_str:
        description = apartment.get('description', '')
        caracteristiques = apartment.get('caracteristiques', '')
        text = f"{description} {caracteristiques}".lower()
        
        # Chercher "1er étage", "2e étage", etc.
        etage_match = re.search(r'(\d+)(?:er?|e|ème?)\s*étage', text, re.IGNORECASE)
        if etage_match:
            num = etage_match.group(1)
            if num == '1':
                etage_str = "1er étage"
            else:
                etage_str = f"{num}e étage"
        elif 'rdc' in text or 'rez-de-chaussée' in text or 'rez de chaussée' in text:
            etage_str = "RDC"
        # Chercher aussi "au 3e", "au 4e", etc.
        elif not etage_str:
            etage_match = re.search(r'au\s+(\d+)(?:er?|e|ème?)', text, re.IGNORECASE)
            if etage_match:
                num = etage_match.group(1)
                if num == '1':
                    etage_str = "1er étage"
                else:
                    etage_str = f"{num}e étage"
    
    # Style depuis style_analysis
    style_str = None
    style_analysis = apartment.get('style_analysis', {})
    style_data = style_analysis.get('style', {})
    style_type = style_data.get('type', '').lower()
    
    # Ancien / Atypique / Neuf
    style_type_lower = style_type.lower() if style_type else ''
    if 'haussmann' in style_type_lower:
        style_str = "Ancien"
    elif 'loft' in style_type_lower or 'atypique' in style_type_lower or 'unique' in style_type_lower or 'original' in style_type_lower:
        style_str = "Atypique"
    elif style_type and style_type not in ['autre', 'inconnu']:
        # Tout le reste = Neuf
        style_str = "Neuf"
    
    subtitle_parts = []
    if surface_str:
        subtitle_parts.append(surface_str)
    if etage_str:
        subtitle_parts.append(etage_str)
    if style_str:
        subtitle_parts.append(style_str)
    
    subtitle = ' · '.join(subtitle_parts) if subtitle_parts else 'Informations non disponibles'
    
    return {
        'title': title,
        'subtitle': subtitle
    }


def get_score_badge_color(score, max_score):
    """Détermine la couleur du badge de score"""
    percentage = (score / max_score) * 100
    if percentage >= 80:
        return "#00966D"  # Vert
    elif percentage >= 60:
        return "#FFC107"  # Jaune
    else:
        return "#F85457"  # Rouge


def get_score_badge_class(score, max_score):
    """Détermine la classe du badge de score"""
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


def generate_html(apartments):
    """
    Génère le HTML depuis la liste d'appartements scorés
    
    Args:
        apartments: List de dicts avec données scrapées + scores
        
    Returns:
        String HTML complet
    """
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HomeScore - Évaluation d'Appartements</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8f9fa;
            color: #212529;
            line-height: 1.5;
            font-size: 14px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 5px;
            font-weight: 700;
        }
        
        .apartments-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .scorecard {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            overflow: hidden;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .scorecard:hover {
            box-shadow: 0 6px 16px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        .apartment-image-container {
            position: relative;
            width: 100%;
            height: 286px;
        }
        
        .apartment-image {
            width: 100%;
            height: 286px;
            background-size: cover;
            background-position: center;
            border-radius: 8px 8px 0 0;
        }
        
        .apartment-image-placeholder {
            width: 100%;
            height: 286px;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
        }
        
        .score-badge-top {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 16px;
            z-index: 10;
        }
        
        .carousel-container {
            position: relative;
            width: 100%;
            height: 286px;
            overflow: hidden;
        }
        
        .carousel-track {
            display: flex;
            transition: transform 0.3s ease;
            height: 100%;
        }
        
        .carousel-slide {
            min-width: 100%;
            height: 100%;
        }
        
        .carousel-slide img {
            width: 100%;
            height: 286px;
            object-fit: cover;
        }
        
        .carousel-nav {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(255, 255, 255, 0.9);
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            cursor: pointer;
            z-index: 10;
            font-size: 20px;
            color: #333;
        }
        
        .carousel-nav.prev {
            left: 10px;
        }
        
        .carousel-nav.next {
            right: 10px;
        }
        
        .carousel-dots {
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 6px;
            z-index: 10;
        }
        
        .carousel-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .carousel-dot.active {
            background: white;
            width: 24px;
            border-radius: 4px;
        }
        
        .apartment-info {
            padding: 24px;
        }
        
        .apartment-title {
            font-size: 20px;
            font-weight: 500;
            color: #212529;
            margin-bottom: 4px;
        }
        
        .apartment-subtitle {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 24px;
        }
        
        .criterion {
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        }
        
        .criterion:last-child {
            border-bottom: none;
        }
        
        .criterion-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0;
            gap: 12px;
        }
        
        .criterion-name {
            font-size: 14px;
            font-weight: 500;
            color: #212529;
            flex: 1;
        }
        
        .criterion-score-badge {
            font-size: 14px;
            font-weight: 500;
            padding: 4px 12px;
            border-radius: 9999px;
            flex-shrink: 0;
        }
        
        .criterion-score-badge.green {
            color: #00966D;
            background: rgba(0, 150, 109, 0.1);
        }
        
        .criterion-score-badge.yellow {
            color: #F59E0B;
            background: rgba(245, 158, 11, 0.1);
        }
        
        .criterion-score-badge.red {
            color: #F85457;
            background: rgba(248, 84, 87, 0.1);
        }
        
        .tier-label {
            font-weight: 600;
        }
        
        .tier-label.good {
            color: #00966D;
        }
        
        .tier-label.moyen {
            color: #F59E0B !important;
        }
        
        .criterion-details .tier-label.moyen {
            color: #F59E0B !important;
        }
        
        .tier-label.bad {
            color: #F85457;
        }
        
        .criterion-details {
            font-size: 13px;
            color: #6c757d;
            margin-top: 4px;
        }
        
        .criterion-details .tier-label {
            font-weight: 600;
        }
        
        .criterion-details .tier-label.good {
            color: #00966D !important;
        }
        
        .criterion-details .tier-label.moyen {
            color: #F59E0B !important;
        }
        
        .criterion-details .tier-label.bad {
            color: #F85457 !important;
        }
        
        .criterion-sub-details {
            font-size: 12px;
            color: #999;
            margin-top: 2px;
        }
        
        .confidence-badge {
            font-size: 10px;
            font-weight: 500;
            color: rgba(0, 0, 0, 0.5);
            background: rgba(0, 0, 0, 0.1);
            padding: 0 8px;
            height: 18px;
            line-height: 18px;
            border-radius: 9999px;
            margin-left: 4px;
            display: inline-block;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        @media (max-width: 768px) {
            .apartments-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 HomeScore</h1>
            <p>Évaluation d'appartements avec analyse IA</p>
        </div>
        <div class="apartments-grid">
"""
    
    # Trier par score décroissant
    sorted_apartments = sorted(apartments, key=lambda x: x.get('score_total', 0), reverse=True)
    
    # Mapping des critères
    criteria_mapping = {
        'localisation': {'name': 'LOCALISATION', 'max': 20, 'formatter': format_localisation},
        'prix': {'name': 'PRIX', 'max': 20, 'formatter': format_prix},
        'style': {'name': 'STYLE', 'max': 20, 'formatter': format_style},
        'ensoleillement': {'name': 'EXPOSITION', 'max': 10, 'formatter': format_exposition},
        'cuisine': {'name': 'CUISINE OUVERTE', 'max': 10, 'formatter': format_cuisine},
        'baignoire': {'name': 'BAIGNOIRE', 'max': 10, 'formatter': format_baignoire}
    }
    
    for i, apartment in enumerate(sorted_apartments, 1):
        score_total = apartment.get('score_total', 0)
        apartment_info = format_apartment_info(apartment)
        scores_detaille = apartment.get('scores_detaille', {})
        all_photos = get_all_apartment_photos(apartment)
        score_badge_color = get_score_badge_color(score_total, 100)
        apartment_url = apartment.get('url', '#')
        carousel_id = f"carousel-{i}"
        
        # Générer HTML des photos
        if len(all_photos) > 1:
            slides_html = ""
            for photo_idx, photo_url in enumerate(all_photos):
                slides_html += f'<div class="carousel-slide"><img src="{photo_url}" alt="Photo {photo_idx + 1}" onerror="this.parentElement.style.display=\'none\'"></div>'
            
            dots_html = ""
            for dot_idx in range(len(all_photos)):
                dots_html += f'<div class="carousel-dot {"active" if dot_idx == 0 else ""}" onclick="event.stopPropagation(); goToSlide(\'{carousel_id}\', {dot_idx})"></div>'
            
            photo_html = f"""
                <div class="apartment-image-container">
                    <div class="score-badge-top" style="background: {score_badge_color};">{score_total}</div>
                    <div class="carousel-container" data-carousel-id="{carousel_id}">
                        <button class="carousel-nav prev" onclick="event.stopPropagation(); prevSlide('{carousel_id}')">‹</button>
                        <div class="carousel-track" id="{carousel_id}-track">
                            {slides_html}
                        </div>
                        <button class="carousel-nav next" onclick="event.stopPropagation(); nextSlide('{carousel_id}')">›</button>
                        <div class="carousel-dots">{dots_html}</div>
                    </div>
                </div>
            """
        elif len(all_photos) == 1:
            photo_url = all_photos[0]
            photo_html = f'<div class="apartment-image-container"><div class="score-badge-top" style="background: {score_badge_color};">{score_total}</div><div class="apartment-image" style="background-image: url(\'{photo_url}\')"></div></div>'
        else:
            photo_html = f'<div class="apartment-image-container"><div class="score-badge-top" style="background: {score_badge_color};">{score_total}</div><div class="apartment-image-placeholder">📷</div></div>'
        
        html += f"""
            <div class="scorecard" onclick="window.open('{apartment_url}', '_blank')">
                {photo_html}
                <div class="apartment-info">
                    <div class="apartment-title">{apartment_info['title']}</div>
                    <div class="apartment-subtitle">{apartment_info['subtitle']}</div>
"""
        
        # Générer les critères
        for key, info in criteria_mapping.items():
            if key == 'baignoire' or key in scores_detaille:
                score = 0
                tier = 'tier3'  # Défaut
                if key in scores_detaille:
                    criterion = scores_detaille[key]
                    score = criterion.get('score', 0)
                    tier = criterion.get('tier', 'tier3')
                elif key == 'baignoire':
                    # Pour baignoire, pas de score dans scores_detaille, utiliser 0 par défaut
                    # Le formatage sera fait par format_baignoire() qui utilise l'analyse texte rapide
                    score = 0
                    tier = 'tier3'
                
                # Classe du badge basée sur le tier, pas le pourcentage
                badge_class = get_tier_badge_class(tier)
                formatted = info['formatter'](apartment)
                main_value = formatted.get('main_value', 'Non spécifié')
                confidence = formatted.get('confidence')
                indices = formatted.get('indices')
                
                confidence_html = ""
                if confidence is not None:
                    confidence_html = f'<span class="confidence-badge">{confidence}% confiance</span>'
                
                details_html = f'{main_value}{confidence_html}'
                if indices:
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
        const carouselStates = {};
        
        function initCarousel(carouselId) {
            const container = document.querySelector(`[data-carousel-id="${carouselId}"]`);
            if (!container) return;
            const track = container.querySelector('.carousel-track');
            const slides = track.querySelectorAll('.carousel-slide');
            carouselStates[carouselId] = { current: 0, total: slides.length };
            updateCarousel(carouselId);
        }
        
        function updateCarousel(carouselId) {
            const track = document.getElementById(carouselId + '-track');
            const state = carouselStates[carouselId];
            if (!track || !state) return;
            
            track.style.transform = `translateX(-${state.current * 100}%)`;
            
            const dots = track.parentElement.querySelectorAll('.carousel-dot');
            dots.forEach((dot, idx) => {
                dot.classList.toggle('active', idx === state.current);
            });
        }
        
        function prevSlide(carouselId) {
            const state = carouselStates[carouselId];
            if (!state) return;
            state.current = (state.current > 0) ? state.current - 1 : state.total - 1;
            updateCarousel(carouselId);
        }
        
        function nextSlide(carouselId) {
            const state = carouselStates[carouselId];
            if (!state) return;
            state.current = (state.current < state.total - 1) ? state.current + 1 : 0;
            updateCarousel(carouselId);
        }
        
        function goToSlide(carouselId, index) {
            const state = carouselStates[carouselId];
            if (!state) return;
            state.current = index;
            updateCarousel(carouselId);
        }
        
        // Initialiser tous les carousels au chargement
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('[data-carousel-id]').forEach(container => {
                const carouselId = container.getAttribute('data-carousel-id');
                initCarousel(carouselId);
            });
        });
    </script>
</body>
</html>
"""
    
    return html


def main():
    """Fonction principale"""
    print("📊 Génération du rapport HTML...")
    
    apartments = load_scored_apartments()
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"✅ {len(apartments)} appartements chargés")
    
    html = generate_html(apartments)
    
    # Sauvegarder
    os.makedirs('output', exist_ok=True)
    output_file = 'output/homepage.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML généré: {output_file}")


if __name__ == "__main__":
    main()

