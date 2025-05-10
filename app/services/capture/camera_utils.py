import os
import shutil
import subprocess



def find_v4l2_path():
    """Trouve le chemin complet de v4l2-ctl sur le système."""
    # Recherche dans le PATH
    v4l2_path = shutil.which("v4l2-ctl")
    if v4l2_path:
        return v4l2_path
        
    # Chemins courants
    common_paths = [
        "/usr/bin/v4l2-ctl",
        "/usr/local/bin/v4l2-ctl",
        "/bin/v4l2-ctl"
    ]
    
    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
            
    # Recherche plus approfondie si nécessaire
    try:
        find_result = subprocess.run(
            ["find", "/", "-name", "v4l2-ctl", "-type", "f"],
            capture_output=True, text=True, timeout=10
        )
        paths = find_result.stdout.strip().split('\n')
        for path in paths:
            if path and os.access(path, os.X_OK):
                return path
    except:
        pass
        
    return None