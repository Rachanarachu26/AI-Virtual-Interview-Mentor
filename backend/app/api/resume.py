"""Resume endpoints: upload (PDF) & fetch."""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeOut
from app.services import resume_service

logger = logging.getLogger("resume_api")

router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ---- Validate file type ----
    # Accept common resume formats: PDF, Word, and plain/rich text.
    filename = (file.filename or "").lower()
    allowed_ext = (".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt")
    if not filename.endswith(allowed_ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload a PDF, Word (.doc/.docx) or text (.txt/.rtf) resume.",
        )

    contents = await file.read()

    # ---- Validate size ----
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max {settings.MAX_UPLOAD_MB} MB.",
        )

    # ---- Parse ----
    try:
        parsed = resume_service.parse_resume(contents, filename=file.filename or "")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as exc:
        logger.error("Resume parsing failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not read this file. Please try a different resume.",
        )

    resume = Resume(
        user_id=current_user.id,
        file_name=file.filename,
        raw_text=parsed.get("raw_text"),
        name=parsed.get("name"),
        email=parsed.get("email"),
        education=parsed.get("education"),
        skills=parsed.get("skills"),
        programming_languages=parsed.get("programming_languages"),
        frameworks=parsed.get("frameworks"),
        technologies=parsed.get("technologies"),
        projects=parsed.get("projects"),
        internships=parsed.get("internships"),
        certifications=parsed.get("certifications"),
        experience=parsed.get("experience"),
        summary=parsed.get("summary"),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/latest", response_model=ResumeOut)
def latest_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")
    return resume


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume
