"""Interview question model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(
        Integer, ForeignKey("interviews.id"), nullable=False, index=True
    )

    order_index = Column(Integer, default=0)
    question_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    difficulty = Column(String(20), nullable=True)
    # initial | follow_up
    question_type = Column(String(20), default="initial")

    created_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="questions")
    answer = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan",
        uselist=False,
    )
