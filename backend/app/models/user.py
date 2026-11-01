"""User model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship(
        "Resume", back_populates="user", cascade="all, delete-orphan"
    )
    interviews = relationship(
        "Interview", back_populates="user", cascade="all, delete-orphan"
    )
