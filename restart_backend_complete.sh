#!/bin/bash
# Script pour redémarrer complètement le backend

echo "🛑 Arrêt de tous les processus backend..."
pkill -9 -f "uvicorn.*backend.main" 2>/dev/null
pkill -9 -f "python.*start_backend" 2>/dev/null
pkill -9 -f "python3.*start_backend" 2>/dev/null

sleep 2

echo "🧹 Nettoyage du cache Python..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

echo "🚀 Démarrage du backend..."
cd /Users/sou/Desktop/CURSOR/HomeScore
python3 start_backend.py &

sleep 3

echo "✅ Backend redémarré complètement"
echo "💡 Vérifiez les logs dans le terminal où le backend tourne"


