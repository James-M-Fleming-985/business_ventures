from sqlalchemy import (
    Column, String, DateTime, JSON, Index, BigInteger,
    Enum as SQLEnum, UniqueConstraint, func, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from ..models.metrics import EngagementType, ContentType

Base = declarative_base()


class EngagementEvent(Base):
    """Core engagement tracking table."""
    __tablename__ = "engagement_events"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    user_id = Column(String(255), nullable=False, index=True)
    content_id = Column(String(255), nullable=False, index=True)
    content_type = Column(
        SQLEnum(ContentType, name="content_type"),
        nullable=False,
        index=True
    )
    engagement_type = Column(
        SQLEnum(EngagementType, name="engagement_type"),
        nullable=False,
        index=True
    )
    session_id = Column(String(255), nullable=True, index=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    __table_args__ = (
        # Composite indexes for common queries
        Index(
            "idx_user_content_engagement",
            "user_id",
            "content_id",
            "engagement_type"
        ),
        Index(
            "idx_content_type_created",
            "content_id",
            "content_type",
            "created_at"
        ),
        Index(
            "idx_created_at_desc",
            created_at.desc()
        ),
        # Prevent duplicate engagements for certain types
        UniqueConstraint(
            "user_id",
            "content_id",
            "engagement_type",
            name="uq_user_content_engagement",
            postgresql_where=text(
                "engagement_type IN ('like', 'save', 'follow')"
            )
        ),
    )


class EngagementMetricsCache(Base):
    """Cached aggregated metrics for performance."""
    __tablename__ = "engagement_metrics_cache"
    
    content_id = Column(String(255), primary_key=True)
    content_type = Column(
        SQLEnum(ContentType, name="content_type"),
        nullable=False,
        index=True
    )
    total_views = Column(BigInteger, nullable=False, default=0)
    total_clicks = Column(BigInteger, nullable=False, default=0)
    total_shares = Column(BigInteger, nullable=False, default=0)
    total_comments = Column(BigInteger, nullable=False, default=0)
    total_likes = Column(BigInteger, nullable=False, default=0)
    total_saves = Column(BigInteger, nullable=False, default=0)
    unique_users = Column(BigInteger, nullable=False, default=0)
    engagement_score = Column(BigInteger, nullable=False, default=0, index=True)
    last_engagement_at = Column(DateTime(timezone=True), nullable=True)
    last_calculated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    __table_args__ = (
        Index(
            "idx_content_type_score",
            "content_type",
            "engagement_score"
        ),
        Index(
            "idx_last_engagement_desc",
            last_engagement_at.desc()
        ),
    )


class UserEngagementSummary(Base):
    """User engagement summary table."""
    __tablename__ = "user_engagement_summary"
    
    user_id = Column(String(255), primary_key=True)
    total_engagements = Column(BigInteger, nullable=False, default=0)
    engagement_breakdown = Column(JSON, nullable=False, default={})
    content_type_breakdown = Column(JSON, nullable=False, default={})
    first_engagement_at = Column(DateTime(timezone=True), nullable=True)
    last_engagement_at = Column(DateTime(timezone=True), nullable=True)
    last_calculated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    __table_args__ = (
        Index("idx_total_engagements", "total_engagements"),
        Index("idx_last_engagement_at", "last_engagement_at"),
    )


class EngagementTimeSeriesData(Base):
    """Time series data for engagement analytics."""
    __tablename__ = "engagement_time_series"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    content_id = Column(String(255), nullable=False, index=True)
    content_type = Column(
        SQLEnum(ContentType, name="content_type"),
        nullable=False
    )
    engagement_type = Column(
        SQLEnum(EngagementType, name="engagement_type"),
        nullable=False
    )
    time_bucket = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    granularity = Column(String(20), nullable=False)  # hour, day, week, month
    count = Column(BigInteger, nullable=False, default=0)
    unique_users = Column(BigInteger, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    __table_args__ = (
        Index(
            "idx_content_time_bucket",
            "content_id",
            "time_bucket",
            "granularity"
        ),
        UniqueConstraint(
            "content_id",
            "engagement_type",
            "time_bucket",
            "granularity",
            name="uq_content_engagement_time_bucket"
        ),
    )


# Export all models
__all__ = [
    "Base",
    "EngagementEvent",
    "EngagementMetricsCache",
    "UserEngagementSummary",
    "EngagementTimeSeriesData"
]