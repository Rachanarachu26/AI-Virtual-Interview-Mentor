"""Resume-related Pydantic schemas."""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: int
    user_id: int
    file_name: str
    name: Optional[str] = None
    email: Optional[str] = None
    education: Optional[Any] = None
    skills: Optional[List[str]] = None
    programming_languages: Optional[List[str]] = None
    frameworks: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    projects: Optional[Any] = None
    internships: Optional[Any] = None
    certifications: Optional[Any] = None
    experience: Optional[Any] = None
    summary: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
