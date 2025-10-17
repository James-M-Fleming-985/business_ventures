from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class EngagementType(str, Enum):
    """Types of engagement events."""
    VIEW = "view"
    CLICK = "click"
    SHARE = "share"
    COMMENT = "comment"
    LIKE = "like"
    SAVE = "save"
    REPORT = "report"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"


class ContentType(str, Enum):
    """Types of content that can be tracked."""
    POST = "post"
    ARTICLE = "article"
    VIDEO = "video"
    IMAGE = "image"
    STORY = "story"
    PROFILE = "profile"
    COMMENT = "comment"


class BaseEngagementModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EngagementCreate(BaseEngagementModel):
    """Schema for creating engagement events."""
    user_id: str = Field(..., min_length=1, max_length=255)
    content_id: str = Field(..., min_length=1, max_length=255)
    content_type: ContentType
    engagement_type: EngagementType
    session_id: Optional[str] = Field(None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is not None and len(str(v)) > 5000:
            raise ValueError("Metadata too large")
        return v


class EngagementResponse(BaseEngagementModel):
    """Schema for engagement response."""
    id: str
    user_id: str
    content_id: str
    content_type: ContentType
    engagement_type: EngagementType
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class EngagementMetrics(BaseModel):
    """Aggregated engagement metrics."""
    content_id: str
    content_type: ContentType
    total_views: int = 0
    total_clicks: int = 0
    total_shares: int = 0
    total_comments: int = 0
    total_likes: int = 0
    total_saves: int = 0
    unique_users: int = 0
    engagement_rate: float = 0.0
    last_engagement: Optional[datetime] = None


class UserEngagementSummary(BaseModel):
    """User engagement summary."""
    user_id: str
    total_engagements: int
    engagement_breakdown: Dict[EngagementType, int]
    content_type_breakdown: Dict[ContentType, int]
    most_engaged_content: List[str]
    first_engagement: datetime
    last_engagement: datetime
    average_daily_engagements: float


class TimeSeriesMetric(BaseModel):
    """Time series data point."""
    timestamp: datetime
    value: float
    label: Optional[str] = None


class EngagementTimeSeries(BaseModel):
    """Time series engagement data."""
    content_id: str
    metric_type: str
    period_start: datetime
    period_end: datetime
    granularity: str  # hour, day, week, month
    data_points: List[TimeSeriesMetric]
    total: float
    average: float
    peak_value: float
    peak_timestamp: Optional[datetime] = None


class ContentPerformance(BaseModel):
    """Content performance metrics."""
    content_id: str
    content_type: ContentType
    title: Optional[str] = None
    engagement_score: float
    velocity_score: float  # engagement rate over time
    virality_score: float  # share rate
    retention_score: float  # return engagement rate
    metrics: EngagementMetrics
    trending_rank: Optional[int] = None
    category_rank: Optional[int] = None


class EngagementFilter(BaseModel):
    """Filter criteria for engagement queries."""
    user_ids: Optional[List[str]] = None
    content_ids: Optional[List[str]] = None
    content_types: Optional[List[ContentType]] = None
    engagement_types: Optional[List[EngagementType]] = None
    session_ids: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class BulkEngagementCreate(BaseModel):
    """Schema for bulk engagement creation."""
    engagements: List[EngagementCreate] = Field(..., min_items=1, max_items=1000)
    

class BulkEngagementResponse(BaseModel):
    """Response for bulk engagement creation."""
    created: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)