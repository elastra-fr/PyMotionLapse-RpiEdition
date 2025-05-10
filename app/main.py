from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.routes import pages, capture


app = FastAPI()

app.include_router(pages.router, tags=["pages"])

app.include_router(capture.router, prefix="/api/capture", tags=["capture"])


