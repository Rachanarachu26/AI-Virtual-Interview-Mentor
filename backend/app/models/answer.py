"""Candidate answer model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(
        Integer, ForeignKey("interviews.id"), nullable=False, index=True
    )
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="answers")
    question = relationship("Question", back_populates="answer")

    speech_metric = relationship(
        "SpeechMetric",
        back_populates="answer",
        cascade="all, delete-orphan",
        uselist=False,
    )
    vision_metric = relationship(
        "VisionMetric",
        back_populates="answer",
        cascade="all, delete-orphan",
        uselist=False,
    )
    evaluation = relationship(
        "Evaluation",
        back_populates="answer",
        cascade="all, delete-orphan",
        uselist=False,
    )
