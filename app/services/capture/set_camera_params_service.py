import os
import logging
import subprocess
import re

from . import camera_utils

class CameraSettingsService:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.logger = logging.getLogger(__name__)
        
        # Vérifier si v4l2-ctl est disponible
        self.v4l2_path = camera_utils.find_v4l2_path()
        if not self.v4l2_path:
            self.logger.error("v4l2-ctl est requis. Installez avec: sudo apt install v4l-utils")
            raise RuntimeError("v4l2-ctl est requis. Installez avec: sudo apt install v4l-utils")
            
        self.logger.info(f"v4l2-ctl trouvé à {self.v4l2_path}")
    
    def set_resolution(self, width, height, pixel_format=None):
        """
        Définit la résolution de la caméra.
        Retourne True si réussi, False sinon.
        """
        try:
            device = f"/dev/video{self.camera_index}"
            
            # Préparer la commande
            cmd = [self.v4l2_path, "-d", device, "--set-fmt-video"]
            
            # Ajouter les dimensions
            cmd.extend([f"width={width}", f"height={height}"])
            
            # Ajouter le format de pixel si spécifié
            if pixel_format:
                cmd.append(f"pixelformat={pixel_format}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Erreur lors de la définition de la résolution: {result.stderr}")
                return False
                
            self.logger.info(f"Résolution définie à {width}x{height}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la définition de la résolution: {str(e)}")
            return False