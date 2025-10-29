#!/usr/bin/env python3
"""
Génération du rapport HTML avec le design de scorecard
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
    if percentage >= 80:
        return '<span class="rating-badge good">EXCELLENT</span>'
    elif percentage >= 60:
        return '<span class="rating-badge moyen">BON</span>'
    else:
        return '<span class="rating-badge faible">MOYEN</span>'

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
        'subtitle': f"{surface} - {pieces} • {prix}",
        'stations': stations_str,
        'prix': prix
    }

def get_apartment_photo(apartment):
    """Récupère la première photo d'appartement (locale ou URL)"""
    apartment_id = apartment.get('id', 'unknown')
    
    # D'abord, chercher les photos téléchargées localement
    photos_dir = f"data/photos/{apartment_id}"
    if os.path.exists(photos_dir):
        # Chercher la première photo dans le dossier
        for filename in os.listdir(photos_dir):
            if filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.png'):
                # Chemin relatif depuis le dossier output/
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
        }}
        
        .apartment-image {{
            width: 100%;
            height: 220px;
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
        
        .apartment-image.no-photo::before {{
            content: "📷 Photo d'appartement";
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
        
        .rating-badge.excellent {{
            background: #4CAF50;
            color: white;
        }}
        
        .rating-badge.good {{
            background: #8BC34A;
            color: white;
        }}
        
        .rating-badge.moyen {{
            background: #FFC107;
            color: #333;
        }}
        
        .rating-badge.faible {{
            background: #FF9800;
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
        
        # Récupérer la photo de l'appartement
        photo_url = get_apartment_photo(apartment)
        photo_style = f"background-image: url('{photo_url}');" if photo_url else ""
        photo_class = "apartment-image" if photo_url else "apartment-image no-photo"
        
        # Couleur du score global
        score_color = get_score_color(score_total, 100)
        
        html += f"""
            <div class="scorecard">
                <div class="{photo_class}" style="{photo_style}"></div>
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
