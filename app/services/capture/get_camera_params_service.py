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
                "resolution": self._get_current_resolution(device),
                "info": self.get_camera_info()
            }
            
            return params
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des paramètres: {str(e)}")
            return {"error": str(e)}

    def _get_current_controls(self, device):
        """Récupère les valeurs actuelles des contrôles de la caméra."""
        try:
            # Utiliser --list-ctrls pour obtenir les contrôles avec leurs valeurs
            cmd = [self.v4l2_path, "-d", device, "--list-ctrls"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Erreur lors de la récupération des contrôles: {result.stderr}")
                return {}
                
            controls = {}
            # Format typique: "brightness (int)   : min=0 max=255 step=1 default=128 value=128"
            control_pattern = r"(\w+)\s+\(\w+\)\s*:.+value=(-?\d+)"
            
            for line in result.stdout.splitlines():
                match = re.search(control_pattern, line)
                if match:
                    key = match.group(1)
                    value = int(match.group(2))
                    controls[key] = value
            
            return controls
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des contrôles: {str(e)}")
            return {}

    def _get_current_resolution(self, device):
        """Récupère la résolution actuelle de la caméra."""
        try:
            cmd = [self.v4l2_path, "-d", device, "--get-fmt-video"]
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

    def get_camera_info(self):
        """Récupère les informations générales sur la caméra."""
        try:
            device = f"/dev/video{self.camera_index}"
            cmd = [self.v4l2_path, "-d", device, "--info"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Erreur lors de la récupération des infos caméra: {result.stderr}")
                return {}
                
            info = {}
            for line in result.stdout.splitlines():
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        info[key] = value
                        
            return info
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des infos caméra: {str(e)}")
            return {}
            
    def get_supported_resolutions(self):
        """Récupère toutes les résolutions supportées par la caméra."""
        try:
            device = f"/dev/video{self.camera_index}"
            cmd = [self.v4l2_path, "-d", device, "--list-formats-ext"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Erreur lors de la récupération des résolutions supportées: {result.stderr}")
                return []
                
            resolutions = []
            current_format = None
            
            for line in result.stdout.splitlines():
                # Chercher un nouveau format
                format_match = re.search(r"Pixel Format: '([^']+)'", line)
                if format_match:
                    current_format = format_match.group(1)
                    continue
                
                # Chercher une résolution pour le format actuel
                res_match = re.search(r"Size: Discrete (\d+)x(\d+)", line)
                if res_match and current_format:
                    resolutions.append({
                        "format": current_format,
                        "width": int(res_match.group(1)),
                        "height": int(res_match.group(2))
                    })
                    
            return resolutions
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des résolutions supportées: {str(e)}")
            return []
            
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
            
    def set_control(self, control_name, value):
        """
        Définit un contrôle spécifique de la caméra.
        Retourne True si réussi, False sinon.
        """
        try:
            device = f"/dev/video{self.camera_index}"
            cmd = [self.v4l2_path, "-d", device, "--set-ctrl", f"{control_name}={value}"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Erreur lors de la définition du contrôle {control_name}: {result.stderr}")
                return False
                
            self.logger.info(f"Contrôle {control_name} défini à {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la définition du contrôle {control_name}: {str(e)}")
            return False