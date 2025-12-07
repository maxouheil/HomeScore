#!/usr/bin/env python3
"""
Générateur de rapport HTML pour les appartements scorés
"""

import json
import os
from datetime import datetime

def load_apartment_data(apartment_id):
    """Charge les données d'un appartement"""
    try:
        apartment_file = f"data/appartements/{apartment_id}.json"
        with open(apartment_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def load_score_data(apartment_id):
    """Charge les scores d'un appartement"""
    try:
        score_file = f"data/scores/{apartment_id}_score.json"
        with open(score_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def get_score_color(score, max_score):
    """Retourne la couleur selon le score"""
    percentage = (score / max_score) * 100
    if percentage >= 80:
        return "#22c55e"  # Vert
    elif percentage >= 60:
        return "#f59e0b"  # Orange
    else:
        return "#ef4444"  # Rouge

def get_level_emoji(level):
    """Retourne l'emoji selon le niveau"""
    if "Excellent" in level:
        return "⭐️⭐️⭐️"
    elif "Bon" in level:
        return "⭐️⭐️"
    else:
        return "⭐️"

def generate_html_report():
    """Génère le rapport HTML"""
    print("📊 Génération du rapport HTML...")
    
    # Trouver tous les scores
    scores_dir = "data/scores"
    if not os.path.exists(scores_dir):
        print("❌ Aucun score trouvé dans data/scores")
        return False
    
    score_files = [f for f in os.listdir(scores_dir) if f.endswith('_score.json')]
    print(f"📋 {len(score_files)} scores trouvés")
    
    # Charger et trier les appartements par score
    apartments_with_scores = []
    for score_file in score_files:
        apartment_id = score_file.replace('_score.json', '')
        score_data = load_score_data(apartment_id)
        apartment_data = load_apartment_data(apartment_id)
        
        if score_data and apartment_data:
            apartments_with_scores.append({
                'id': apartment_id,
                'apartment': apartment_data,
                'score': score_data
            })
    
    # Trier par score décroissant
    apartments_with_scores.sort(key=lambda x: x['score'].get('score_global', 0), reverse=True)
    
    # Générer le HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HomeScore - Rapport Appartements</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        
        .apartments-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 30px;
        }}
        
        .apartment-card {{
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .apartment-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }}
        
        .apartment-image {{
            width: 100%;
            height: 250px;
            background: linear-gradient(45deg, #f0f0f0, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 1.1rem;
        }}
        
        .apartment-content {{
            padding: 25px;
        }}
        
        .apartment-title {{
            font-size: 1.3rem;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            line-height: 1.4;
        }}
        
        .apartment-price {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 15px;
        }}
        
        .apartment-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: #666;
        }}
        
        .score-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }}
        
        .score-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .score-global {{
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }}
        
        .score-level {{
            font-size: 1.1rem;
            color: #666;
        }}
        
        .score-axes {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }}
        
        .score-axe {{
            background: white;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #ddd;
        }}
        
        .score-axe-name {{
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .score-axe-value {{
            font-size: 1.2rem;
            font-weight: bold;
        }}
        
        .apartment-actions {{
            display: flex;
            gap: 10px;
        }}
        
        .btn {{
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 10px;
            font-weight: bold;
            text-decoration: none;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5a67d8;
            transform: translateY(-2px);
        }}
        
        .btn-secondary {{
            background: #f1f5f9;
            color: #475569;
        }}
        
        .btn-secondary:hover {{
            background: #e2e8f0;
        }}
        
        .no-data {{
            text-align: center;
            color: white;
            font-size: 1.2rem;
            margin-top: 50px;
        }}
        
        @media (max-width: 768px) {{
            .apartments-grid {{
                grid-template-columns: 1fr;
            }}
            
            .apartment-details {{
                grid-template-columns: 1fr;
            }}
            
            .score-axes {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 HomeScore</h1>
            <p>Rapport d'évaluation des appartements Jinka</p>
            <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(apartments_with_scores)}</div>
                <div class="stat-label">Appartements analysés</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len([a for a in apartments_with_scores if a['score'].get('score_global', 0) >= 75])}</div>
                <div class="stat-label">Score ≥ 75/100</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{round(sum(a['score'].get('score_global', 0) for a in apartments_with_scores) / len(apartments_with_scores), 1) if apartments_with_scores else 0}</div>
                <div class="stat-label">Score moyen</div>
            </div>
        </div>
        
        <div class="apartments-grid">
"""
    
    if not apartments_with_scores:
        html_content += """
            <div class="no-data">
                <p>Aucun appartement trouvé avec des scores</p>
            </div>
        """
    else:
        for item in apartments_with_scores:
            apartment = item['apartment']
            score = item['score']
            
            # Photo principale (première photo ou placeholder)
            main_photo = ""
            if apartment.get('photos') and len(apartment['photos']) > 0:
                main_photo = f'<img src="{apartment["photos"][0]}" alt="Appartement" style="width: 100%; height: 100%; object-fit: cover;">'
            else:
                main_photo = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 3rem;">🏠</div>'
            
            # Score global et niveau
            score_global = score.get('score_global', 0)
            fit_global = score.get('fit_global', 'Moyen')
            score_color = get_score_color(score_global, 100)
            
            # Axes de scoring
            axes_html = ""
            for axe in score.get('scores_par_axe', []):
                axe_name = axe.get('axe', '')
                axe_score = axe.get('score', 0)
                axe_max = axe.get('max', 0)
                axe_level = axe.get('niveau', 'Moyen')
                axe_color = get_score_color(axe_score, axe_max)
                
                axes_html += f"""
                <div class="score-axe" style="border-left-color: {axe_color};">
                    <div class="score-axe-name">{axe_name}</div>
                    <div class="score-axe-value" style="color: {axe_color};">{axe_score}/{axe_max}</div>
                </div>
                """
            
            html_content += f"""
            <div class="apartment-card">
                <div class="apartment-image">
                    {main_photo}
                </div>
                <div class="apartment-content">
                    <div class="apartment-title">{apartment.get('titre', 'Titre non disponible')}</div>
                    <div class="apartment-price">{apartment.get('prix', 'Prix non disponible')}</div>
                    
                    <div class="apartment-details">
                        <div>📍 {apartment.get('localisation', 'Localisation non disponible')}</div>
                        <div>📐 {apartment.get('surface', 'Surface non disponible')}</div>
                        <div>🏠 {apartment.get('pieces', 'Pièces non disponible')}</div>
                        <div>🏢 {apartment.get('agence', 'Agence non disponible')}</div>
                    </div>
                    
                    <div class="score-section">
                        <div class="score-header">
                            <div class="score-global" style="color: {score_color};">{score_global}/100</div>
                            <div class="score-level">{get_level_emoji(fit_global)} {fit_global}</div>
                        </div>
                        <div class="score-axes">
                            {axes_html}
                        </div>
                    </div>
                    
                    <div class="apartment-actions">
                        <a href="{apartment.get('url', '#')}" target="_blank" class="btn btn-primary">Voir sur Jinka</a>
                        <a href="#" class="btn btn-secondary">Détails</a>
                    </div>
                </div>
            </div>
            """
    
    html_content += """
        </div>
    </div>
</body>
</html>
"""
    
    # Sauvegarder le rapport
    os.makedirs('output', exist_ok=True)
    report_file = 'output/rapport_appartements.html'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Rapport généré: {report_file}")
    return True

if __name__ == "__main__":
    generate_html_report()
