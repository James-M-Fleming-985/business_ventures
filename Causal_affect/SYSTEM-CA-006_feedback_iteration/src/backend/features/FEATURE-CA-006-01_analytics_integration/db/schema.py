"""SQLAlchemy models for analytics events."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AnalyticsEventDB(Base):
    """Analytics event database model."""
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    event_name = Column(String(255), nullable=False, index=True)
    event_params = Column(JSON, nullable=True)
    user_properties = Column(JSON, nullable=True)
    provider = Column(String(50), nullable=False, default="both")
    session_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    sent_to_ga = Column(Boolean, default=False, nullable=False)
    sent_to_mixpanel = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AnalyticsEvent(id={self.id}, user_id={self.user_id}, event_name={self.event_name})>"
