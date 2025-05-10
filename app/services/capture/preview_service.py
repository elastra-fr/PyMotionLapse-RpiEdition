import os
import logging
import time
from pathlib import Path
from datetime import datetime


from .import camera_utils
from .import camera_commands as v4l2_wrapper

class PreviewService:
    def __init__(self, camera_index=0, output_dir="captures"):
        self.camera_index = camera_index
        self.output_dir = output_dir
        
        # Créer le répertoire de capture si inexistant
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        
        # Sur Raspberry Pi, on vérifie v4l2-ctl
        self.v4l2_path = camera_utils.find_v4l2_path()
        if not self.v4l2_path:
            self.logger.error("v4l2-ctl est requis. Installez avec: sudo apt install v4l-utils")
            raise RuntimeError("v4l2-ctl est requis. Installez avec: sudo apt install v4l-utils")
            
        self.logger.info(f"v4l2-ctl trouvé à {self.v4l2_path}")

    def capture_image(self):
        """
        Capture une image brute avec v4l2 sans modification de qualité.
        """
        start_time = time.time()
        
        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        image_path = os.path.join(self.output_dir, f"capture_{timestamp}.jpg")
        
        try:
            device = f"/dev/video{self.camera_index}"
            capture_success = v4l2_wrapper.capture_image(self.v4l2_path, device, image_path)
            
            if not capture_success or not os.path.exists(image_path):
                self.logger.error("Échec de la capture avec v4l2")
                raise RuntimeError("Impossible de capturer une image avec v4l2")
                
            elapsed_time = time.time() - start_time
            self.logger.info(f"Image capturée en {elapsed_time:.2f}s")
            return image_path
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la capture: {str(e)}")
            raise RuntimeError(f"Échec de capture: {str(e)}")

    def select_camera(self, camera_index):
        """Sélectionne une caméra par son index."""
        self.camera_index = int(camera_index)
        self.logger.info(f"Caméra sélectionnée: {camera_index}")
        return {"status": "success", "message": f"Caméra {camera_index} sélectionnée"}