import os
import time
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from app.models.timelapse import TimelapseProject
from app.services.timelapse.project_service import TimelapseProjectService
from app.services.timelapse.capture_service import TimelapseCapture

class TimelapseAutoCaptureService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_service = TimelapseProjectService()
        self.capture_service = TimelapseCapture()
        
        # État du service
        self.active_captures: Dict[str, Dict] = {}
        self.stop_flags: Dict[str, bool] = {}
        self.threads: Dict[str, threading.Thread] = {}
    
    def start_capture(self, project_id: str) -> bool:
        """Démarre la capture automatique pour un projet."""
        if project_id in self.active_captures:
            self.logger.warning(f"Capture déjà active pour le projet {project_id}")
            return False
            
        # Récupérer le projet
        project = self.project_service.get_project(project_id)
        if not project:
            self.logger.error(f"Projet {project_id} introuvable")
            return False
            
        # Vérifier si le projet est déjà terminé
        if project.captures_count >= project.total_captures:
            self.logger.warning(f"Projet {project_id} déjà terminé")
            return False
            
        # Configurer le drapeau d'arrêt
        self.stop_flags[project_id] = False
            
        # Démarrer un thread pour la capture
        thread = threading.Thread(
            target=self._capture_loop,
            args=(project_id, project.interval_seconds),
            daemon=True
        )
        
        self.threads[project_id] = thread
        thread.start()
        
        # Enregistrer la capture active
        self.active_captures[project_id] = {
            "started_at": datetime.now(),
            "project": project,
            "next_capture": time.time() + project.interval_seconds
        }
        
        self.logger.info(f"Capture automatique démarrée pour le projet {project_id}")
        return True
    
    def stop_capture(self, project_id: str) -> bool:
        """Arrête la capture automatique pour un projet."""
        if project_id not in self.active_captures:
            self.logger.warning(f"Aucune capture active pour le projet {project_id}")
            return False
            
        # Demander l'arrêt du thread
        self.stop_flags[project_id] = True
        
        # Attendre un court moment pour que le thread se termine
        if project_id in self.threads:
            self.threads[project_id].join(timeout=2.0)
            
        # Supprimer les références
        if project_id in self.active_captures:
            del self.active_captures[project_id]
        if project_id in self.stop_flags:
            del self.stop_flags[project_id]
        if project_id in self.threads:
            del self.threads[project_id]
            
        self.logger.info(f"Capture automatique arrêtée pour le projet {project_id}")
        return True
    
    def get_capture_status(self, project_id: str) -> Optional[Dict]:
        """Retourne l'état de la capture pour un projet."""
        if project_id not in self.active_captures:
            return None
            
        status = self.active_captures[project_id].copy()
        
        # Mise à jour des informations du projet
        project = self.project_service.get_project(project_id)
        if project:
            status["project"] = project
            
        # Calcul du temps restant avant la prochaine capture
        status["seconds_to_next"] = max(0, round(status["next_capture"] - time.time()))
        
        return status
    
    def get_all_active_captures(self) -> Dict[str, Dict]:
        """Retourne l'état de toutes les captures actives."""
        result = {}
        for project_id in list(self.active_captures.keys()):
            status = self.get_capture_status(project_id)
            if status:
                result[project_id] = status
        return result
    
    def _capture_loop(self, project_id: str, interval_seconds: int) -> None:
        """Boucle de capture pour un projet."""
        try:
            while not self.stop_flags.get(project_id, True):
                # Récupérer le projet pour avoir les infos à jour
                project = self.project_service.get_project(project_id)
                if not project:
                    self.logger.error(f"Projet {project_id} introuvable, arrêt de la capture")
                    break
                    
                # Vérifier si toutes les captures ont été effectuées
                if project.captures_count >= project.total_captures:
                    self.logger.info(f"Projet {project_id} terminé, arrêt de la capture")
                    break
                
                # Effectuer la capture
                success = self.capture_service.capture_for_project(project_id)
                
                if success:
                    self.logger.info(f"Capture {project.captures_count + 1} réussie pour le projet {project_id}")
                    
                    # Mettre à jour l'heure de la prochaine capture
                    next_capture = time.time() + interval_seconds
                    if project_id in self.active_captures:
                        self.active_captures[project_id]["next_capture"] = next_capture
                    
                    # Attendre jusqu'à la prochaine capture
                    sleep_time = interval_seconds
                    while sleep_time > 0 and not self.stop_flags.get(project_id, True):
                        time.sleep(1)
                        sleep_time -= 1
                else:
                    self.logger.error(f"Échec de la capture pour le projet {project_id}")
                    # Attendre un peu avant de réessayer
                    time.sleep(5)
        except Exception as e:
            self.logger.exception(f"Erreur dans la boucle de capture pour le projet {project_id}: {str(e)}")
        finally:
            # S'assurer que le projet est retiré des captures actives
            if project_id in self.active_captures:
                del self.active_captures[project_id]
            if project_id in self.stop_flags:
                del self.stop_flags[project_id]
            if project_id in self.threads:
                del self.threads[project_id]