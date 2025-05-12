import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

# Configurer le logging
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Handler pour le fichier
    file_handler = RotatingFileHandler(
        log_dir / "pymotionlapse.log", 
        maxBytes=10485760,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Ajouter les handlers au logger racine
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# Initialiser les services essentiels
def init_services():
    from app.services.timelapse.auto_capture_service import TimelapseAutoCaptureService
    # Le service est instancié lors de l'import mais nous pouvons aussi
    # le faire explicitement si nécessaire
    return {
        "auto_capture_service": TimelapseAutoCaptureService()
    }

# Créer les répertoires nécessaires
def create_required_directories():
    dirs = [
        Path("data"),
        Path("data/projects"),
        Path("logs")
    ]
    
    for directory in dirs:
        directory.mkdir(exist_ok=True)

# Fonction principale d'initialisation de l'application
def init_app():
    setup_logging()
    create_required_directories()
    services = init_services()
    
    # Loguer l'initialisation
    logging.getLogger(__name__).info("Application PyMotionLapse initialisée")
    
    return services

# Initialiser l'application lors de l'import
app_services = init_app()