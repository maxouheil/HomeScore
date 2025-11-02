#!/usr/bin/env python3
"""
Module d'analyse textuelle intelligente avec IA
Analyse contextuelle des annonces immobilières pour éviter les faux positifs
"""

import json
import os
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from cache_api import get_cache

load_dotenv()

class TextAIAnalyzer:
    """Analyseur de texte intelligent avec IA pour annonces immobilières"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o-mini"  # Utiliser mini pour économiser
        self.cache = get_cache()
    
    def analyze_exposition(self, description: str, caracteristiques: str = "", etage: str = "") -> Dict:
        """Analyse l'exposition avec IA en combinant étage, vue et exposition explicite pour une confiance globale"""
        prompt = f"""Tu es un expert en annonces immobilières parisiennes. Analyse ce texte de manière GLOBALE pour déterminer l'exposition et la qualité de la luminosité.

Texte à analyser:
Description: {description}
Caractéristiques: {caracteristiques}
Étage: {etage}

## TÂCHES D'ANALYSE :

### 1. EXPOSITION EXPLICITE
Détecte si une EXPOSITION (orientation) est vraiment mentionnée.
⚠️ ATTENTION: Évite les faux positifs !
- "est" dans "4ème étage" ou "le plus est..." n'est PAS une exposition
- "sud" dans "sud parisien" n'est PAS une exposition
- "nord" dans "nord de Paris" n'est PAS une exposition
- Seule une exposition EXPLICITE comme "exposition Sud", "orientation Est", "plein Sud" compte

### 2. ÉTAGE MENTIONNÉ
Analyse l'étage mentionné et son impact sur la luminosité :
- Étages élevés (4ème, 5ème, 6ème+) = meilleure luminosité potentielle = +confiance
- Étages moyens (2ème, 3ème) = luminosité correcte = confiance neutre
- Étages bas (RDC, 1er) = luminosité limitée = -confiance

### 3. VUE MENTIONNÉE
Détecte si une VUE est mentionnée (dégagée, panoramique, sur cour, vis-à-vis, etc.) :
- Vue dégagée/panoramique = meilleure luminosité = +confiance
- Vue correcte = confiance neutre
- Vis-à-vis/obstrué = moins de luminosité = -confiance
- Pas de mention = neutre

### 4. CONFIDENCE GLOBALE
Calcule une confiance globale (0.0-1.0) basée sur :
- Exposition explicite trouvée = +0.4 à +0.6
- Étage élevé (4ème+) = +0.1 à +0.2
- Vue dégagée mentionnée = +0.1 à +0.2
- Combinaison de plusieurs indices positifs = +0.1 bonus
- Faux positif détecté = confiance très faible (0.0-0.2)
- Aucun indice = confiance faible (0.2-0.4)

Réponds UNIQUEMENT au format JSON (pas de texte avant/après):
{{
    "exposition": "sud|sud_ouest|ouest|est|nord|nord_est|null",
    "confiance_exposition": 0.0-1.0,
    "confiance_globale": 0.0-1.0,
    "etage_analyse": {{
        "etage_trouve": "4ème|5ème|3ème|2ème|1er|RDC|null",
        "impact_luminosite": "positif|neutre|negatif|null",
        "confiance_etage": 0.0-1.0
    }},
    "vue_mentionnee": {{
        "vue_trouvee": true|false,
        "type_vue": "degagee|panoramique|correcte|vis_a_vis|obstruee|null",
        "impact_luminosite": "positif|neutre|negatif|null",
        "confiance_vue": 0.0-1.0
    }},
    "justification": "explication détaillée combinant exposition, étage et vue",
    "est_faux_positif": true|false,
    "indices_trouves": ["liste des indices détectés"]
}}"""

        return self._call_ai(prompt, "exposition")
    
    def analyze_baignoire(self, description: str, caracteristiques: str = "") -> Dict:
        """Analyse la présence de baignoire avec IA"""
        prompt = f"""Tu es un expert en annonces immobilières parisiennes. Analyse ce texte et détermine si une BAIGNOIRE est mentionnée.

Texte à analyser:
Description: {description}
Caractéristiques: {caracteristiques}

⚠️ ATTENTION: Sois précis !
- "baignoire" = présence confirmée
- "salle de bain" seule = ambigu (peut être douche ou baignoire)
- "douche" ou "douche italienne" = PAS de baignoire
- "salle d'eau" = généralement douche, PAS baignoire
- Si ambiguïté, retourne null

Réponds UNIQUEMENT au format JSON (pas de texte avant/après):
{{
    "baignoire_presente": true|false|null,
    "douche_seule": true|false,
    "confiance": 0.0-1.0,
    "justification": "explication courte",
    "indices": ["liste des indices trouvés"]
}}"""

        return self._call_ai(prompt, "baignoire")
    
    def analyze_cuisine_ouverte(self, description: str, caracteristiques: str = "") -> Dict:
        """Analyse si la cuisine est ouverte avec IA"""
        prompt = f"""Tu es un expert en annonces immobilières parisiennes. Analyse ce texte et détermine si la CUISINE EST OUVERTE.

Texte à analyser:
Description: {description}
Caractéristiques: {caracteristiques}

⚠️ ATTENTION: Sois précis !
- "cuisine américaine" = OUVERTE
- "cuisine ouverte" = OUVERTE
- "cuisine intégrée" = OUVERTE
- "séjour cuisine" = OUVERTE
- "pièce à vivre" = généralement OUVERTE
- "cuisine fermée" = FERMÉE
- "cuisine indépendante" = généralement FERMÉE
- Si pas mentionné = null (ambigu)

Réponds UNIQUEMENT au format JSON (pas de texte avant/après):
{{
    "cuisine_ouverte": true|false|null,
    "confiance": 0.0-1.0,
    "justification": "explication courte",
    "indices": ["liste des indices trouvés"]
}}"""

        return self._call_ai(prompt, "cuisine")
    
    def analyze_style(self, description: str, caracteristiques: str = "") -> Dict:
        """Analyse le style architectural avec IA en comprenant le contexte complet"""
        prompt = f"""Tu es un expert en architecture parisienne et en immobilier. Analyse ce texte de manière GLOBALE pour déterminer le STYLE ARCHITECTURAL avec précision.

Texte à analyser:
Description: {description}
Caractéristiques: {caracteristiques}

## TÂCHES D'ANALYSE :

### 1. STYLE ARCHITECTURAL PRINCIPAL
Détermine le style parmi ces catégories :

**"haussmannien"** (Ancien - 20pts) :
- Bâtiments 1850-1900 (période Haussmann)
- Éléments caractéristiques : parquet ancien, moulures, corniches, cheminée, hauteur sous plafond élevée (3m+), balcon en fer forgé, fenêtres hautes, plafonds moulurés

**"atypique"** (Atypique - 10pts) :
- Loft, ancien entrepôt aménagé, ancienne usine, ancien atelier
- Ancien garage/bureaux/commande/entrepôt reconverti
- Espaces atypiques, volumes généreux, hauteurs sous plafond très élevées (4m+)
- Structure industrielle apparente (poutres métalliques, briques apparentes)
- Caractère unique, original, atypique explicitement mentionné
- Architecture non conventionnelle

**"moderne"** (Neuf - 0pts) :
- Années 70, 80, 90, 2000+, contemporain, récent
- Design moderne, contemporain, clean, minimaliste
- Terrasse métal, sol moderne, fenêtres modernes, hauteur plafond réduite
- Lignes épurées, matériaux modernes

**"autre"** :
- Autres styles non catégorisés

### 2. ANALYSE CONTEXTUELLE APPROFONDIE
⚠️ COMPRENDS LE CONTEXTE COMPLET :
- "ancien entrepôt aménagé" = **atypique** (pas moderne !)
- "loft" = **atypique**
- "ancienne usine reconvertie" = **atypique**
- "ancien atelier" = **atypique**
- "ancien garage reconverti" = **atypique**
- "volume atypique" = **atypique**
- "caractère unique" + indices anciens = **atypique**
- "haussmannien" explicite = **haussmannien**
- "années 70" ou "design années 70" = **moderne** (pas atypique !)
- "contemporain" ou "moderne" = **moderne**

### 3. INDICES DÉTECTÉS
Identifie TOUS les indices présents :
- Éléments architecturaux (parquet, moulures, poutres, briques, etc.)
- Mentions de conversion/rénovation (ancien entrepôt, loft, etc.)
- Période de construction mentionnée
- Caractéristiques spatiales (volumes, hauteurs, etc.)

### 4. CONFIDENCE GLOBALE
Calcule une confiance globale (0.0-1.0) basée sur :
- Style explicite mentionné ("haussmannien", "loft", "ancien entrepôt") = +0.4 à +0.6
- Plusieurs indices cohérents avec le style = +0.2 à +0.3
- Contexte clair (conversion d'entrepôt mentionnée) = +0.2
- Indices contradictoires = -0.2 à -0.3
- Peu d'indices = confiance faible (0.3-0.5)
- Indices très clairs et nombreux = confiance élevée (0.8-1.0)

Réponds UNIQUEMENT au format JSON (pas de texte avant/après):
{{
    "style": "haussmannien|atypique|moderne|autre",
    "confiance_globale": 0.0-1.0,
    "style_principal": "haussmannien|atypique|moderne|autre",
    "contexte_detection": {{
        "est_conversion": true|false,
        "type_conversion": "entrepot|usine|atelier|garage|loft|null",
        "indices_conversion": ["liste des indices de conversion trouvés"],
        "periode_mentionnee": "1850-1900|70s|80s|90s|2000+|null",
        "confiance_contexte": 0.0-1.0
    }},
    "indices_architecturaux": {{
        "elements_haussmannien": ["parquet", "moulures", "cheminée", ...],
        "elements_atypique": ["poutres", "briques", "volumes", ...],
        "elements_moderne": ["design", "contemporain", ...],
        "confiance_indices": 0.0-1.0
    }},
    "justification": "explication détaillée du style détecté et du contexte",
    "indices": ["liste complète de tous les indices trouvés"],
    "note_scoring": "Haussmannien=20pts | Atypique=10pts | Moderne/autre=0pts"
}}"""

        return self._call_ai(prompt, "style")
    
    def _call_ai(self, prompt: str, analysis_type: str) -> Dict:
        """Appel générique à l'API OpenAI avec cache"""
        if not self.openai_api_key:
            return {
                'error': 'No API key',
                'available': False
            }
        
        # Vérifier le cache
        cached_result = self.cache.get(analysis_type, prompt)
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            system_prompt = self._get_system_prompt(analysis_type)
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,  # Basse température pour plus de précision
                'max_tokens': 500  # Augmenté pour les réponses enrichies avec étage/vue
            }
            
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                return {
                    'error': f'API error: {response.status_code}',
                    'available': False
                }
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Parser le JSON
            try:
                # Nettoyer le contenu (enlever les blocs markdown)
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                analysis = json.loads(content)
                analysis['available'] = True
                
                # Mettre en cache avant de retourner
                self.cache.set(analysis_type, prompt, analysis)
                
                return analysis
                
            except json.JSONDecodeError as e:
                return {
                    'error': f'JSON parse error: {e}',
                    'raw_content': content[:200],
                    'available': False
                }
                
        except requests.exceptions.Timeout:
            return {
                'error': 'Timeout (10s)',
                'available': False
            }
        except Exception as e:
            return {
                'error': str(e),
                'available': False
            }
    
    def _get_system_prompt(self, analysis_type: str) -> str:
        """Retourne le prompt système selon le type d'analyse"""
        prompts = {
            'exposition': 'Tu es un expert en analyse d\'annonces immobilières. Tu détectes les expositions réelles et évites les faux positifs.',
            'baignoire': 'Tu es un expert en analyse d\'annonces immobilières. Tu détectes précisément la présence de baignoire ou douche.',
            'cuisine': 'Tu es un expert en analyse d\'annonces immobilières. Tu détectes si une cuisine est ouverte ou fermée.',
            'style': 'Tu es un expert en architecture parisienne. Tu identifies le style architectural des appartements.'
        }
        return prompts.get(analysis_type, 'Tu es un expert en analyse d\'annonces immobilières.')

