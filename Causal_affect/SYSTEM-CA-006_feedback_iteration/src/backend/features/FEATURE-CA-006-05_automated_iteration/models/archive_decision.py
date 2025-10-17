"""Archive decision models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ArchiveReason(str, Enum):
    """Archive reason."""

    COMPLETED = "completed"
    FAILED = "failed"
    OUTDATED = "outdated"
    DUPLICATE = "duplicate"
    MANUAL = "manual"
    AUTO_CLEANUP = "auto_cleanup"
    RESOURCE_LIMIT = "resource_limit"
    POLICY_VIOLATION = "policy_violation"


class ArchiveStatus(str, Enum):
    """Archive status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ArchiveDecisionBase(BaseModel):
    """Base archive decision model."""

    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_id: UUID
    reason: ArchiveReason
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    retention_days: int = Field(default=90, ge=0, le=3650)
    compress: bool = True
    encrypt: bool = True
    tags: List[str] = Field(default_factory=list)

    @validator("entity_type")
    def validate_entity_type(cls, v: str) -> str:
        allowed_types = [
            "experiment",
            "iteration_plan",
            "model",
            "dataset",
            "artifact",
            "result",
        ]
        v = v.strip().lower()
        if v not in allowed_types:
            raise ValueError(f"Entity type must be one of: {', '.join(allowed_types)}")
        return v

    @validator("description")
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @validator("tags")
    def validate_tags(cls, v: List[str]) -> List[str]:
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        # Clean and validate tags
        cleaned_tags = []
        for tag in v:
            tag = tag.strip().lower()
            if tag and len(tag) <= 50:
                cleaned_tags.append(tag)
        return list(set(cleaned_tags))  # Remove duplicates


class ArchiveDecisionCreate(ArchiveDecisionBase):
    """Create archive decision model."""

    scheduled_at: Optional[datetime] = None
    auto_approve: bool = False
    approval_required: bool = True
    approver_id: Optional[UUID] = None
    priority: int = Field(default=3, ge=1, le=5)

    @validator("scheduled_at")
    def validate_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v < datetime.utcnow():
            raise ValueError("Scheduled time cannot be in the past")
        return v

    @validator("approver_id")
    def validate_approver(cls, v: Optional[UUID], values: Dict[str, Any]) -> Optional[UUID]:
        if values.get("approval_required") and not values.get("auto_approve") and not v:
            raise ValueError("Approver ID required when approval is required")
        return v


class ArchiveDecisionUpdate(BaseModel):
    """Update archive decision model."""

    reason: Optional[ArchiveReason] = None
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None
    retention_days: Optional[int] = Field(None, ge=0, le=3650)
    compress: Optional[bool] = None
    encrypt: Optional[bool] = None
    tags: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[ArchiveStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)

    @validator("description")
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @validator("tags")
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            # Clean and validate tags
            cleaned_tags = []
            for tag in v:
                tag = tag.strip().lower()
                if tag and len(tag) <= 50:
                    cleaned_tags.append(tag)
            return list(set(cleaned_tags))  # Remove duplicates
        return v

    @validator("scheduled_at")
    def validate_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v < datetime.utcnow():
            raise ValueError("Scheduled time cannot be in the past")
        return v


class ArchiveDecision(ArchiveDecisionBase):
    """Archive decision model."""

    id: UUID
    status: ArchiveStatus = ArchiveStatus.PENDING
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approval_required: bool = True
    auto_approve: bool = False
    priority: int = Field(default=3, ge=1, le=5)


class ArchiveDecisionResponse(ArchiveDecision):
    """Archive decision response model."""

    archive_location: Optional[str] = None
    archive_size_bytes: Optional[int] = None
    original_size_bytes: Optional[int] = None
    compression_ratio: Optional[float] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    checksum: Optional[str] = None
    expiry_date: Optional[datetime] = None
    restore_count: int = 0
    last_restored_at: Optional[datetime] = None

    class Config:
        orm_mode = True

    @validator("expiry_date")
    def calculate_expiry_date(cls, v: Optional[datetime], values: Dict[str, Any]) -> Optional[datetime]:
        if not v and values.get("completed_at") and "retention_days" in values:
            from datetime import timedelta
            return values["completed_at"] + timedelta(days=values["retention_days"])
        return v

    @validator("compression_ratio")
    def calculate_compression_ratio(cls, v: Optional[float], values: Dict[str, Any]) -> Optional[float]:
        if not v and values.get("original_size_bytes") and values.get("archive_size_bytes"):
            original = values["original_size_bytes"]
            archive = values["archive_size_bytes"]
            if original > 0:
                return round(1 - (archive / original), 3)
        return v