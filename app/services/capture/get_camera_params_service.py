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
        Récupère les paramètres actuels de la caméra dans un format lisible.
        """
        try:
            device = f"/dev/video{self.camera_index}"
            
            # Récupérer tous les paramètres bruts
            raw_controls = self._get_current_controls(device)
            mappings = raw_controls.pop("_mappings", {})
            
            # Créer un dictionnaire inversé pour trouver l'ID hex par nom
            name_to_id = {v: k for k, v in mappings.items()}
            
            # Organiser les contrôles de manière plus lisible
            readable_controls = {}
            for name, hex_id in name_to_id.items():
                if hex_id in raw_controls:
                    readable_controls[name] = {
                        "id": hex_id,
                        "value": raw_controls[hex_id]
                    }
            
            # Ajouter les contrôles qui n'ont pas de mappage
            for key, value in raw_controls.items():
                if key not in [v for k, v in name_to_id.items()]:
                    readable_controls[key] = {
                        "id": key,
                        "value": value
                    }
            
            # Construire la réponse finale
            params = {
                "camera_index": self.camera_index,
                "device": device,
                "controls": readable_controls,
                "resolution": self._get_current_resolution(device),
                "info": self.get_camera_info()
            }
            
            return params
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des paramètres: {str(e)}")
            return {"error": str(e)}

    def _get_current_controls(self, device):
        """Récupère les valeurs actuelles des contrôles de la caméra avec un mappage des noms."""
        try:
            # Utiliser --list-ctrls pour obtenir les contrôles avec leurs valeurs
            cmd = [self.v4l2_path, "-d", device, "--list-ctrls"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Erreur lors de la récupération des contrôles: {result.stderr}")
                return {}
                
            controls = {}
            control_mappings = {
                # User Controls
                "0x00980900": "brightness",
                "0x00980901": "contrast",
                "0x00980902": "saturation",
                "0x00980903": "hue",
                "0x0098090c": "white_balance_automatic",
                "0x00980910": "gamma",
                "0x00980913": "gain",
                "0x00980918": "power_line_frequency",
                "0x0098091a": "white_balance_temperature",
                "0x0098091b": "sharpness",
                "0x0098091c": "backlight_compensation",
                
                # Camera Controls
                "0x009a0901": "auto_exposure",
                "0x009a0902": "exposure_time_absolute",
                "0x009a090a": "focus_absolute",
                "0x009a090c": "focus_automatic_continuous"
            }
            
            # Format typique: "brightness 0x00980900 (int)   : min=0 max=255 step=1 default=128 value=128"
            # Extraire à la fois le nom et l'identifiant
            full_pattern = r"(\w+)\s+(0x[0-9a-f]+)\s+\(\w+\)\s*:.+value=(-?\d+)"
            
            for line in result.stdout.splitlines():
                # Essayer d'abord avec le pattern complet
                match = re.search(full_pattern, line)
                if match:
                    name = match.group(1)
                    hex_id = match.group(2)
                    value = int(match.group(3))
                    controls[hex_id] = value
                    continue
                
                # Pattern simplifié pour les cas où l'ID n'est pas visible
                simple_pattern = r"(\w+)\s+\(\w+\)\s*:.+value=(-?\d+)"
                match = re.search(simple_pattern, line)
                if match:
                    name = match.group(1)
                    value = int(match.group(2))
                    
                    # Chercher l'ID hex pour ce nom
                    for hex_id, mapped_name in control_mappings.items():
                        if mapped_name == name:
                            controls[hex_id] = value
                            break
                    else:
                        # Si aucun ID n'est trouvé, utiliser le nom comme clé
                        controls[name] = value
            
            # Ajouter le mappage pour référence
            controls["_mappings"] = control_mappings
            
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