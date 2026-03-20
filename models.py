"""
Database Models for Correlation Discovery Engine
SQLAlchemy models for time series data, correlations, and metadata
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class VariableMetadata(Base):
    """Catalog of all variables tracked in the system"""
    __tablename__ = 'variable_metadata'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    unit = Column(String(50))
    data_type = Column(String(50))  # 'time_series', 'count', 'event'
    source = Column(String(100), nullable=False)  # 'alpha_vantage', 'usgs', 'nasa_eonet', etc.
    api_endpoint = Column(String(500))
    update_frequency = Column(String(50))  # 'daily', 'hourly', 'realtime'
    parameters = Column(Text)  # JSON string of API parameters (symbol, country_code, etc.)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    time_series_data = relationship("TimeSeriesData", back_populates="variable")
    
    def __repr__(self):
        return f"<Variable {self.name} ({self.source})>"


class TimeSeriesData(Base):
    """Raw time series data from API sources"""
    __tablename__ = 'time_series_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    variable_id = Column(Integer, ForeignKey('variable_metadata.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    source_updated_at = Column(DateTime)  # When the source API last updated
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    variable = relationship("VariableMetadata", back_populates="time_series_data")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_time_series_variable_timestamp', 'variable_id', 'timestamp'),
        Index('ix_time_series_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<TimeSeriesData var={self.variable_id} ts={self.timestamp} val={self.value}>"


class CorrelationResult(Base):
    """Calculated correlation results between variable pairs"""
    __tablename__ = 'correlation_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    variable1_id = Column(Integer, ForeignKey('variable_metadata.id'), nullable=False)
    variable2_id = Column(Integer, ForeignKey('variable_metadata.id'), nullable=False)
    correlation_value = Column(Float, nullable=False)  # r-value (-1 to 1)
    p_value = Column(Float, nullable=False)
    method = Column(String(50), nullable=False)  # 'pearson', 'spearman', 'kendall'
    sample_size = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_significant = Column(Boolean)  # p < 0.05
    abs_correlation = Column(Float)  # For ranking by strength
    
    # Phase 2: Granger Causality fields
    causal_direction = Column(String(20))  # 'x_to_y', 'y_to_x', 'bidirectional', 'none', or NULL
    granger_p_value_xy = Column(Float)  # p-value for var1 → var2
    granger_p_value_yx = Column(Float)  # p-value for var2 → var1
    granger_lags = Column(Integer)  # Optimal lag found by Granger test
    
    # Source tags for cross-domain filtering
    source1 = Column(String(100))  # Source of variable1 (e.g., 'alphavantage', 'worldbank')
    source2 = Column(String(100))  # Source of variable2
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    analysis_job_id = Column(Integer, ForeignKey('analysis_jobs.id'))
    
    # Relationships
    variable1 = relationship("VariableMetadata", foreign_keys=[variable1_id])
    variable2 = relationship("VariableMetadata", foreign_keys=[variable2_id])
    analysis_job = relationship("AnalysisJob", back_populates="correlation_results")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_correlation_vars', 'variable1_id', 'variable2_id'),
        Index('ix_correlation_abs_value', 'abs_correlation'),
        Index('ix_correlation_significant', 'is_significant', 'abs_correlation'),
        Index('ix_correlation_job', 'analysis_job_id'),
        Index('ix_correlation_cross_domain', 'source1', 'source2'),  # For cross-domain filtering
    )
    
    def __repr__(self):
        return f"<Correlation v{self.variable1_id}-v{self.variable2_id} r={self.correlation_value:.3f} p={self.p_value:.4f}>"


class RollingCorrelation(Base):
    """Rolling correlation calculations for drift analysis"""
    __tablename__ = 'rolling_correlations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    variable1_id = Column(Integer, ForeignKey('variable_metadata.id'), nullable=False)
    variable2_id = Column(Integer, ForeignKey('variable_metadata.id'), nullable=False)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    window_size_days = Column(Integer)
    correlation_value = Column(Float, nullable=False)
    p_value = Column(Float)
    method = Column(String(50), default='pearson')
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    variable1 = relationship("VariableMetadata", foreign_keys=[variable1_id])
    variable2 = relationship("VariableMetadata", foreign_keys=[variable2_id])
    
    # Indexes
    __table_args__ = (
        Index('ix_rolling_vars_window', 'variable1_id', 'variable2_id', 'window_end'),
    )
    
    def __repr__(self):
        return f"<RollingCorr v{self.variable1_id}-v{self.variable2_id} window={self.window_size_days}d r={self.correlation_value:.3f}>"


class AnalysisJob(Base):
    """Track analysis job runs"""
    __tablename__ = 'analysis_jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_type = Column(String(50), nullable=False)  # 'full_correlation', 'rolling_correlation', 'data_fetch'
    status = Column(String(50), nullable=False)  # 'pending', 'running', 'completed', 'failed'
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    variables_count = Column(Integer)
    correlation_pairs_calculated = Column(Integer)
    significant_correlations_found = Column(Integer)
    error_message = Column(Text)
    parameters = Column(Text)  # JSON string of job parameters
    
    # Relationships
    correlation_results = relationship("CorrelationResult", back_populates="analysis_job")
    
    # Indexes
    __table_args__ = (
        Index('ix_analysis_job_status', 'status', 'start_time'),
    )
    
    def __repr__(self):
        return f"<AnalysisJob {self.id} {self.job_type} {self.status}>"


class APIStatus(Base):
    """Track API health and status"""
    __tablename__ = 'api_status'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False, unique=True)
    status = Column(String(50), nullable=False)  # 'active', 'degraded', 'failed'
    last_success = Column(DateTime)
    last_failure = Column(DateTime)
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    avg_response_time_ms = Column(Float)
    error_message = Column(Text)
    checked_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<APIStatus {self.source} {self.status}>"


class PredictionTracking(Base):
    """CA-002-10: Track predictions made by deep-analysis and their outcomes"""
    __tablename__ = 'prediction_tracking'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(String(50), unique=True, nullable=False, index=True)

    # Variables involved
    signal_name = Column(String(255), nullable=False)   # e.g. "ChatGPT"
    target_name = Column(String(255), nullable=False)   # e.g. "NVIDIA Stock"

    # Timing
    predicted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    target_date = Column(DateTime)                      # When prediction matures
    optimal_lag_days = Column(Integer)

    # The prediction
    predicted_direction = Column(String(10))             # 'up' or 'down'
    predicted_value = Column(Float)
    predicted_change_pct = Column(Float)
    current_target_value = Column(Float)                # Baseline at prediction time
    current_signal_value = Column(Float)
    signal_momentum = Column(Float)                     # Momentum % at prediction time

    # Regression info
    r_squared = Column(Float)
    confidence = Column(String(20))                     # 'high', 'medium', 'low'
    model_version = Column(String(50), default='granger_v1')

    # Actual outcome (NULL until target_date passes and actuals fetched)
    actual_value = Column(Float)
    actual_direction = Column(String(10))
    direction_correct = Column(Boolean)
    value_error_pct = Column(Float)
    actual_change_pct = Column(Float)            # Actual % change from baseline
    actual_lag_days = Column(Integer)             # Days to actual peak/trough
    lag_error_days = Column(Integer)              # actual_lag - predicted_lag
    granger_p_value = Column(Float)               # p-value at prediction time
    target_source = Column(String(100))           # e.g. 'stock', 'arxiv', 'fred'

    # Status: 'pending', 'validated', 'expired'
    status = Column(String(20), default='pending')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_pred_target_date', 'target_date'),
        Index('ix_pred_status', 'status'),
        Index('ix_pred_model', 'model_version'),
        Index('ix_pred_signal_target', 'signal_name', 'target_name'),
    )

    def __repr__(self):
        return f"<Prediction {self.prediction_id} {self.signal_name}→{self.target_name} {self.predicted_direction}>"

    def to_dict(self):
        return {
            "prediction_id": self.prediction_id,
            "signal_name": self.signal_name,
            "target_name": self.target_name,
            "predicted_at": self.predicted_at.isoformat() if self.predicted_at else None,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "optimal_lag_days": self.optimal_lag_days,
            "predicted_direction": self.predicted_direction,
            "predicted_value": self.predicted_value,
            "predicted_change_pct": self.predicted_change_pct,
            "current_target_value": self.current_target_value,
            "current_signal_value": self.current_signal_value,
            "signal_momentum": self.signal_momentum,
            "r_squared": self.r_squared,
            "confidence": self.confidence,
            "model_version": self.model_version,
            "actual_value": self.actual_value,
            "actual_direction": self.actual_direction,
            "direction_correct": self.direction_correct,
            "value_error_pct": self.value_error_pct,
            "actual_change_pct": self.actual_change_pct,
            "actual_lag_days": self.actual_lag_days,
            "lag_error_days": self.lag_error_days,
            "granger_p_value": self.granger_p_value,
            "target_source": self.target_source,
            "status": self.status,
        }


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    
    # Roles: 'superuser', 'admin', 'subscriber', 'free'
    role = Column(String(50), nullable=False, default='free')
    
    # Subscription status
    subscription_tier = Column(String(50), default='free')  # 'free', 'basic', 'pro', 'enterprise'
    subscription_expires_at = Column(DateTime)
    stripe_customer_id = Column(String(255))  # For Stripe integration
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('ix_users_role', 'role'),
        Index('ix_users_subscription', 'subscription_tier', 'subscription_expires_at'),
    )
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
    @property
    def is_superuser(self):
        return self.role == 'superuser'
    
    @property
    def is_admin(self):
        return self.role in ('superuser', 'admin')
    
    @property
    def has_active_subscription(self):
        if self.subscription_tier == 'free':
            return True
        if self.subscription_expires_at is None:
            return False
        return self.subscription_expires_at > datetime.utcnow()


class ExploitationRecommendation(Base):
    """Actionable recommendations generated from Granger causality analysis.
    
    Each recommendation represents an exploitable signal→target relationship
    classified as BUY/SELL (stocks/crypto), BUILD (apps/products), or MONITOR
    (economic indicators). Recommendations have a manual status lifecycle:
    NEW → REVIEWING → PURSUING → COMPLETED/DISMISSED.
    """
    __tablename__ = 'exploitation_recommendations'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Signal (Layer 1 — what we observe)
    signal_name = Column(String(255), nullable=False)          # e.g. "wiki_interest-rate"
    signal_display_name = Column(String(255), nullable=False)  # e.g. "Interest Rate"

    # Target (Layer 2/3 — what the signal predicts)
    target_name = Column(String(255), nullable=False)          # e.g. "stock_nvda"
    target_display_name = Column(String(255), nullable=False)  # e.g. "NVDA Stock Price"
    target_source = Column(String(100))                        # e.g. "stock", "fred", "arxiv"

    # Action classification
    action_type = Column(String(20), nullable=False)           # BUY, SELL, BUILD, MONITOR
    reasoning = Column(Text)                                   # Natural language explanation

    # Statistical basis
    granger_p_value = Column(Float)
    correlation = Column(Float)
    optimal_lag = Column(Integer)                              # Lag in periods (months)
    sample_size = Column(Integer)

    # Prediction
    predicted_direction = Column(String(10))                   # 'up' or 'down'
    predicted_change_pct = Column(Float)
    signal_momentum = Column(Float)                            # Current signal momentum %

    # Scoring
    opportunity_score = Column(Float)                          # 0-100 composite score

    # BUILD-specific viability (NULL for BUY/SELL/MONITOR)
    build_viability_score = Column(Float)                      # 0-100 BUILD viability composite
    estimated_monthly_searches = Column(Integer)               # Wikipedia pageview demand proxy
    search_trend_direction = Column(String(10))                # 'growing', 'stable', 'declining'
    search_growth_pct = Column(Float)                          # Monthly growth rate %
    opportunity_duration_months = Column(Integer)              # Window duration from lag stability
    revenue_potential = Column(String(10))                     # 'LOW', 'MEDIUM', 'HIGH'
    competition_level = Column(String(10))                     # 'LOW', 'MEDIUM', 'HIGH'
    market_category = Column(String(100))                      # e.g. 'health_tech', 'ai_tools'

    # Lifecycle
    status = Column(String(20), nullable=False, default='NEW') # NEW, REVIEWING, PURSUING, COMPLETED, DISMISSED
    notes = Column(Text)                                       # User free-text notes

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_exploit_status', 'status'),
        Index('ix_exploit_action', 'action_type'),
        Index('ix_exploit_score', 'opportunity_score'),
        Index('ix_exploit_signal_target', 'signal_name', 'target_name', unique=True),
    )

    def __repr__(self):
        return f"<Exploitation {self.action_type} {self.signal_display_name}→{self.target_display_name} score={self.opportunity_score}>"

    def to_dict(self):
        return {
            "id": self.id,
            "signal_name": self.signal_name,
            "signal_display_name": self.signal_display_name,
            "target_name": self.target_name,
            "target_display_name": self.target_display_name,
            "target_source": self.target_source,
            "action_type": self.action_type,
            "reasoning": self.reasoning,
            "granger_p_value": self.granger_p_value,
            "correlation": self.correlation,
            "optimal_lag": self.optimal_lag,
            "sample_size": self.sample_size,
            "predicted_direction": self.predicted_direction,
            "predicted_change_pct": self.predicted_change_pct,
            "signal_momentum": self.signal_momentum,
            "opportunity_score": self.opportunity_score,
            "build_viability_score": self.build_viability_score,
            "estimated_monthly_searches": self.estimated_monthly_searches,
            "search_trend_direction": self.search_trend_direction,
            "search_growth_pct": self.search_growth_pct,
            "opportunity_duration_months": self.opportunity_duration_months,
            "revenue_potential": self.revenue_potential,
            "competition_level": self.competition_level,
            "market_category": self.market_category,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ExploitationValidation(Base):
    """Manual validation records for exploitation recommendations.
    
    Tracks whether BUILD viability assessments were accurate by recording
    real-world outcomes. Used to compute exploitation accuracy baseline (M0).
    """
    __tablename__ = 'exploitation_validations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(Integer, ForeignKey('exploitation_recommendations.id'), nullable=False)
    validated_at = Column(DateTime, default=datetime.utcnow)
    validator = Column(String(100), default='manual')

    # Outcome assessment
    actual_outcome = Column(String(20), nullable=False)  # SUCCESS, PARTIAL, FAILED, UNKNOWN
    outcome_notes = Column(Text)

    # Market reality checks
    demand_accurate = Column(Boolean)         # Was estimated search volume roughly right?
    competition_accurate = Column(Boolean)     # Was competition level assessment correct?
    revenue_potential_accurate = Column(Boolean)  # Was revenue potential assessment correct?
    actual_revenue = Column(Float, nullable=True)

    # Score snapshot at validation time
    viability_score_at_validation = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_validation_rec_id', 'recommendation_id'),
        Index('ix_validation_outcome', 'actual_outcome'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "recommendation_id": self.recommendation_id,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "validator": self.validator,
            "actual_outcome": self.actual_outcome,
            "outcome_notes": self.outcome_notes,
            "demand_accurate": self.demand_accurate,
            "competition_accurate": self.competition_accurate,
            "revenue_potential_accurate": self.revenue_potential_accurate,
            "actual_revenue": self.actual_revenue,
            "viability_score_at_validation": self.viability_score_at_validation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MVPBuild(Base):
    """Tracks MVP builds triggered from exploitation recommendations.
    
    Each build generates code from templates + AI, stores artifacts in S3,
    and optionally auto-deploys to Railway as a standalone service.
    """
    __tablename__ = 'mvp_builds'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(Integer, ForeignKey('exploitation_recommendations.id'), nullable=False)
    complexity = Column(String(10), nullable=False)  # LOW, MEDIUM, HIGH
    status = Column(String(20), nullable=False, default='QUEUED')  # QUEUED, GENERATING, UPLOADING, DEPLOYING, LIVE, FAILED

    # Build configuration
    build_config = Column(JSON)  # Template matches, params, layers selected

    # Storage
    s3_prefix = Column(String(500))  # S3 path: mvps/{build_id}/

    # Railway deployment
    railway_project_id = Column(String(100))
    railway_service_id = Column(String(100))
    railway_url = Column(String(500))  # Live MVP URL

    # Error tracking
    error_message = Column(Text)
    total_errors = Column(Integer, default=0)
    error_breakdown = Column(JSON)  # {syntax: 0, test: 0, import: 0, ...}

    # Metrics
    duration_seconds = Column(Float)
    ai_cost_usd = Column(Float)

    # Progress tracking
    build_steps = Column(JSON)  # [{step, at, detail}, ...]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recommendation = relationship('ExploitationRecommendation', backref='builds')
    files = relationship('MVPBuildFile', back_populates='build', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_build_status', 'status'),
        Index('ix_build_rec_id', 'recommendation_id'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "recommendation_id": self.recommendation_id,
            "complexity": self.complexity,
            "status": self.status,
            "build_config": self.build_config,
            "s3_prefix": self.s3_prefix,
            "railway_project_id": self.railway_project_id,
            "railway_service_id": self.railway_service_id,
            "railway_url": self.railway_url,
            "error_message": self.error_message,
            "total_errors": self.total_errors,
            "error_breakdown": self.error_breakdown,
            "duration_seconds": self.duration_seconds,
            "ai_cost_usd": self.ai_cost_usd,
            "build_steps": self.build_steps,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "file_count": len(self.files) if self.files else 0,
        }


class MVPBuildFile(Base):
    """Individual files generated during an MVP build."""
    __tablename__ = 'mvp_build_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    build_id = Column(Integer, ForeignKey('mvp_builds.id'), nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative path: backend/app/router.py
    s3_key = Column(String(500), nullable=False)  # Full S3 key
    file_size_bytes = Column(Integer, default=0)
    template_id = Column(String(100))  # Which template generated this file
    content = Column(Text)  # Generated file content (persisted in DB)
    created_at = Column(DateTime, default=datetime.utcnow)

    build = relationship('MVPBuild', back_populates='files')

    def to_dict(self, include_content=False):
        d = {
            "id": self.id,
            "build_id": self.build_id,
            "file_path": self.file_path,
            "s3_key": self.s3_key,
            "file_size_bytes": self.file_size_bytes,
            "template_id": self.template_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_content:
            d["content"] = self.content
        return d
