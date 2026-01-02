"""
Serveur FastAPI principal pour l'API HomeScore
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.api import apartments, alerts, criteria_analysis
from backend.watch_service import WatchService
import uvicorn

app = FastAPI(
    title="HomeScore API",
    description="API pour accéder aux données des appartements scorés",
    version="1.0.0"
)

# CORS middleware pour permettre les requêtes depuis le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(apartments.router)
app.include_router(alerts.router)
app.include_router(criteria_analysis.router)

# Store des connexions WebSocket actives
active_connections: list[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour les mises à jour en temps réel"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Envoyer un message de bienvenue
        await websocket.send_json({
            "type": "connected",
            "message": "Connexion WebSocket établie"
        })
        
        # Attendre les messages du client (pour garder la connexion ouverte)
        while True:
            try:
                data = await websocket.receive_text()
                # Pour l'instant, on ignore les messages du client
                # On pourrait implémenter des commandes si nécessaire
            except WebSocketDisconnect:
                break
    except Exception as e:
        print(f"Erreur WebSocket: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

async def broadcast_to_clients(message: dict):
    """Envoie un message à tous les clients WebSocket connectés"""
    # #region agent log
    import json as json_module
    import time
    with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
        logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"main.py:60","message":"broadcast_to_clients called","data":{"message_type":message.get("type"),"connections_count":len(active_connections)},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
    # #endregion
    disconnected = []
    for connection in active_connections:
        try:
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"main.py:68","message":"Sending WebSocket message to client","data":{"message_type":message.get("type")},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            # #endregion
            await connection.send_json(message)
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"main.py:72","message":"WebSocket message sent successfully","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            # #endregion
        except Exception as e:
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"main.py:75","message":"Error sending WebSocket message","data":{"error":str(e)},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            # #endregion
            print(f"Erreur lors de l'envoi WebSocket: {e}")
            disconnected.append(connection)
    
    # Nettoyer les connexions déconnectées
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)
    # #region agent log
    with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
        logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"main.py:83","message":"broadcast_to_clients completed","data":{"sent_count":len(active_connections) - len(disconnected),"disconnected_count":len(disconnected)},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
    # #endregion

# Instance globale du service de surveillance
watch_service_instance = None

@app.on_event("startup")
async def startup_event():
    """Démarre le service de surveillance des fichiers"""
    global watch_service_instance
    import asyncio
    print("🚀 Démarrage du serveur HomeScore API")
    # Obtenir la boucle principale pour le watch service
    main_loop = asyncio.get_event_loop()
    watch_service_instance = WatchService(broadcast_callback=broadcast_to_clients)
    # Stocker la boucle principale pour pouvoir l'utiliser depuis le thread de watch
    watch_service_instance._main_loop = main_loop
    watch_service_instance.start_watching()

@app.on_event("shutdown")
async def shutdown_event():
    """Arrête le service de surveillance"""
    global watch_service_instance
    if watch_service_instance:
        watch_service_instance.stop_watching()

@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "HomeScore API",
        "version": "1.0.0",
        "endpoints": {
            "apartments": "/api/apartments",
            "alerts": "/api/alerts",
            "websocket": "/ws"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import os
    # Désactiver le reload par défaut pour éviter les rechargements constants
    # Activer avec RELOAD=true dans l'environnement si nécessaire
    reload_enabled = os.getenv("RELOAD", "false").lower() == "true"
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled,
        log_level="info"
    )

