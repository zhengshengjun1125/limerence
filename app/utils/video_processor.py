"""
Video frame extractor using OpenCV.

Extracts NUM_FRAMES frames evenly distributed across the video duration,
converts them to RGB PIL Images ready for the detector.
"""

import logging
from pathlib import Path
from typing import List, Union

import cv2
from PIL import Image

logger = logging.getLogger(__name__)

SAMPLE_INTERVAL_SEC = 1   # extract one frame every N seconds
MAX_FRAMES = 60           # hard upper limit to control memory / inference time
MIN_FRAMES = 1            # minimum acceptable frames


def extract_frames(
    video_path: Union[str, Path],
    interval_sec: float = SAMPLE_INTERVAL_SEC,
    max_frames: int = MAX_FRAMES,
) -> List[Image.Image]:
    """
    Extract frames from a video at a fixed time interval.

    One frame is sampled every `interval_sec` seconds, up to `max_frames`
    total.  For very short clips (< interval_sec) at least one frame is
    always returned.

    Parameters
    ----------
    video_path : str or Path
        Absolute path to the video file.
    interval_sec : float
        Seconds between sampled frames (default 1 s).
    max_frames : int
        Hard upper limit on the number of frames returned (default 60).

    Returns
    -------
    List of PIL Images (RGB).

    Raises
    ------
    ValueError  – if the file cannot be opened or yields no frames.
    """
    path = str(video_path)
    cap = cv2.VideoCapture(path)

    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0   # fallback to 25 fps if unknown
    duration = total_frames / fps

    logger.info(
        "Video: %s | total_frames=%d | fps=%.2f | duration=%.2fs",
        path, total_frames, fps, duration,
    )

    if total_frames < MIN_FRAMES:
        cap.release()
        raise ValueError(f"Video has too few frames: {total_frames}")

    # Build list of frame indices: one every `interval_sec` seconds
    frame_step = max(int(round(fps * interval_sec)), 1)
    indices = list(range(0, total_frames, frame_step))

    # Enforce upper limit (trim from the end to keep temporal coverage)
    if len(indices) > max_frames:
        # Keep evenly distributed subset within the already-spaced indices
        step = len(indices) / max_frames
        indices = [indices[int(i * step)] for i in range(max_frames)]

    # Always include at least one frame
    if not indices:
        indices = [0]

    logger.info(
        "Sampling %d frames (every %.1fs, max %d) from %.2fs video",
        len(indices), interval_sec, max_frames, duration,
    )

    frames: List[Image.Image] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            logger.warning("Failed to read frame at index %d, skipping.", idx)
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(rgb))

    cap.release()

    if not frames:
        raise ValueError("Could not extract any frames from the video.")

    logger.info("Extracted %d frames.", len(frames))
    return frames
