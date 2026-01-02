#!/usr/bin/env python3
"""
Script de comparaison des coûts pour l'analyse visuelle avec différents modèles IA.
Compare OpenAI GPT-4o-mini avec d'autres alternatives (Claude, Gemini, etc.)
"""

import json
from datetime import datetime
from typing import Dict, List

# Données réelles de consommation (basées sur le récapitulatif)
REAL_USAGE = {
    'total_apartments': 1360,
    'apartments_with_analysis': 793,
    'total_photos_analyzed': 10294,
    'current_cost_usd': 20.76,
    'avg_photos_per_apt': 13.0,  # 10294 / 793
}

# Prix par modèle (basés sur les recherches web et documentation officielle)
# Prix en $ par image (résolution moyenne ~1024x1024 pixels)
MODEL_PRICING = {
    'openai_gpt4o_mini': {
        'name': 'OpenAI GPT-4o-mini',
        'provider': 'OpenAI',
        'cost_per_image': 0.0003,  # ~$0.30 per 1K images
        'cost_per_1k_images': 0.30,
        'notes': 'Modèle actuellement utilisé',
        'quality': 'Bonne',
        'speed': 'Rapide',
        'api_availability': 'Excellent',
        'features': ['Vision', 'Multimodal', 'JSON mode']
    },
    'openai_gpt4o': {
        'name': 'OpenAI GPT-4o',
        'provider': 'OpenAI',
        'cost_per_image': 0.005525,  # Pour 1920x1080
        'cost_per_1k_images': 5.525,
        'notes': 'Plus performant mais plus cher',
        'quality': 'Excellente',
        'speed': 'Moyenne',
        'api_availability': 'Excellent',
        'features': ['Vision avancée', 'Multimodal', 'Meilleure précision']
    },
    'google_gemini_1_5_flash': {
        'name': 'Google Gemini 1.5 Flash',
        'provider': 'Google',
        'cost_per_image': 0.000075,  # Gratuit jusqu'à 15 RPM, puis très économique
        'cost_per_1k_images': 0.075,
        'notes': 'Très économique, gratuit pour usage limité',
        'quality': 'Bonne',
        'speed': 'Très rapide',
        'api_availability': 'Bon',
        'features': ['Vision', 'Multimodal', 'Gratuit jusqu\'à 15 req/min']
    },
    'google_gemini_1_5_pro': {
        'name': 'Google Gemini 1.5 Pro',
        'provider': 'Google',
        'cost_per_image': 0.001315,  # Pour 1920x1080
        'cost_per_1k_images': 1.315,
        'notes': 'Meilleur rapport qualité/prix',
        'quality': 'Excellente',
        'speed': 'Moyenne',
        'api_availability': 'Bon',
        'features': ['Vision avancée', 'Multimodal', 'Contexte long']
    },
    'anthropic_claude_3_5_sonnet': {
        'name': 'Anthropic Claude 3.5 Sonnet',
        'provider': 'Anthropic',
        'cost_per_image': 0.003,  # Estimation basée sur pricing
        'cost_per_1k_images': 3.0,
        'notes': 'Bon pour analyse détaillée',
        'quality': 'Excellente',
        'speed': 'Moyenne',
        'api_availability': 'Bon',
        'features': ['Vision', 'Analyse approfondie', 'Sécurité']
    },
    'anthropic_claude_3_opus': {
        'name': 'Anthropic Claude 3 Opus',
        'provider': 'Anthropic',
        'cost_per_image': 0.02355,  # Pour 1920x1080
        'cost_per_1k_images': 23.55,
        'notes': 'Le plus cher, meilleure qualité',
        'quality': 'Exceptionnelle',
        'speed': 'Lente',
        'api_availability': 'Bon',
        'features': ['Vision premium', 'Analyse très détaillée']
    },
    'openai_gpt4o_mini_batch': {
        'name': 'OpenAI GPT-4o-mini (Batch)',
        'provider': 'OpenAI',
        'cost_per_image': 0.00015,  # 50% de réduction en batch
        'cost_per_1k_images': 0.15,
        'notes': 'Version batch avec réduction de 50%',
        'quality': 'Bonne',
        'speed': 'Lente (batch)',
        'api_availability': 'Excellent',
        'features': ['Vision', 'Batch API', 'Réduction coûts']
    },
    'replicate_llava': {
        'name': 'LLaVA (Replicate)',
        'provider': 'Replicate',
        'cost_per_image': 0.0001,  # Modèle open-source hébergé
        'cost_per_1k_images': 0.10,
        'notes': 'Modèle open-source, très économique',
        'quality': 'Correcte',
        'speed': 'Variable',
        'api_availability': 'Moyenne',
        'features': ['Open-source', 'Économique', 'Personnalisable']
    },
    'together_ai_llama_vision': {
        'name': 'Llama 3.2 Vision (Together AI)',
        'provider': 'Together AI',
        'cost_per_image': 0.00005,  # Très économique
        'cost_per_1k_images': 0.05,
        'notes': 'Modèle open-source, très économique',
        'quality': 'Correcte',
        'speed': 'Rapide',
        'api_availability': 'Bon',
        'features': ['Open-source', 'Très économique', 'API simple']
    }
}


def calculer_couts_scenario(nb_photos: int, model_key: str) -> Dict:
    """Calcule les coûts pour un scénario donné."""
    model = MODEL_PRICING[model_key]
    
    cost_total = nb_photos * model['cost_per_image']
    cost_per_1k = model['cost_per_1k_images']
    
    return {
        'model': model['name'],
        'provider': model['provider'],
        'total_photos': nb_photos,
        'cost_total': round(cost_total, 2),
        'cost_per_1k': cost_per_1k,
        'savings_vs_current': round(REAL_USAGE['current_cost_usd'] - cost_total, 2),
        'savings_percent': round((1 - cost_total / REAL_USAGE['current_cost_usd']) * 100, 1) if REAL_USAGE['current_cost_usd'] > 0 else 0,
        'notes': model['notes'],
        'quality': model['quality'],
        'speed': model['speed']
    }


def generer_comparaison():
    """Génère une comparaison complète des coûts."""
    nb_photos = REAL_USAGE['total_photos_analyzed']
    
    scenarios = []
    for model_key in MODEL_PRICING.keys():
        scenario = calculer_couts_scenario(nb_photos, model_key)
        scenarios.append(scenario)
    
    # Trier par coût croissant
    scenarios.sort(key=lambda x: x['cost_total'])
    
    return {
        'date_generation': datetime.now().isoformat(),
        'usage_reel': REAL_USAGE,
        'comparaison_par_modele': scenarios,
        'recommandations': generer_recommandations(scenarios)
    }


def generer_recommandations(scenarios: List[Dict]) -> Dict:
    """Génère des recommandations basées sur la comparaison."""
    # Meilleur rapport qualité/prix
    best_value = [s for s in scenarios if s['quality'] in ['Bonne', 'Excellente']][:3]
    
    # Plus économique
    cheapest = scenarios[0]
    
    # Meilleure qualité
    best_quality = [s for s in scenarios if s['quality'] == 'Exceptionnelle'][0] if any(s['quality'] == 'Exceptionnelle' for s in scenarios) else None
    
    return {
        'plus_economique': {
            'model': cheapest['model'],
            'cost': cheapest['cost_total'],
            'savings': cheapest['savings_vs_current'],
            'savings_percent': cheapest['savings_percent']
        },
        'meilleur_rapport_qualite_prix': [
            {
                'model': s['model'],
                'cost': s['cost_total'],
                'quality': s['quality'],
                'savings': s['savings_vs_current']
            } for s in best_value
        ],
        'meilleure_qualite': {
            'model': best_quality['model'] if best_quality else None,
            'cost': best_quality['cost_total'] if best_quality else None
        },
        'economies_potentielles': {
            'minimum': scenarios[0]['savings_vs_current'],
            'maximum': scenarios[-1]['savings_vs_current'] if scenarios[-1]['cost_total'] > REAL_USAGE['current_cost_usd'] else 0,
            'moyenne_recommandee': best_value[0]['savings_vs_current'] if best_value else 0
        }
    }


def generer_rapport_markdown(comparison: Dict) -> str:
    """Génère un rapport Markdown formaté."""
    md = f"""# 💰 Comparaison des Coûts - Modèles d'Analyse Visuelle

**Date de génération:** {comparison['date_generation']}

## 📊 Usage Réel Actuel

- **Total appartements analysés:** {comparison['usage_reel']['total_apartments']}
- **Appartements avec analyses visuelles:** {comparison['usage_reel']['apartments_with_analysis']}
- **Total photos analysées:** {comparison['usage_reel']['total_photos_analyzed']}
- **💰 Coût actuel (GPT-4o-mini):** ${comparison['usage_reel']['current_cost_usd']:.2f} USD
- **Moyenne photos par appartement:** {comparison['usage_reel']['avg_photos_per_apt']:.1f}

---

## 🔍 Comparaison Détaillée des Modèles

| Modèle | Fournisseur | Coût Total | Coût/1K images | Économies | Économies % | Qualité | Vitesse |
|--------|-------------|------------|----------------|-----------|-------------|---------|---------|
"""
    
    for scenario in comparison['comparaison_par_modele']:
        savings_str = f"${scenario['savings_vs_current']:.2f}" if scenario['savings_vs_current'] > 0 else f"+${abs(scenario['savings_vs_current']):.2f}"
        savings_pct = f"{scenario['savings_percent']:.1f}%" if scenario['savings_percent'] > 0 else f"+{abs(scenario['savings_percent']):.1f}%"
        
        md += f"| {scenario['model']} | {scenario['provider']} | ${scenario['cost_total']:.2f} | ${scenario['cost_per_1k']:.3f} | {savings_str} | {savings_pct} | {scenario['quality']} | {scenario['speed']} |\n"
    
    md += "\n---\n\n"
    
    # Recommandations
    rec = comparison['recommandations']
    md += f"""## 🎯 Recommandations

### 💵 Option la Plus Économique

**{rec['plus_economique']['model']}**
- Coût total: **${rec['plus_economique']['cost']:.2f}**
- Économies: **${rec['plus_economique']['savings']:.2f}** ({rec['plus_economique']['savings_percent']:.1f}%)

### ⚖️ Meilleur Rapport Qualité/Prix

"""
    
    for i, model in enumerate(rec['meilleur_rapport_qualite_prix'], 1):
        md += f"{i}. **{model['model']}** - ${model['cost']:.2f} ({model['quality']}) - Économies: ${model['savings']:.2f}\n"
    
    md += f"""
### 🏆 Meilleure Qualité

"""
    if rec['meilleure_qualite']['model']:
        md += f"**{rec['meilleure_qualite']['model']}** - ${rec['meilleure_qualite']['cost']:.2f}\n"
    else:
        md += "Aucun modèle premium dans la comparaison.\n"
    
    md += f"""
### 💡 Économies Potentielles

- **Minimum:** ${rec['economies_potentielles']['minimum']:.2f}
- **Maximum:** ${rec['economies_potentielles']['maximum']:.2f}
- **Recommandé:** ${rec['economies_potentielles']['moyenne_recommandee']:.2f}

---

## 📈 Analyse par Scénario

### Scénario 1: 100 appartements (1,300 photos)
"""
    
    for model_key in ['openai_gpt4o_mini', 'google_gemini_1_5_flash', 'google_gemini_1_5_pro', 'together_ai_llama_vision']:
        model = MODEL_PRICING[model_key]
        cost = 1300 * model['cost_per_image']
        md += f"- **{model['name']}:** ${cost:.2f}\n"
    
    md += """
### Scénario 2: 1,000 appartements (13,000 photos)
"""
    
    for model_key in ['openai_gpt4o_mini', 'google_gemini_1_5_flash', 'google_gemini_1_5_pro', 'together_ai_llama_vision']:
        model = MODEL_PRICING[model_key]
        cost = 13000 * model['cost_per_image']
        md += f"- **{model['name']}:** ${cost:.2f}\n"
    
    md += """
---

## 🔧 Stratégies d'Optimisation

### 1. **Utilisation Hybride**
- Utiliser **Gemini 1.5 Flash** pour les analyses simples (détection présence/absence)
- Utiliser **GPT-4o-mini** pour les analyses complexes (style détaillé)
- **Économies estimées:** 40-60%

### 2. **Batch Processing**
- Utiliser l'API Batch d'OpenAI pour les analyses non-urgentes
- **Économies:** 50% sur les coûts OpenAI

### 3. **Cache Agressif**
- Mettre en cache toutes les analyses pour éviter les ré-analyses
- **Économies:** 80-90% sur les coûts répétitifs

### 4. **Modèles Open-Source**
- Utiliser **Llama Vision** ou **LLaVA** pour les tâches simples
- **Économies:** 70-85% vs OpenAI

### 5. **Limite de Photos**
- Analyser seulement les 3-5 premières photos au lieu de toutes
- **Économies:** 50-70% selon le nombre de photos

---

## 📝 Notes Importantes

- Les prix sont basés sur les tarifs publics de décembre 2025
- Les coûts peuvent varier selon la résolution des images
- Les modèles open-source peuvent nécessiter une infrastructure supplémentaire
- Les performances peuvent varier selon les cas d'usage spécifiques
- Il est recommandé de tester plusieurs modèles avant de migrer

---

**Recommandation finale:** Pour optimiser les coûts tout en maintenant une bonne qualité, considérer **Google Gemini 1.5 Flash** pour les analyses simples et **Gemini 1.5 Pro** pour les analyses complexes. Cela permettrait d'économiser environ **60-80%** sur les coûts actuels.
"""
    
    return md


def main():
    """Fonction principale."""
    print("🔍 Génération de la comparaison des coûts...")
    
    comparison = generer_comparaison()
    
    # Sauvegarder en JSON
    json_file = f"comparaison_couts_modeles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Données JSON sauvegardées dans {json_file}")
    
    # Générer le rapport Markdown
    md_content = generer_rapport_markdown(comparison)
    md_file = f"COMPARAISON_COUTS_MODELES_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ Rapport Markdown sauvegardé dans {md_file}")
    
    # Afficher le résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DE LA COMPARAISON")
    print("="*80)
    print(f"\n💰 Coût actuel (GPT-4o-mini): ${comparison['usage_reel']['current_cost_usd']:.2f}")
    print(f"\n🏆 Top 3 Modèles les Plus Économiques:")
    for i, scenario in enumerate(comparison['comparaison_par_modele'][:3], 1):
        print(f"  {i}. {scenario['model']}: ${scenario['cost_total']:.2f} (Économies: ${scenario['savings_vs_current']:.2f})")
    
    print(f"\n💡 Recommandation: {comparison['recommandations']['meilleur_rapport_qualite_prix'][0]['model']}")
    print(f"   Coût: ${comparison['recommandations']['meilleur_rapport_qualite_prix'][0]['cost']:.2f}")
    print(f"   Économies: ${comparison['recommandations']['meilleur_rapport_qualite_prix'][0]['savings']:.2f}")
    print("\n" + "="*80)


if __name__ == '__main__':
    main()

