"""Vision endpoint: analyze captured webcam frames (MediaPipe + OpenCV)."""
import base64
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services import vision_service

logger = logging.getLogger("vision_api")

router = APIRouter(prefix="/api/vision", tags=["vision"])


class VisionRequest(BaseModel):
    # List of base64-encoded image frames (data URLs or raw base64).
    frames: List[str] = []


def _decode_data_url(s: str) -> Optional[bytes]:
    try:
        if "," in s and s.strip().startswith("data:"):
            s = s.split(",", 1)[1]
        return base64.b64decode(s)
    except Exception:
        return None


@router.post("/analyze")
def analyze(
    payload: VisionRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze webcam frames. Always returns a metrics object.

    If computer vision fails for any reason, `available` is False and the
    interview continues normally (vision metrics simply marked unavailable).
    """
    frames_bytes: List[bytes] = []
    for f in payload.frames:
        decoded = _decode_data_url(f)
        if decoded:
            frames_bytes.append(decoded)

    try:
        metrics = vision_service.analyze_frames(frames_bytes)
    except Exception as exc:
        logger.error("Vision analysis failed: %s", exc)
        metrics = {
            "available": False,
            "eye_contact_percentage": 0.0,
            "posture_score": 0.0,
            "head_movement_score": 0.0,
            "gesture_score": 0.0,
            "frames_analyzed": 0,
        }
    return metrics
