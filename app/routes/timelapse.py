from fastapi import APIRouter, HTTPException, Response, Request, Form, Query
from fastapi.responses import FileResponse, HTMLResponse
from typing import List, Optional, Dict
import os
import logging

from app.models.timelapse import TimelapseProject
from app.services.timelapse.project_service import TimelapseProjectService
from app.services.timelapse.capture_service import TimelapseCapture
from app.services.timelapse.auto_capture_service import TimelapseAutoCaptureService
from app.templates import templates

router = APIRouter()
logger = logging.getLogger(__name__)

project_service = TimelapseProjectService()
capture_service = TimelapseCapture()
auto_capture_service = TimelapseAutoCaptureService()

# Route pour afficher la page time-lapse
@router.get("/timelapse", response_class=HTMLResponse)
async def timelapse_page(request: Request):
    """Affiche la page de time-lapse."""
    return templates.TemplateResponse(
        "timelapse.html", 
        {"request": request, "title": "Time-lapse"}
    )

# Routes de l'API REST pour les projets time-lapse
@router.get("/api/timelapse/projects", response_model=List[TimelapseProject])
async def get_all_projects():
    """Récupère tous les projets time-lapse."""
    try:
        projects = project_service.get_all_projects()
        return projects
    except Exception as e:
        logger.exception("Erreur lors de la récupération des projets")
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
        logger.exception(f"Erreur lors de la récupération du projet {project_id}")
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
        logger.exception("Erreur lors de la création du projet")
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
        if auto_capture_service.get_capture_status(project_id):
            raise HTTPException(
                status_code=400, 
                detail="Impossible de modifier le projet pendant une capture automatique active."
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
        logger.exception(f"Erreur lors de la mise à jour du projet {project_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/timelapse/projects/{project_id}", response_model=dict)
async def delete_project(project_id: str):
    """Supprime un projet time-lapse."""
    try:
        # Vérifier si une capture auto est en cours
        if auto_capture_service.get_capture_status(project_id):
            # Arrêter la capture automatique
            auto_capture_service.stop_capture(project_id)
        
        success = project_service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Projet {project_id} introuvable")
        return {"status": "success", "message": f"Projet {project_id} supprimé"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors de la suppression du projet {project_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/timelapse/projects/{project_id}/capture", response_model=dict)
async def capture_for_project(project_id: str):
    """Effectue une capture manuelle pour un projet time-lapse."""
    try:
        # Vérifier si une capture auto est en cours
        if auto_capture_service.get_capture_status(project_id):
            raise HTTPException(
                status_code=400, 
                detail="Impossible de faire une capture manuelle pendant une capture automatique active."
            )
            
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
        logger.exception(f"Erreur lors de la capture pour le projet {project_id}")
        raise HTTPException(status_code=500, detail=str(e))

# ROUTES POUR LA CAPTURE AUTOMATIQUE
@router.post("/api/timelapse/projects/{project_id}/auto-capture/start", response_model=dict)
async def start_auto_capture(project_id: str):
    """Démarre la capture automatique pour un projet."""
    try:
        success = auto_capture_service.start_capture(project_id)
        if not success:
            raise HTTPException(status_code=400, detail="Impossible de démarrer la capture automatique")
        
        return {
            "status": "success",
            "message": f"Capture automatique démarrée pour le projet {project_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors du démarrage de la capture auto pour le projet {project_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/timelapse/projects/{project_id}/auto-capture/stop", response_model=dict)
async def stop_auto_capture(project_id: str):
    """Arrête la capture automatique pour un projet."""
    try:
        success = auto_capture_service.stop_capture(project_id)
        if not success:
            raise HTTPException(status_code=400, detail="Aucune capture automatique en cours")
        
        return {
            "status": "success",
            "message": f"Capture automatique arrêtée pour le projet {project_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors de l'arrêt de la capture auto pour le projet {project_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/timelapse/projects/{project_id}/auto-capture/status", response_model=dict)
async def get_auto_capture_status(project_id: str):
    """Récupère l'état de la capture automatique pour un projet."""
    try:
        status = auto_capture_service.get_capture_status(project_id)
        
        # Si aucune capture active, retourne un état par défaut
        if not status:
            project = project_service.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail=f"Projet {project_id} introuvable")
                
            return {
                "active": False,
                "project_id": project_id,
                "project": project.dict()
            }
        
        # Sinon, retourne l'état actif
        return {
            "active": True,
            "project_id": project_id,
            "started_at": status["started_at"].isoformat(),
            "seconds_to_next": status["seconds_to_next"],
            "project": status["project"].dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors de la récupération du statut pour le projet {project_id}")
        raise HTTPException(status_code=500, detail=str(e))