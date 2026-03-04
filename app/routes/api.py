"""
API routes for the Deepfake Detector.

Endpoints
---------
GET  /         – serve the main HTML page (handled by main.py)
POST /detect   – upload a video, run inference, return JSON result
GET  /health   – simple liveness check
"""

import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.models.detector import predict
from app.utils.video_processor import extract_frames

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 100 * 1024 * 1024   # 100 MB in bytes
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _check_extension(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. "
                   f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )


async def _save_upload(file: UploadFile) -> Path:
    """Stream the uploaded file to disk, enforcing the size limit."""
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    tmp_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"

    size = 0
    try:
        with open(tmp_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1 MB chunks
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum allowed size is "
                               f"{MAX_FILE_SIZE // (1024 * 1024)} MB.",
                    )
                f.write(chunk)
    except HTTPException:
        tmp_path.unlink(missing_ok=True)
        raise

    return tmp_path


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post("/detect")
async def detect_video(file: UploadFile = File(...)):
    """
    Upload a video file and get a deepfake detection result.

    Returns
    -------
    JSON:
      label        : "AI Generated" | "Real"
      confidence   : float  (0–1, probability of being AI-generated)
      frame_scores : list[float]
      demo_mode    : bool  (True when no fine-tuned weights are loaded)
      filename     : str
    """
    # 1. Validate extension
    _check_extension(file.filename or "")

    # 2. Save to disk
    tmp_path: Optional[Path] = None
    try:
        tmp_path = await _save_upload(file)
        logger.info("Saved upload: %s (%.2f MB)", tmp_path, tmp_path.stat().st_size / 1e6)

        # 3. Extract frames (run blocking I/O in thread pool)
        loop = asyncio.get_event_loop()
        frames = await loop.run_in_executor(None, extract_frames, tmp_path)

        # 4. Run model inference (CPU-bound, also off-thread)
        result = await loop.run_in_executor(None, predict, frames)

        result["filename"] = file.filename
        logger.info("Result for %s: %s (conf=%.4f)", file.filename, result["label"], result["confidence"])
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Processing error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during detection")
        raise HTTPException(status_code=500, detail="Internal server error.")
    finally:
        # Always clean up the temporary file
        if tmp_path and tmp_path.exists():
            try:
                os.remove(tmp_path)
                logger.info("Removed temp file: %s", tmp_path)
            except OSError as e:
                logger.warning("Could not remove temp file %s: %s", tmp_path, e)
