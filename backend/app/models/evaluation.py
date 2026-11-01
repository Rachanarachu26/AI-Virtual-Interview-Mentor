"""Per-answer evaluation combining answer quality, speech and vision."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(
        Integer, ForeignKey("interviews.id"), nullable=False, index=True
    )
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False)

    # Answer-quality sub-scores from Gemini (0-10).
    technical_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    completeness_score = Column(Float, default=0.0)
    clarity_score = Column(Float, default=0.0)

    # Normalised aggregate scores (0-100).
    answer_quality_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    eye_contact_score = Column(Float, default=0.0)
    posture_score = Column(Float, default=0.0)
    gesture_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)

    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="evaluations")
    answer = relationship("Answer", back_populates="evaluation")
