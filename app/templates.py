from fastapi.templating import Jinja2Templates
from pathlib import Path

# Définir le chemin des templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))