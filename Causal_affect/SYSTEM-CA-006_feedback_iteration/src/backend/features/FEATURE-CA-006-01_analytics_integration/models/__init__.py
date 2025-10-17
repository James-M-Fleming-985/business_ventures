"""Analytics integration models."""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Standard event types."""
    
    # User events
    USER_SIGNUP = "user_signup"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PROFILE_UPDATE = "user_profile_update"
    USER_DELETED = "user_deleted"
    
    # Feature events
    FEATURE_USED = "feature_used"
    FEATURE_ENABLED = "feature_enabled"
    FEATURE_DISABLED = "feature_disabled"
    
    # API events
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    
    # Business events
    PAYMENT_COMPLETED = "payment_completed"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    
    # Custom events
    CUSTOM = "custom"


class EventProperty(BaseModel):
    """Base event property model."""
    
    name: str
    value: Any
    type: Optional[str] = None
    
    @field_validator("type", mode="before")
    @classmethod
    def infer_type(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if v:
            return v
        
        value = values.get("value")
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, (list, tuple)):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"


class AnalyticsEvent(BaseModel):
    """Base analytics event model."""
    
    event_type: Union[EventType, str] = Field(..., description="Event type or name")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Event properties")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    
    # Context
    app_version: Optional[str] = None
    environment: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class UserProfile(BaseModel):
    """User profile for analytics."""
    
    user_id: str = Field(..., description="User identifier")
    email: Optional[str] = None
    name: Optional[str] = None
    
    # Demographics
    age: Optional[int] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    
    # User properties
    created_at: datetime
    last_seen: Optional[datetime] = None
    
    # Engagement
    total_events: int = 0
    total_sessions: int = 0
    
    # Custom properties
    custom_properties: Dict[str, Any] = Field(default_factory=dict)
    
    # Segments
    segments: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class EventFilter(BaseModel):
    """Filter for querying events."""
    
    event_types: Optional[List[Union[EventType, str]]] = None
    user_ids: Optional[List[str]] = None
    from_timestamp: Optional[datetime] = None
    to_timestamp: Optional[datetime] = None
    properties: Optional[Dict[str, Any]] = None
    limit: int = Field(100, ge=1, le=10000)
    offset: int = Field(0, ge=0)


class EventAggregate(BaseModel):
    """Aggregated event data."""
    
    event_type: str
    count: int
    unique_users: int
    properties: Dict[str, Any] = Field(default_factory=dict)
    time_period: Optional[str] = None
    

class AnalyticsReport(BaseModel):
    """Analytics report model."""
    
    report_id: str
    name: str
    description: Optional[str] = None
    
    # Time range
    from_date: datetime
    to_date: datetime
    
    # Metrics
    total_events: int = 0
    unique_users: int = 0
    
    # Event breakdown
    events_by_type: List[EventAggregate] = Field(default_factory=list)
    
    # Additional data
    top_users: List[Dict[str, Any]] = Field(default_factory=list)
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class TrackingPlan(BaseModel):
    """Tracking plan for event validation."""
    
    event_name: str
    description: Optional[str] = None
    required_properties: List[str] = Field(default_factory=list)
    optional_properties: List[str] = Field(default_factory=list)
    property_types: Dict[str, str] = Field(default_factory=dict)
    
    def validate_event(self, event: AnalyticsEvent) -> List[str]:
        """Validate event against tracking plan."""
        errors = []
        
        # Check required properties
        for prop in self.required_properties:
            if prop not in event.properties:
                errors.append(f"Missing required property: {prop}")
        
        # Check property types
        for prop, expected_type in self.property_types.items():
            if prop in event.properties:
                value = event.properties[prop]
                actual_type = type(value).__name__
                
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Property {prop} should be string, got {actual_type}")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Property {prop} should be number, got {actual_type}")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Property {prop} should be boolean, got {actual_type}")
                elif expected_type == "array" and not isinstance(value, (list, tuple)):
                    errors.append(f"Property {prop} should be array, got {actual_type}")
                elif expected_type == "object" and not isinstance(value, dict):
                    errors.append(f"Property {prop} should be object, got {actual_type}")
        
        return errors


__all__ = [
    "EventType",
    "EventProperty",
    "AnalyticsEvent",
    "UserProfile",
    "EventFilter",
    "EventAggregate",
    "AnalyticsReport",
    "TrackingPlan",
]
