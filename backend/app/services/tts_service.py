"""Text-to-Speech service (modular provider).

The DEFAULT provider is the browser's Web Speech API (window.speechSynthesis),
which runs entirely in the React frontend and requires no paid API. This backend
service therefore simply prepares/normalises the text and returns speech
directives (rate, pitch, volume) that the frontend applies to a
SpeechSynthesisUtterance.

The design is modular so a cloud TTS provider (e.g. returning audio bytes) can be
added later behind the same interface without changing the API contract.
"""
from __future__ import annotations

import re
from typing import Dict

# Configurable default voice directives for the browser TTS.
DEFAULT_DIRECTIVES = {
    "rate": 0.95,
    "pitch": 1.0,
    "volume": 1.0,
    "provider": "browser",
}


def prepare_speech(text: str) -> Dict:
    """Return the text and directives the frontend should speak.

    Cleans markdown/JSON artefacts so the interviewer voice sounds natural.
    """
    clean = _normalise(text)
    return {
        "text": clean,
        **DEFAULT_DIRECTIVES,
    }


def _normalise(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    # Remove code fences / stray braces that occasionally leak from the model.
    t = re.sub(r"```[a-zA-Z]*", "", t)
    t = t.replace("```", "")
    t = t.strip().strip('"').strip()
    # Collapse whitespace.
    t = re.sub(r"\s+", " ", t)
    return t
