from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from app.services.capture.preview_service import PreviewService
import os

router = APIRouter()

preview_service = PreviewService()

@router.get("/preview", response_class=Response)
async def get_preview():
    """Récupère un aperçu en direct de la caméra."""
    try:
        # Capturer une image avec une qualité inférieure pour la performance
        image_path = preview_service.capture_image()
        
        # Renvoyer l'image si elle existe
        if os.path.exists(image_path):
            return FileResponse(image_path, media_type="image/jpeg")
        else:
            raise HTTPException(status_code=404, detail="Impossible de générer l'aperçu")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))