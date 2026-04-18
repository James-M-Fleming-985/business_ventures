"""
Database Models for Correlation Discovery Engine
SQLAlchemy models for time series data, correlations, and metadata
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index, JSON, Numeric
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

    # Outcome tracking (M1 Track C)
    target_growth_actual = Column(Float, nullable=True)        # Actual target % change over opportunity window
    target_growth_measured_at = Column(DateTime, nullable=True) # When actual growth was recorded

    # Ensemble model enrichment (M2 Track A)
    ensemble_confidence = Column(String(20), nullable=True)    # 'high', 'medium', 'low' from ensemble model
    ensemble_direction = Column(String(10), nullable=True)     # 'up' or 'down' from ensemble prediction
    ensemble_predicted_at = Column(DateTime, nullable=True)    # When ensemble prediction was made
    ensemble_r_squared = Column(Float, nullable=True)          # OLS R² from ensemble prediction
    ensemble_change_pct = Column(Float, nullable=True)         # Ensemble-predicted % change magnitude

    # AI-generated product concepts (M3 Track G)
    product_concepts = Column(JSON, nullable=True)             # List of 3 product concept dicts from LLM
    selected_concept_index = Column(Integer, nullable=True)    # 0-2: which concept user selected for build
    user_requirements = Column(Text, nullable=True)            # Free-text user requirements for build spec
    concepts_generation_status = Column(String(20), nullable=True)  # NULL | 'generating' | 'done' | 'failed'
    concepts_error = Column(Text, nullable=True)               # Error message if generation failed
    concepts_generated_at = Column(DateTime, nullable=True)    # When concepts were last successfully generated

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
            "target_growth_actual": self.target_growth_actual,
            "target_growth_measured_at": self.target_growth_measured_at.isoformat() if self.target_growth_measured_at else None,
            "ensemble_confidence": self.ensemble_confidence,
            "ensemble_direction": self.ensemble_direction,
            "ensemble_predicted_at": self.ensemble_predicted_at.isoformat() if self.ensemble_predicted_at else None,
            "ensemble_r_squared": self.ensemble_r_squared,
            "ensemble_change_pct": self.ensemble_change_pct,
            "product_concepts": self.product_concepts,
            "selected_concept_index": self.selected_concept_index,
            "user_requirements": self.user_requirements,
            "concepts_generation_status": self.concepts_generation_status,
            "concepts_error": self.concepts_error,
            "concepts_generated_at": self.concepts_generated_at.isoformat() if self.concepts_generated_at else None,
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
    railway_url = Column(String(500))  # Live MVP URL (Railway domain)
    github_url = Column(String(500))   # GitHub repo URL

    # Error tracking
    error_message = Column(Text)
    total_errors = Column(Integer, default=0)
    error_breakdown = Column(JSON)  # {syntax: 0, test: 0, import: 0, ...}

    # Metrics
    duration_seconds = Column(Float)
    ai_cost_usd = Column(Float)

    # Progress tracking
    build_steps = Column(JSON)  # [{step, at, detail}, ...]

    # Iteration tracking
    iteration_number = Column(Integer, default=1)
    parent_build_id = Column(Integer, ForeignKey('mvp_builds.id'), nullable=True)
    iterate_reason = Column(String(100), nullable=True)  # error_fix, ml_recommendation_update, engagement_growth, custom

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recommendation = relationship('ExploitationRecommendation', backref='builds')
    files = relationship('MVPBuildFile', back_populates='build', cascade='all, delete-orphan')
    parent_build = relationship('MVPBuild', remote_side=[id], backref='iterations')

    __table_args__ = (
        Index('ix_build_status', 'status'),
        Index('ix_build_rec_id', 'recommendation_id'),
        Index('ix_build_parent', 'parent_build_id'),
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
            "github_url": self.github_url,
            "error_message": self.error_message,
            "total_errors": self.total_errors,
            "error_breakdown": self.error_breakdown,
            "duration_seconds": self.duration_seconds,
            "ai_cost_usd": self.ai_cost_usd,
            "build_steps": self.build_steps,
            "iteration_number": self.iteration_number or 1,
            "parent_build_id": self.parent_build_id,
            "iterate_reason": self.iterate_reason,
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


class RevenueEvent(Base):
    """Central revenue event log populated by Stripe webhooks (M1 Track E).

    Every subscription creation, renewal, upgrade, downgrade, cancellation,
    and payment is logged here for aggregation into MRR, subscriber counts,
    and per-app breakdowns.
    """
    __tablename__ = 'revenue_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    app_id = Column(String(100), nullable=False)       # e.g. 'causal_affect', 'mvp_builder'
    event_type = Column(String(50), nullable=False)     # subscription_created, subscription_renewed,
                                                        # subscription_upgraded, subscription_downgraded,
                                                        # subscription_cancelled, payment_failed
    amount_cents = Column(Integer, nullable=False, default=0)  # In cents to avoid float rounding
    currency = Column(String(3), nullable=False, default='gbp')
    stripe_event_id = Column(String(255), unique=True)  # Idempotency key from Stripe
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    tier = Column(String(50))                           # free, pro, enterprise
    interval = Column(String(20))                       # monthly, yearly
    metadata_json = Column(JSON)                        # Extra Stripe event data
    event_at = Column(DateTime, nullable=False)         # When the Stripe event occurred
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_rev_app', 'app_id'),
        Index('ix_rev_type', 'event_type'),
        Index('ix_rev_event_at', 'event_at'),
        Index('ix_rev_stripe_event', 'stripe_event_id', unique=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "app_id": self.app_id,
            "event_type": self.event_type,
            "amount_cents": self.amount_cents,
            "amount": round(self.amount_cents / 100, 2),
            "currency": self.currency,
            "stripe_event_id": self.stripe_event_id,
            "user_id": self.user_id,
            "tier": self.tier,
            "interval": self.interval,
            "event_at": self.event_at.isoformat() if self.event_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProductDeployment(Base):
    """Tracks every product/MVP deployed commercially (M1 Track G).

    Links to ExploitationRecommendation (origin signal) and MVPBuild (code).
    Records tech stack, target market, pricing tier, and eventual outcome.
    """
    __tablename__ = 'product_deployments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(Integer, ForeignKey('exploitation_recommendations.id'), nullable=True)
    build_id = Column(Integer, ForeignKey('mvp_builds.id'), nullable=True)

    # Product identity
    product_name = Column(String(255), nullable=False)
    app_id = Column(String(100), nullable=False)          # Key for joining with RevenueEvent
    description = Column(Text)

    # Configuration snapshot
    tech_stack = Column(JSON)                              # e.g. {"framework": "fastapi", "db": "postgres", "hosting": "railway"}
    template_ids = Column(JSON)                            # Which templates were used
    pricing_model = Column(String(50))                     # free, freemium, subscription, one_time

    # Target market
    market_category = Column(String(100))                  # e.g. 'health_tech', 'ai_tools'
    target_demographic = Column(String(255))               # e.g. 'developers', 'small_business'
    geographic_focus = Column(String(100))                  # e.g. 'US', 'EU', 'global'

    # Deployment details
    railway_url = Column(String(500))
    domain = Column(String(255))
    deployed_at = Column(DateTime)
    status = Column(String(20), nullable=False, default='active')  # active, paused, retired

    # Outcome (updated over time)
    outcome = Column(String(20))                           # success, moderate, failed, too_early
    outcome_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recommendation = relationship('ExploitationRecommendation', backref='deployments')
    build = relationship('MVPBuild', backref='deployment')
    metrics = relationship('ProductMetrics', back_populates='deployment', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_pd_app_id', 'app_id'),
        Index('ix_pd_status', 'status'),
        Index('ix_pd_market', 'market_category'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "recommendation_id": self.recommendation_id,
            "build_id": self.build_id,
            "product_name": self.product_name,
            "app_id": self.app_id,
            "description": self.description,
            "tech_stack": self.tech_stack,
            "pricing_model": self.pricing_model,
            "market_category": self.market_category,
            "target_demographic": self.target_demographic,
            "geographic_focus": self.geographic_focus,
            "railway_url": self.railway_url,
            "domain": self.domain,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "status": self.status,
            "outcome": self.outcome,
            "outcome_notes": self.outcome_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProductMetrics(Base):
    """Time-series commercial metrics per ProductDeployment (M1 Track G).

    Populated by Stripe webhooks (revenue, subscribers) and GA4 pulls
    (traffic, conversion, churn). One row per deployment per period.
    """
    __tablename__ = 'product_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    deployment_id = Column(Integer, ForeignKey('product_deployments.id'), nullable=False)

    period_start = Column(DateTime, nullable=False)       # Start of measurement period
    period_end = Column(DateTime, nullable=False)          # End of measurement period

    # Revenue (from Stripe / RevenueEvent aggregation)
    mrr_cents = Column(Integer, default=0)                 # Monthly recurring revenue in cents
    subscriber_count = Column(Integer, default=0)

    # Traffic (from GA4 or similar)
    page_views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    avg_session_seconds = Column(Float)

    # Conversion
    conversion_rate = Column(Float)                        # visitors → subscribers %
    churn_rate = Column(Float)                             # monthly churn %

    # Source tracking
    source = Column(String(50), default='manual')          # stripe, ga4, manual

    created_at = Column(DateTime, default=datetime.utcnow)

    deployment = relationship('ProductDeployment', back_populates='metrics')

    __table_args__ = (
        Index('ix_pm_deployment', 'deployment_id'),
        Index('ix_pm_period', 'period_start', 'period_end'),
        Index('ix_pm_deploy_period', 'deployment_id', 'period_start', unique=True),
    )


class MvpPageView(Base):
    """Raw page-view beacon data from deployed MVPs.

    Each row = one page load event. Aggregated periodically into
    ProductMetrics for the builds-portfolio engagement column.
    """
    __tablename__ = 'mvp_page_views'

    id = Column(Integer, primary_key=True, autoincrement=True)
    build_id = Column(Integer, ForeignKey('mvp_builds.id'), nullable=False)
    visitor_hash = Column(String(64), nullable=False)  # SHA-256(IP + UA), no PII
    user_agent = Column(String(500))
    referrer = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    build = relationship('MVPBuild', backref='page_views')

    __table_args__ = (
        Index('ix_mpv_build_time', 'build_id', 'created_at'),
    )
