"""Database schema definitions for time-series data."""

from sqlalchemy import (
    Table, Column, Integer, String, Float, DateTime,
    Index, text, MetaData
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

metadata = MetaData()

timeseries_data_table = Table(
    "timeseries_data",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "timestamp",
        DateTime(timezone=True),
        nullable=False,
        index=True
    ),
    Column(
        "metric_name",
        String(255),
        nullable=False,
        index=True
    ),
    Column("value", Float, nullable=False),
    Column(
        "tags",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    ),
    Column(
        "metadata",
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb")
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
)


def create_indexes():
    """Create additional indexes for time-series data."""
    return [
        # Composite index for metric queries
        Index(
            "idx_timeseries_metric_timestamp",
            timeseries_data_table.c.metric_name,
            timeseries_data_table.c.timestamp.desc()
        ),
        
        # GIN index for JSONB tags
        Index(
            "idx_timeseries_tags",
            timeseries_data_table.c.tags,
            postgresql_using="gin"
        ),
        
        # Partial index for recent data
        Index(
            "idx_timeseries_recent",
            timeseries_data_table.c.timestamp,
            timeseries_data_table.c.metric_name,
            postgresql_where=text(
                "timestamp > (CURRENT_TIMESTAMP - INTERVAL '7 days')"
            )
        ),
        
        # Index for specific tag queries
        Index(
            "idx_timeseries_tags_keys",
            text("jsonb_object_keys(tags)"),
            postgresql_using="gin"
        )
    ]
