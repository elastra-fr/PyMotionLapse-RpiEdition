from pydantic import BaseModel, Field

class ResolutionSettings(BaseModel):
    """Modèle pour les paramètres de résolution de la caméra."""
    width: int = Field(..., description="Largeur en pixels", gt=0)
    height: int = Field(..., description="Hauteur en pixels", gt=0)
    fps: int = Field(30, description="Images par seconde", ge=5, le=30)
    format: str = Field("MJPG", description="Format d'image (par exemple: MJPG, YUYV)")
    
    class Config:
        schema_extra = {
            "example": {
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "format": "MJPG"
            }
        }