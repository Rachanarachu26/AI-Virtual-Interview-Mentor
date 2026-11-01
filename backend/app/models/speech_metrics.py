"""Speech / communication metrics derived from Whisper transcription."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship

from app.database.database import Base


class SpeechMetric(Base):
    __tablename__ = "speech_metrics"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False, index=True)

    word_count = Column(Integer, default=0)
    speaking_duration = Column(Float, default=0.0)  # seconds
    words_per_minute = Column(Float, default=0.0)
    filler_word_count = Column(Integer, default=0)
    filler_word_frequency = Column(Float, default=0.0)  # fillers per 100 words
    filler_words_detail = Column(JSON, nullable=True)
    pause_count = Column(Integer, default=0)
    answer_length = Column(Integer, default=0)  # characters
    communication_score = Column(Float, default=0.0)  # 0-100

    created_at = Column(DateTime, default=datetime.utcnow)

    answer = relationship("Answer", back_populates="speech_metric")
