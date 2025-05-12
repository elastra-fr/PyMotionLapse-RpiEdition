from fastapi import APIRouter, HTTPException, Response, Request, Form, Query
from fastapi.responses import FileResponse, HTMLResponse
from typing import List, Optional, Dict
import os

from app.models.timelapse import TimelapseProject
from app.services.timelapse.project_service import TimelapseProjectService
from app.services.timelapse.capture_service import TimelapseCapture
from app.services.timelapse.auto_capture_service import TimelapseAutoCaptureService
from app.templates import templates

router = APIRouter()

project_service = TimelapseProjectService()
capture_service = TimelapseCapture()
auto_capture_service = TimelapseAutoCaptureService()

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
        
        # Vérifier si une capture auto est en cours pour ce projet
        capture_status = auto_capture_service.get_capture_status(project_id)
        if capture_status:
            raise HTTPException(
                status_code=400, 
                detail="Impossible de modifier le projet pendant une capture automatique active. Arrêtez la capture d'abord."
            )
        
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
        # Vérifier si une capture auto est en cours pour ce projet
        capture_status = auto_capture_service.get_capture_status(project_id)
        if capture_status:
            # Arrêter la capture automatique
            auto_capture_service.stop_capture(project_id)
        
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

# Nouvelles routes pour la capture automatique
@router.post("/api/timelapse/projects/{project_id}/auto-capture/start", response_model=dict)
async def start_auto_capture(project_id: str):
    """Démarre la capture automatique pour un projet."""
    try:
        # Vérifier si le projet existe
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Projet {project_id} introuvable")
        
        # Démarrer la capture automatique
        success = auto_capture_service.start_capture(project_id)
        if not success:
            raise HTTPException(status_code=500, detail="Impossible de démarrer la capture automatique")
        
        return {
            "status": "success",
            "message": f"Capture automatique démarrée pour le projet {project.name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/timelapse/projects/{project_id}/auto-capture/stop", response_model=dict)
async def stop_auto_capture(project_id: str):
    """Arrête la capture automatique pour un projet."""
    try:
        # Arrêter la capture automatique
        success = auto_capture_service.stop_capture(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Aucune capture automatique active pour le projet {project_id}")
        
        return {
            "status": "success",
            "message": f"Capture automatique arrêtée pour le projet {project_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/timelapse/projects/{project_id}/auto-capture/status", response_model=dict)
async def get_auto_capture_status(project_id: str):
    """Récupère l'état de la capture automatique pour un projet."""
    try:
        # Vérifier si le projet existe
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Projet {project_id} introuvable")
        
        # Récupérer l'état de la capture automatique
        status = auto_capture_service.get_capture_status(project_id)
        
        if not status:
            return {
                "active": False,
                "project": project.dict()
            }
        
        return {
            "active": True,
            "started_at": status["started_at"].isoformat(),
            "seconds_to_next": status["seconds_to_next"],
            "project": status["project"].dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/timelapse/auto-captures", response_model=dict)
async def get_all_auto_captures():
    """Récupère l'état de toutes les captures automatiques actives."""
    try:
        active_captures = auto_capture_service.get_all_active_captures()
        
        result = {}
        for project_id, status in active_captures.items():
            result[project_id] = {
                "active": True,
                "started_at": status["started_at"].isoformat(),
                "seconds_to_next": status["seconds_to_next"],
                "project": status["project"].dict()
            }
        
        return {"active_captures": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))