from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class EngagementSession(Base):
    """User engagement session tracking"""
    __tablename__ = "engagement_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(String(128), nullable=False, unique=True, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    duration_seconds = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    page_views = Column(Integer, default=0)
    interactions = Column(Integer, default=0)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    events = relationship("EngagementEvent", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_session_user_active", "user_id", "is_active"),
        Index("idx_session_dates", "started_at", "ended_at"),
    )


class EngagementEvent(Base):
    """Individual engagement events"""
    __tablename__ = "engagement_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(128), ForeignKey("engagement_sessions.session_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_name = Column(String(100), nullable=False)
    event_category = Column(String(50), nullable=True)
    event_value = Column(String(255), nullable=True)
    numeric_value = Column(Float, nullable=True)
    page_url = Column(String(500), nullable=True)
    element_id = Column(String(100), nullable=True)
    element_class = Column(String(200), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    metadata = Column(String, nullable=True)  # JSON string for additional data
    
    # Relationships
    session = relationship("EngagementSession", back_populates="events")
    
    __table_args__ = (
        Index("idx_event_session_time", "session_id", "timestamp"),
        Index("idx_event_type_time", "event_type", "timestamp"),
        Index("idx_event_user_time", "user_id", "timestamp"),
    )


class EngagementMetrics(Base):
    """Aggregated engagement metrics"""
    __tablename__ = "engagement_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    metric_date = Column(DateTime, nullable=False)
    metric_type = Column(String(50), nullable=False)  # daily, weekly, monthly
    total_sessions = Column(Integer, default=0)
    total_duration_seconds = Column(Integer, default=0)
    avg_session_duration = Column(Float, default=0.0)
    total_page_views = Column(Integer, default=0)
    total_interactions = Column(Integer, default=0)
    unique_pages_visited = Column(Integer, default=0)
    bounce_rate = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    most_visited_page = Column(String(500), nullable=True)
    peak_hour = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("user_id", "metric_date", "metric_type", name="uq_user_date_type"),
        Index("idx_metrics_user_date", "user_id", "metric_date"),
        Index("idx_metrics_type_date", "metric_type", "metric_date"),
    )


class PageEngagement(Base):
    """Page-level engagement tracking"""
    __tablename__ = "page_engagement"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_url = Column(String(500), nullable=False)
    page_title = Column(String(200), nullable=True)
    date = Column(DateTime, nullable=False)
    total_views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    avg_time_on_page = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)
    exit_rate = Column(Float, default=0.0)
    total_interactions = Column(Integer, default=0)
    scroll_depth_avg = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("page_url", "date", name="uq_page_date"),
        Index("idx_page_date", "page_url", "date"),
    )