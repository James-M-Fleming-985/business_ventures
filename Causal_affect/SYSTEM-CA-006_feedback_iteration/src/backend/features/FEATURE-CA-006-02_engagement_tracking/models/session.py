from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from ipaddress import IPv4Address, IPv6Address

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field


class DeviceType(str):
    """Device type enumeration"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    TV = "tv"
    UNKNOWN = "unknown"


class Browser(BaseModel):
    """Browser information"""
    name: str
    version: Optional[str] = None
    engine: Optional[str] = None


class OperatingSystem(BaseModel):
    """Operating system information"""
    name: str
    version: Optional[str] = None
    platform: Optional[str] = None


class Device(BaseModel):
    """Device information"""
    type: DeviceType = DeviceType.UNKNOWN
    brand: Optional[str] = None
    model: Optional[str] = None
    screen_width: Optional[int] = Field(None, gt=0)
    screen_height: Optional[int] = Field(None, gt=0)


class GeoLocation(BaseModel):
    """Geographic location information"""
    country: Optional[str] = Field(None, max_length=2)
    country_name: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    timezone: Optional[str] = None


class SessionBase(BaseModel):
    """Base session model"""
    user_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    landing_page: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip(cls, v: Optional[str]) -> Optional[str]:
        if v:
            try:
                IPv4Address(v)
            except ValueError:
                try:
                    IPv6Address(v)
                except ValueError:
                    raise ValueError("Invalid IP address format")
        return v


class SessionCreate(SessionBase):
    """Model for creating a new session"""
    browser: Optional[Browser] = None
    os: Optional[OperatingSystem] = None
    device: Optional[Device] = None
    geo_location: Optional[GeoLocation] = None
    custom_properties: Dict[str, Any] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    """Model for updating session data"""
    last_activity: Optional[datetime] = None
    exit_page: Optional[str] = None
    is_bounce: Optional[bool] = None
    custom_properties: Optional[Dict[str, Any]] = None


class SessionMetrics(BaseModel):
    """Session metrics and statistics"""
    page_views: int = 0
    events_count: int = 0
    duration_seconds: float = 0
    bounce_rate: float = Field(ge=0, le=1, default=0)
    pages_per_session: float = 0
    engagement_score: float = Field(ge=0, le=100, default=0)
    
    @computed_field
    @property
    def duration_formatted(self) -> str:
        """Format duration as human-readable string"""
        if self.duration_seconds < 60:
            return f"{int(self.duration_seconds)}s"
        elif self.duration_seconds < 3600:
            minutes = int(self.duration_seconds // 60)
            seconds = int(self.duration_seconds % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(self.duration_seconds // 3600)
            minutes = int((self.duration_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


class Session(SessionBase):
    """Complete session model"""
    id: UUID
    started_at: datetime
    last_activity: datetime
    ended_at: Optional[datetime] = None
    is_active: bool = True
    exit_page: Optional[str] = None
    browser: Optional[Browser] = None
    os: Optional[OperatingSystem] = None
    device: Optional[Device] = None
    geo_location: Optional[GeoLocation] = None
    metrics: SessionMetrics = Field(default_factory=SessionMetrics)
    custom_properties: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)
    
    @computed_field
    @property
    def duration(self) -> timedelta:
        """Calculate session duration"""
        end_time = self.ended_at or self.last_activity
        return end_time - self.started_at
    
    @computed_field
    @property
    def is_bounce(self) -> bool:
        """Determine if session is a bounce"""
        return self.metrics.page_views <= 1 and self.duration.total_seconds() < 10


class SessionResponse(Session):
    """Session response model for API"""
    events: Optional[List[Dict[str, Any]]] = None


class SessionFilter(BaseModel):
    """Filters for querying sessions"""
    user_id: Optional[UUID] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    is_active: Optional[bool] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    device_type: Optional[DeviceType] = None
    country: Optional[str] = None
    min_duration: Optional[float] = Field(None, ge=0)
    max_duration: Optional[float] = Field(None, ge=0)
    min_page_views: Optional[int] = Field(None, ge=0)
    
    @field_validator('started_before')
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], values: dict) -> Optional[datetime]:
        if v and values.get('started_after') and v <= values['started_after']:
            raise ValueError("started_before must be after started_after")
        return v


class SessionAggregate(BaseModel):
    """Aggregated session statistics"""
    total_sessions: int = 0
    unique_users: int = 0
    avg_duration: float = 0
    avg_page_views: float = 0
    bounce_rate: float = Field(ge=0, le=1, default=0)
    new_vs_returning: Dict[str, int] = Field(default_factory=lambda: {"new": 0, "returning": 0})
    top_landing_pages: List[Dict[str, Any]] = Field(default_factory=list)
    top_exit_pages: List[Dict[str, Any]] = Field(default_factory=list)
    device_breakdown: Dict[str, int] = Field(default_factory=dict)
    browser_breakdown: Dict[str, int] = Field(default_factory=dict)
    country_breakdown: Dict[str, int] = Field(default_factory=dict)
    utm_source_breakdown: Dict[str, int] = Field(default_factory=dict)
    time_period: Dict[str, datetime] = Field(default_factory=dict)


class UserSessionHistory(BaseModel):
    """User's session history"""
    user_id: UUID
    total_sessions: int = 0
    first_session: Optional[datetime] = None
    last_session: Optional[datetime] = None
    total_time_spent: float = 0
    total_page_views: int = 0
    avg_session_duration: float = 0
    avg_pages_per_session: float = 0
    preferred_device: Optional[DeviceType] = None
    preferred_browser: Optional[str] = None
    sessions: List[Session] = Field(default_factory=list)