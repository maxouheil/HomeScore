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
        
        # Fichiers à surveiller
        self.files_to_watch = [
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
        if not self.broadcast_callback:
            return
        
        # Debounce: éviter les notifications trop fréquentes
        current_time = time.time()
        last_time = self.last_notification_time.get('apartments', 0)
        
        if current_time - last_time < self.debounce_seconds:
            return
        
        self.last_notification_time['apartments'] = current_time
        
        # Invalider le cache de l'API apartments
        try:
            from backend.api.apartments import invalidate_cache
            invalidate_cache()
        except Exception as e:
            print(f"⚠️  Erreur lors de l'invalidation du cache: {e}")
        
        # Envoyer la notification aux clients
        message = {
            "type": "apartments_updated",
            "timestamp": datetime.now().isoformat(),
            "changed_files": changed_files
        }
        
        try:
            if self.broadcast_callback:
                import asyncio
                # Si callback est async, créer une task
                if asyncio.iscoroutinefunction(self.broadcast_callback):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(self.broadcast_callback(message))
                        else:
                            loop.run_until_complete(self.broadcast_callback(message))
                    except RuntimeError:
                        # Nouveau thread si nécessaire
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.broadcast_callback(message))
                        loop.close()
                else:
                    self.broadcast_callback(message)
            print(f"📢 [{datetime.now().strftime('%H:%M:%S')}] Notification envoyée: {len(changed_files)} fichier(s) modifié(s)")
        except Exception as e:
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

