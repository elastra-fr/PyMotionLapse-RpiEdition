import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from app.models.timelapse import TimelapseProject

class TimelapseProjectService:
    def __init__(self, base_dir: str = "captures"):
        self.base_dir = base_dir
        self.projects_dir = os.path.join(base_dir, "projects")
        self.logger = logging.getLogger(__name__)
        
        # Créer les répertoires nécessaires
        Path(self.projects_dir).mkdir(parents=True, exist_ok=True)
        
    def get_project_file_path(self, project_id: str) -> str:
        """Retourne le chemin du fichier JSON pour un projet."""
        return os.path.join(self.projects_dir, f"{project_id}.json")
    
    def get_project_captures_dir(self, project_id: str) -> str:
        """Retourne le répertoire des captures pour un projet."""
        project_dir = os.path.join(self.base_dir, project_id)
        Path(project_dir).mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def create_project(self, name: str, duration_minutes: int, interval_seconds: int, 
                      fps: int = 30, rotation: int = 0) -> TimelapseProject:
        """Crée un nouveau projet time-lapse."""
        # Générer un ID unique
        now = datetime.now()
        project_id = f"timelapse-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        
        # Créer le projet
        project = TimelapseProject(
            id=project_id,
            name=name,
            duration_minutes=duration_minutes,
            interval_seconds=interval_seconds,
            fps=fps,
            rotation=rotation,
            created_at=now,
            last_modified=now,
            captures_count=0
        )
        
        # Sauvegarder le projet
        self._save_project(project)
        
        return project
    
    def get_all_projects(self) -> List[TimelapseProject]:
        """Récupère tous les projets time-lapse."""
        projects = []
        
        if not os.path.exists(self.projects_dir):
            return projects
            
        for filename in os.listdir(self.projects_dir):
            if filename.endswith('.json'):
                try:
                    project_id = filename[:-5]  # Enlever l'extension .json
                    project = self.get_project(project_id)
                    if project:
                        projects.append(project)
                except Exception as e:
                    self.logger.error(f"Erreur lors du chargement du projet {filename}: {str(e)}")
        
        # Trier par date de modification descendante
        return sorted(projects, key=lambda p: p.last_modified, reverse=True)
    
    def get_project(self, project_id: str) -> Optional[TimelapseProject]:
        """Récupère un projet time-lapse par son ID."""
        file_path = self.get_project_file_path(project_id)
        
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Convertir les timestamps en datetime
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if 'last_modified' in data:
                data['last_modified'] = datetime.fromisoformat(data['last_modified'])
                
            return TimelapseProject(**data)
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du projet {project_id}: {str(e)}")
            return None
    
    def update_project(self, project: TimelapseProject) -> TimelapseProject:
        """Met à jour un projet existant."""
        # Vérifier si le projet existe déjà
        existing_project = self.get_project(project.id)
        if not existing_project:
            raise ValueError(f"Le projet {project.id} n'existe pas")
        
        # Mettre à jour la date de modification
        project.last_modified = datetime.now()
        
        # Sauvegarder le projet
        self._save_project(project)
        
        return project
    
    def delete_project(self, project_id: str) -> bool:
        """Supprime un projet time-lapse."""
        file_path = self.get_project_file_path(project_id)
        
        if not os.path.exists(file_path):
            return False
            
        try:
            # Supprimer le fichier JSON
            os.remove(file_path)
            
            # Supprimer le répertoire des captures (optionnel)
            captures_dir = self.get_project_captures_dir(project_id)
            if os.path.exists(captures_dir):
                import shutil
                shutil.rmtree(captures_dir)
                
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du projet {project_id}: {str(e)}")
            return False
    
    def _save_project(self, project: TimelapseProject) -> None:
        """Sauvegarde un projet au format JSON."""
        file_path = self.get_project_file_path(project.id)
        
        try:
            # Convertir le modèle en dictionnaire
            data = project.dict()
            
            # Convertir les datetime en strings pour la sérialisation JSON
            if 'created_at' in data:
                data['created_at'] = data['created_at'].isoformat()
            if 'last_modified' in data:
                data['last_modified'] = data['last_modified'].isoformat()
            
            # Sauvegarder au format JSON
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du projet {project.id}: {str(e)}")
            raise