"""SQLAlchemy database schema for automated iteration feature."""

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
    Enum as SQLEnum,
    CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

Base = declarative_base()


class IterationStatus(str, enum.Enum):
    """Status of an iteration run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class IterationType(str, enum.Enum):
    """Type of iteration process."""
    PARAMETER_OPTIMIZATION = "parameter_optimization"
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"
    ARCHITECTURE_SEARCH = "architecture_search"
    FEATURE_ENGINEERING = "feature_engineering"
    ENSEMBLE_OPTIMIZATION = "ensemble_optimization"
    CUSTOM = "custom"


class OptimizationStrategy(str, enum.Enum):
    """Strategy for optimization."""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    GRADIENT_BASED = "gradient_based"
    REINFORCEMENT_LEARNING = "reinforcement_learning"


class MetricType(str, enum.Enum):
    """Type of metric being tracked."""
    LOSS = "loss"
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    AUC_ROC = "auc_roc"
    RMSE = "rmse"
    MAE = "mae"
    CUSTOM = "custom"


class ArtifactType(str, enum.Enum):
    """Type of artifact produced."""
    MODEL = "model"
    DATASET = "dataset"
    VISUALIZATION = "visualization"
    REPORT = "report"
    CONFIG = "config"
    LOG = "log"
    CHECKPOINT = "checkpoint"


class IterationConfig(Base):
    """Configuration for an iteration process."""
    __tablename__ = "iteration_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Iteration settings
    iteration_type = Column(SQLEnum(IterationType), nullable=False)
    max_iterations = Column(Integer, nullable=False, default=100)
    convergence_threshold = Column(Float, nullable=True)
    early_stopping_patience = Column(Integer, nullable=True)
    optimization_strategy = Column(SQLEnum(OptimizationStrategy), nullable=False)
    
    # Search space and parameters
    search_space = Column(JSONB, nullable=False, default={})
    initial_parameters = Column(JSONB, nullable=True)
    constraints = Column(JSONB, nullable=True)
    
    # Resource limits
    max_runtime_seconds = Column(Integer, nullable=True)
    max_memory_gb = Column(Float, nullable=True)
    max_gpu_memory_gb = Column(Float, nullable=True)
    priority = Column(Integer, nullable=False, default=5)
    
    # Configuration
    config = Column(JSONB, nullable=False, default={})
    tags = Column(JSONB, nullable=False, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    runs = relationship("IterationRun", back_populates="config", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_iteration_config_project_name"),
        Index("idx_iteration_config_user", "user_id"),
        Index("idx_iteration_config_created", "created_at"),
        CheckConstraint("max_iterations > 0", name="ck_max_iterations_positive"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="ck_priority_range"),
    )


class IterationRun(Base):
    """Individual run of an iteration process."""
    __tablename__ = "iteration_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("iteration_configs.id"), nullable=False)
    run_number = Column(Integer, nullable=False)
    
    # Status and timing
    status = Column(SQLEnum(IterationStatus), nullable=False, default=IterationStatus.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Resource usage
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_gb = Column(Float, nullable=True)
    gpu_memory_usage_gb = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    metadata = Column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    config = relationship("IterationConfig", back_populates="runs")
    results = relationship("IterationResult", back_populates="run", cascade="all, delete-orphan")
    metrics = relationship("IterationMetric", back_populates="run", cascade="all, delete-orphan")
    artifacts = relationship("IterationArtifact", back_populates="run", cascade="all, delete-orphan")
    checkpoints = relationship("IterationCheckpoint", back_populates="run", cascade="all, delete-orphan")
    feedback = relationship("IterationFeedback", back_populates="run", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("config_id", "run_number", name="uq_iteration_run_config_number"),
        Index("idx_iteration_run_status", "status"),
        Index("idx_iteration_run_started", "started_at"),
        CheckConstraint("run_number > 0", name="ck_run_number_positive"),
    )


class IterationResult(Base):
    """Results from an iteration run."""
    __tablename__ = "iteration_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("iteration_runs.id"), nullable=False)
    iteration_number = Column(Integer, nullable=False)
    
    # Parameters and scores
    parameters = Column(JSONB, nullable=False)
    objective_value = Column(Float, nullable=False)
    constraint_violations = Column(JSONB, nullable=True)
    
    # Performance metrics
    training_loss = Column(Float, nullable=True)
    validation_loss = Column(Float, nullable=True)
    test_loss = Column(Float, nullable=True)
    custom_metrics = Column(JSONB, nullable=False, default={})
    
    # Convergence info
    improvement_ratio = Column(Float, nullable=True)
    is_best_so_far = Column(Boolean, nullable=False, default=False)
    converged = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    run = relationship("IterationRun", back_populates="results")
    
    __table_args__ = (
        UniqueConstraint("run_id", "iteration_number", name="uq_iteration_result_run_iter"),
        Index("idx_iteration_result_objective", "objective_value"),
        Index("idx_iteration_result_best", "is_best_so_far"),
        CheckConstraint("iteration_number >= 0", name="ck_iteration_number_non_negative"),
    )


class IterationMetric(Base):
    """Metrics tracked during iteration."""
    __tablename__ = "iteration_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("iteration_runs.id"), nullable=False)
    iteration_number = Column(Integer, nullable=False)
    
    # Metric info
    metric_type = Column(SQLEnum(MetricType), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    
    # Additional context
    dataset_split = Column(String(50), nullable=True)  # train, validation, test
    epoch_number = Column(Integer, nullable=True)
    batch_number = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    run = relationship("IterationRun", back_populates="metrics")
    
    __table_args__ = (
        Index("idx_iteration_metric_run_iter", "run_id", "iteration_number"),
        Index("idx_iteration_metric_type", "metric_type"),
        Index("idx_iteration_metric_name", "metric_name"),
    )


class IterationArtifact(Base):
    """Artifacts produced during iteration."""
    __tablename__ = "iteration_artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("iteration_runs.id"), nullable=False)
    iteration_number = Column(Integer, nullable=False)
    
    # Artifact info
    artifact_type = Column(SQLEnum(ArtifactType), nullable=False)
    artifact_name = Column(String(255), nullable=False)
    artifact_path = Column(String(1024), nullable=False)
    artifact_size_bytes = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True)
    
    # Version control
    version = Column(String(50), nullable=True)
    is_latest = Column(Boolean, nullable=False, default=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=False, default={})
    tags = Column(JSONB, nullable=False, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    run = relationship("IterationRun", back_populates="artifacts")
    
    __table_args__ = (
        Index("idx_iteration_artifact_run_iter", "run_id", "iteration_number"),
        Index("idx_iteration_artifact_type", "artifact_type"),
        Index("idx_iteration_artifact_latest", "is_latest"),
    )


class IterationCheckpoint(Base):
    """Checkpoints for resuming iteration."""
    __tablename__ = "iteration_checkpoints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("iteration_runs.id"), nullable=False)
    iteration_number = Column(Integer, nullable=False)
    
    # Checkpoint data
    state_data = Column(JSONB, nullable=False)
    optimizer_state = Column(JSONB, nullable=True)
    random_state = Column(JSONB, nullable=True)
    
    # Storage info
    storage_path = Column(String(1024), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    
    # Validation
    is_valid = Column(Boolean, nullable=False, default=True)
    validation_checksum = Column(String(64), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    run = relationship("IterationRun", back_populates="checkpoints")
    
    __table_args__ = (
        UniqueConstraint("run_id", "iteration_number", name="uq_checkpoint_run_iter"),
        Index("idx_checkpoint_valid", "is_valid"),
    )


class IterationFeedback(Base):
    """User feedback on iteration results."""
    __tablename__ = "iteration_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("iteration_runs.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Feedback data
    rating = Column(Integer, nullable=True)  # 1-5 scale
    comments = Column(Text, nullable=True)
    suggestions = Column(JSONB, nullable=True)
    
    # Specific feedback
    parameter_feedback = Column(JSONB, nullable=True)
    metric_feedback = Column(JSONB, nullable=True)
    
    # Actions taken
    action_required = Column(Boolean, nullable=False, default=False)
    action_taken = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    run = relationship("IterationRun", back_populates="feedback")
    
    __table_args__ = (
        Index("idx_feedback_user", "user_id"),
        Index("idx_feedback_rating", "rating"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rating_range"),
    )


class IterationOptimization(Base):
    """Optimization history and suggestions."""
    __tablename__ = "iteration_optimizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("iteration_configs.id"), nullable=False)
    
    # Optimization summary
    total_iterations = Column(Integer, nullable=False, default=0)
    best_objective_value = Column(Float, nullable=True)
    best_parameters = Column(JSONB, nullable=True)
    best_iteration_number = Column(Integer, nullable=True)
    
    # Performance analysis
    convergence_rate = Column(Float, nullable=True)
    improvement_history = Column(JSONB, nullable=False, default=[])
    parameter_importance = Column(JSONB, nullable=True)
    
    # Suggestions
    suggested_parameters = Column(JSONB, nullable=True)
    suggested_search_space = Column(JSONB, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_optimization_config", "config_id"),
        Index("idx_optimization_best", "best_objective_value"),
    )