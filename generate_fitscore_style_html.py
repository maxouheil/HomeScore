#!/usr/bin/env python3
"""
Génération du rapport HTML avec le design EXACT de Fitscore
"""

import json
import os
from datetime import datetime

def load_scored_apartments():
    """Charge les appartements scorés"""
    try:
        with open('data/scores/all_apartments_scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Fichier de scores non trouvé")
        return []

def get_score_color_class(score, max_score):
    """Détermine la classe CSS du score"""
    percentage = (score / max_score) * 100
    if percentage >= 80:
        return "green"
    elif percentage >= 60:
        return "orange"
    else:
        return "red"

def get_score_badge_class(score, max_score):
    """Détermine la classe du badge de score"""
    percentage = (score / max_score) * 100
    if percentage >= 80:
        return ""
    elif percentage >= 60:
        return "orange"
    else:
        return "red"

def get_apartment_photo(apartment):
    """Récupère la première photo d'appartement téléchargée (depuis la bonne div)"""
    apartment_id = apartment.get('id', 'unknown')
    
    # Chercher les photos téléchargées localement (qui viennent de la bonne div)
    photos_dir = f"data/photos/{apartment_id}"
    if os.path.exists(photos_dir):
        # Prendre simplement la première photo trouvée (elles viennent toutes de la bonne div)
        for filename in sorted(os.listdir(photos_dir)):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                return f"../data/photos/{apartment_id}/{filename}"
    
    # Fallback: chercher dans les photos de l'appartement
    photos = apartment.get('photos', [])
    if photos and len(photos) > 0:
        for photo in photos:
            if isinstance(photo, dict):
                url = photo.get('url', '')
                alt = photo.get('alt', '').lower()
                # Filtrer les vraies photos d'appartements
                if ('upload_pro_ad' in url or 'upload_p' in url or 'media.apimo.pro' in url) and ('logement' in alt or 'appartement' in alt):
                    return url
            elif isinstance(photo, str):
                if 'upload_pro_ad' in photo or 'upload_p' in photo or 'media.apimo.pro' in photo:
                    return photo
    return ''

def format_apartment_info(apartment):
    """Formate les informations de l'appartement"""
    localisation = apartment.get('localisation', 'Non spécifié')
    surface = apartment.get('surface', 'Non spécifié')
    pieces = apartment.get('pieces', 'Non spécifié')
    prix = apartment.get('prix', 'Non spécifié')
    
    # Extraire les stations de métro
    transports = apartment.get('transports', [])
    stations_str = " · ".join(transports[:2]) if transports else ""
    
    return {
        'title': f"{localisation}",
        'subtitle': f"{surface} - {pieces} • {prix} • {stations_str}",
        'prix': prix
    }

def generate_fitscore_style_html(apartments):
    """Génère le HTML avec le design EXACT de Fitscore"""
    
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HomeScore - Rapport Appartements</title>
    <style>
        /* Fonts personnalisées */
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
        
        @font-face {{
            font-family: 'Cera Pro';
            src: url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&display=swap');
            font-weight: 400;
            font-style: normal;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', 'Cera Pro', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .header {{
            display: none;
        }}
        
        .stats {{
            display: none;
        }}
        
        .candidates-grid {{
            max-width: 1600px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 25px;
        }}
        
        .candidate-card {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            border: 1px solid #f0f0f0;
        }}
        
        .candidate-image-header {{
            position: relative;
            margin-bottom: 20px;
        }}
        
        .candidate-photo {{
            width: 100%;
            height: 200px;
            border-radius: 12px;
            object-fit: cover;
            flex-shrink: 0;
        }}
        
        .candidate-info {{
            margin-bottom: 20px;
        }}
        
        .candidate-name {{
            font-family: 'Cera Pro', 'Inter', sans-serif;
            font-size: 1.5rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 4px;
            line-height: 1.2;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .candidate-subtitle {{
            font-size: 0.85rem;
            color: #999;
            font-weight: 400;
            margin-bottom: 0;
        }}
        
        .candidate-score-badge {{
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0,0,0,0.8);
            color: white;
            font-size: 1.8rem;
            font-weight: 700;
            padding: 10px 18px;
            border-radius: 14px;
            display: inline-block;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        
        .candidate-score-badge.orange {{
            background: #fff3e0;
            color: #ff9800;
        }}
        
        .candidate-score-badge.red {{
            background: #ffebee;
            color: #e74c3c;
        }}
        
        .candidate-justification {{
            font-size: 0.9rem;
            line-height: 1.6;
            color: #333;
            margin-bottom: 20px;
            font-weight: 400;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .score-excellent {{ color: #27ae60; }}
        .score-good {{ color: #f39c12; }}
        .score-medium {{ color: #e67e22; }}
        .score-weak {{ color: #e74c3c; }}
        
        .scores-breakdown {{
            margin: 20px 0;
        }}
        
        .score-accordion {{
            margin-bottom: 0;
            border-bottom: 1px solid #f5f5f5;
        }}
        
        .score-accordion:last-child {{
            border-bottom: none;
        }}
        
        .score-accordion-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 18px 0;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .score-accordion-header:hover {{
            opacity: 0.7;
        }}
        
        .score-accordion-title {{
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            font-size: 0.9rem;
            color: #333;
            flex: 1;
        }}
        
        .score-accordion-score {{
            font-weight: 600;
            font-size: 0.9rem;
            margin-right: 10px;
        }}
        
        .score-accordion-score.green {{
            color: #27ae60;
        }}
        
        .score-accordion-score.orange {{
            color: #ff9800;
        }}
        
        .score-accordion-score.red {{
            color: #e74c3c;
        }}
        
        .score-accordion-badge {{
            font-size: 0.75rem;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
            margin-right: 10px;
            text-transform: uppercase;
        }}
        
        .score-accordion-badge:not(.orange):not(.red) {{
            background: #d4f4dd;
            color: #27ae60;
        }}
        
        .score-accordion-badge.orange {{
            background: #fff3e0;
            color: #ff9800;
        }}
        
        .score-accordion-badge.red {{
            background: #ffebee;
            color: #e74c3c;
        }}
        
        .score-accordion-arrow {{
            font-size: 0.8rem;
            color: #999;
            transition: transform 0.2s ease;
        }}
        
        .score-accordion-content {{
            display: none;
            padding: 0 0 20px 0;
        }}
        
        .score-accordion-content.active {{
            display: block;
        }}
        
        .score-accordion-body {{
            padding-top: 10px;
        }}
        
        .score-point-item {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 12px;
            gap: 12px;
        }}
        
        .score-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
            margin-top: 6px;
        }}
        
        .score-dot.good {{
            background: #27ae60;
        }}
        
        .score-dot.bad {{
            background: #e74c3c;
        }}
        
        .score-point-text {{
            font-size: 0.85rem;
            line-height: 1.5;
            color: #555;
            flex: 1;
        }}
        
        @media (max-width: 1200px) {{
            .candidates-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 768px) {{
            .candidates-grid {{
                grid-template-columns: 1fr;
            }}
            
            .candidate-card {{
                padding: 20px;
            }}
            
            .candidate-name {{
                font-size: 1.3rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="candidates-grid">
"""
    
    # Trier les appartements par score décroissant
    sorted_apartments = sorted(apartments, key=lambda x: x.get('score_total', 0), reverse=True)
    
    for apartment in sorted_apartments:
        score_total = apartment.get('score_total', 0)
        apartment_info = format_apartment_info(apartment)
        scores_detaille = apartment.get('scores_detaille', {})
        
        # Récupérer la photo de l'appartement
        photo_url = get_apartment_photo(apartment)
        photo_html = f'<img src="{photo_url}" alt="Photo d\'appartement" class="candidate-photo">' if photo_url else '<div class="candidate-photo" style="background: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #999; font-size: 0.8rem;">📷</div>'
        
        # Classes CSS pour le score
        score_class = get_score_color_class(score_total, 100)
        badge_class = get_score_badge_class(score_total, 100)
        
        html += f"""
        <div class="candidate-card">
            <div class="candidate-image-header">
                {photo_html}
                <div class="candidate-score-badge {badge_class}">{score_total}</div>
            </div>
            
            <div class="candidate-info">
                <div class="candidate-name">{apartment_info['title']}</div>
                <div class="candidate-subtitle">{apartment_info['subtitle']}</div>
            </div>
            
            <div class="candidate-justification">{apartment.get('recommandation', 'Aucune recommandation disponible')}</div>
            
            <div class="scores-breakdown">
"""
        
        # Afficher les critères de scoring avec accordion
        criteria_mapping = {
            'localisation': {'name': 'Localisation', 'max': 20},
            'prix': {'name': 'Prix', 'max': 20},
            'style': {'name': 'Style', 'max': 20},
            'ensoleillement': {'name': 'Exposition', 'max': 10},
            'cuisine': {'name': 'Cuisine ouverte', 'max': 10},
            'etage': {'name': 'Étage', 'max': 10}
        }
        
        for key, info in criteria_mapping.items():
            if key in scores_detaille:
                criterion = scores_detaille[key]
                score = criterion.get('score', 0)
                justification = criterion.get('justification', 'Non spécifié')
                
                # Couleur et badge
                score_class = get_score_color_class(score, info['max'])
                badge_class = get_score_badge_class(score, info['max'])
                badge_text = "EXCELLENT" if score >= info['max'] * 0.8 else "GOOD" if score >= info['max'] * 0.6 else "MOYEN" if score >= info['max'] * 0.4 else "FAIBLE"
                
                html += f"""
                <div class="score-accordion">
                    <div class="score-accordion-header" onclick="toggleAccordion(this)">
                        <span class="score-accordion-title">{info['name']}</span>
                        <span class="score-accordion-score {score_class}">{score}/{info['max']}</span>
                        <span class="score-accordion-badge {badge_class}">{badge_text}</span>
                        <span class="score-accordion-arrow">▾</span>
                    </div>
                    <div class="score-accordion-content">
                        <div class="score-accordion-body">
                            <div class="score-point-item">
                                <div class="score-dot good"></div>
                                <div class="score-point-text">{justification}</div>
                            </div>
                        </div>
                    </div>
                </div>
"""
        
        html += """
            </div>
        </div>
"""
    
    html += """
    </div>
    
    <script>
        function toggleAccordion(header) {
            const content = header.nextElementSibling;
            const arrow = header.querySelector('.score-accordion-arrow');
            
            if (content.classList.contains('active')) {
                content.classList.remove('active');
                arrow.style.transform = 'rotate(0deg)';
            } else {
                content.classList.add('active');
                arrow.style.transform = 'rotate(180deg)';
            }
        }
    </script>
</body>
</html>
"""
    
    return html

def main():
    """Fonction principale"""
    print("🏠 GÉNÉRATION DU RAPPORT HTML - STYLE FITSCORE")
    print("=" * 60)
    
    # Charger les appartements scorés
    apartments = load_scored_apartments()
    if not apartments:
        print("❌ Aucun appartement scoré trouvé")
        return
    
    print(f"📋 {len(apartments)} appartements trouvés")
    
    # Créer le répertoire de sortie
    os.makedirs("output", exist_ok=True)
    
    # Générer le HTML
    html_content = generate_fitscore_style_html(apartments)
    
    # Sauvegarder le fichier
    output_file = "output/scorecard_fitscore_style.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Rapport généré: {output_file}")
    print(f"🌐 Ouvrez le fichier dans votre navigateur pour voir le rapport")

if __name__ == "__main__":
    main()
