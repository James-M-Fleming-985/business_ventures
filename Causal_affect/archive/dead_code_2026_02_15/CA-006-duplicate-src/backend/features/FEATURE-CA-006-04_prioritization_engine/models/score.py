"""Score-related data models for prioritization engine."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ScoreType(str, Enum):
    """Types of scoring components."""
    URGENCY = "urgency"
    IMPACT = "impact"
    COMPLEXITY = "complexity"
    RISK = "risk"
    VALUE = "value"
    EFFORT = "effort"
    CUSTOM = "custom"


class ScoreWeight(BaseModel):
    """Weight configuration for a score component."""
    model_config = ConfigDict(from_attributes=True)
    
    score_type: ScoreType
    weight: Decimal = Field(
        ge=0,
        le=1,
        decimal_places=2,
        description="Weight value between 0 and 1"
    )
    enabled: bool = True
    
    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: Decimal) -> Decimal:
        if not 0 <= v <= 1:
            raise ValueError("Weight must be between 0 and 1")
        return v


class ScoreComponent(BaseModel):
    """Individual score component."""
    model_config = ConfigDict(from_attributes=True)
    
    type: ScoreType
    value: Decimal = Field(
        ge=0,
        le=100,
        decimal_places=2,
        description="Score value between 0 and 100"
    )
    weight: Decimal = Field(
        ge=0,
        le=1,
        decimal_places=2,
        description="Component weight"
    )
    weighted_value: Optional[Decimal] = Field(
        None,
        description="Calculated weighted value"
    )
    metadata: Optional[Dict[str, any]] = None
    
    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Decimal) -> Decimal:
        if not 0 <= v <= 100:
            raise ValueError("Score value must be between 0 and 100")
        return v


class ScoreCalculation(BaseModel):
    """Score calculation request/result."""
    model_config = ConfigDict(from_attributes=True)
    
    entity_id: UUID
    entity_type: str
    components: List[ScoreComponent]
    total_score: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Calculated total score"
    )
    calculation_method: str = "weighted_average"
    calculated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, any]] = None


class ScoreCreate(BaseModel):
    """Create a new score entry."""
    entity_id: UUID
    entity_type: str
    score_type: ScoreType
    value: Decimal = Field(
        ge=0,
        le=100,
        decimal_places=2
    )
    components: Optional[List[ScoreComponent]] = None
    metadata: Optional[Dict[str, any]] = None


class ScoreUpdate(BaseModel):
    """Update score entry."""
    value: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        decimal_places=2
    )
    components: Optional[List[ScoreComponent]] = None
    metadata: Optional[Dict[str, any]] = None


class ScoreResponse(BaseModel):
    """Score response model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    entity_id: UUID
    entity_type: str
    score_type: ScoreType
    value: Decimal
    components: Optional[List[ScoreComponent]] = None
    metadata: Optional[Dict[str, any]] = None
    created_at: datetime
    updated_at: datetime


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown."""
    model_config = ConfigDict(from_attributes=True)
    
    entity_id: UUID
    entity_type: str
    total_score: Decimal = Field(
        ge=0,
        le=100,
        description="Overall weighted score"
    )
    components: List[ScoreComponent]
    calculation_method: str
    weights: List[ScoreWeight]
    calculated_at: datetime
    metadata: Optional[Dict[str, any]] = None


class ScoreHistory(BaseModel):
    """Historical score entry."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    entity_id: UUID
    entity_type: str
    score_type: ScoreType
    value: Decimal
    previous_value: Optional[Decimal] = None
    change_percentage: Optional[Decimal] = None
    components: Optional[List[ScoreComponent]] = None
    recorded_at: datetime
    metadata: Optional[Dict[str, any]] = None


class ScoreHistoryResponse(BaseModel):
    """Score history response."""
    entity_id: UUID
    entity_type: str
    score_type: Optional[ScoreType] = None
    history: List[ScoreHistory]
    total_entries: int
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class ScoreThreshold(BaseModel):
    """Score threshold configuration."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    score_type: ScoreType
    min_value: Decimal = Field(
        ge=0,
        le=100,
        description="Minimum score value"
    )
    max_value: Decimal = Field(
        ge=0,
        le=100,
        description="Maximum score value"
    )
    priority_level: str
    color_code: Optional[str] = None
    description: Optional[str] = None
    
    @field_validator("max_value")
    @classmethod
    def validate_range(cls, v: Decimal, info) -> Decimal:
        if "min_value" in info.data and v < info.data["min_value"]:
            raise ValueError("max_value must be greater than min_value")
        return v


class ScoreThresholdCreate(BaseModel):
    """Create score threshold."""
    name: str
    score_type: ScoreType
    min_value: Decimal = Field(ge=0, le=100)
    max_value: Decimal = Field(ge=0, le=100)
    priority_level: str
    color_code: Optional[str] = None
    description: Optional[str] = None


class ScoreThresholdResponse(BaseModel):
    """Score threshold response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    score_type: ScoreType
    min_value: Decimal
    max_value: Decimal
    priority_level: str
    color_code: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime