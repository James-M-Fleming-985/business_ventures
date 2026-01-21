"""
Database Models for Correlation Discovery Engine
SQLAlchemy models for time series data, correlations, and metadata
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
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


class User(Base):
    """User accounts with role-based access control"""
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
