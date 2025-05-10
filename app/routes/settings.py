from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from app.services.capture.get_camera_params_service import CameraParamsService

router = APIRouter()

@router.get("/params")
async def get_camera_params():
    """Récupère les paramètres actuels de la caméra."""
    try:
        params_service = CameraParamsService()
        return params_service.get_current_params()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))