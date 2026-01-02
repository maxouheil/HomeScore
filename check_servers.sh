#!/bin/bash
# Script pour vérifier l'état des serveurs backend et frontend

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Vérification des serveurs HomeScore${NC}"
echo "=================================="
echo ""

# Vérifier les processus
echo -e "${BLUE}📊 Processus en cours :${NC}"
BACKEND_PROCESS=$(ps aux | grep -E "uvicorn.*backend.main" | grep -v grep)
FRONTEND_PROCESS=$(ps aux | grep -E "vite" | grep -v grep)

if [ ! -z "$BACKEND_PROCESS" ]; then
    echo -e "${GREEN}✅ Backend (uvicorn)${NC}"
    echo "   $BACKEND_PROCESS" | awk '{print "   PID:", $2, "| CPU:", $3"% | MEM:", $4"%"}'
else
    echo -e "${RED}❌ Backend (uvicorn) - Non démarré${NC}"
fi

if [ ! -z "$FRONTEND_PROCESS" ]; then
    echo -e "${GREEN}✅ Frontend (vite)${NC}"
    echo "   $FRONTEND_PROCESS" | awk '{print "   PID:", $2, "| CPU:", $3"% | MEM:", $4"%"}'
else
    echo -e "${RED}❌ Frontend (vite) - Non démarré${NC}"
fi

echo ""

# Vérifier les ports
echo -e "${BLUE}🔌 Ports en écoute :${NC}"
BACKEND_PORT=$(lsof -i :8000 -sTCP:LISTEN 2>/dev/null)
FRONTEND_PORT=$(lsof -i :5173 -sTCP:LISTEN 2>/dev/null)

if [ ! -z "$BACKEND_PORT" ]; then
    echo -e "${GREEN}✅ Port 8000 (Backend)${NC}"
else
    echo -e "${RED}❌ Port 8000 (Backend) - Non utilisé${NC}"
fi

if [ ! -z "$FRONTEND_PORT" ]; then
    echo -e "${GREEN}✅ Port 5173 (Frontend)${NC}"
else
    echo -e "${RED}❌ Port 5173 (Frontend) - Non utilisé${NC}"
fi

echo ""

# Tester les endpoints HTTP
echo -e "${BLUE}🌐 Test des endpoints HTTP :${NC}"

# Backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null)
    echo -e "${GREEN}✅ Backend API répond${NC}"
    echo "   http://localhost:8000/health → $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Backend API ne répond pas${NC}"
    echo "   http://localhost:8000/health → Timeout ou erreur"
fi

# Frontend
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend répond${NC}"
    echo "   http://localhost:5173 → OK"
else
    echo -e "${RED}❌ Frontend ne répond pas${NC}"
    echo "   http://localhost:5173 → Timeout ou erreur"
fi

echo ""
echo "=================================="

# Résumé
BACKEND_OK=false
FRONTEND_OK=false

if [ ! -z "$BACKEND_PROCESS" ] && [ ! -z "$BACKEND_PORT" ] && curl -s http://localhost:8000/health > /dev/null 2>&1; then
    BACKEND_OK=true
fi

if [ ! -z "$FRONTEND_PROCESS" ] && [ ! -z "$FRONTEND_PORT" ] && curl -s http://localhost:5173 > /dev/null 2>&1; then
    FRONTEND_OK=true
fi

if [ "$BACKEND_OK" = true ] && [ "$FRONTEND_OK" = true ]; then
    echo -e "${GREEN}✅ Tous les serveurs fonctionnent correctement !${NC}"
    echo ""
    echo -e "${BLUE}📊 Backend API:${NC}    http://localhost:8000"
    echo -e "${BLUE}📚 Documentation:${NC}  http://localhost:8000/docs"
    echo -e "${BLUE}🎨 Frontend:${NC}       http://localhost:5173"
    exit 0
elif [ "$BACKEND_OK" = true ]; then
    echo -e "${YELLOW}⚠️  Backend OK mais Frontend non disponible${NC}"
    exit 1
elif [ "$FRONTEND_OK" = true ]; then
    echo -e "${YELLOW}⚠️  Frontend OK mais Backend non disponible${NC}"
    exit 1
else
    echo -e "${RED}❌ Aucun serveur ne fonctionne${NC}"
    echo ""
    echo -e "${YELLOW}💡 Pour démarrer les serveurs :${NC}"
    echo "   ./start_separate.sh  (recommandé - terminaux séparés)"
    echo "   ./start.sh           (même terminal)"
    exit 1
fi

