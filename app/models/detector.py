"""
Deepfake Detector using EfficientNet-B4.

Two modes:
  1. Demo mode  – loads ImageNet-pretrained weights (no external file needed).
     The classifier head is randomly initialised, so results are NOT meaningful,
     but the pipeline runs end-to-end for testing purposes.
  2. Custom mode – loads a fine-tuned .pth checkpoint from app/models/weights/.
     Replace WEIGHTS_PATH with the real file and set DEMO_MODE = False.

To obtain real weights:
  - FaceForensics++: https://github.com/ondyari/FaceForensics
  - Kaggle Deepfake Detection Challenge winning models
  Download the .pth file to app/models/weights/detector.pth
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
WEIGHTS_PATH = BASE_DIR / "weights" / "detector.pth"
DEMO_MODE = not WEIGHTS_PATH.exists()          # auto-detect

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ImageNet normalisation (same statistics used during EfficientNet pre-training)
_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


# ---------------------------------------------------------------------------
# Model definition
# ---------------------------------------------------------------------------
def _build_model() -> nn.Module:
    """Build EfficientNet-B4 with a binary classification head."""
    # Use weights=DEFAULT for the backbone, then replace the classifier
    model = models.efficientnet_b4(weights=models.EfficientNet_B4_Weights.DEFAULT)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.4, inplace=True),
        nn.Linear(in_features, 1),   # single logit → sigmoid → P(fake)
    )
    return model


# ---------------------------------------------------------------------------
# Singleton loader
# ---------------------------------------------------------------------------
_model: Optional[nn.Module] = None


def get_model() -> nn.Module:
    """Return the cached model, loading it on first call."""
    global _model
    if _model is not None:
        return _model

    model = _build_model()

    if DEMO_MODE:
        logger.warning(
            "DEMO MODE: no weights found at %s. "
            "Predictions are RANDOM – for pipeline testing only.",
            WEIGHTS_PATH,
        )
    else:
        logger.info("Loading weights from %s onto %s", WEIGHTS_PATH, DEVICE)
        state = torch.load(str(WEIGHTS_PATH), map_location=DEVICE)
        # Support both raw state_dict and {'model': state_dict} checkpoints
        if isinstance(state, dict) and "model" in state:
            state = state["model"]
        model.load_state_dict(state, strict=False)
        logger.info("Weights loaded successfully.")

    model.to(DEVICE)
    model.eval()
    _model = model
    return _model


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
def predict(frames: List[Image.Image]) -> dict:
    """
    Run inference on a list of PIL Image frames.

    Parameters
    ----------
    frames : list of PIL.Image
        Video frames (typically 10 frames extracted by video_processor).

    Returns
    -------
    dict with keys:
        label       : "AI Generated" | "Real"
        confidence  : float in [0, 1]  – probability of being AI-generated
        frame_scores: list of per-frame probabilities
        demo_mode   : bool
    """
    if not frames:
        raise ValueError("No frames provided for prediction.")

    model = get_model()

    tensors = torch.stack([_TRANSFORM(f) for f in frames]).to(DEVICE)  # (N, 3, 224, 224)

    with torch.no_grad():
        logits = model(tensors).squeeze(1)          # (N,)
        probs = torch.sigmoid(logits).cpu().tolist()  # per-frame P(fake)

    avg_prob = sum(probs) / len(probs)
    label = "AI Generated" if avg_prob >= 0.5 else "Real"

    return {
        "label": label,
        "confidence": round(avg_prob, 4),
        "frame_scores": [round(p, 4) for p in probs],
        "demo_mode": DEMO_MODE,
    }
