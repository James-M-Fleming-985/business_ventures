from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Float, JSON, Text,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class APIConfigDB(Base):
    """API configuration database model"""
    __tablename__ = "api_configs"
    __table_args__ = (
        UniqueConstraint("name", name="uq_api_configs_name"),
        Index("ix_api_configs_is_active", "is_active"),
        Index("ix_api_configs_created_at", "created_at"),
        {"schema": "api_connector"}
    )
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    version: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Authentication
    auth_type: Mapped[Optional[str]] = mapped_column(String(50))
    auth_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Rate limiting
    rate_limit_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Retry configuration
    retry_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Webhook configuration
    webhook_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Request defaults
    default_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    default_timeout_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    ssl_verify: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    follow_redirects: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_redirects: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    health_status: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Relationships
    endpoints: Mapped[list["APIEndpointDB"]] = relationship(
        back_populates="api_config", cascade="all, delete-orphan"
    )
    call_logs: Mapped[list["APICallLogDB"]] = relationship(
        back_populates="api_config", cascade="all, delete-orphan"
    )
    rate_limit_states: Mapped[list["RateLimitStateDB"]] = relationship(
        back_populates="api_config", cascade="all, delete-orphan"
    )


class APIEndpointDB(Base):
    """API endpoint configuration database model"""
    __tablename__ = "api_endpoints"
    __table_args__ = (
        UniqueConstraint("api_config_id", "name", name="uq_api_endpoints_config_name"),
        Index("ix_api_endpoints_api_config_id", "api_config_id"),
        Index("ix_api_endpoints_is_active", "is_active"),
        Index("ix_api_endpoints_method", "method"),
        {"schema": "api_connector"}
    )
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    api_config_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("api_connector.api_configs.id"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False, default="GET")
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Request configuration
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    query_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    body_template: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Response configuration
    response_mapping: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    
    # Pagination
    is_paginated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pagination_type: Mapped[Optional[str]] = mapped_column(String(50))
    max_pages: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    api_config: Mapped["APIConfigDB"] = relationship(back_populates="endpoints")
    call_logs: Mapped[list["APICallLogDB"]] = relationship(
        back_populates="api_endpoint", cascade="all, delete-orphan"
    )


class APICallLogDB(Base):
    """API call log for TimescaleDB hypertable"""
    __tablename__ = "api_call_logs"
    __table_args__ = (
        Index("ix_api_call_logs_api_config_id", "api_config_id"),
        Index("ix_api_call_logs_api_endpoint_id", "api_endpoint_id"),
        Index("ix_api_call_logs_status_code", "status_code"),
        Index("ix_api_call_logs_timestamp", "timestamp", postgresql_using="brin"),
        CheckConstraint("response_time_ms >= 0", name="ck_response_time_positive"),
        {"schema": "api_connector"}
    )
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, primary_key=True,
        server_default=func.now()
    )
    api_config_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("api_connector.api_configs.id"),
        nullable=False
    )
    api_endpoint_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("api_connector.api_endpoints.id")
    )
    
    # Request details
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    request_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    request_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Response details
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    response_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    
    # Error details
    error_type: Mapped[Optional[str]] = mapped_column(String(100))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Retry information
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_retry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Relationships
    api_config: Mapped["APIConfigDB"] = relationship(back_populates="call_logs")
    api_endpoint: Mapped[Optional["APIEndpointDB"]] = relationship(back_populates="call_logs")


class WebhookEventDB(Base):
    """Webhook event log for TimescaleDB hypertable"""
    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("ix_webhook_events_api_config_id", "api_config_id"),
        Index("ix_webhook_events_event_type", "event_type"),
        Index("ix_webhook_events_timestamp", "timestamp", postgresql_using="brin"),
        Index("ix_webhook_events_status_code", "status_code"),
        {"schema": "api_connector"}
    )
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, primary_key=True,
        server_default=func.now()
    )
    api_config_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("api_connector.api_configs.id"),
        nullable=False
    )
    api_call_log_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    webhook_url: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Delivery details
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    response_body: Mapped[Optional[str]] = mapped_column(Text)
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class RateLimitStateDB(Base):
    """Rate limit state tracking"""
    __tablename__ = "rate_limit_states"
    __table_args__ = (
        UniqueConstraint("api_config_id", "bucket_key", name="uq_rate_limit_states_config_bucket"),
        Index("ix_rate_limit_states_api_config_id", "api_config_id"),
        Index("ix_rate_limit_states_reset_at", "reset_at"),
        {"schema": "api_connector"}
    )
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    api_config_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("api_connector.api_configs.id"),
        nullable=False
    )
    bucket_key: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Rate limit state
    requests_made: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    limit_value: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    api_config: Mapped["APIConfigDB"] = relationship(back_populates="rate_limit_states")