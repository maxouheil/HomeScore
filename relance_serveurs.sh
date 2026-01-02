#!/bin/bash
# Script pour relancer les serveurs backend et frontend dans des terminaux externes

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Aller dans le répertoire du projet
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🔄 Relance des serveurs HomeScore${NC}"
echo "=================================="
echo ""

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 n'est pas installé${NC}"
    exit 1
fi

# Vérifier que npm est disponible
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm n'est pas installé${NC}"
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
echo -e "${YELLOW}🛑 Arrêt des processus existants...${NC}"
pkill -9 -f "uvicorn.*backend.main" 2>/dev/null
pkill -9 -f "python.*start_backend" 2>/dev/null
pkill -9 -f "python3.*start_backend" 2>/dev/null
pkill -9 -f "vite" 2>/dev/null
pkill -9 -f "npm run dev" 2>/dev/null
kill_port 8000
kill_port 5173
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
        
        # Attendre un peu
        sleep 2
        
        # Lancer le frontend dans un nouveau terminal
        echo -e "${GREEN}🎨 Lancement du frontend dans un nouveau terminal...${NC}"
        osascript <<EOF
tell application "Terminal"
    do script "cd '$SCRIPT_DIR/frontend' && npm run dev"
end tell
EOF
        
        sleep 2
        
        echo ""
        echo -e "${GREEN}✅ Serveurs relancés dans des terminaux séparés${NC}"
        echo ""
        echo -e "${GREEN}📊 Backend API:${NC}    http://localhost:8000"
        echo -e "${GREEN}📚 Documentation:${NC}  http://localhost:8000/docs"
        echo -e "${GREEN}🎨 Frontend:${NC}       http://localhost:5173"
        echo ""
        echo -e "${YELLOW}💡 Les serveurs tournent dans des fenêtres Terminal séparées${NC}"
    else
        echo -e "${RED}❌ osascript non disponible. Lancez manuellement:${NC}"
        echo "   Backend:  cd '$SCRIPT_DIR' && python3 start_backend.py"
        echo "   Frontend: cd '$SCRIPT_DIR/frontend' && npm run dev"
        exit 1
    fi
else
    # Pour Linux, utiliser gnome-terminal ou xterm
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && python3 start_backend.py; exec bash" &
        sleep 1
        gnome-terminal -- bash -c "cd '$SCRIPT_DIR/frontend' && npm run dev; exec bash" &
        echo -e "${GREEN}✅ Serveurs relancés dans des terminaux séparés${NC}"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$SCRIPT_DIR' && python3 start_backend.py" &
        sleep 1
        xterm -e "cd '$SCRIPT_DIR/frontend' && npm run dev" &
        echo -e "${GREEN}✅ Serveurs relancés dans des terminaux séparés${NC}"
    else
        echo -e "${RED}❌ Terminal non supporté. Lancez manuellement:${NC}"
        echo "   Backend:  cd '$SCRIPT_DIR' && python3 start_backend.py"
        echo "   Frontend: cd '$SCRIPT_DIR/frontend' && npm run dev"
        exit 1
    fi
fi
