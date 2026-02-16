"""User model placeholder."""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
