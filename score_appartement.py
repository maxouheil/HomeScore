#!/usr/bin/env python3
"""
Script de scoring des appartements avec OpenAI
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
        print("💡 Ajoutez votre clé dans le fichier .env")
        return False
    openai.api_key = api_key
    return True

def load_scoring_config():
    """Charge la configuration de scoring"""
    try:
        with open('scoring_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Fichier scoring_config.json non trouvé")
        return None
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")
        return None

def load_apartment_data(apartment_id):
    """Charge les données d'un appartement"""
    try:
        apartment_file = f"data/appartements/{apartment_id}.json"
        with open(apartment_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement appartement {apartment_id}: {e}")
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
Date: {apartment_data.get('date', 'Non fourni')}

Transports proches: {', '.join(apartment_data.get('transports', []))}

Description:
{apartment_data.get('description', 'Non fourni')}

Caractéristiques:
{apartment_data.get('caracteristiques', 'Non fourni')}

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
        # Extraire le score global
        score_global_match = re.search(r'Score global : (\d+)/100', response_text)
        score_global = int(score_global_match.group(1)) if score_global_match else 0
        
        # Extraire le fit global
        fit_global_match = re.search(r'Fit global : ([^\n]+)', response_text)
        fit_global = fit_global_match.group(1).strip() if fit_global_match else "Moyen"
        
        # Parser chaque axe
        scores_par_axe = []
        
        # Axe 1: Localisation
        loc_match = re.search(r'1\. Localisation — (\d+)/20 — ([^\n]+)', response_text)
        if loc_match:
            scores_par_axe.append({
                "axe": "Localisation",
                "score": int(loc_match.group(1)),
                "max": 20,
                "niveau": loc_match.group(2).strip()
            })
        
        # Axe 2: Style haussmannien
        style_match = re.search(r'2\. Style haussmannien — (\d+)/20 — ([^\n]+)', response_text)
        if style_match:
            scores_par_axe.append({
                "axe": "Style haussmannien",
                "score": int(style_match.group(1)),
                "max": 20,
                "niveau": style_match.group(2).strip()
            })
        
        # Axe 3: Prix
        prix_match = re.search(r'3\. Prix — (\d+)/20 — ([^\n]+)', response_text)
        if prix_match:
            scores_par_axe.append({
                "axe": "Prix",
                "score": int(prix_match.group(1)),
                "max": 20,
                "niveau": prix_match.group(2).strip()
            })
        
        # Axe 4: Ensoleillement
        ens_match = re.search(r'4\. Ensoleillement — (\d+)/10 — ([^\n]+)', response_text)
        if ens_match:
            scores_par_axe.append({
                "axe": "Ensoleillement",
                "score": int(ens_match.group(1)),
                "max": 10,
                "niveau": ens_match.group(2).strip()
            })
        
        # Axe 5: Cuisine ouverte
        cuisine_match = re.search(r'5\. Cuisine ouverte — (\d+)/10 — ([^\n]+)', response_text)
        if cuisine_match:
            scores_par_axe.append({
                "axe": "Cuisine ouverte",
                "score": int(cuisine_match.group(1)),
                "max": 10,
                "niveau": cuisine_match.group(2).strip()
            })
        
        # Axe 6: Étage
        etage_match = re.search(r'6\. Étage — (\d+)/10 — ([^\n]+)', response_text)
        if etage_match:
            scores_par_axe.append({
                "axe": "Étage",
                "score": int(etage_match.group(1)),
                "max": 10,
                "niveau": etage_match.group(2).strip()
            })
        
        # Axe 7: Vue
        vue_match = re.search(r'7\. Vue — (\d+)/5 — ([^\n]+)', response_text)
        if vue_match:
            scores_par_axe.append({
                "axe": "Vue",
                "score": int(vue_match.group(1)),
                "max": 5,
                "niveau": vue_match.group(2).strip()
            })
        
        # Axe 8: Surface
        surface_match = re.search(r'8\. Surface — (\d+)/5 — ([^\n]+)', response_text)
        if surface_match:
            scores_par_axe.append({
                "axe": "Surface",
                "score": int(surface_match.group(1)),
                "max": 5,
                "niveau": surface_match.group(2).strip()
            })
        
        # Construire la réponse au format JSON
        return {
            "id": apartment_id,
            "scores_par_axe": scores_par_axe,
            "score_global": score_global,
            "fit_global": fit_global,
            "date_scoring": datetime.now().isoformat(),
            "model_used": "gpt-4o"
        }
        
    except Exception as e:
        print(f"  ⚠️ Erreur parsing réponse: {e}")
        return {
            "id": apartment_id,
            "scores_par_axe": [],
            "score_global": 0,
            "fit_global": "Erreur",
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
                {"role": "system", "content": "Tu es un expert immobilier parisien spécialisé dans l'analyse d'appartements haussmanniens. Tu analyses les appartements selon une grille de notation précise et fournis des scores justifiés."},
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
        
        print(f"  ✓ Score global: {score_data.get('score_global', 'N/A')}/100")
        print(f"  ✓ {len(score_data.get('scores_par_axe', []))} axes analysés")
        
        return score_data
        
    except Exception as e:
        print(f"  ❌ Erreur OpenAI: {e}")
        return None

def save_score(score_result, apartment_id):
    """Sauvegarde le score d'un appartement"""
    try:
        os.makedirs("data/scores", exist_ok=True)
        score_file = f"data/scores/{apartment_id}_score.json"
        
        with open(score_file, 'w', encoding='utf-8') as f:
            json.dump(score_result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Score sauvegardé dans {score_file}")
        return True
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return False

def score_all_apartments():
    """Score tous les appartements scrapés"""
    print("🏠 Scoring de tous les appartements...")
    
    if not setup_openai():
        return False
    
    scoring_config = load_scoring_config()
    if not scoring_config:
        return False
    
    # Trouver tous les appartements scrapés
    apartments_dir = "data/appartements"
    if not os.path.exists(apartments_dir):
        print("❌ Aucun appartement trouvé dans data/appartements")
        return False
    
    apartment_files = [f for f in os.listdir(apartments_dir) if f.endswith('.json')]
    print(f"📋 {len(apartment_files)} appartements trouvés")
    
    scored_count = 0
    for apartment_file in apartment_files:
        apartment_id = apartment_file.replace('.json', '')
        
        # Vérifier si déjà scoré
        score_file = f"data/scores/{apartment_id}_score.json"
        if os.path.exists(score_file):
            print(f"⏭️ Appartement {apartment_id} déjà scoré")
            continue
        
        # Charger les données de l'appartement
        apartment_data = load_apartment_data(apartment_id)
        if not apartment_data:
            continue
        
        # Scorer l'appartement
        score_result = score_apartment_with_openai(apartment_data, scoring_config)
        if score_result:
            save_score(score_result, apartment_id)
            scored_count += 1
        
        print()  # Ligne vide pour la lisibilité
    
    print(f"✅ Scoring terminé: {scored_count} appartements scorés")
    return True

if __name__ == "__main__":
    score_all_apartments()
