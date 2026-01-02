#!/bin/bash
# Script pour surveiller les logs du backend en temps réel

echo "🔍 Surveillance des logs du backend..."
echo "💡 Appuyez sur Ctrl+C pour arrêter"
echo ""

# Chercher le processus uvicorn
PID=$(pgrep -f "uvicorn.*backend.main" | head -1)

if [ -z "$PID" ]; then
    echo "❌ Aucun processus backend trouvé"
    echo "💡 Assurez-vous que le backend est démarré avec ./start.sh"
    exit 1
fi

echo "✅ Processus backend trouvé (PID: $PID)"
echo ""

# Suivre les logs (sur macOS, on peut utiliser lsof pour voir les fichiers ouverts)
# Ou simplement afficher les sorties du processus
# Note: Sur macOS, on peut utiliser `log stream` pour voir les logs système

# Méthode simple: afficher les informations du processus et suggérer de regarder le terminal
echo "📊 Pour voir les logs en temps réel:"
echo "   1. Regardez le terminal où vous avez lancé ./start.sh"
echo "   2. Ou utilisez: tail -f /dev/null (les logs sont dans stdout)"
echo ""
echo "🔍 Vérification du statut du backend..."
echo ""

# Tester l'endpoint de diagnostic
echo "📈 Diagnostic du backend:"
curl -s http://localhost:8000/api/apartments/diagnostics | python3 -m json.tool 2>/dev/null || echo "❌ Impossible de récupérer les diagnostics"

echo ""
echo "💡 Pour voir les performances en temps réel, rechargez la page frontend"
echo "   Les logs de performance s'afficheront dans le terminal du backend"

