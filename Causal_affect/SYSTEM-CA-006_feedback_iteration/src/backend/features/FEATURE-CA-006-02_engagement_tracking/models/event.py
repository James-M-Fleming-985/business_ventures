from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class EventType(str, Enum):
    """Supported engagement event types"""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    SCROLL = "scroll"
    TIME_SPENT = "time_spent"
    FORM_INTERACTION = "form_interaction"
    VIDEO_PLAY = "video_play"
    VIDEO_PAUSE = "video_pause"
    VIDEO_COMPLETE = "video_complete"
    DOWNLOAD = "download"
    SHARE = "share"
    COMMENT = "comment"
    LIKE = "like"
    CUSTOM = "custom"


class EventSource(str, Enum):
    """Source of the event"""
    WEB = "web"
    MOBILE_APP = "mobile_app"
    API = "api"
    SERVER = "server"


class EventBase(BaseModel):
    """Base event model"""
    event_type: EventType
    session_id: UUID
    user_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: EventSource = EventSource.WEB
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(use_enum_values=True)


class PageViewEvent(EventBase):
    """Page view event model"""
    event_type: EventType = Field(default=EventType.PAGE_VIEW, frozen=True)
    page_url: str
    page_title: Optional[str] = None
    referrer: Optional[str] = None
    
    @field_validator('page_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Page URL cannot be empty")
        return v.strip()


class ClickEvent(EventBase):
    """Click event model"""
    event_type: EventType = Field(default=EventType.CLICK, frozen=True)
    element_id: Optional[str] = None
    element_class: Optional[str] = None
    element_text: Optional[str] = None
    target_url: Optional[str] = None
    x_position: Optional[int] = None
    y_position: Optional[int] = None


class ScrollEvent(EventBase):
    """Scroll event model"""
    event_type: EventType = Field(default=EventType.SCROLL, frozen=True)
    scroll_depth: float = Field(ge=0, le=100)
    page_height: Optional[int] = Field(None, gt=0)
    viewport_height: Optional[int] = Field(None, gt=0)


class TimeSpentEvent(EventBase):
    """Time spent event model"""
    event_type: EventType = Field(default=EventType.TIME_SPENT, frozen=True)
    duration_seconds: float = Field(gt=0)
    page_url: str
    is_active: bool = True


class FormInteractionEvent(EventBase):
    """Form interaction event model"""
    event_type: EventType = Field(default=EventType.FORM_INTERACTION, frozen=True)
    form_id: str
    field_name: Optional[str] = None
    action: str = Field(pattern="^(focus|blur|change|submit)$")
    

class VideoEvent(EventBase):
    """Video event model"""
    video_id: str
    video_title: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, gt=0)
    current_time: Optional[float] = Field(None, ge=0)
    

class VideoPlayEvent(VideoEvent):
    """Video play event model"""
    event_type: EventType = Field(default=EventType.VIDEO_PLAY, frozen=True)


class VideoPauseEvent(VideoEvent):
    """Video pause event model"""
    event_type: EventType = Field(default=EventType.VIDEO_PAUSE, frozen=True)


class VideoCompleteEvent(VideoEvent):
    """Video complete event model"""
    event_type: EventType = Field(default=EventType.VIDEO_COMPLETE, frozen=True)
    completion_rate: float = Field(ge=0, le=100)


class DownloadEvent(EventBase):
    """Download event model"""
    event_type: EventType = Field(default=EventType.DOWNLOAD, frozen=True)
    file_name: str
    file_type: Optional[str] = None
    file_size: Optional[int] = Field(None, gt=0)
    download_url: str


class ShareEvent(EventBase):
    """Share event model"""
    event_type: EventType = Field(default=EventType.SHARE, frozen=True)
    platform: str
    content_id: str
    content_type: Optional[str] = None
    share_url: Optional[str] = None


class EngagementEvent(EventBase):
    """Generic engagement event model"""
    content_id: str
    content_type: Optional[str] = None


class CommentEvent(EngagementEvent):
    """Comment event model"""
    event_type: EventType = Field(default=EventType.COMMENT, frozen=True)
    comment_id: Optional[str] = None
    parent_comment_id: Optional[str] = None


class LikeEvent(EngagementEvent):
    """Like event model"""
    event_type: EventType = Field(default=EventType.LIKE, frozen=True)
    is_unlike: bool = False


class CustomEvent(EventBase):
    """Custom event model for extensibility"""
    event_type: EventType = Field(default=EventType.CUSTOM, frozen=True)
    event_name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('event_name')
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Event name cannot be empty")
        return v.strip()


class EventCreate(BaseModel):
    """Model for creating events via API"""
    event_type: EventType
    session_id: UUID
    user_id: Optional[UUID] = None
    source: EventSource = EventSource.WEB
    metadata: Dict[str, Any] = Field(default_factory=dict)
    event_data: Dict[str, Any]
    
    model_config = ConfigDict(use_enum_values=True)


class EventResponse(EventBase):
    """Event response model"""
    id: UUID
    created_at: datetime
    processed: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class EventBatch(BaseModel):
    """Batch of events for bulk processing"""
    events: list[EventCreate]
    
    @field_validator('events')
    @classmethod
    def validate_events(cls, v: list[EventCreate]) -> list[EventCreate]:
        if not v:
            raise ValueError("Events list cannot be empty")
        if len(v) > 1000:
            raise ValueError("Maximum 1000 events per batch")
        return v


class EventStats(BaseModel):
    """Event statistics model"""
    event_type: EventType
    count: int = 0
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)