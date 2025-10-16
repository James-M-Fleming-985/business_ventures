"""Database models and repositories for revenue tracking."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Numeric, DateTime, Enum as SQLEnum, Index, ForeignKey, CheckConstraint, Integer, Date
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from features.FEATURE-CA-006-03_revenue_tracking.models.conversion import ConversionType, ConversionStatus
from features.FEATURE-CA-006-03_revenue_tracking.models.revenue import RevenuePeriod


class Conversion:
    """Database model for conversions."""
    __tablename__ = "conversions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    conversion_type: Mapped[ConversionType] = mapped_column(SQLEnum(ConversionType), nullable=False)
    status: Mapped[ConversionStatus] = mapped_column(
        SQLEnum(ConversionStatus), default=ConversionStatus.PENDING, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    product_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    campaign_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    commission_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    commission_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_conversions_user_created", "user_id", "created_at"),
        Index("idx_conversions_campaign_created", "campaign_id", "created_at"),
        Index("idx_conversions_status", "status"),
        CheckConstraint("amount >= 0", name="check_amount_positive"),
    )


class Revenue:
    """Database model for revenue tracking."""
    __tablename__ = "revenues"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    campaign_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    period: Mapped[RevenuePeriod] = mapped_column(SQLEnum(RevenuePeriod), nullable=False)
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    gross_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    net_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    refunds: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    commission_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    conversion_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_revenues_period", "period", "period_start", "period_end"),
        Index("idx_revenues_user_period", "user_id", "period", "period_start"),
        Index("idx_revenues_campaign_period", "campaign_id", "period", "period_start"),
        CheckConstraint("gross_revenue >= 0", name="check_gross_revenue_positive"),
        CheckConstraint("net_revenue >= 0", name="check_net_revenue_positive"),
        CheckConstraint("refunds >= 0", name="check_refunds_positive"),
        CheckConstraint("commission_paid >= 0", name="check_commission_positive"),
        CheckConstraint("period_start <= period_end", name="check_period_order"),
    )
