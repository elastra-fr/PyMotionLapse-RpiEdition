from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from app.services.capture.get_camera_params_service import CameraParamsService
from app.services.capture.set_camera_params_service import CameraSettingsService
from app.models.camera import ResolutionSettings

router = APIRouter()

@router.get("/params")
async def get_camera_params():
    """Récupère les paramètres actuels de la caméra."""
    try:
        params_service = CameraParamsService()
        return params_service.get_current_params()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/resolution")
async def set_camera_resolution(settings: ResolutionSettings):
    """Modifie la résolution de la caméra."""
    try:
        settings_service = CameraSettingsService()
        success = settings_service.set_resolution(
            width=settings.width,
            height=settings.height,
            pixel_format=settings.format
        )
        
        if success:
            return {"success": True, "message": f"Résolution modifiée à {settings.width}x{settings.height}"}
        else:
            raise HTTPException(status_code=500, detail="Échec de la modification de la résolution")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))