def test_text_ai_analyzer():
    """Test de l'analyseur IA"""
    analyzer = TextAIAnalyzer()
    
    if not analyzer.openai_api_key:
        print("❌ Clé API OpenAI non configurée")
        return
    
    print("🤖 TEST ANALYSEUR IA TEXTUELLE")
    print("=" * 70)
    
    # Test 1: Exposition (faux positif)
    print("\n1️⃣ TEST EXPOSITION (faux positif)")
    print("-" * 70)
    result = analyzer.analyze_exposition(
        description="Appartement spacieux",
        caracteristiques="Étage4ème étage",
        etage="4ème étage"
    )
    print(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('available'):
        print(f"  → Confiance globale: {result.get('confiance_globale', 0):.0%}")
        print(f"  → Étage analysé: {result.get('etage_analyse', {}).get('etage_trouve', 'N/A')}")
        print(f"  → Vue mentionnée: {result.get('vue_mentionnee', {}).get('vue_trouvee', False)}")
    
    # Test 2: Exposition (vrai positif avec étage et vue)
    print("\n2️⃣ TEST EXPOSITION (vrai positif avec étage élevé + vue)")
    print("-" * 70)
    result = analyzer.analyze_exposition(
        description="Appartement avec exposition Sud, très lumineux, vue dégagée sur Paris",
        caracteristiques="Balcon, 5ème étage",
        etage="5ème étage"
    )
    print(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('available'):
        print(f"  → Confiance globale: {result.get('confiance_globale', 0):.0%}")
        print(f"  → Confiance exposition: {result.get('confiance_exposition', 0):.0%}")
        etage_info = result.get('etage_analyse', {})
        print(f"  → Étage: {etage_info.get('etage_trouve', 'N/A')} (impact: {etage_info.get('impact_luminosite', 'N/A')})")
        vue_info = result.get('vue_mentionnee', {})
        print(f"  → Vue: {vue_info.get('type_vue', 'N/A')} (impact: {vue_info.get('impact_luminosite', 'N/A')})")
    
    # Test 3: Pas d'exposition explicite mais bonnes indications
    print("\n3️⃣ TEST PAS D'EXPOSITION MAIS INDICES POSITIFS")
    print("-" * 70)
    result = analyzer.analyze_exposition(
        description="Appartement très lumineux au 6ème étage avec vue panoramique",
        caracteristiques="Grand balcon, ascenseur",
        etage="6ème étage"
    )
    print(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('available'):
        print(f"  → Confiance globale: {result.get('confiance_globale', 0):.0%}")
        print(f"  → Exposition: {result.get('exposition', 'null')}")
        print(f"  → Indices trouvés: {result.get('indices_trouves', [])}")
    
    # Test 4: Baignoire
    print("\n4️⃣ TEST BAIGNOIRE")
    print("-" * 70)
    result = analyzer.analyze_baignoire(
        description="Appartement avec salle de bain équipée d'une baignoire",
        caracteristiques="Baignoire"
    )
    print(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 5: Cuisine ouverte
    print("\n5️⃣ TEST CUISINE OUVERTE")
    print("-" * 70)
    result = analyzer.analyze_cuisine_ouverte(
        description="Grand séjour avec cuisine américaine ouverte",
        caracteristiques="Cuisine américaine"
    )
    print(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 6: Style haussmannien
    print("\n6️⃣ TEST STYLE HAUSSMANNIEN")
    print("-" * 70)
    result = analyzer.analyze_style(
        description="Magnifique appartement haussmannien avec parquet et moulures",
        caracteristiques="Parquet, cheminée, hauteur sous plafond 3.5m"
    )
    print(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('available'):
        print(f"  → Style: {result.get('style', 'N/A')}")
        print(f"  → Confiance globale: {result.get('confiance_globale', 0):.0%}")
        contexte = result.get('contexte_detection', {})
        print(f"  → Conversion: {contexte.get('est_conversion', False)}")
        indices = result.get('indices_architecturaux', {})
        print(f"  → Éléments haussmanniens: {indices.get('elements_haussmannien', [])}")
    
    # Test 7: Style atypique (ancien entrepôt)
    print("\n7️⃣ TEST STYLE ATYPIQUE (ANCIEN ENTREPÔT)")
    print("-" * 70)
    result = analyzer.analyze_style(
        description="Loft dans un ancien entrepôt aménagé, volumes généreux, poutres apparentes",
        caracteristiques="Poutres métalliques, briques apparentes, hauteur sous plafond 4.5m"
    )
    print(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('available'):
        print(f"  → Style: {result.get('style', 'N/A')}")
        print(f"  → Confiance globale: {result.get('confiance_globale', 0):.0%}")
        contexte = result.get('contexte_detection', {})
        print(f"  → Type conversion: {contexte.get('type_conversion', 'N/A')}")
        print(f"  → Indices conversion: {contexte.get('indices_conversion', [])}")
        indices = result.get('indices_architecturaux', {})
        print(f"  → Éléments atypiques: {indices.get('elements_atypique', [])}")
    
    # Test 8: Style moderne
    print("\n8️⃣ TEST STYLE MODERNE")
    print("-" * 70)
    result = analyzer.analyze_style(
        description="Appartement contemporain des années 90, design moderne et épuré",
        caracteristiques="Terrasse métal, sol moderne, fenêtres modernes"
    )
    print(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('available'):
        print(f"  → Style: {result.get('style', 'N/A')}")
        print(f"  → Confiance globale: {result.get('confiance_globale', 0):.0%}")
        contexte = result.get('contexte_detection', {})
        print(f"  → Période: {contexte.get('periode_mentionnee', 'N/A')}")
        indices = result.get('indices_architecturaux', {})
        print(f"  → Éléments modernes: {indices.get('elements_moderne', [])}")

if __name__ == "__main__":
    test_text_ai_analyzer()

