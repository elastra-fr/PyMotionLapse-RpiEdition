from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.routes import pages, capture


app = FastAPI()

#Monter le répertoire statique pour servir les fichiers CSS, JS, etc.
app.mount("/static", StaticFiles(directory="app/static"), name="static")

#Routeur vers les pages
app.include_router(pages.router, tags=["pages"])

#Routeur vers l'API de capture
app.include_router(capture.router, prefix="/api/capture", tags=["capture"])
#Routeur vers l'API de paramètres
app.include_router(capture.router, prefix="/api/settings", tags=["settings"])


