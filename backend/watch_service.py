"""
Service de surveillance des fichiers pour détecter les changements
et notifier les clients via WebSocket
"""
import os
import time
import threading
from pathlib import Path
from typing import Callable, Dict, List
from datetime import datetime

class WatchService:
    """Service de surveillance des fichiers JSON et notification via WebSocket"""
    
    def __init__(self, broadcast_callback: Callable[[Dict], None] = None, debounce_seconds: float = 1.0):
        """
        Args:
            broadcast_callback: Fonction appelée pour envoyer des messages aux clients WebSocket
            debounce_seconds: Délai en secondes avant d'envoyer une notification après un changement
        """
        import asyncio
        self.loop = None
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            # Si pas de loop en cours, créer un nouveau thread avec un loop
            pass
        self.broadcast_callback = broadcast_callback
        self.debounce_seconds = debounce_seconds
        self.last_notification_time = {}
        self.watching = False
        self.watch_thread = None
        self._main_loop = None  # Sera défini lors du startup pour permettre run_coroutine_threadsafe
        
        # Fichiers à surveiller
        self.files_to_watch = [
            'data/all_apartments.json',  # Fichier principal où sont sauvegardés les appartements enrichis
            'data/scores/all_apartments_scores.json',
            'data/scraped_apartments.json',
        ]
        
        # Cache des temps de modification
        self.file_mtimes: Dict[str, float] = {}
        self.init_cache()
    
    def init_cache(self):
        """Initialise le cache avec les temps de modification actuels"""
        for filepath in self.files_to_watch:
            if os.path.exists(filepath):
                self.file_mtimes[filepath] = os.path.getmtime(filepath)
    
    def check_changes(self) -> List[str]:
        """Vérifie si des fichiers ont changé et retourne la liste des fichiers modifiés"""
        changed_files = []
        
        for filepath in self.files_to_watch:
            if not os.path.exists(filepath):
                continue
            
            current_mtime = os.path.getmtime(filepath)
            cached_mtime = self.file_mtimes.get(filepath, 0)
            
            if current_mtime > cached_mtime:
                changed_files.append(filepath)
                self.file_mtimes[filepath] = current_mtime
        
        return changed_files
    
    def notify_change(self, changed_files: List[str]):
        """Notifie les clients d'un changement via WebSocket"""
        # #region agent log
        import json as json_module
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:69","message":"notify_change called","data":{"changed_files":changed_files,"has_callback":self.broadcast_callback is not None},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
        # #endregion
        if not self.broadcast_callback:
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:72","message":"No broadcast callback, returning early","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            # #endregion
            return
        
        # Debounce: éviter les notifications trop fréquentes
        current_time = time.time()
        last_time = self.last_notification_time.get('apartments', 0)
        
        if current_time - last_time < self.debounce_seconds:
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:80","message":"Debounced, skipping notification","data":{"time_since_last":current_time - last_time,"debounce_seconds":self.debounce_seconds},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            # #endregion
            return
        
        self.last_notification_time['apartments'] = current_time
        # #region agent log
        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:84","message":"Proceeding with notification","data":{"has_main_loop":hasattr(self, '_main_loop') and self._main_loop is not None},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
        # #endregion
        
        # Invalider le cache de l'API apartments
        try:
            from backend.api.apartments import invalidate_cache
            print(f"🔄 Invalidation du cache après modification de {changed_files}")
            invalidate_cache()
            print(f"✅ Cache invalidé avec succès")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'invalidation du cache: {e}")
            import traceback
            traceback.print_exc()
        
        # Envoyer la notification aux clients
        message = {
            "type": "apartments_updated",
            "timestamp": datetime.now().isoformat(),
            "changed_files": changed_files
        }
        
        try:
            if self.broadcast_callback:
                import asyncio
                # #region agent log
                import json as json_module
                # Ne pas réimporter time ici pour éviter le conflit avec le module time importé au niveau du fichier
                with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                    logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:97","message":"Broadcasting WebSocket message","data":{"callback_is_coro":asyncio.iscoroutinefunction(self.broadcast_callback) if self.broadcast_callback else False,"changed_files_count":len(changed_files)},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                # #endregion
                # Si callback est async, utiliser run_coroutine_threadsafe pour appeler depuis un thread différent
                if asyncio.iscoroutinefunction(self.broadcast_callback):
                    # Le watch service s'exécute dans un thread séparé, donc on doit utiliser run_coroutine_threadsafe
                    # avec la boucle principale stockée lors du startup
                    if hasattr(self, '_main_loop') and self._main_loop is not None:
                        # #region agent log
                        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:104","message":"Using stored main loop with run_coroutine_threadsafe","data":{"main_loop_running":self._main_loop.is_running()},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                        # #endregion
                        try:
                            future = asyncio.run_coroutine_threadsafe(self.broadcast_callback(message), self._main_loop)
                            # Attendre un peu pour voir si ça réussit (mais ne pas bloquer indéfiniment)
                            # #region agent log
                            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:110","message":"run_coroutine_threadsafe called, future created","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                            # #endregion
                        except Exception as e:
                            # #region agent log
                            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:115","message":"Exception calling run_coroutine_threadsafe","data":{"error":str(e),"error_type":type(e).__name__},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                            # #endregion
                            raise
                    else:
                        # Fallback: essayer de créer une nouvelle boucle (ne devrait pas arriver normalement)
                        # #region agent log
                        with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                            logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:121","message":"No main loop stored, creating new loop (fallback)","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                        # #endregion
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(self.broadcast_callback(message))
                            loop.close()
                        except Exception as e:
                            # #region agent log
                            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:130","message":"Exception in fallback loop","data":{"error":str(e),"error_type":type(e).__name__},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                            # #endregion
                            raise
                else:
                    # #region agent log
                    with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                        logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:121","message":"Callback is not async, calling directly","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                    # #endregion
                    self.broadcast_callback(message)
                # #region agent log
                with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                    logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:125","message":"Broadcast completed successfully","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
                # #endregion
            print(f"📢 [{datetime.now().strftime('%H:%M:%S')}] Notification envoyée: {len(changed_files)} fichier(s) modifié(s)")
        except Exception as e:
            # #region agent log
            with open('/Users/sou/Desktop/CURSOR/HomeScore/.cursor/debug.log', 'a') as logf:
                logf.write(json_module.dumps({"id":f"log_{int(time.time()*1000)}","timestamp":int(time.time()*1000),"location":"watch_service.py:130","message":"ERROR broadcasting WebSocket message","data":{"error":str(e),"error_type":type(e).__name__},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
            # #endregion
            print(f"⚠️  Erreur lors de l'envoi de la notification: {e}")
    
    def watch_loop(self):
        """Boucle de surveillance (à exécuter dans un thread séparé)"""
        print("👀 Surveillance des fichiers démarrée")
        print(f"   Fichiers surveillés: {', '.join(self.files_to_watch)}")
        
        while self.watching:
            try:
                changed_files = self.check_changes()
                
                if changed_files:
                    print(f"📝 [{datetime.now().strftime('%H:%M:%S')}] Fichiers modifiés détectés:")
                    for filepath in changed_files:
                        print(f"   • {filepath}")
                    self.notify_change(changed_files)
                
                time.sleep(1)  # Vérifier toutes les secondes
            except Exception as e:
                print(f"⚠️  Erreur dans la boucle de surveillance: {e}")
                time.sleep(5)  # Attendre plus longtemps en cas d'erreur
    
    def start_watching(self):
        """Démarre la surveillance dans un thread séparé"""
        if self.watching:
            return
        
        self.watching = True
        self.watch_thread = threading.Thread(target=self.watch_loop, daemon=True)
        self.watch_thread.start()
        print("✅ Service de surveillance démarré")
    
    def stop_watching(self):
        """Arrête la surveillance"""
        self.watching = False
        if self.watch_thread:
            self.watch_thread.join(timeout=2)
        print("🛑 Service de surveillance arrêté")

