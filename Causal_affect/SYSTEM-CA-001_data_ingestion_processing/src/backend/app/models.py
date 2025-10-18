from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class FeedbackStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"

class FeedbackPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IterationStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class AnalysisType(str, Enum):
    SENTIMENT = "sentiment"
    TREND = "trend"
    PRIORITY = "priority"

class NotificationType(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"

class FeedbackCreate(BaseModel):
    user_id: str
    content: str
    category: str
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    metadata: Optional[Dict[str, Any]] = None

class Feedback(BaseModel):
    id: str
    user_id: str
    content: str
    category: str
    priority: FeedbackPriority
    status: FeedbackStatus = FeedbackStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class FeedbackUpdate(BaseModel):
    status: Optional[FeedbackStatus] = None
    priority: Optional[FeedbackPriority] = None
    content: Optional[str] = None

class IterationCreate(BaseModel):
    name: str
    description: str
    feedback_ids: List[str]
    start_date: datetime
    end_date: datetime

class Iteration(BaseModel):
    id: str
    name: str
    description: str
    feedback_ids: List[str]
    status: IterationStatus = IterationStatus.PLANNED
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime

class IterationUpdate(BaseModel):
    status: Optional[IterationStatus] = None
    name: Optional[str] = None
    description: Optional[str] = None

class AnalysisRequest(BaseModel):
    analysis_type: AnalysisType
    feedback_ids: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class AnalysisResult(BaseModel):
    id: str
    analysis_type: AnalysisType
    results: Dict[str, Any]
    created_at: datetime

class NotificationConfig(BaseModel):
    notification_type: NotificationType
    recipient: str
    events: List[str]
    enabled: bool = True

class NotificationConfigResponse(BaseModel):
    id: str
    notification_type: NotificationType
    recipient: str
    events: List[str]
    enabled: bool
    created_at: datetime

class ExportRequest(BaseModel):
    format: ExportFormat
    feedback_ids: Optional[List[str]] = None
    iteration_ids: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class ExportResponse(BaseModel):
    id: str
    format: ExportFormat
    url: str
    created_at: datetime
    expires_at: datetime
