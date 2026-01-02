#!/bin/bash
# Script pour lancer uniquement le backend dans un terminal externe

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Aller dans le répertoire du projet
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 Lancement du backend dans un terminal externe${NC}"
echo ""

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 n'est pas installé${NC}"
    exit 1
fi

# Fonction pour arrêter les processus sur un port
kill_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}⚠️  Arrêt des processus sur le port $port...${NC}"
        kill $pids 2>/dev/null
        sleep 1
        # Forcer l'arrêt si nécessaire
        pids=$(lsof -ti :$port 2>/dev/null)
        if [ ! -z "$pids" ]; then
            kill -9 $pids 2>/dev/null
        fi
    fi
}

# Arrêter les processus existants
echo -e "${YELLOW}🛑 Arrêt des processus backend existants...${NC}"
pkill -9 -f "uvicorn.*backend.main" 2>/dev/null
pkill -9 -f "python.*start_backend" 2>/dev/null
pkill -9 -f "python3.*start_backend" 2>/dev/null
kill_port 8000
sleep 2

# Détecter le terminal par défaut (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v osascript &> /dev/null; then
        # Lancer le backend dans un nouveau terminal
        echo -e "${GREEN}📊 Lancement du backend dans un nouveau terminal...${NC}"
        osascript <<EOF
tell application "Terminal"
    do script "cd '$SCRIPT_DIR' && python3 start_backend.py"
end tell
EOF
        
        sleep 2
        
        echo ""
        echo -e "${GREEN}✅ Backend lancé dans un terminal externe${NC}"
        echo ""
        echo -e "${GREEN}📊 Backend API:${NC}    http://localhost:8000"
        echo -e "${GREEN}📚 Documentation:${NC}  http://localhost:8000/docs"
        echo ""
        echo -e "${YELLOW}💡 Le serveur tourne dans une fenêtre Terminal séparée${NC}"
    else
        echo -e "${RED}❌ osascript non disponible. Lancez manuellement:${NC}"
        echo "   cd '$SCRIPT_DIR' && python3 start_backend.py"
        exit 1
    fi
else
    # Pour Linux, utiliser gnome-terminal ou xterm
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && python3 start_backend.py; exec bash" &
        echo -e "${GREEN}✅ Backend lancé dans un terminal externe${NC}"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$SCRIPT_DIR' && python3 start_backend.py" &
        echo -e "${GREEN}✅ Backend lancé dans un terminal externe${NC}"
    else
        echo -e "${RED}❌ Terminal non supporté. Lancez manuellement:${NC}"
        echo "   cd '$SCRIPT_DIR' && python3 start_backend.py"
        exit 1
    fi
fi
