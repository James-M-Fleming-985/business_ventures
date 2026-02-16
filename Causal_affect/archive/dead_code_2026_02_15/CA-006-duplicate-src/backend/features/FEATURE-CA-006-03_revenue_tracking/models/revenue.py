"""Revenue tracking models."""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RevenueStatus(str, Enum):
    """Revenue status enum."""
    
    PENDING = "pending"
    COLLECTED = "collected"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    WRITTEN_OFF = "written_off"


class RevenueSource(str, Enum):
    """Revenue source enum."""
    
    PRODUCT_SALE = "product_sale"
    SUBSCRIPTION = "subscription"
    SERVICE = "service"
    LICENSE = "license"
    ADVERTISING = "advertising"
    COMMISSION = "commission"
    OTHER = "other"


class RevenueType(str, Enum):
    """Revenue type enum."""
    
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    USAGE_BASED = "usage_based"
    MILESTONE = "milestone"


class RevenuePeriod(str, Enum):
    """Revenue period enum."""
    
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class RevenueRecordBase(BaseModel):
    """Base revenue record model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    transaction_id: str
    customer_id: UUID
    product_id: Optional[UUID] = None
    source: RevenueSource
    revenue_type: RevenueType
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    tax_amount: Decimal = Field(ge=0, decimal_places=2, default=Decimal("0"))
    discount_amount: Decimal = Field(ge=0, decimal_places=2, default=Decimal("0"))
    transaction_date: datetime
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()
    
    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount."""
        return self.amount - self.tax_amount - self.discount_amount


class RevenueRecordCreate(RevenueRecordBase):
    """Model for creating revenue records."""
    
    conversion_id: Optional[UUID] = None


class RevenueRecordUpdate(BaseModel):
    """Model for updating revenue records."""
    
    model_config = ConfigDict(from_attributes=True)
    
    status: Optional[RevenueStatus] = None
    collected_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class RevenueRecord(RevenueRecordBase):
    """Complete revenue record model."""
    
    id: UUID
    status: RevenueStatus
    conversion_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    collected_date: Optional[datetime] = None
    refund_amount: Decimal = Field(ge=0, decimal_places=2, default=Decimal("0"))
    
    @property
    def collected_amount(self) -> Decimal:
        """Calculate collected amount."""
        if self.status == RevenueStatus.COLLECTED:
            return self.net_amount - self.refund_amount
        return Decimal("0")


class RevenueRecordResponse(RevenueRecord):
    """API response model for revenue records."""
    
    net_amount: Decimal = Field(decimal_places=2)
    collected_amount: Decimal = Field(decimal_places=2)


class RevenueMetrics(BaseModel):
    """Revenue metrics model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    total_revenue: Decimal = Field(ge=0, decimal_places=2)
    collected_revenue: Decimal = Field(ge=0, decimal_places=2)
    pending_revenue: Decimal = Field(ge=0, decimal_places=2)
    refunded_amount: Decimal = Field(ge=0, decimal_places=2)
    tax_collected: Decimal = Field(ge=0, decimal_places=2)
    discounts_given: Decimal = Field(ge=0, decimal_places=2)
    
    transaction_count: int = Field(ge=0)
    customer_count: int = Field(ge=0)
    average_transaction: Decimal = Field(ge=0, decimal_places=2)
    
    period: RevenuePeriod
    start_date: datetime
    end_date: datetime
    
    growth_rate: float = 0.0
    by_source: Dict[str, Decimal] = Field(default_factory=dict)
    by_type: Dict[str, Decimal] = Field(default_factory=dict)
    by_status: Dict[str, Decimal] = Field(default_factory=dict)


class RevenueBreakdown(BaseModel):
    """Revenue breakdown model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    category: str
    amount: Decimal = Field(ge=0, decimal_places=2)
    percentage: float = Field(ge=0, le=100)
    count: int = Field(ge=0)
    average: Decimal = Field(ge=0, decimal_places=2)


class RevenueTrend(BaseModel):
    """Revenue trend model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    date: date
    revenue: Decimal = Field(ge=0, decimal_places=2)
    transactions: int = Field(ge=0)
    customers: int = Field(ge=0)
    average_value: Decimal = Field(ge=0, decimal_places=2)
    growth_rate: float


class ProductRevenue(BaseModel):
    """Product revenue model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    product_id: UUID
    product_name: str
    revenue: Decimal = Field(ge=0, decimal_places=2)
    transactions: int = Field(ge=0)
    units_sold: int = Field(ge=0)
    average_price: Decimal = Field(ge=0, decimal_places=2)
    refund_rate: float = Field(ge=0, le=100)


class CustomerRevenue(BaseModel):
    """Customer revenue model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    customer_id: UUID
    customer_name: str
    total_revenue: Decimal = Field(ge=0, decimal_places=2)
    transaction_count: int = Field(ge=0)
    average_order_value: Decimal = Field(ge=0, decimal_places=2)
    first_purchase_date: datetime
    last_purchase_date: datetime
    lifetime_value: Decimal = Field(ge=0, decimal_places=2)


class RevenueReport(BaseModel):
    """Revenue report model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    metrics: RevenueMetrics
    trends: List[RevenueTrend]
    top_products: List[ProductRevenue]
    top_customers: List[CustomerRevenue]
    breakdowns: Dict[str, List[RevenueBreakdown]]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class RevenueFilters(BaseModel):
    """Filters for revenue queries."""
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source: Optional[List[RevenueSource]] = None
    revenue_type: Optional[List[RevenueType]] = None
    status: Optional[List[RevenueStatus]] = None
    customer_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
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
    
    @field_validator("max_amount")
    @classmethod
    def validate_amount_range(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        if v and info.data.get("min_amount") and v < info.data["min_amount"]:
            raise ValueError("max_amount must be greater than min_amount")
        return v