"""Time series data models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class DataType(str, Enum):
    """Supported data types for time series values."""
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"


class AggregationFunction(str, Enum):
    """Available aggregation functions."""
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    FIRST = "first"
    LAST = "last"
    STDDEV = "stddev"
    VARIANCE = "variance"
    MEDIAN = "median"


class TimeInterval(str, Enum):
    """Time intervals for aggregation."""
    MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    HOUR = "1h"
    FOUR_HOURS = "4h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"


class TimeSeriesDataPoint(BaseModel):
    """Single time series data point."""
    timestamp: datetime = Field(..., description="Data point timestamp")
    value: Union[int, float, Decimal, str, bool, Dict[str, Any]] = Field(
        ..., description="Data point value"
    )
    tags: Optional[Dict[str, str]] = Field(
        default=None, description="Additional tags for filtering"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any) -> Any:
        if isinstance(v, dict):
            # Validate JSON structure
            return v
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }


class TimeSeriesDataCreate(BaseModel):
    """Create time series data request."""
    series_id: UUID = Field(..., description="Time series identifier")
    timestamp: datetime = Field(..., description="Data point timestamp")
    value: Union[int, float, Decimal, str, bool, Dict[str, Any]] = Field(
        ..., description="Data point value"
    )
    data_type: DataType = Field(..., description="Value data type")
    tags: Optional[Dict[str, str]] = Field(
        default=None, description="Additional tags"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )

    @model_validator(mode="after")
    def validate_value_type(self) -> "TimeSeriesDataCreate":
        """Validate value matches declared data type."""
        value_type_map = {
            DataType.INTEGER: int,
            DataType.FLOAT: (int, float),
            DataType.DECIMAL: (int, float, Decimal),
            DataType.STRING: str,
            DataType.BOOLEAN: bool,
            DataType.JSON: dict,
        }

        expected_type = value_type_map.get(self.data_type)
        if expected_type and not isinstance(self.value, expected_type):
            raise ValueError(
                f"Value type {type(self.value).__name__} does not match "
                f"declared data type {self.data_type.value}"
            )

        return self


class TimeSeriesDataUpdate(BaseModel):
    """Update time series data request."""
    value: Optional[Union[int, float, Decimal, str, bool, Dict[str, Any]]] = None
    tags: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TimeSeriesDataResponse(BaseModel):
    """Time series data response."""
    id: UUID = Field(..., description="Data point ID")
    series_id: UUID = Field(..., description="Time series ID")
    timestamp: datetime = Field(..., description="Data point timestamp")
    value: Union[int, float, Decimal, str, bool, Dict[str, Any]] = Field(
        ..., description="Data point value"
    )
    data_type: DataType = Field(..., description="Value data type")
    tags: Optional[Dict[str, str]] = Field(
        default=None, description="Additional tags"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v),
        }


class TimeSeriesBatch(BaseModel):
    """Batch of time series data points."""
    series_id: UUID = Field(..., description="Time series ID")
    data_type: DataType = Field(..., description="Value data type")
    points: List[TimeSeriesDataPoint] = Field(
        ..., description="List of data points"
    )

    @field_validator("points")
    @classmethod
    def validate_points(cls, v: List[TimeSeriesDataPoint]) -> List[TimeSeriesDataPoint]:
        if not v:
            raise ValueError("At least one data point is required")
        if len(v) > 10000:
            raise ValueError("Maximum 10000 points per batch")
        return v


class TimeSeriesBatchCreate(BaseModel):
    """Create batch of time series data."""
    batches: List[TimeSeriesBatch] = Field(
        ..., description="List of time series batches"
    )

    @field_validator("batches")
    @classmethod
    def validate_batches(cls, v: List[TimeSeriesBatch]) -> List[TimeSeriesBatch]:
        if not v:
            raise ValueError("At least one batch is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 batches per request")
        return v


class TimeSeriesQuery(BaseModel):
    """Query parameters for time series data."""
    series_ids: List[UUID] = Field(..., description="Time series IDs to query")
    start_time: datetime = Field(..., description="Query start time")
    end_time: datetime = Field(..., description="Query end time")
    tags: Optional[Dict[str, Union[str, List[str]]]] = Field(
        default=None, description="Tag filters"
    )
    limit: int = Field(default=1000, ge=1, le=10000, description="Result limit")
    offset: int = Field(default=0, ge=0, description="Result offset")
    order: str = Field(
        default="asc", pattern="^(asc|desc)$", description="Sort order"
    )

    @model_validator(mode="after")
    def validate_time_range(self) -> "TimeSeriesQuery":
        """Validate time range."""
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        
        # Maximum query range of 1 year
        max_range = 365 * 24 * 60 * 60  # seconds
        if (self.end_time - self.start_time).total_seconds() > max_range:
            raise ValueError("Maximum query range is 1 year")
        
        return self


class TimeSeriesAggregation(BaseModel):
    """Aggregation parameters for time series data."""
    series_ids: List[UUID] = Field(..., description="Time series IDs to aggregate")
    start_time: datetime = Field(..., description="Aggregation start time")
    end_time: datetime = Field(..., description="Aggregation end time")
    interval: TimeInterval = Field(..., description="Time interval for aggregation")
    function: AggregationFunction = Field(..., description="Aggregation function")
    tags: Optional[Dict[str, Union[str, List[str]]]] = Field(
        default=None, description="Tag filters"
    )
    group_by: Optional[List[str]] = Field(
        default=None, description="Group by tags"
    )
    fill_missing: bool = Field(
        default=False, description="Fill missing data points with null"
    )

    @model_validator(mode="after")
    def validate_aggregation(self) -> "TimeSeriesAggregation":
        """Validate aggregation parameters."""
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        
        # Validate group_by tags exist in tags filter
        if self.group_by and self.tags:
            for tag in self.group_by:
                if tag not in self.tags:
                    raise ValueError(f"Group by tag '{tag}' not in tag filters")
        
        return self


class TimeSeriesMetadata(BaseModel):
    """Time series metadata."""
    series_id: UUID = Field(..., description="Time series ID")
    data_type: DataType = Field(..., description="Value data type")
    point_count: int = Field(..., description="Total number of data points")
    first_timestamp: Optional[datetime] = Field(
        default=None, description="First data point timestamp"
    )
    last_timestamp: Optional[datetime] = Field(
        default=None, description="Last data point timestamp"
    )
    tags: Dict[str, List[str]] = Field(
        default_factory=dict, description="Available tags and their values"
    )
    statistics: Optional[Dict[str, Any]] = Field(
        default=None, description="Basic statistics"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
