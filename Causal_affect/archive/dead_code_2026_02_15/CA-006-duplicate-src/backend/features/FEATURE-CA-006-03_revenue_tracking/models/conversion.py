"""Conversion tracking models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConversionStatus(str, Enum):
    """Conversion status enum."""
    
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ConversionSource(str, Enum):
    """Conversion source enum."""
    
    DIRECT = "direct"
    ORGANIC = "organic"
    PAID_SEARCH = "paid_search"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    REFERRAL = "referral"
    AFFILIATE = "affiliate"
    OTHER = "other"


class ConversionType(str, Enum):
    """Conversion type enum."""
    
    PURCHASE = "purchase"
    SUBSCRIPTION = "subscription"
    SIGNUP = "signup"
    LEAD = "lead"
    DOWNLOAD = "download"
    TRIAL = "trial"
    UPGRADE = "upgrade"
    OTHER = "other"


class ConversionPeriod(str, Enum):
    """Time period enum for analytics."""
    
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ConversionEventBase(BaseModel):
    """Base conversion event model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    session_id: Optional[UUID] = None
    conversion_type: ConversionType
    source: ConversionSource
    campaign_id: Optional[str] = None
    product_id: Optional[UUID] = None
    value: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()


class ConversionEventCreate(ConversionEventBase):
    """Model for creating conversion events."""
    
    pass


class ConversionEventUpdate(BaseModel):
    """Model for updating conversion events."""
    
    model_config = ConfigDict(from_attributes=True)
    
    status: Optional[ConversionStatus] = None
    value: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    metadata: Optional[Dict[str, Any]] = None


class ConversionEvent(ConversionEventBase):
    """Complete conversion event model."""
    
    id: UUID
    status: ConversionStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    attribution_data: Optional[Dict[str, Any]] = None


class ConversionEventResponse(ConversionEvent):
    """API response model for conversion events."""
    
    pass


class ConversionMetrics(BaseModel):
    """Conversion metrics model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    total_conversions: int = Field(ge=0)
    total_value: Decimal = Field(ge=0, decimal_places=2)
    average_value: Decimal = Field(ge=0, decimal_places=2)
    conversion_rate: float = Field(ge=0, le=100)
    unique_users: int = Field(ge=0)
    period: ConversionPeriod
    start_date: datetime
    end_date: datetime
    
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_source: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)


class ConversionRate(BaseModel):
    """Conversion rate model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    period: datetime
    rate: float = Field(ge=0, le=100)
    conversions: int = Field(ge=0)
    visitors: int = Field(ge=0)
    value: Decimal = Field(ge=0, decimal_places=2)


class ConversionTrend(BaseModel):
    """Conversion trend model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    period: ConversionPeriod
    data_points: List[ConversionRate]
    growth_rate: float
    total_conversions: int = Field(ge=0)
    total_value: Decimal = Field(ge=0, decimal_places=2)
    average_rate: float = Field(ge=0, le=100)


class ConversionFilters(BaseModel):
    """Filters for conversion queries."""
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    conversion_type: Optional[List[ConversionType]] = None
    source: Optional[List[ConversionSource]] = None
    status: Optional[List[ConversionStatus]] = None
    campaign_id: Optional[str] = None
    product_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    min_value: Optional[Decimal] = Field(None, ge=0)
    max_value: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = None
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else None
    
    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v