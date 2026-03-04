"""
FastAPI application entry point.

Start with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes.api import router as api_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Video Detector",
    description="Detect whether a video is AI-generated (Deepfake) using EfficientNet-B4.",
    version="1.0.0",
)

# Static files (CSS / JS / uploaded assets)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# API routes
app.include_router(api_router, prefix="/api")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------------------------------------------------------
# Startup event – pre-load model so first request isn't slow
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("Pre-loading detection model…")
    try:
        from app.models.detector import get_model
        get_model()
        logger.info("Model ready.")
    except Exception as e:
        logger.error("Model failed to load: %s", e)
