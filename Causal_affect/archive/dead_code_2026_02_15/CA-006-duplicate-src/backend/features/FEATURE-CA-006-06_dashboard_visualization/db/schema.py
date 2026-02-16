"""Database schema for dashboard visualization."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class DashboardConfig(Base):
    """Dashboard configuration table."""

    __tablename__ = "dashboard_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    widgets = relationship("WidgetConfig", back_populates="dashboard", cascade="all, delete-orphan")
    layouts = relationship("DashboardLayout", back_populates="dashboard", cascade="all, delete-orphan")
    shares = relationship("DashboardShare", back_populates="dashboard", cascade="all, delete-orphan")
    versions = relationship("DashboardVersion", back_populates="dashboard", cascade="all, delete-orphan")
    preferences = relationship("UserDashboardPreference", back_populates="dashboard", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_dashboard_owner_org", "owner_id", "organization_id"),
        Index("idx_dashboard_active_public", "is_active", "is_public"),
    )


class WidgetConfig(Base):
    """Widget configuration table."""

    __tablename__ = "widget_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboard_configs.id"), nullable=False)
    widget_type = Column(String(50), nullable=False)  # chart, metric, table, text
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(JSON, nullable=False)  # {x, y, width, height}
    settings = Column(JSON, default=dict, nullable=False)
    data_source = Column(JSON, nullable=False)  # query config, API endpoint, etc.
    refresh_interval = Column(Integer, nullable=True)  # seconds
    is_visible = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    dashboard = relationship("DashboardConfig", back_populates="widgets")
    charts = relationship("ChartConfig", back_populates="widget", cascade="all, delete-orphan")
    filters = relationship("FilterConfig", back_populates="widget", cascade="all, delete-orphan")
    data = relationship("WidgetData", back_populates="widget", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_widget_dashboard_type", "dashboard_id", "widget_type"),)


class ChartConfig(Base):
    """Chart configuration table."""

    __tablename__ = "chart_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    widget_id = Column(UUID(as_uuid=True), ForeignKey("widget_configs.id"), nullable=False)
    chart_type = Column(String(50), nullable=False)  # line, bar, pie, scatter, etc.
    x_axis = Column(JSON, nullable=False)
    y_axis = Column(JSON, nullable=False)
    series = Column(JSON, default=list, nullable=False)
    colors = Column(JSON, default=list, nullable=False)
    legend = Column(JSON, default=dict, nullable=False)
    tooltip = Column(JSON, default=dict, nullable=False)
    annotations = Column(JSON, default=list, nullable=False)
    custom_options = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    widget = relationship("WidgetConfig", back_populates="charts")

    __table_args__ = (UniqueConstraint("widget_id", name="uq_chart_widget"),)


class FilterConfig(Base):
    """Filter configuration table."""

    __tablename__ = "filter_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    widget_id = Column(UUID(as_uuid=True), ForeignKey("widget_configs.id"), nullable=True)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboard_configs.id"), nullable=True)
    filter_type = Column(String(50), nullable=False)  # date_range, dropdown, multi_select, etc.
    field_name = Column(String(255), nullable=False)
    label = Column(String(255), nullable=False)
    default_value = Column(JSON, nullable=True)
    options = Column(JSON, default=list, nullable=False)
    validation = Column(JSON, default=dict, nullable=False)
    dependencies = Column(JSON, default=list, nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    widget = relationship("WidgetConfig", back_populates="filters")

    __table_args__ = (
        Index("idx_filter_widget_dashboard", "widget_id", "dashboard_id"),
        Index("idx_filter_type_field", "filter_type", "field_name"),
    )


class DashboardLayout(Base):
    """Dashboard layout configuration table."""

    __tablename__ = "dashboard_layouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboard_configs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    breakpoint = Column(String(20), nullable=False)  # desktop, tablet, mobile
    columns = Column(Integer, default=12, nullable=False)
    row_height = Column(Integer, default=60, nullable=False)
    margin = Column(JSON, default=dict, nullable=False)
    padding = Column(JSON, default=dict, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    dashboard = relationship("DashboardConfig", back_populates="layouts")

    __table_args__ = (
        UniqueConstraint("dashboard_id", "breakpoint", name="uq_dashboard_layout_breakpoint"),
        Index("idx_layout_dashboard_default", "dashboard_id", "is_default"),
    )


class DashboardShare(Base):
    """Dashboard sharing configuration table."""

    __tablename__ = "dashboard_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboard_configs.id"), nullable=False)
    shared_with_id = Column(UUID(as_uuid=True), nullable=True)  # user_id or group_id
    share_type = Column(String(20), nullable=False)  # user, group, public_link
    permission_level = Column(String(20), nullable=False)  # view, edit, admin
    share_token = Column(String(255), nullable=True, unique=True)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    dashboard = relationship("DashboardConfig", back_populates="shares")

    __table_args__ = (
        Index("idx_share_dashboard_type", "dashboard_id", "share_type"),
        Index("idx_share_token", "share_token"),
        UniqueConstraint(
            "dashboard_id", "shared_with_id", "share_type", name="uq_dashboard_share"
        ),
    )


class DashboardVersion(Base):
    """Dashboard version history table."""

    __tablename__ = "dashboard_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboard_configs.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    config_snapshot = Column(JSON, nullable=False)
    change_description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)

    # Relationships
    dashboard = relationship("DashboardConfig", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("dashboard_id", "version_number", name="uq_dashboard_version"),
        Index("idx_version_dashboard_current", "dashboard_id", "is_current"),
    )


class WidgetData(Base):
    """Widget data cache table."""

    __tablename__ = "widget_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    widget_id = Column(UUID(as_uuid=True), ForeignKey("widget_configs.id"), nullable=False)
    data = Column(JSON, nullable=False)
    query_hash = Column(String(64), nullable=False)
    parameters = Column(JSON, default=dict, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    row_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    cached_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    widget = relationship("WidgetConfig", back_populates="data")

    __table_args__ = (
        Index("idx_widget_data_cache", "widget_id", "query_hash"),
        Index("idx_widget_data_expires", "expires_at"),
    )


class UserDashboardPreference(Base):
    """User dashboard preferences table."""

    __tablename__ = "user_dashboard_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboard_configs.id"), nullable=False)
    theme = Column(String(20), default="light", nullable=False)
    default_filters = Column(JSON, default=dict, nullable=False)
    widget_preferences = Column(JSON, default=dict, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    dashboard = relationship("DashboardConfig", back_populates="preferences")

    __table_args__ = (
        UniqueConstraint("user_id", "dashboard_id", name="uq_user_dashboard_pref"),
        Index("idx_user_pref_favorite", "user_id", "is_favorite"),
    )


class DashboardTemplate(Base):
    """Dashboard template table."""

    __tablename__ = "dashboard_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    template_config = Column(JSON, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_template_category_public", "category", "is_public"),
        Index("idx_template_usage", "usage_count"),
    )