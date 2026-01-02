#!/bin/bash
# Script pour lancer le backend et le frontend ensemble

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour vérifier si un port est utilisé
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port utilisé
    else
        return 1  # Port libre
    fi
}

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

# Fonction pour nettoyer les processus à l'arrêt
cleanup() {
    echo -e "\n${YELLOW}🛑 Arrêt des serveurs...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    # Nettoyer les ports
    kill_port 8000
    kill_port 5173
    # Nettoyer les processus restants
    pkill -f "uvicorn.*backend.main" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    echo -e "${GREEN}✅ Serveurs arrêtés${NC}"
    exit 0
}

# Capturer Ctrl+C
trap cleanup SIGINT SIGTERM

# Aller dans le répertoire du projet
cd "$(dirname "$0")"

echo -e "${BLUE}🚀 Démarrage de HomeScore${NC}"
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

# Vérifier et libérer le port 8000 (backend)
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Le port 8000 est déjà utilisé${NC}"
    kill_port 8000
    sleep 1
fi

# Vérifier et libérer le port 5173 (frontend)
if check_port 5173; then
    echo -e "${YELLOW}⚠️  Le port 5173 est déjà utilisé${NC}"
    kill_port 5173
    sleep 1
fi

# Démarrer le backend en arrière-plan
echo -e "${GREEN}📊 Démarrage du backend...${NC}"
python3 start_backend.py &
BACKEND_PID=$!

# Attendre un peu que le backend démarre
sleep 3

# Vérifier que le backend a démarré
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Le backend n'a pas démarré correctement${NC}"
    echo -e "${YELLOW}💡 Vérifiez les logs ci-dessus pour plus de détails${NC}"
    exit 1
fi

# Vérifier que le port 8000 est bien utilisé par notre processus
if ! check_port 8000; then
    echo -e "${RED}❌ Le backend n'a pas réussi à démarrer sur le port 8000${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Démarrer le frontend en arrière-plan
echo -e "${GREEN}🎨 Démarrage du frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Attendre un peu que le frontend démarre
sleep 3

# Vérifier que le frontend a démarré
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Le frontend n'a pas démarré correctement${NC}"
    echo -e "${YELLOW}💡 Vérifiez les logs ci-dessus pour plus de détails${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Vérifier que le port 5173 est bien utilisé par notre processus
if ! check_port 5173; then
    echo -e "${YELLOW}⚠️  Le frontend peut prendre quelques secondes supplémentaires pour démarrer${NC}"
    sleep 2
fi

echo ""
echo -e "${BLUE}=================================="
echo -e "✅ Serveurs démarrés!${NC}"
echo -e "${BLUE}=================================="
echo ""
echo -e "${GREEN}📊 Backend API:${NC}    http://localhost:8000"
echo -e "${GREEN}📚 Documentation:${NC}  http://localhost:8000/docs"
echo -e "${GREEN}🎨 Frontend:${NC}       http://localhost:5173"
echo ""
echo -e "${YELLOW}💡 Appuyez sur Ctrl+C pour arrêter les serveurs${NC}"
echo -e "${YELLOW}💡 Les logs s'affichent ci-dessus${NC}"
echo ""

# Attendre que les processus se terminent
wait $BACKEND_PID $FRONTEND_PID

