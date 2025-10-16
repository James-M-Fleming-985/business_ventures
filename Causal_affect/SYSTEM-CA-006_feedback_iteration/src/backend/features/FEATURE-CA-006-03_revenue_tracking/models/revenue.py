"""Pydantic models for revenue tracking."""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class RevenuePeriod(str, Enum):
    """Revenue aggregation period."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class RevenueMetricType(str, Enum):
    """Types of revenue metrics."""
    GROSS_REVENUE = "gross_revenue"
    NET_REVENUE = "net_revenue"
    COMMISSION = "commission"
    REFUNDS = "refunds"
    ARR = "arr"  # Annual Recurring Revenue
    MRR = "mrr"  # Monthly Recurring Revenue


class RevenueBase(BaseModel):
    """Base revenue schema."""
    period: RevenuePeriod
    period_start: date
    period_end: date
    gross_revenue: Decimal = Field(ge=0, decimal_places=2)
    net_revenue: Decimal = Field(ge=0, decimal_places=2)
    refunds: Decimal = Field(ge=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class RevenueCreate(RevenueBase):
    """Schema for creating revenue record."""
    user_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    conversion_count: int = Field(default=0, ge=0)
    metadata: Optional[dict] = None


class RevenueResponse(RevenueBase):
    """Schema for revenue response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    conversion_count: int
    commission_paid: Decimal
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = None


class RevenueAggregation(BaseModel):
    """Schema for revenue aggregation."""
    period: RevenuePeriod
    period_start: date
    period_end: date
    total_gross_revenue: Decimal
    total_net_revenue: Decimal
    total_refunds: Decimal
    total_commission: Decimal
    conversion_count: int
    unique_users: int
    currency: str = "USD"


class RevenueByUser(BaseModel):
    """Schema for revenue grouped by user."""
    user_id: UUID
    gross_revenue: Decimal
    net_revenue: Decimal
    commission_earned: Decimal
    conversion_count: int
    last_conversion_at: Optional[datetime] = None


class RevenueByCampaign(BaseModel):
    """Schema for revenue grouped by campaign."""
    campaign_id: UUID
    gross_revenue: Decimal
    net_revenue: Decimal
    commission_paid: Decimal
    conversion_count: int
    roi: Optional[Decimal] = None


class RevenueStats(BaseModel):
    """Schema for revenue statistics."""
    total_revenue: Decimal
    avg_conversion_value: Decimal
    conversion_rate: Decimal
    growth_rate: Optional[Decimal] = None
    mrr: Optional[Decimal] = None
    arr: Optional[Decimal] = None
    ltv: Optional[Decimal] = None  # Lifetime Value
