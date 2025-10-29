#!/usr/bin/env python3
"""
Script simple pour scorer les 7 appartements scrapés en batch
"""

import json
import os
import openai
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def setup_openai():
    """Configure OpenAI"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY non définie")
        return False
    openai.api_key = api_key
    return True

def load_scoring_config():
    """Charge la configuration de scoring"""
    try:
        with open('scoring_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")
        return None

def create_scoring_prompt(apartment_data, scoring_config):
    """Crée le prompt de scoring pour OpenAI"""
    
    # Lire le prompt depuis le fichier
    try:
        with open('scoring_prompt.txt', 'r', encoding='utf-8') as f:
            base_prompt = f.read()
    except FileNotFoundError:
        print("❌ Fichier scoring_prompt.txt non trouvé")
        return None
    
    # Construire les données de l'appartement
    apartment_info = f"""
DONNÉES APPARTEMENT:
ID: {apartment_data.get('id', 'Inconnu')}
URL: {apartment_data.get('url', 'Non fourni')}

Titre: {apartment_data.get('titre', 'Non fourni')}
Prix: {apartment_data.get('prix', 'Non fourni')}
Prix/m²: {apartment_data.get('prix_m2', 'Non fourni')}
Localisation: {apartment_data.get('localisation', 'Non fourni')}
Surface: {apartment_data.get('surface', 'Non fourni')}
Pièces: {apartment_data.get('pieces', 'Non fourni')}
Étage: {apartment_data.get('etage', 'Non fourni')}
Date: {apartment_data.get('date', 'Non fourni')}

Transports proches: {', '.join(apartment_data.get('transports', []))}

Description:
{apartment_data.get('description', 'Non fourni')}

Caractéristiques:
{apartment_data.get('caracteristiques', 'Non fourni')}

Style détecté: {apartment_data.get('style_analyzed', {}).get('style', 'Non analysé')}
Cuisine: {apartment_data.get('style_analyzed', {}).get('cuisine', 'Non analysé')}
Luminosité: {apartment_data.get('style_analyzed', {}).get('luminosite', 'Non analysé')}

Exposition: {apartment_data.get('exposition', {}).get('exposition', 'Non spécifiée')}
Score exposition: {apartment_data.get('exposition', {}).get('score', 'N/A')}

Agence: {apartment_data.get('agence', 'Non fourni')}
"""
    
    # Construire le prompt complet
    prompt = f"""{base_prompt}

GRILLE DE NOTATION (100 points):
{json.dumps(scoring_config, ensure_ascii=False, indent=2)}

{apartment_info}
"""
    
    return prompt

def parse_scoring_response(response_text, apartment_id):
    """Parse la réponse de scoring d'OpenAI"""
    try:
        # Essayer de parser le JSON directement
        if response_text.strip().startswith('```json'):
            # Enlever les balises markdown
            json_text = response_text.replace('```json', '').replace('```', '').strip()
        else:
            json_text = response_text.strip()
        
        try:
            # Parser le JSON
            data = json.loads(json_text)
            return {
                "id": apartment_id,
                "score_total": data.get('score_total', 0),
                "tier": data.get('tier', 'tier3'),
                "recommandation": data.get('recommandation', 'À reconsidérer'),
                "scores_detaille": data.get('scores_detaille', {}),
                "date_scoring": datetime.now().isoformat(),
                "model_used": "gpt-4o"
            }
        except json.JSONDecodeError:
            # Fallback: parsing avec regex
            print(f"  ⚠️ JSON invalide, parsing avec regex...")
            
            # Extraire le score global
            score_global_match = re.search(r'"score_total":\s*(\d+)', response_text)
            score_global = int(score_global_match.group(1)) if score_global_match else 0
            
            # Extraire le tier
            tier_match = re.search(r'"tier":\s*"([^"]+)"', response_text)
            tier = tier_match.group(1) if tier_match else "tier3"
            
            # Extraire la recommandation
            rec_match = re.search(r'"recommandation":\s*"([^"]+)"', response_text)
            recommandation = rec_match.group(1) if rec_match else "À reconsidérer"
            
            return {
                "id": apartment_id,
                "score_total": score_global,
                "tier": tier,
                "recommandation": recommandation,
                "scores_detaille": {},
                "date_scoring": datetime.now().isoformat(),
                "model_used": "gpt-4o"
            }
        
    except Exception as e:
        print(f"  ⚠️ Erreur parsing réponse: {e}")
        return {
            "id": apartment_id,
            "score_total": 0,
            "tier": "tier3",
            "recommandation": "Erreur d'analyse",
            "scores_detaille": {},
            "date_scoring": datetime.now().isoformat(),
            "model_used": "gpt-4o"
        }

