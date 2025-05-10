import os
import logging
import subprocess
import re
import json

from . import camera_utils

class CameraParamsService:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.logger = logging.getLogger(__name__)
        
        # Vérifier si v4l2-ctl est disponible
        self.v4l2_path = camera_utils.find_v4l2_path()
        if not self.v4l2_path:
            self.logger.error("v4l2-ctl est requis. Installez avec: sudo apt install v4l-utils")
            raise RuntimeError("v4l2-ctl est requis. Installez avec: sudo apt install v4l-utils")
            
        self.logger.info(f"v4l2-ctl trouvé à {self.v4l2_path}")

    def get_current_params(self):
        """
        Récupère les paramètres actuels de la caméra au format JSON.
        """
        try:
            device = f"/dev/video{self.camera_index}"
            
            # Récupérer les paramètres
            params = {
                "camera_index": self.camera_index,
                "device": device,
                "controls": self._get_current_controls(device),
                "resolution": self._get_current_resolution(device)
            }
            
            return params
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des paramètres: {str(e)}")
            return {"error": str(e)}

    def _get_current_controls(self, device):
        """Récupère les valeurs actuelles des contrôles de la caméra."""
        try:
            cmd = [self.v4l2_path, "-d", device, "-C"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Erreur lors de la récupération des contrôles: {result.stderr}")
                return {}
                
            controls = {}
            for line in result.stdout.splitlines():
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value_parts = parts[1].strip().split()
                        
                        # Extraire la valeur numérique si possible
                        if len(value_parts) > 0:
                            try:
                                # Tenter de convertir en int ou float
                                value = int(value_parts[0])
                            except ValueError:
                                try:
                                    value = float(value_parts[0])
                                except ValueError:
                                    value = value_parts[0]
                            
                            controls[key] = value
            
            return controls
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des contrôles: {str(e)}")
            return {}

    def _get_current_resolution(self, device):
        """Récupère la résolution actuelle de la caméra."""
        try:
            cmd = [self.v4l2_path, "-d", device, "--get-fmt"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Erreur lors de la récupération de la résolution: {result.stderr}")
                return {}
            
            resolution = {}
            width_pattern = r"Width/Height\s*:\s*(\d+)/(\d+)"
            format_pattern = r"Pixel Format\s*:\s*'([^']+)'"
            
            # Extraire largeur et hauteur
            width_match = re.search(width_pattern, result.stdout)
            if width_match:
                resolution["width"] = int(width_match.group(1))
                resolution["height"] = int(width_match.group(2))
            
            # Extraire le format
            format_match = re.search(format_pattern, result.stdout)
            if format_match:
                resolution["format"] = format_match.group(1)
                
            return resolution
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de la résolution: {str(e)}")
            return {}