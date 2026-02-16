from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class AnalyticsEventDB(Base):
    __tablename__ = "analytics_events"
    
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    event_name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    user_id = Column(String(255), index=True)
    session_id = Column(String(255), index=True)
    properties = Column(JSON, default=dict)
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0, nullable=False)
    
    __table_args__ = (
        Index(
            "idx_analytics_events_status_created",
            "status",
            "created_at",
        ),
        Index(
            "idx_analytics_events_provider_status",
            "provider",
            "status",
        ),
        Index(
            "idx_analytics_events_user_created",
            "user_id",
            "created_at",
        ),
    )