# 🚀 Prochaines Étapes : Intégrer Gemini dans votre Projet

Maintenant que vous avez votre clé API Gemini, voici les étapes pour l'utiliser dans votre projet HomeScore.

## 📋 Checklist des Étapes

- [ ] 1. Installer la bibliothèque Google Generative AI
- [ ] 2. Configurer votre clé API (fichier .env)
- [ ] 3. Tester votre clé API
- [ ] 4. Créer un script d'exemple pour l'analyse visuelle
- [ ] 5. Intégrer Gemini dans votre code existant

---

## Étape 1 : Installer la Bibliothèque

Installez le SDK Python de Google Generative AI :

```bash
pip install google-generativeai
```

Ou avec pip3 :

```bash
pip3 install google-generativeai
```

---

## Étape 2 : Configurer votre Clé API

### Option A : Fichier .env (Recommandé)

1. Créez un fichier `.env` à la racine de votre projet :

```bash
touch .env
```

2. Ajoutez votre clé API dans le fichier `.env` :

```
GEMINI_API_KEY=AlzaSyC5agb8weYyq7zfGO8fLvPSNytzR6dtlZo
```

⚠️ **IMPORTANT** : Assurez-vous que `.env` est dans votre `.gitignore` pour ne pas commiter votre clé !

3. Installez `python-dotenv` si ce n'est pas déjà fait :

```bash
pip install python-dotenv
```

### Option B : Variable d'environnement système

Sur macOS/Linux :

```bash
export GEMINI_API_KEY="AlzaSyC5agb8weYyq7zfGO8fLvPSNytzR6dtlZo"
```

---

## Étape 3 : Tester votre Clé API

Créez un fichier `test_gemini.py` pour tester votre clé :

```python
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Charger les variables d'environnement
load_dotenv()

# Configurer Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY non trouvée dans les variables d'environnement")

genai.configure(api_key=GEMINI_API_KEY)

# Tester avec un modèle texte simple
print("🧪 Test de connexion à Gemini API...")
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Dis-moi bonjour en français")
print(f"✅ Réponse: {response.text}")

# Tester avec un modèle vision (pour analyse d'images)
print("\n🧪 Test du modèle vision...")
vision_model = genai.GenerativeModel('gemini-1.5-flash')
print(f"✅ Modèle {vision_model.model_name} chargé avec succès")
print("✅ Votre clé API fonctionne correctement !")
```

Exécutez le test :

```bash
python test_gemini.py
```

---

## Étape 4 : Exemple d'Analyse Visuelle avec Gemini

Créez un fichier `exemple_analyse_gemini.py` :

```python
#!/usr/bin/env python3
"""
Exemple d'analyse visuelle d'une photo d'appartement avec Gemini 1.5 Flash
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path

# Charger les variables d'environnement
load_dotenv()

# Configurer Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def analyser_photo_avec_gemini(image_path: str, prompt: str) -> str:
    """
    Analyse une photo avec Gemini 1.5 Flash
    
    Args:
        image_path: Chemin vers l'image
        prompt: Question ou instruction pour l'analyse
    
    Returns:
        Réponse textuelle de Gemini
    """
    # Utiliser Gemini 1.5 Flash (économique et rapide)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Charger l'image
    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Image non trouvée: {image_path}")
    
    # Lire l'image
    import PIL.Image
    img = PIL.Image.open(image_path)
    
    # Générer la réponse
    response = model.generate_content([prompt, img])
    
    return response.text


def analyser_style_appartement(image_path: str) -> dict:
    """
    Analyse le style d'un appartement à partir d'une photo
    
    Returns:
        Dictionnaire avec les informations extraites
    """
    prompt = """Analyse cette photo d'appartement et réponds en JSON avec les informations suivantes:
    - style (moderne, haussmannien, contemporain, etc.)
    - hauteur_plafond (estimation en mètres)
    - luminosite (faible, moyenne, forte)
    - presence_fenetres (oui/non)
    - type_piece (salon, chambre, cuisine, etc.)
    
    Réponds UNIQUEMENT avec un JSON valide, sans texte supplémentaire."""
    
    try:
        response_text = analyser_photo_avec_gemini(image_path, prompt)
        
        # Parser le JSON de la réponse
        import json
        # Nettoyer la réponse (enlever markdown si présent)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return {}


if __name__ == "__main__":
    # Exemple d'utilisation
    print("🔍 Exemple d'analyse avec Gemini 1.5 Flash\n")
    
    # Remplacez par le chemin d'une vraie image
    image_path = "data/calme/example.jpg"  # À adapter
    
    if os.path.exists(image_path):
        print(f"📸 Analyse de: {image_path}")
        result = analyser_style_appartement(image_path)
        print(f"\n✅ Résultat:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"⚠️ Image non trouvée: {image_path}")
        print("💡 Modifiez le chemin dans le script pour tester avec une vraie image")
```

