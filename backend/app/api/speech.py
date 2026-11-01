"""Speech endpoint: transcribe audio (Whisper) and return communication metrics."""
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services import speech_service

logger = logging.getLogger("speech_api")

router = APIRouter(prefix="/api/speech", tags=["speech"])


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    # Browser live-recognition transcript, used as a fallback if Whisper can't
    # decode the audio. Ensures a real spoken answer is never scored as empty.
    fallback_transcript: str = Form(""),
    # Recording length (seconds) measured client-side, used for WPM when the
    # fallback transcript is used (no audio segments to measure from).
    duration_seconds: float = Form(0.0),
    current_user: User = Depends(get_current_user),
):
    contents = await file.read()
    if not contents and not fallback_transcript.strip():
        raise HTTPException(status_code=400, detail="Empty audio file.")

    try:
        metrics = speech_service.transcribe_audio(
            contents,
            filename=file.filename or "audio.webm",
            fallback_transcript=fallback_transcript,
            duration_hint=duration_seconds,
        )
    except Exception as exc:
        logger.error("Transcription failed: %s", exc)
        # Never break the interview: fall back to the browser transcript if any.
        fb = (fallback_transcript or "").strip()
        metrics = speech_service.compute_metrics(fb, duration_seconds or 0.0)
        metrics["transcript"] = fb
        metrics["transcript_source"] = "browser" if fb else "none"
        if not fb:
            metrics["error"] = "Transcription temporarily unavailable."

    return metrics