def score_apartment_with_openai(apartment_data, scoring_config, model="gpt-4o"):
    """Score un appartement avec OpenAI"""
    print(f"🤖 Scoring de l'appartement {apartment_data.get('id', 'Inconnu')} avec OpenAI ({model})...")
    
    try:
        # Créer le prompt
        prompt = create_scoring_prompt(apartment_data, scoring_config)
        if not prompt:
            return None
        
        # Appel à l'API OpenAI
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Tu es un expert immobilier parisien spécialisé dans l'analyse d'appartements. Tu analyses les appartements selon une grille de notation précise et fournis des scores justifiés."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3000
        )
        
        # Extraire la réponse
        response_text = response.choices[0].message.content.strip()
        
        # Debug: afficher la réponse brute
        print(f"  🔍 Réponse OpenAI brute:")
        print(f"  {response_text[:300]}...")
        print()
        
        # Parser la réponse
        score_data = parse_scoring_response(response_text, apartment_data.get('id', 'Inconnu'))
        
        print(f"  ✓ Score global: {score_data.get('score_total', 'N/A')}/100")
        print(f"  ✓ Tier: {score_data.get('tier', 'N/A')}")
        print(f"  ✓ Recommandation: {score_data.get('recommandation', 'N/A')}")
        
        return score_data
        
    except Exception as e:
        print(f"  ❌ Erreur OpenAI: {e}")
        return None

def score_batch_apartments():
    """Score les 7 appartements scrapés"""
    print("🏠 SCORING DES 7 APPARTEMENTS SCRAPÉS")
    print("=" * 60)
    
    # Configuration
    if not setup_openai():
        return False
    
    scoring_config = load_scoring_config()
    if not scoring_config:
        return False
    
    # Charger les données scrapées
    data_file = "data/batch_scraped_apartments.json"
    if not os.path.exists(data_file):
        print(f"❌ Fichier {data_file} non trouvé")
        return False
    
    with open(data_file, 'r', encoding='utf-8') as f:
        apartments_data = json.load(f)
    
    print(f"📋 {len(apartments_data)} appartements trouvés")
    print()
    
    # Créer le répertoire de sortie
    os.makedirs("data/scores", exist_ok=True)
    
    scored_apartments = []
    
    for i, apartment in enumerate(apartments_data, 1):
        print(f"🏠 SCORING APPARTEMENT {i}/{len(apartments_data)}")
        print(f"   ID: {apartment.get('id', 'N/A')}")
        print(f"   Localisation: {apartment.get('localisation', 'N/A')}")
        print(f"   Prix: {apartment.get('prix', 'N/A')}")
        print(f"   Surface: {apartment.get('surface', 'N/A')}")
        print("   " + "-" * 50)
        
        try:
            # Score l'appartement
            score_result = score_apartment_with_openai(apartment, scoring_config)
            
            if score_result:
                # Ajouter les données originales au résultat
                score_result.update(apartment)
                scored_apartments.append(score_result)
                
                # Sauvegarder individuellement
                score_file = f"data/scores/apartment_{apartment.get('id', i)}_score.json"
                with open(score_file, 'w', encoding='utf-8') as f:
                    json.dump(score_result, f, ensure_ascii=False, indent=2)
                
            else:
                print(f"   ❌ Échec du scoring")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print()
    
    # Sauvegarder tous les scores
    all_scores_file = "data/scores/all_apartments_scores.json"
    with open(all_scores_file, 'w', encoding='utf-8') as f:
        json.dump(scored_apartments, f, ensure_ascii=False, indent=2)
    
    print("📊 RÉSULTATS FINAUX")
    print("=" * 60)
    print(f"✅ Appartements scorés: {len(scored_apartments)}")
    print(f"💾 Scores sauvegardés: {all_scores_file}")
    print()
    
    # Afficher le classement
    if scored_apartments:
        print("🏆 CLASSEMENT PAR SCORE")
        print("-" * 40)
        sorted_apartments = sorted(scored_apartments, key=lambda x: x.get('score_total', 0), reverse=True)
        
        for i, apt in enumerate(sorted_apartments, 1):
            score = apt.get('score_total', 0)
            tier = apt.get('tier', 'N/A')
            loc = apt.get('localisation', 'N/A')
            prix = apt.get('prix', 'N/A')
            surface = apt.get('surface', 'N/A')
            
            print(f"{i:2d}. {score:2d}/100 - {tier:12s} - {loc} - {prix} - {surface}")
    
    print()
    print("🎉 SCORING TERMINÉ !")
    print(f"   📊 {len(scored_apartments)} appartements scorés")
    print(f"   📁 Données: {all_scores_file}")
    
    return True

if __name__ == "__main__":
    score_batch_apartments()
