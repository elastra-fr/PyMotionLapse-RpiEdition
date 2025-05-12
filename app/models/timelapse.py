from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TimelapseProject(BaseModel):
    """Modèle représentant un projet de time-lapse."""
    id: str = Field(..., description="Identifiant unique du projet")
    name: str = Field(..., description="Nom du projet")
    duration_minutes: int = Field(..., description="Durée totale en minutes")
    interval_seconds: int = Field(..., description="Intervalle entre captures en secondes")
    fps: int = Field(30, description="Images par seconde pour la vidéo finale")
    rotation: int = Field(0, description="Rotation de la caméra en degrés (0, 90, 180, 270)")
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    captures_count: int = Field(0, description="Nombre de captures déjà effectuées")
    
    @property
    def total_captures(self) -> int:
        """Calcule le nombre total de captures basé sur la durée et l'intervalle."""
        return (self.duration_minutes * 60) // self.interval_seconds
    
    @property
    def video_duration_seconds(self) -> float:
        """Calcule la durée estimée de la vidéo finale en secondes."""
        return self.total_captures / self.fps
    
    @property
    def completion_percentage(self) -> float:
        """Calcule le pourcentage d'achèvement du projet."""
        if self.total_captures == 0:
            return 0
        return min(100, (self.captures_count / self.total_captures) * 100)