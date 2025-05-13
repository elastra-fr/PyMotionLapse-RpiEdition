import logging
import subprocess


logger = logging.getLogger(__name__)

## Fonction pour capturer une image avec v4l2-ctl
def capture_image(v4l2_path, device, output_path):
    """Capture une image avec v4l2-ctl."""
    try:
        result = subprocess.run([
            v4l2_path,
            "--device", device,
            "--set-fmt-video=width=1920,height=1080,pixelformat=MJPG",
            "--stream-mmap",
            "--stream-count=1",
            "--stream-to=" + output_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Image capturée: {output_path}")
            return True
        else:
            logger.warning(f"Erreur lors de la capture: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Exception lors de la capture: {str(e)}")
        return False