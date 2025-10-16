"""Pydantic models for conversion tracking."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ConversionType(str, Enum):
    """Types of conversions."""
    PURCHASE = "purchase"
    SUBSCRIPTION = "subscription"
    UPGRADE = "upgrade"
    RENEWAL = "renewal"
    REFUND = "refund"


class ConversionStatus(str, Enum):
    """Status of conversion."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ConversionBase(BaseModel):
    """Base conversion schema."""
    user_id: UUID
    conversion_type: ConversionType
    amount: Decimal = Field(ge=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    product_id: Optional[str] = None
    campaign_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class ConversionCreate(ConversionBase):
    """Schema for creating conversion."""
    pass


class ConversionUpdate(BaseModel):
    """Schema for updating conversion."""
    status: Optional[ConversionStatus] = None
    amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    metadata: Optional[dict] = None


class ConversionResponse(ConversionBase):
    """Schema for conversion response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ConversionStatus
    created_at: datetime
    updated_at: datetime
    commission_amount: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None


class ConversionListResponse(BaseModel):
    """Schema for paginated conversion list."""
    items: list[ConversionResponse]
    total: int
    page: int
    page_size: int
    pages: int
