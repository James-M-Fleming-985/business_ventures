"""Pydantic models for time-series data."""

from datetime import datetime
from typing import Optional, Dict, Any, Union
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class TimeSeriesDataCreate(BaseModel):
    """Model for creating time-series data."""
    
    timestamp: datetime = Field(
        ...,
        description="Timestamp of the data point"
    )
    metric_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the metric"
    )
    value: Union[float, int, Decimal] = Field(
        ...,
        description="Numeric value of the metric"
    )
    tags: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Key-value tags for filtering and grouping"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v: Union[float, int, Decimal]) -> float:
        """Convert value to float and validate."""
        value = float(v)
        if not (-1e308 < value < 1e308):
            raise ValueError("Value out of range")
        return value
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Validate tags dictionary."""
        if v is None:
            return {}
        if len(v) > 50:
            raise ValueError("Too many tags (max 50)")
        for key, val in v.items():
            if len(key) > 100:
                raise ValueError(f"Tag key '{key}' too long (max 100 chars)")
            if len(val) > 1000:
                raise ValueError(f"Tag value for '{key}' too long (max 1000 chars)")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class TimeSeriesData(TimeSeriesDataCreate):
    """Model for time-series data with database fields."""
    
    id: int = Field(
        ...,
        description="Unique identifier"
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp"
    )
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
