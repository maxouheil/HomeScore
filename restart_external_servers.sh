#!/bin/bash
# Script pour redémarrer les serveurs sur les serveurs externes via SSH

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration par défaut
# Modifiez ces variables selon vos serveurs externes
DEFAULT_SERVER="${HOMESCORE_SERVER:-user@server.example.com}"
DEFAULT_PATH="${HOMESCORE_REMOTE_PATH:-/path/to/HomeScore}"

# Utiliser les arguments ou les valeurs par défaut
SERVER="${1:-$DEFAULT_SERVER}"
REMOTE_PATH="${2:-$DEFAULT_PATH}"

echo -e "${BLUE}🔄 Redémarrage des serveurs HomeScore sur serveur externe${NC}"
echo -e "${BLUE}====================================================${NC}"
echo ""
echo -e "${YELLOW}Serveur:${NC} $SERVER"
echo -e "${YELLOW}Chemin:${NC}  $REMOTE_PATH"
echo ""

# Vérifier que SSH est disponible
if ! command -v ssh &> /dev/null; then
    echo -e "${RED}❌ SSH n'est pas installé${NC}"
    exit 1
fi

# Commande SSH pour redémarrer les serveurs
echo -e "${BLUE}🛑 Arrêt des processus existants...${NC}"
ssh "$SERVER" "cd $REMOTE_PATH && \
    pkill -9 -f 'uvicorn.*backend.main' 2>/dev/null; \
    pkill -9 -f 'python.*start_backend' 2>/dev/null; \
    pkill -9 -f 'python3.*start_backend' 2>/dev/null; \
    pkill -9 -f 'vite' 2>/dev/null; \
    pkill -9 -f 'npm run dev' 2>/dev/null; \
    echo '✅ Processus arrêtés'"

sleep 2

echo -e "${BLUE}🧹 Nettoyage du cache...${NC}"
ssh "$SERVER" "cd $REMOTE_PATH && \
    find . -type d -name '__pycache__' -exec rm -r {} + 2>/dev/null; \
    find . -name '*.pyc' -delete 2>/dev/null; \
    echo '✅ Cache nettoyé'"

echo -e "${BLUE}🚀 Démarrage du backend...${NC}"
ssh "$SERVER" "cd $REMOTE_PATH && \
    nohup python3 start_backend.py > /tmp/homescore_backend.log 2>&1 & \
    echo '✅ Backend démarré (PID: \$!)'"

sleep 3

echo -e "${BLUE}🚀 Démarrage du frontend...${NC}"
ssh "$SERVER" "cd $REMOTE_PATH/frontend && \
    nohup npm run dev > /tmp/homescore_frontend.log 2>&1 & \
    echo '✅ Frontend démarré (PID: \$!)'"

sleep 2

echo ""
echo -e "${GREEN}✅ Redémarrage terminé!${NC}"
echo ""
echo -e "${YELLOW}💡 Pour vérifier les logs:${NC}"
echo "   ssh $SERVER 'tail -f /tmp/homescore_backend.log'"
echo "   ssh $SERVER 'tail -f /tmp/homescore_frontend.log'"
echo ""
echo -e "${YELLOW}💡 Pour vérifier l'état des serveurs:${NC}"
echo "   ssh $SERVER 'cd $REMOTE_PATH && ./check_servers.sh'"
