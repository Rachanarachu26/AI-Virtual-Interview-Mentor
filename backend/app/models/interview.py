"""Interview session model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)

    category = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False)
    total_questions = Column(Integer, default=5)

    # pending | in_progress | completed
    status = Column(String(20), default="in_progress")
    overall_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="interviews")
    resume = relationship("Resume", back_populates="interviews")

    questions = relationship(
        "Question", back_populates="interview", cascade="all, delete-orphan"
    )
    answers = relationship(
        "Answer", back_populates="interview", cascade="all, delete-orphan"
    )
    evaluations = relationship(
        "Evaluation", back_populates="interview", cascade="all, delete-orphan"
    )
    feedback = relationship(
        "Feedback",
        back_populates="interview",
        cascade="all, delete-orphan",
        uselist=False,
    )
