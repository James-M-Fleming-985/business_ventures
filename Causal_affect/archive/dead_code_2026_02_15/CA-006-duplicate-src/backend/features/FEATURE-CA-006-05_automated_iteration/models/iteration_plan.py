"""Iteration plan models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class IterationPlanStatus(str, Enum):
    """Iteration plan status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IterationStepType(str, Enum):
    """Iteration step type."""

    DATA_COLLECTION = "data_collection"
    PREPROCESSING = "preprocessing"
    TRAINING = "training"
    EVALUATION = "evaluation"
    OPTIMIZATION = "optimization"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"


class IterationStepStatus(str, Enum):
    """Iteration step status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class IterationMetric(BaseModel):
    """Iteration metric model."""

    name: str = Field(..., min_length=1, max_length=100)
    target_value: float
    current_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    higher_is_better: bool = True
    threshold: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("name")
    def validate_name(cls, v: str) -> str:
        return v.strip()


class IterationGoal(BaseModel):
    """Iteration goal model."""

    description: str = Field(..., min_length=1, max_length=500)
    metrics: List[IterationMetric] = Field(default_factory=list)
    priority: int = Field(default=1, ge=1, le=5)
    deadline: Optional[datetime] = None
    achieved: bool = False
    achieved_at: Optional[datetime] = None

    @validator("description")
    def validate_description(cls, v: str) -> str:
        return v.strip()

    @validator("metrics")
    def validate_metrics(cls, v: List[IterationMetric]) -> List[IterationMetric]:
        if len(v) > 10:
            raise ValueError("Maximum 10 metrics allowed per goal")
        return v


class IterationStep(BaseModel):
    """Iteration step model."""

    id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=200)
    type: IterationStepType
    description: Optional[str] = Field(None, max_length=1000)
    status: IterationStepStatus = IterationStepStatus.PENDING
    order: int = Field(..., ge=0)
    dependencies: List[UUID] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    @validator("name", "description")
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @validator("dependencies")
    def validate_dependencies(cls, v: List[UUID]) -> List[UUID]:
        if len(v) > 20:
            raise ValueError("Maximum 20 dependencies allowed per step")
        return v


class IterationPlanBase(BaseModel):
    """Base iteration plan model."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    experiment_id: UUID
    goals: List[IterationGoal] = Field(default_factory=list)
    steps: List[IterationStep] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    auto_execute: bool = False
    max_iterations: int = Field(default=10, ge=1, le=100)
    convergence_criteria: Dict[str, Any] = Field(default_factory=dict)

    @validator("name", "description")
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @validator("goals")
    def validate_goals(cls, v: List[IterationGoal]) -> List[IterationGoal]:
        if not v:
            raise ValueError("At least one goal is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 goals allowed per plan")
        return v

    @validator("steps")
    def validate_steps(cls, v: List[IterationStep]) -> List[IterationStep]:
        if not v:
            raise ValueError("At least one step is required")
        if len(v) > 50:
            raise ValueError("Maximum 50 steps allowed per plan")
        # Validate order uniqueness
        orders = [step.order for step in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Step orders must be unique")
        return v


class IterationPlanCreate(IterationPlanBase):
    """Create iteration plan model."""

    pass


class IterationPlanUpdate(BaseModel):
    """Update iteration plan model."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    goals: Optional[List[IterationGoal]] = None
    steps: Optional[List[IterationStep]] = None
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    auto_execute: Optional[bool] = None
    max_iterations: Optional[int] = Field(None, ge=1, le=100)
    convergence_criteria: Optional[Dict[str, Any]] = None
    status: Optional[IterationPlanStatus] = None

    @validator("name", "description")
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @validator("goals")
    def validate_goals(
        cls, v: Optional[List[IterationGoal]]
    ) -> Optional[List[IterationGoal]]:
        if v is not None:
            if not v:
                raise ValueError("At least one goal is required")
            if len(v) > 10:
                raise ValueError("Maximum 10 goals allowed per plan")
        return v

    @validator("steps")
    def validate_steps(
        cls, v: Optional[List[IterationStep]]
    ) -> Optional[List[IterationStep]]:
        if v is not None:
            if not v:
                raise ValueError("At least one step is required")
            if len(v) > 50:
                raise ValueError("Maximum 50 steps allowed per plan")
            # Validate order uniqueness
            orders = [step.order for step in v]
            if len(orders) != len(set(orders)):
                raise ValueError("Step orders must be unique")
        return v


class IterationPlan(IterationPlanBase):
    """Iteration plan model."""

    id: UUID
    status: IterationPlanStatus = IterationPlanStatus.DRAFT
    current_iteration: int = 0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: UUID
    updated_by: UUID


class IterationPlanResponse(IterationPlan):
    """Iteration plan response model."""

    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    estimated_completion: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    success_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    active_step: Optional[IterationStep] = None
    completed_steps_count: int = 0
    failed_steps_count: int = 0
    pending_steps_count: int = 0

    class Config:
        orm_mode = True