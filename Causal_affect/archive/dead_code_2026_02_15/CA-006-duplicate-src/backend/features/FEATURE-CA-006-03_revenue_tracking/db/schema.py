from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, DateTime, Numeric, Boolean, Text, 
    ForeignKey, Date, Enum, Index, CheckConstraint,
    UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import text
import enum

Base = declarative_base()


class RevenueStatus(str, enum.Enum):
    PENDING = "pending"
    RECEIVED = "received"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class RecurrenceFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    ONLINE = "online"
    OTHER = "other"


class RevenueSource(Base):
    __tablename__ = "revenue_sources"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    revenues = relationship("Revenue", back_populates="source")
    
    __table_args__ = (
        Index("idx_revenue_source_name", "name"),
        UniqueConstraint("name", name="uq_revenue_source_name"),
    )


class RevenueCategory(Base):
    __tablename__ = "revenue_categories"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(PGUUID(as_uuid=True), ForeignKey("revenue_categories.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    parent = relationship("RevenueCategory", remote_side=[id], backref="subcategories")
    revenues = relationship("Revenue", back_populates="category")
    
    __table_args__ = (
        Index("idx_revenue_category_name", "name"),
        Index("idx_revenue_category_parent", "parent_id"),
        UniqueConstraint("name", "parent_id", name="uq_category_name_parent"),
    )


class Revenue(Base):
    __tablename__ = "revenues"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    description = Column(Text)
    invoice_number = Column(String(50))
    status = Column(Enum(RevenueStatus), default=RevenueStatus.PENDING, nullable=False)
    payment_method = Column(Enum(PaymentMethod))
    
    # Dates
    transaction_date = Column(Date, nullable=False)
    due_date = Column(Date)
    payment_date = Column(Date)
    
    # Foreign keys
    source_id = Column(PGUUID(as_uuid=True), ForeignKey("revenue_sources.id"), nullable=False)
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("revenue_categories.id"), nullable=False)
    recurring_revenue_id = Column(PGUUID(as_uuid=True), ForeignKey("recurring_revenues.id"), nullable=True)
    
    # Customer info
    customer_name = Column(String(200))
    customer_email = Column(String(255))
    customer_reference = Column(String(100))
    
    # Metadata
    notes = Column(Text)
    tags = Column(Text)  # JSON array stored as text
    metadata = Column(Text)  # JSON object stored as text
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(PGUUID(as_uuid=True))  # User ID reference
    updated_by = Column(PGUUID(as_uuid=True))  # User ID reference
    
    # Relationships
    source = relationship("RevenueSource", back_populates="revenues")
    category = relationship("RevenueCategory", back_populates="revenues")
    recurring_revenue = relationship("RecurringRevenue", back_populates="revenues")
    
    __table_args__ = (
        Index("idx_revenue_transaction_date", "transaction_date"),
        Index("idx_revenue_status", "status"),
        Index("idx_revenue_source", "source_id"),
        Index("idx_revenue_category", "category_id"),
        Index("idx_revenue_customer_email", "customer_email"),
        Index("idx_revenue_invoice_number", "invoice_number"),
        CheckConstraint("amount > 0", name="check_revenue_amount_positive"),
    )


class RecurringRevenue(Base):
    __tablename__ = "recurring_revenues"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Recurrence settings
    frequency = Column(Enum(RecurrenceFrequency), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    next_due_date = Column(Date, nullable=False)
    
    # Foreign keys
    source_id = Column(PGUUID(as_uuid=True), ForeignKey("revenue_sources.id"), nullable=False)
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("revenue_categories.id"), nullable=False)
    
    # Customer info
    customer_name = Column(String(200))
    customer_email = Column(String(255))
    customer_reference = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    auto_generate = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    metadata = Column(Text)  # JSON object stored as text
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(PGUUID(as_uuid=True))  # User ID reference
    
    # Relationships
    revenues = relationship("Revenue", back_populates="recurring_revenue")
    source = relationship("RevenueSource")
    category = relationship("RevenueCategory")
    
    __table_args__ = (
        Index("idx_recurring_revenue_next_due", "next_due_date"),
        Index("idx_recurring_revenue_active", "is_active"),
        Index("idx_recurring_revenue_customer_email", "customer_email"),
        CheckConstraint("amount > 0", name="check_recurring_amount_positive"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="check_recurring_dates"),
    )


class RevenueGoal(Base):
    __tablename__ = "revenue_goals"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    target_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Scope
    source_id = Column(PGUUID(as_uuid=True), ForeignKey("revenue_sources.id"), nullable=True)
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("revenue_categories.id"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(PGUUID(as_uuid=True))  # User ID reference
    
    # Relationships
    source = relationship("RevenueSource")
    category = relationship("RevenueCategory")
    
    __table_args__ = (
        Index("idx_revenue_goal_period", "period_start", "period_end"),
        Index("idx_revenue_goal_active", "is_active"),
        CheckConstraint("target_amount > 0", name="check_goal_amount_positive"),
        CheckConstraint("period_end >= period_start", name="check_goal_period"),
    )


class RevenueReport(Base):
    __tablename__ = "revenue_reports"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    report_type = Column(String(50), nullable=False)  # summary, detailed, forecast, etc.
    
    # Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Filters (stored as JSON)
    filters = Column(Text)  # JSON object with applied filters
    
    # Results
    total_revenue = Column(Numeric(15, 2))
    revenue_count = Column(Integer)
    report_data = Column(Text)  # JSON object with full report data
    
    # Scheduling
    is_scheduled = Column(Boolean, default=False, nullable=False)
    schedule_frequency = Column(Enum(RecurrenceFrequency))
    next_run_date = Column(DateTime(timezone=True))
    last_run_date = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(PGUUID(as_uuid=True))  # User ID reference
    
    __table_args__ = (
        Index("idx_revenue_report_period", "period_start", "period_end"),
        Index("idx_revenue_report_type", "report_type"),
        Index("idx_revenue_report_scheduled", "is_scheduled", "next_run_date"),
        CheckConstraint("period_end >= period_start", name="check_report_period"),
    )
