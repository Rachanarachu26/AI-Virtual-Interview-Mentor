"""Speech-to-text (Whisper) and communication-metric calculation.

Whisper is responsible ONLY for transcription. The communication metrics
(WPM, filler words, etc.) are derived here from the transcript and audio
duration; Whisper is not the performance evaluator.
"""
from __future__ import annotations

import logging
import os
import tempfile
from typing import Dict, List

logger = logging.getLogger("speech_service")

FILLER_WORDS = [
    "um", "uh", "erm", "hmm", "like", "you know", "actually",
    "basically", "literally", "sort of", "kind of", "i mean", "so yeah",
]

_whisper_model = None
_whisper_failed = False


def _get_model():
    """Lazy-load the Whisper model once."""
    global _whisper_model, _whisper_failed
    if _whisper_model is not None:
        return _whisper_model
    if _whisper_failed:
        return None
    try:
        import whisper  # imported lazily
        from app.core.config import settings

        logger.info("Loading Whisper model: %s", settings.WHISPER_MODEL)
        _whisper_model = whisper.load_model(settings.WHISPER_MODEL)
        return _whisper_model
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.error("Failed to load Whisper model: %s", exc)
        _whisper_failed = True
        return None


def transcribe_audio(
    file_bytes: bytes,
    filename: str = "audio.webm",
    fallback_transcript: str = "",
    duration_hint: float = 0.0,
) -> Dict:
    """Transcribe audio bytes to text and compute speech metrics.

    Whisper is the primary transcriber. If Whisper is unavailable or cannot
    decode the browser's audio (returns empty), we fall back to the browser's
    own live speech-recognition transcript (`fallback_transcript`) so the
    candidate's verbal score is never wrongly zero when they actually spoke.
    Never raises.
    """
    suffix = os.path.splitext(filename)[1] or ".webm"
    tmp_path = None
    transcript = ""
    duration = 0.0
    source = "none"

    model = _get_model()
    if model is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            result = model.transcribe(tmp_path, fp16=False)
            transcript = (result.get("text") or "").strip()
            segments = result.get("segments") or []
            if segments:
                duration = float(segments[-1].get("end", 0.0))
            if transcript:
                source = "whisper"
        except Exception as exc:
            logger.error("Whisper transcription failed: %s", exc)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    # Fallback: use the browser transcript when Whisper produced nothing usable.
    fallback_transcript = (fallback_transcript or "").strip()
    if not transcript and fallback_transcript:
        transcript = fallback_transcript
        source = "browser"

    # Prefer measured audio duration; else use the recording-time hint from the client.
    if (not duration or duration <= 0) and duration_hint and duration_hint > 0:
        duration = float(duration_hint)

    logger.info(
        "Transcription source=%s | words=%s | duration=%.1fs",
        source, len(transcript.split()), duration or 0.0,
    )

    metrics = compute_metrics(transcript, duration)
    metrics["transcript"] = transcript
    metrics["transcript_source"] = source
    return metrics


def compute_metrics(transcript: str, duration_seconds: float) -> Dict:
    """Derive communication metrics from a transcript and its duration."""
    text = (transcript or "").strip()
    words = text.split()
    word_count = len(words)
    lower = text.lower()

    # Filler words (count multi-word phrases too).
    filler_detail: Dict[str, int] = {}
    filler_total = 0
    for fw in FILLER_WORDS:
        count = lower.count(fw)
        if count:
            filler_detail[fw] = count
            filler_total += count

    # Speaking duration: prefer measured audio duration, else estimate.
    if duration_seconds and duration_seconds > 0:
        duration = round(duration_seconds, 2)
    else:
        # Assume ~2.5 words/second as a rough estimate when duration is unknown.
        duration = round(word_count / 2.5, 2) if word_count else 0.0

    wpm = round((word_count / duration) * 60, 1) if duration > 0 else 0.0
    filler_freq = round((filler_total / word_count) * 100, 1) if word_count else 0.0
    # Pause estimate: sentence-ending punctuation is a proxy for natural pauses.
    pause_count = lower.count(".") + lower.count("?") + lower.count("!")

    communication_score = _communication_score(wpm, filler_freq, word_count)

    return {
        "transcript": text,
        "word_count": word_count,
        "speaking_duration": duration,
        "words_per_minute": wpm,
        "filler_word_count": filler_total,
        "filler_word_frequency": filler_freq,
        "filler_words_detail": filler_detail,
        "pause_count": pause_count,
        "answer_length": len(text),
        "communication_score": communication_score,
    }


def _communication_score(wpm: float, filler_freq: float, word_count: int) -> float:
    """Blend pace, filler usage and length into a 0-100 communication score."""
    if word_count == 0:
        return 0.0

    # Pace: ideal 110-160 WPM. Penalise deviation gently.
    if 110 <= wpm <= 160:
        pace = 100.0
    elif wpm == 0:
        pace = 0.0
    else:
        target = 135.0
        pace = max(0.0, 100.0 - abs(wpm - target) * 0.8)

    # Fillers: forgive a few, penalise heavy use. freq is per-100-words.
    filler = max(0.0, 100.0 - max(0.0, filler_freq - 3.0) * 6.0)

    # Length: reward substantive answers up to a point.
    if word_count >= 60:
        length = 100.0
    elif word_count >= 30:
        length = 80.0
    elif word_count >= 15:
        length = 60.0
    else:
        length = 40.0

    score = pace * 0.4 + filler * 0.35 + length * 0.25
    return round(max(0.0, min(100.0, score)), 1)
