from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnalyticsProvider(str):
    GOOGLE_ANALYTICS = "google_analytics"
    MIXPANEL = "mixpanel"


class EventCategory(str):
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"
    PERFORMANCE = "performance"
    CONVERSION = "conversion"


class AnalyticsEventBase(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=100)
    category: EventCategory
    provider: AnalyticsProvider
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        return v.strip().lower().replace(" ", "_")


class AnalyticsEventCreate(AnalyticsEventBase):
    pass


class AnalyticsEventUpdate(BaseModel):
    properties: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class AnalyticsEvent(AnalyticsEventBase):
    id: UUID
    status: str = "pending"
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    class Config:
        from_attributes = True


class AnalyticsEventBatch(BaseModel):
    events: list[AnalyticsEventCreate]
    
    @field_validator("events")
    @classmethod
    def validate_batch_size(cls, v: list) -> list:
        if len(v) > 1000:
            raise ValueError("Batch size cannot exceed 1000 events")
        return v


class GoogleAnalyticsConfig(BaseModel):
    measurement_id: str
    api_secret: str
    

class MixpanelConfig(BaseModel):
    project_token: str
    api_key: Optional[str] = None
    server_url: str = "https://api.mixpanel.com"


class AnalyticsProviderConfig(BaseModel):
    google_analytics: Optional[GoogleAnalyticsConfig] = None
    mixpanel: Optional[MixpanelConfig] = None