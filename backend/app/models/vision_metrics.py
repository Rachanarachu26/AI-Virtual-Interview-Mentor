"""Non-verbal / computer-vision metrics derived from MediaPipe landmarks."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database.database import Base


class VisionMetric(Base):
    __tablename__ = "vision_metrics"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False, index=True)

    available = Column(Boolean, default=True)
    eye_contact_percentage = Column(Float, default=0.0)  # 0-100
    posture_score = Column(Float, default=0.0)  # 0-100
    head_movement_score = Column(Float, default=0.0)  # 0-100 (stability)
    gesture_score = Column(Float, default=0.0)  # 0-100
    frames_analyzed = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    answer = relationship("Answer", back_populates="vision_metric")
