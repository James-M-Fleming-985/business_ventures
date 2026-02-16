"""Priority-related data models for prioritization engine."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class PriorityLevel(str, Enum):
    """Standard priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class PriorityCreate(BaseModel):
    """Create priority assignment."""
    entity_id: UUID
    entity_type: str
    priority_level: PriorityLevel
    score: Decimal = Field(
        ge=0,
        le=100,
        decimal_places=2,
        description="Priority score 0-100"
    )
    reason: Optional[str] = None
    metadata: Optional[Dict[str, any]] = None
    expires_at: Optional[datetime] = None


class PriorityUpdate(BaseModel):
    """Update priority assignment."""
    priority_level: Optional[PriorityLevel] = None
    score: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        decimal_places=2
    )
    reason: Optional[str] = None
    metadata: Optional[Dict[str, any]] = None
    expires_at: Optional[datetime] = None


class PriorityResponse(BaseModel):
    """Priority response model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    entity_id: UUID
    entity_type: str
    priority_level: PriorityLevel
    score: Decimal
    reason: Optional[str] = None
    metadata: Optional[Dict[str, any]] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class PriorityListResponse(BaseModel):
    """List of priorities with pagination."""
    items: List[PriorityResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_prev: bool = False


class PriorityCalculationRequest(BaseModel):
    """Request to calculate priority."""
    entity_id: UUID
    entity_type: str
    factors: Dict[str, Any] = Field(
        description="Factors affecting priority calculation"
    )
    weights: Optional[Dict[str, Decimal]] = Field(
        None,
        description="Custom weights for factors"
    )
    override_rules: Optional[List[str]] = Field(
        None,
        description="Rule IDs to override"
    )


class PriorityCalculationResponse(BaseModel):
    """Priority calculation result."""
    model_config = ConfigDict(from_attributes=True)
    
    entity_id: UUID
    entity_type: str
    priority_level: PriorityLevel
    score: Decimal = Field(
        ge=0,
        le=100,
        description="Calculated priority score"
    )
    breakdown: Dict[str, Decimal] = Field(
        description="Score breakdown by factor"
    )
    applied_rules: List[str] = Field(
        description="Rules applied during calculation"
    )
    recommendations: Optional[List[str]] = None
    calculated_at: datetime
    expires_at: Optional[datetime] = None


class PriorityRule(BaseModel):
    """Priority calculation rule."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    entity_type: str
    condition: Dict[str, Any] = Field(
        description="Rule condition in JSON format"
    )
    action: Dict[str, Any] = Field(
        description="Action to take when condition matches"
    )
    priority: int = Field(
        default=0,
        description="Rule execution priority (higher executes first)"
    )
    enabled: bool = True
    metadata: Optional[Dict[str, any]] = None


class PriorityRuleCreate(BaseModel):
    """Create priority rule."""
    name: str
    description: Optional[str] = None
    entity_type: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    priority: int = 0
    enabled: bool = True
    metadata: Optional[Dict[str, any]] = None


class PriorityRuleUpdate(BaseModel):
    """Update priority rule."""
    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
    metadata: Optional[Dict[str, any]] = None


class PriorityRuleResponse(BaseModel):
    """Priority rule response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    entity_type: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    priority: int
    enabled: bool
    metadata: Optional[Dict[str, any]] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    @field_validator("condition", "action")
    @classmethod
    def validate_json_fields(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON fields are proper dictionaries."""
        if not isinstance(v, dict):
            raise ValueError("Must be a valid dictionary")
        return v