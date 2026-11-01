"""Resume parsing service.

Uses PyMuPDF to extract text from a PDF, cleans it, then structures it.
Structuring prefers Gemini; a regex/keyword heuristic is the fallback so the
feature still works without an API key.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

from app.services import gemini_service

logger = logging.getLogger("resume_service")

# Common tech keywords used by the offline heuristic extractor.
PROGRAMMING_LANGUAGES = [
    "python", "java", "javascript", "typescript", "c++", "c#", "c",
    "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
    "r", "matlab", "sql", "dart", "perl",
]
FRAMEWORKS = [
    "react", "angular", "vue", "next.js", "nextjs", "node.js", "nodejs",
    "express", "django", "flask", "fastapi", "spring", "spring boot",
    "laravel", "rails", "svelte", ".net", "tailwind", "bootstrap",
    "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy",
]
TECHNOLOGIES = [
    "docker", "kubernetes", "aws", "azure", "gcp", "mysql", "postgresql",
    "mongodb", "redis", "git", "linux", "graphql", "rest", "kafka",
    "rabbitmq", "elasticsearch", "firebase", "jenkins", "terraform",
    "mediapipe", "opencv", "whisper", "gemini",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF byte stream using PyMuPDF."""
    import fitz  # PyMuPDF, imported lazily

    text_parts: List[str] = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text("text"))
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a .docx (Office Open XML) using only the standard library.

    A .docx is a zip; the body text lives in word/document.xml as <w:t> runs
    grouped by <w:p> paragraphs.
    """
    import io
    import zipfile
    from xml.etree import ElementTree as ET

    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: List[str] = []
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
        with z.open("word/document.xml") as doc_xml:
            tree = ET.parse(doc_xml)
    for para in tree.iter(ns + "p"):
        runs = [node.text for node in para.iter(ns + "t") if node.text]
        if runs:
            paragraphs.append("".join(runs))
    return "\n".join(paragraphs)


def _strip_rtf(file_bytes: bytes) -> str:
    """Very small RTF-to-text cleaner (no external dependency)."""
    text = file_bytes.decode("latin-1", errors="ignore")
    text = re.sub(r"\\par[d]?", "\n", text)       # paragraph breaks
    text = re.sub(r"\\'[0-9a-fA-F]{2}", " ", text)  # hex-escaped chars
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)  # control words
    text = text.replace("{", "").replace("}", "")
    return text


def _decode_text(file_bytes: bytes) -> str:
    """Best-effort decode for plain-text style files."""
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return file_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return file_bytes.decode("utf-8", errors="ignore")


def extract_text(file_bytes: bytes, filename: str = "") -> str:
    """Extract raw text from a resume of any supported type.

    Dispatches by file extension: PDF (PyMuPDF), DOCX (stdlib), TXT/RTF/ODT and
    anything else via best-effort fallbacks. Never relies on a paid service.
    """
    name = (filename or "").lower()

    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    if name.endswith(".rtf"):
        return _strip_rtf(file_bytes)
    if name.endswith(".txt"):
        return _decode_text(file_bytes)

    # .doc (legacy binary), .odt, or unknown: try PDF parser (handles several
    # formats), then fall back to a tolerant text decode so we still get content.
    try:
        return extract_text_from_pdf(file_bytes)
    except Exception:
        pass
    try:
        return extract_text_from_docx(file_bytes)
    except Exception:
        pass
    return _decode_text(file_bytes)


def clean_text(text: str) -> str:
    """Normalise whitespace and strip control characters."""
    text = text.replace("\x00", " ")
    # Collapse 3+ newlines into 2, and trailing spaces.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _find_keywords(text_lower: str, keywords: List[str]) -> List[str]:
    found = []
    for kw in keywords:
        # Word-ish boundary match, tolerant of the dots in things like node.js.
        pattern = r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            found.append(kw)
    # De-duplicate while keeping order, title-casing nicely.
    seen, result = set(), []
    for kw in found:
        key = kw.lower()
        if key not in seen:
            seen.add(key)
            result.append(kw)
    return result


def _heuristic_structure(raw_text: str) -> Dict:
    """Offline fallback extractor based on keywords and simple heuristics."""
    lower = raw_text.lower()
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    # Name guess: first non-empty line that looks like a name (<=4 words, letters).
    name = None
    for line in lines[:5]:
        words = line.split()
        if 1 <= len(words) <= 4 and re.match(r"^[A-Za-z .'-]+$", line):
            name = line.title()
            break

    email_match = EMAIL_RE.search(raw_text)
    email = email_match.group(0) if email_match else None

    def section(header_keywords: List[str]) -> List[str]:
        """Grab lines under a section header until the next likely header."""
        result: List[str] = []
        capturing = False
        for line in lines:
            l = line.lower()
            if any(h in l for h in header_keywords) and len(line) < 40:
                capturing = True
                continue
            if capturing:
                # Stop at a new section-looking header.
                if len(line) < 30 and line.isupper():
                    break
                result.append(line)
                if len(result) >= 8:
                    break
        return result

    return {
        "name": name,
        "email": email,
        "summary": " ".join(lines[:3])[:400] if lines else "",
        "education": section(["education", "academic", "qualification"]),
        "skills": _find_keywords(lower, PROGRAMMING_LANGUAGES + FRAMEWORKS + TECHNOLOGIES),
        "programming_languages": _find_keywords(lower, PROGRAMMING_LANGUAGES),
        "frameworks": _find_keywords(lower, FRAMEWORKS),
        "technologies": _find_keywords(lower, TECHNOLOGIES),
        "projects": section(["project"]),
        "internships": section(["internship", "intern"]),
        "certifications": section(["certification", "certificate", "certified"]),
        "experience": section(["experience", "employment", "work history"]),
    }


def parse_resume(file_bytes: bytes, filename: str = "") -> Dict:
    """Full pipeline: extract -> clean -> structure. Returns a dict of fields.

    Accepts PDF, Word (.doc/.docx), and text (.txt/.rtf/.odt) resumes.
    Always includes a `raw_text` key.
    """
    raw = extract_text(file_bytes, filename)
    cleaned = clean_text(raw)

    if not cleaned:
        raise ValueError("The uploaded file contained no extractable text.")

    structured: Optional[Dict] = None
    try:
        structured = gemini_service.structure_resume_text(cleaned)
    except Exception as exc:  # never let AI structuring break the upload
        logger.warning("Gemini resume structuring failed: %s", exc)

    if not structured:
        structured = _heuristic_structure(cleaned)

    # Merge: fill any missing keys from the heuristic extractor.
    heuristic = _heuristic_structure(cleaned)
    for key, value in heuristic.items():
        if not structured.get(key):
            structured[key] = value

    structured["raw_text"] = cleaned
    return structured
