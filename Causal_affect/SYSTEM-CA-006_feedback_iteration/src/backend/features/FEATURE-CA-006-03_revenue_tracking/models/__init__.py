"""Revenue tracking models and schemas."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class RevenueType(str, Enum):
    """Revenue type enumeration."""
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    USAGE_BASED = "usage_based"
    COMMISSION = "commission"
    REFUND = "refund"


class ConversionType(str, Enum):
    """Conversion event type enumeration."""
    SIGNUP = "signup"
    TRIAL_START = "trial_start"
    TRIAL_CONVERSION = "trial_conversion"
    SUBSCRIPTION = "subscription"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    CANCELLATION = "cancellation"
    REACTIVATION = "reactivation"


class RevenueModelBase(BaseModel):
    """Base revenue model schema."""
    model_config = ConfigDict(from_attributes=True)

    revenue_type: RevenueType
    amount: Decimal = Field(ge=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: Optional[str] = None


class RevenueModelCreate(RevenueModelBase):
    """Revenue model creation schema."""
    user_id: UUID
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)


class RevenueModel(RevenueModelBase):
    """Revenue model response schema."""
    id: UUID
    user_id: UUID
    transaction_date: datetime
    created_at: datetime
    metadata: dict


class ConversionEventBase(BaseModel):
    """Base conversion event schema."""
    model_config = ConfigDict(from_attributes=True)

    conversion_type: ConversionType
    revenue_amount: Decimal = Field(ge=0, decimal_places=2)
    metadata: dict = Field(default_factory=dict)


class ConversionEventCreate(ConversionEventBase):
    """Conversion event creation schema."""
    user_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversionEvent(ConversionEventBase):
    """Conversion event response schema."""
    id: UUID
    user_id: UUID
    timestamp: datetime
    created_at: datetime


class RevenueMetrics(BaseModel):
    """Revenue metrics aggregation schema."""
    model_config = ConfigDict(from_attributes=True)

    period_start: datetime
    period_end: datetime
    total_revenue: Decimal = Field(ge=0, decimal_places=2)
    mrr: Decimal = Field(ge=0, decimal_places=2, description="Monthly Recurring Revenue")
    arr: Decimal = Field(ge=0, decimal_places=2, description="Annual Recurring Revenue")
    arpu: Decimal = Field(ge=0, decimal_places=2, description="Average Revenue Per User")
    ltv: Decimal = Field(ge=0, decimal_places=2, description="Lifetime Value")
    churn_rate: Decimal = Field(ge=0, le=100, decimal_places=2)
    growth_rate: Decimal = Field(decimal_places=2)


__all__ = [
    "RevenueType",
    "ConversionType",
    "RevenueModel",
    "RevenueModelCreate",
    "RevenueModelBase",
    "ConversionEvent",
    "ConversionEventCreate",
    "ConversionEventBase",
    "RevenueMetrics",
]
