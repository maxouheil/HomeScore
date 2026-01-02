#!/bin/bash
# Script de démarrage rapide pour Gemini

echo "🚀 Démarrage rapide Gemini pour HomeScore"
echo "=========================================="
echo ""

# Vérifier si .env existe
if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé"
    echo ""
    echo "Créez un fichier .env avec:"
    echo "  GEMINI_API_KEY=votre_cle_api"
    echo ""
    exit 1
fi

echo "✅ Fichier .env trouvé"
echo ""

# Vérifier si les dépendances sont installées
echo "📦 Vérification des dépendances..."
if ! python3 -c "import google.generativeai" 2>/dev/null; then
    echo "⚠️  google-generativeai non installé"
    echo "Installation en cours..."
    pip3 install -r requirements.txt
else
    echo "✅ Dépendances installées"
fi

echo ""
echo "🧪 Test de la clé API..."
python3 test_gemini.py

echo ""
echo "✅ Prêt à utiliser Gemini !"
echo ""
echo "💡 Prochaines étapes:"
echo "  1. python3 exemple_analyse_gemini.py  # Voir des exemples"
echo "  2. Consultez README_GEMINI.md pour la documentation"
echo "  3. Utilisez gemini_analyzer.py dans votre code"
echo ""

