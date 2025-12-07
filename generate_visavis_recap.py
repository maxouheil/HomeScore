#!/usr/bin/env python3
"""
Génère un récapitulatif markdown de l'analyse du vis-à-vis
"""

import json
from pathlib import Path
from datetime import datetime
from data_loader import load_apartments

def generate_visavis_recap():
    """Génère le récapitulatif markdown"""
    print("📊 GÉNÉRATION DU RÉCAPITULATIF VIS-À-VIS")
    print("=" * 70)
    
    # Charger les appartements
    apartments = load_apartments(prefer_api=True)
    
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    # Charger le récapitulatif JSON si disponible
    recap_file = Path('data/visavis_analysis_recap.json')
    recap_data = None
    if recap_file.exists():
        with open(recap_file, 'r', encoding='utf-8') as f:
            recap_data = json.load(f)
    
    # Compter les statistiques depuis les appartements
    stats = {
        'total': len(apartments),
        'good': 0,
        'moyen': 0,
        'bad': 0,
        'none': 0,
        'with_photos': 0,
        'without_photos': 0
    }
    
    # Détails par appartement
    apartments_details = []
    
    for apartment in apartments:
        apartment_id = apartment.get('id', 'unknown')
        localisation = apartment.get('localisation', 'N/A')
        prix = apartment.get('prix', 'N/A')
        surface = apartment.get('surface', 'N/A')
        
        # Vérifier les photos
        photos = apartment.get('photos', [])
        has_photos = len(photos) > 0
        
        if has_photos:
            stats['with_photos'] += 1
        else:
            stats['without_photos'] += 1
        
        # Extraire le vis-à-vis
        exposition = apartment.get('exposition', {})
        expo_details = exposition.get('details', {})
        visavis = expo_details.get('visavis')
        visavis_confidence = expo_details.get('visavis_confidence', 0.0)
        visavis_justification = expo_details.get('visavis_justification', '')
        visavis_details = expo_details.get('visavis_details', {})
        
        if visavis:
            stats[visavis] = stats.get(visavis, 0) + 1
        else:
            stats['none'] += 1
        
        apartments_details.append({
            'id': apartment_id,
            'localisation': localisation,
            'prix': prix,
            'surface': surface,
            'visavis': visavis,
            'confidence': visavis_confidence,
            'justification': visavis_justification,
            'has_photos': has_photos,
            'photos_count': len(photos),
            'details': visavis_details
        })
    
    # Générer le markdown
    markdown = f"""# 📊 Récapitulatif - Analyse du Vis-à-vis

**Date d'analyse**: {datetime.now().strftime('%d/%m/%Y %H:%M')}

## 📈 Statistiques Globales

- **Total d'appartements**: {stats['total']}
- **Avec photos**: {stats['with_photos']}
- **Sans photos**: {stats['without_photos']}

### Résultats Vis-à-vis

| Catégorie | Nombre | Pourcentage |
|-----------|--------|-------------|
| ✅ **Good** (pas de vis-à-vis ou très lointain) | {stats['good']} | {stats['good']/stats['total']*100:.1f}% |
| ⚠️ **Moyen** (vis-à-vis >20m, rue large) | {stats['moyen']} | {stats['moyen']/stats['total']*100:.1f}% |
| ❌ **Bad** (vis-à-vis proche, rue étroite) | {stats['bad']} | {stats['bad']/stats['total']*100:.1f}% |
| ❓ **Non déterminé** | {stats['none']} | {stats['none']/stats['total']*100:.1f}% |

## 🏠 Détails par Appartement

"""
    
    # Trier par vis-à-vis (good en premier, puis moyen, puis bad, puis none)
    def sort_key(apt):
        order = {'good': 0, 'moyen': 1, 'bad': 2, None: 3}
        return order.get(apt['visavis'], 3)
    
    apartments_details.sort(key=sort_key)
    
    # Grouper par catégorie
    for category in ['good', 'moyen', 'bad', None]:
        category_apts = [apt for apt in apartments_details if apt['visavis'] == category]
        
        if not category_apts:
            continue
        
        category_name = {
            'good': '✅ Good (pas de vis-à-vis ou très lointain)',
            'moyen': '⚠️ Moyen (vis-à-vis >20m, rue large)',
            'bad': '❌ Bad (vis-à-vis proche, rue étroite)',
            None: '❓ Non déterminé'
        }.get(category, '❓ Inconnu')
        
        markdown += f"\n### {category_name} ({len(category_apts)} appartements)\n\n"
        markdown += "| ID | Localisation | Prix | Surface | Confiance | Photos |\n"
        markdown += "|----|--------------|------|---------|-----------|--------|\n"
        
        for apt in category_apts:
            confidence_str = f"{apt['confidence']:.0%}" if apt['confidence'] else "N/A"
            photos_str = f"{apt['photos_count']}" if apt['has_photos'] else "0"
            markdown += f"| {apt['id']} | {apt['localisation'][:40]} | {apt['prix']} | {apt['surface']} | {confidence_str} | {photos_str} |\n"
        
        markdown += "\n"
    
    # Section détaillée pour quelques exemples
    markdown += "\n## 🔍 Exemples Détaillés\n\n"
    
    # Prendre quelques exemples de chaque catégorie
    examples_taken = 0
    for category in ['good', 'moyen', 'bad']:
        category_apts = [apt for apt in apartments_details if apt['visavis'] == category]
        if category_apts and examples_taken < 3:
            apt = category_apts[0]
            markdown += f"\n### Appartement {apt['id']} - Vis-à-vis: {apt['visavis']}\n\n"
            markdown += f"- **Localisation**: {apt['localisation']}\n"
            markdown += f"- **Prix**: {apt['prix']}\n"
            markdown += f"- **Surface**: {apt['surface']}\n"
            markdown += f"- **Confiance**: {apt['confidence']:.0%}\n"
            markdown += f"- **Justification**: {apt['justification']}\n"
            if apt['details']:
                vote_counts = apt['details'].get('vote_counts', {})
                if vote_counts:
                    markdown += f"- **Votes**: {vote_counts}\n"
            examples_taken += 1
    
    # Sauvegarder
    output_file = Path('data/RECAP_VISAVIS.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✅ Récapitulatif généré: {output_file}")
    print(f"\n📊 Statistiques:")
    print(f"   Good: {stats['good']} ({stats['good']/stats['total']*100:.1f}%)")
    print(f"   Moyen: {stats['moyen']} ({stats['moyen']/stats['total']*100:.1f}%)")
    print(f"   Bad: {stats['bad']} ({stats['bad']/stats['total']*100:.1f}%)")
    print(f"   Non déterminé: {stats['none']} ({stats['none']/stats['total']*100:.1f}%)")

if __name__ == "__main__":
    generate_visavis_recap()

