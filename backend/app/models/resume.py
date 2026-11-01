"""Resume model. Structured fields are stored as JSON for flexibility."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.database.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=True)

    # Structured fields extracted from the resume.
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    education = Column(JSON, nullable=True)
    skills = Column(JSON, nullable=True)
    programming_languages = Column(JSON, nullable=True)
    frameworks = Column(JSON, nullable=True)
    technologies = Column(JSON, nullable=True)
    projects = Column(JSON, nullable=True)
    internships = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    experience = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    interviews = relationship("Interview", back_populates="resume")
