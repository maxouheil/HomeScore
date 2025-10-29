#!/usr/bin/env python3
"""
Test HTML du placeholder
"""

def test_placeholder_html():
    """Génère un HTML de test avec placeholder"""
    
    # Appartement de test sans photo
    test_apartment = {
        'id': 'test_no_photo',
        'titre': 'Appartement Test Sans Photo',
        'localisation': 'Paris 19e',
        'surface': '70m²',
        'pieces': '3 pièces',
        'prix': '775 000€',
        'score_total': 75,
        'scores_detaille': {
            'localisation': {'score': 15, 'max': 20},
            'prix': {'score': 18, 'max': 20},
            'style': {'score': 20, 'max': 20},
            'ensoleillement': {'score': 8, 'max': 10},
            'cuisine': {'score': 7, 'max': 10},
            'etage': {'score': 7, 'max': 10}
        },
        'photos': []
    }
    
    # HTML de test simple
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Placeholder</title>
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        
        .candidate-photo {{
            width: 100%;
            height: 200px;
            border-radius: 12px;
            object-fit: cover;
            flex-shrink: 0;
        }}
        
        .candidate-photo-placeholder {{
            width: 100%;
            height: 200px;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 2rem;
            border-radius: 12px;
            flex-shrink: 0;
        }}
        
        .test-card {{
            max-width: 400px;
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        
        .test-title {{
            font-size: 1.2rem;
            font-weight: bold;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <h1>Test Placeholder Photos</h1>
    
    <div class="test-card">
        <h2>Appartement SANS photo (placeholder)</h2>
        <div class="candidate-photo-placeholder"></div>
        <div class="test-title">Paris 19e - 70m² - 3 pièces • 775 000€</div>
        <p>Score: 75/100</p>
    </div>
    
    <div class="test-card">
        <h2>Appartement AVEC photo (exemple)</h2>
        <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkFwcGFydGVtZW50IFBob3RvPC90ZXh0Pjwvc3ZnPg==" alt="Photo d'appartement" class="candidate-photo">
        <div class="test-title">Paris 11e - 87m² - 3 pièces • 749 000€</div>
        <p>Score: 65/100</p>
    </div>
    
    <p><strong>Résultat attendu :</strong> Le premier appartement doit afficher un placeholder gris clair 370x200 avec une icône 📷, le second doit afficher une image.</p>
</body>
</html>
"""
    
    # Sauvegarder le HTML de test
    with open('test_placeholder.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("🧪 TEST PLACEHOLDER HTML")
    print("=" * 50)
    print("✅ HTML de test généré: test_placeholder.html")
    print("🌐 Ouvrez le fichier dans votre navigateur pour voir le placeholder")

if __name__ == "__main__":
    test_placeholder_html()