---

## Étape 5 : Modèles Gemini Disponibles

### Pour l'Analyse Visuelle (Recommandé)

1. **`gemini-1.5-flash`** ⭐ **Recommandé pour votre cas**
   - Coût : $0.000075 par image
   - Très rapide
   - Gratuit jusqu'à 15 requêtes/minute
   - Parfait pour analyses simples

2. **`gemini-1.5-pro`**
   - Coût : $0.001315 par image
   - Meilleure qualité
   - Pour analyses complexes

### Pour le Texte

- **`gemini-pro`** : Modèle texte standard

---

## Étape 6 : Comparaison avec votre Code Actuel

Votre projet utilise actuellement **OpenAI GPT-4o-mini** pour l'analyse visuelle. Voici comment migrer vers Gemini :

### Avant (OpenAI)
```python
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_url}}]}]
)
```

### Après (Gemini)
```python
import google.generativeai as genai
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([prompt, image])
```

**Économies estimées : 96.3%** 🎉

---

## Étape 7 : Intégration dans votre Projet

Pour intégrer Gemini dans votre code existant, vous pouvez :

1. **Créer un wrapper commun** qui supporte OpenAI ET Gemini
2. **Remplacer progressivement** les appels OpenAI par Gemini
3. **Utiliser Gemini pour les analyses simples** et garder OpenAI pour les complexes

---

## 📊 Coûts Comparés

| Modèle | Coût/Image | Coût pour 10,294 photos | Économies |
|--------|-----------|-------------------------|-----------|
| GPT-4o-mini (actuel) | $0.0003 | $20.76 | - |
| **Gemini 1.5 Flash** | **$0.000075** | **$0.77** | **96.3%** |
| Gemini 1.5 Pro | $0.001315 | $13.54 | 34.8% |

---

## 🔧 Commandes Utiles

### Tester la connexion
```bash
python test_gemini.py
```

### Vérifier l'installation
```bash
pip show google-generativeai
```

### Voir les modèles disponibles
```python
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
for m in genai.list_models():
    if 'vision' in m.supported_generation_methods or 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")
```

---

## ⚠️ Notes Importantes

1. **Quota gratuit** : Gemini 1.5 Flash offre 15 requêtes/minute gratuitement
2. **Rate limits** : Respectez les limites de taux pour éviter les erreurs
3. **Format images** : Gemini supporte JPEG, PNG, WebP, GIF
4. **Taille max** : 20MB par image
5. **Sécurité** : Ne commitez jamais votre clé API dans git

---

## 🆘 Dépannage

### Erreur : "API key not valid"
- Vérifiez que votre clé est correctement copiée dans `.env`
- Vérifiez que vous avez activé "Generative Language API" dans Google Cloud Console

### Erreur : "Quota exceeded"
- Vous avez dépassé la limite gratuite (15 req/min pour Flash)
- Attendez quelques minutes ou passez à un plan payant

### Erreur : "Module not found"
- Installez la bibliothèque : `pip install google-generativeai`

---

## 📚 Ressources

- [Documentation Gemini Python SDK](https://ai.google.dev/api/python)
- [Guide de démarrage rapide](https://ai.google.dev/quickstart)
- [Pricing Gemini](https://ai.google.dev/pricing)
- [Exemples de code](https://github.com/google/generative-ai-python)

---

**Prochaine étape recommandée :** Créez le fichier `test_gemini.py` et testez votre clé API ! 🚀

