from fastapi import APIRouter, HTTPException, Response, Request, Form, Query
from fastapi.responses import FileResponse, HTMLResponse
from typing import List, Optional
import os

from app.models.timelapse import TimelapseProject
from app.services.timelapse.project_service import TimelapseProjectService
from app.services.timelapse.capture_service import TimelapseCapture
from app.templates import templates

router = APIRouter()

project_service = TimelapseProjectService()
capture_service = TimelapseCapture()

# Routes de l'API REST pour les projets time-lapse
@router.get("/api/timelapse/projects", response_model=List[TimelapseProject])
async def get_all_projects():
    """Récupère tous les projets time-lapse."""
    try:
        projects = project_service.get_all_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/timelapse/projects/{project_id}", response_model=TimelapseProject)
async def get_project(project_id: str):
    """Récupère un projet time-lapse par son ID."""
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Projet {project_id} introuvable")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/timelapse/projects", response_model=TimelapseProject)
async def create_project(
    name: str = Form(...),
    duration_minutes: int = Form(...),
    interval_seconds: int = Form(...),
    fps: int = Form(30),
    rotation: int = Form(0)
):
    """Crée un nouveau projet time-lapse."""
    try:
        project = project_service.create_project(
            name=name,
            duration_minutes=duration_minutes,
            interval_seconds=interval_seconds,
            fps=fps,
            rotation=rotation
        )
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/timelapse/projects/{project_id}", response_model=TimelapseProject)
async def update_project(
    project_id: str,
    name: str = Form(...),
    duration_minutes: int = Form(...),
    interval_seconds: int = Form(...),
    fps: int = Form(30),
    rotation: int = Form(0)
):
    """Met à jour un projet time-lapse existant."""
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Projet {project_id} introuvable")
        
        # Mettre à jour les propriétés
        project.name = name
        project.duration_minutes = duration_minutes
        project.interval_seconds = interval_seconds
        project.fps = fps
        project.rotation = rotation
        
        # Sauvegarder les modifications
        updated_project = project_service.update_project(project)
        return updated_project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/timelapse/projects/{project_id}", response_model=dict)
async def delete_project(project_id: str):
    """Supprime un projet time-lapse."""
    try:
        success = project_service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Projet {project_id} introuvable")
        return {"status": "success", "message": f"Projet {project_id} supprimé"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/timelapse/projects/{project_id}/capture", response_model=dict)
async def capture_for_project(project_id: str):
    """Effectue une capture pour un projet time-lapse."""
    try:
        success = capture_service.capture_for_project(project_id)
        if not success:
            raise HTTPException(status_code=500, detail="Échec de la capture")
        
        # Récupérer le projet mis à jour
        project = project_service.get_project(project_id)
        
        return {
            "status": "success",
            "message": f"Capture {project.captures_count} réussie",
            "project": project.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/timelapse/projects/{project_id}/preview", response_class=Response)
async def get_project_preview(project_id: str):
    """Récupère un aperçu pour un projet time-lapse avec la rotation appliquée."""
    try:
        preview_path = capture_service.get_preview_with_rotation(project_id)
        
        if not preview_path or not os.path.exists(preview_path):
            raise HTTPException(status_code=500, detail="Échec de la génération de l'aperçu")
        
        return FileResponse(preview_path, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))