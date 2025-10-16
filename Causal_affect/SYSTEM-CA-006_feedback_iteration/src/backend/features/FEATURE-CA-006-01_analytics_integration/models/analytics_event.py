"""Analytics event Pydantic models."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional
from datetime import datetime
from enum import Enum


class AnalyticsProvider(str, Enum):
    """Supported analytics providers."""
    GOOGLE_ANALYTICS = "google_analytics"
    MIXPANEL = "mixpanel"
    BOTH = "both"


class AnalyticsEventCreate(BaseModel):
    """Schema for creating analytics events."""
    user_id: str = Field(..., description="User or client identifier")
    event_name: str = Field(..., min_length=1, max_length=255, description="Event name")
    event_params: Optional[dict[str, Any]] = Field(default=None, description="Event parameters")
    user_properties: Optional[dict[str, Any]] = Field(default=None, description="User properties")
    provider: AnalyticsProvider = Field(default=AnalyticsProvider.BOTH, description="Target provider")
    session_id: Optional[str] = Field(default=None, description="Session identifier")

    model_config = ConfigDict(use_enum_values=True)


class AnalyticsEvent(AnalyticsEventCreate):
    """Schema for analytics events."""
    id: int
    created_at: datetime
    sent_to_ga: bool = False
    sent_to_mixpanel: bool = False
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnalyticsEventInDB(BaseModel):
    """Internal database representation."""
    id: int
    user_id: str
    event_name: str
    event_params: Optional[dict[str, Any]]
    user_properties: Optional[dict[str, Any]]
    provider: str
    session_id: Optional[str]
    created_at: datetime
    sent_to_ga: bool
    sent_to_mixpanel: bool
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)
