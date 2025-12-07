#!/usr/bin/env python3
"""
Test simple du placeholder pour les appartements sans photo
"""

def test_placeholder_simple():
    """Teste le placeholder avec un appartement simple"""
    
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
    
    print("🧪 TEST PLACEHOLDER SIMPLE")
    print("=" * 50)
    print(f"📋 Appartement: {test_apartment['titre']}")
    print(f"📸 Photos: {len(test_apartment['photos'])} (aucune)")
    
    # Test de la fonction get_apartment_photo
    from generate_fitscore_style_html import get_apartment_photo
    
    photo_url = get_apartment_photo(test_apartment)
    print(f"🔍 Photo URL retournée: {photo_url}")
    
    if photo_url is None:
        print("✅ Placeholder sera utilisé (photo_url = None)")
    else:
        print("❌ Une photo a été trouvée, le placeholder ne sera pas utilisé")
    
    # Test du HTML généré
    from generate_fitscore_style_html import format_apartment_info
    
    apartment_info = format_apartment_info(test_apartment)
    print(f"📝 Info formatée: {apartment_info}")

if __name__ == "__main__":
    test_placeholder_simple()
