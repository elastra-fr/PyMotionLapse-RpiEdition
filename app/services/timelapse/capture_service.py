import os
import logging
import time
from pathlib import Path
from datetime import datetime
import subprocess

from app.models.timelapse import TimelapseProject
from app.services.timelapse.project_service import TimelapseProjectService
from app.services.capture import camera_utils, camera_commands

class TimelapseCapture:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.logger = logging.getLogger(__name__)
        self.project_service = TimelapseProjectService()
        
        # Vérifier si v4l2-ctl est disponible
        self.v4l2_path = camera_utils.find_v4l2_path()
        if not self.v4l2_path:
            self.logger.error("v4l2-ctl est requis. Installez avec: sudo apt install v4l-utils")
            raise RuntimeError("v4l2-ctl est requis. Installez avec: sudo apt install v4l-utils")
    
    def capture_for_project(self, project_id: str) -> bool:
        """Effectue une capture pour un projet time-lapse spécifique."""
        # Récupérer le projet
        project = self.project_service.get_project(project_id)
        if not project:
            self.logger.error(f"Projet {project_id} introuvable")
            return False
        
        # Obtenir le répertoire des captures
        captures_dir = self.project_service.get_project_captures_dir(project_id)
        
        # Créer le nom du fichier basé sur le numéro de capture
        sequence_num = project.captures_count + 1
        filename = f"capture_{sequence_num:05d}.jpg"
        output_path = os.path.join(captures_dir, filename)
        
        try:
            # Effectuer la capture
            device = f"/dev/video{self.camera_index}"
            capture_success = camera_commands.capture_image(self.v4l2_path, device, output_path)
            
            if not capture_success or not os.path.exists(output_path):
                self.logger.error(f"Échec de la capture pour le projet {project_id}")
                return False
            
            # Appliquer la rotation si nécessaire
            if project.rotation != 0:
                rotation_success = self._rotate_image(output_path, project.rotation)
                if not rotation_success:
                    self.logger.warning(f"Échec de la rotation pour la capture {sequence_num}")
            
            # Mettre à jour le compteur de captures
            project.captures_count = sequence_num
            self.project_service.update_project(project)
            
            self.logger.info(f"Capture {sequence_num} réussie pour le projet {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la capture pour le projet {project_id}: {str(e)}")
            return False
    
    def _rotate_image(self, image_path: str, rotation: int) -> bool:
        """Applique une rotation à l'image capturée."""
        if rotation not in [0, 90, 180, 270]:
            self.logger.error(f"Angle de rotation non valide: {rotation}")
            return False
        
        if rotation == 0:
            return True  # Pas de rotation nécessaire
        
        try:
            # Vérifier d'abord si imagemagick est installé
            try:
                # Tester si convert est disponible
                subprocess.run(["convert", "--version"], capture_output=True, check=True)
                imagemagick_available = True
            except (subprocess.SubprocessError, FileNotFoundError):
                self.logger.warning("ImageMagick n'est pas disponible, utilisation de la rotation Python")
                imagemagick_available = False
            
            if imagemagick_available:
                # Utiliser ImageMagick pour la rotation
                cmd = ["convert", image_path, "-rotate", str(rotation), image_path]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                self.logger.info(f"Image rotée avec ImageMagick: {rotation}°")
                return True
            else:
                # Utiliser PIL comme alternative
                try:
                    from PIL import Image
                    img = Image.open(image_path)
                    # PIL rotation: 90=ROTATE_90, 180=ROTATE_180, 270=ROTATE_270
                    if rotation == 90:
                        img = img.transpose(Image.ROTATE_90)
                    elif rotation == 180:
                        img = img.transpose(Image.ROTATE_180)
                    elif rotation == 270:
                        img = img.transpose(Image.ROTATE_270)
                    
                    img.save(image_path)
                    self.logger.info(f"Image rotée avec PIL: {rotation}°")
                    return True
                except Exception as e:
                    self.logger.error(f"Échec de la rotation avec PIL: {str(e)}")
                    return False
        except Exception as e:
            self.logger.error(f"Erreur lors de la rotation de l'image: {str(e)}")
            return False
    
    def get_preview_with_rotation(self, project_id: str) -> str:
        """Crée un aperçu pour un projet avec la rotation appliquée."""
        # Récupérer le projet
        project = self.project_service.get_project(project_id)
        if not project:
            self.logger.error(f"Projet {project_id} introuvable")
            return None
        
        # Créer un fichier temporaire pour l'aperçu
        captures_dir = self.project_service.get_project_captures_dir(project_id)
        preview_path = os.path.join(captures_dir, "preview.jpg")
        
        try:
            # Effectuer la capture
            device = f"/dev/video{self.camera_index}"
            capture_success = camera_commands.capture_image(self.v4l2_path, device, preview_path)
            
            if not capture_success or not os.path.exists(preview_path):
                self.logger.error(f"Échec de l'aperçu pour le projet {project_id}")
                return None
            
            # Appliquer la rotation si nécessaire
            if project.rotation != 0:
                rotation_success = self._rotate_image(preview_path, project.rotation)
                if not rotation_success:
                    self.logger.warning(f"Échec de la rotation pour l'aperçu")
            
            return preview_path
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'aperçu pour le projet {project_id}: {str(e)}")
            return None