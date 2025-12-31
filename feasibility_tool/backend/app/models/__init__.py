"""
Database Models for Feasibility Platform
Includes users, baselines, exploration history with multi-tenancy
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    ForeignKey, Float, JSON, Enum as SQLEnum, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class SubscriptionTier(str, enum.Enum):
    """Subscription tier levels"""
    FREE = "free"  # 5 explorations/month
    PRO = "pro"    # Unlimited explorations


class User(Base):
    """User model with subscription tracking"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)  # Admin flag
    
    # Subscription info
    subscription_tier = Column(
        SQLEnum(SubscriptionTier), 
        default=SubscriptionTier.FREE,
        nullable=False
    )
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, index=True)
    subscription_status = Column(String(50))  # active, canceled, past_due, etc.
    subscription_starts_at = Column(DateTime(timezone=True))
    subscription_ends_at = Column(DateTime(timezone=True))
    
    # Usage tracking for FREE tier limits
    monthly_explorations = Column(Integer, default=0)
    monthly_explorations_reset_date = Column(DateTime(timezone=True))
    
    # Relationships
    baselines = relationship("Baseline", back_populates="user", cascade="all, delete-orphan")
    exploration_history = relationship("ExplorationHistory", back_populates="user", cascade="all, delete-orphan")


class Baseline(Base):
    """User's baseline configuration for delta calculations"""
    __tablename__ = "baselines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Baseline values
    baseline_data = Column(JSON, nullable=False)  # Store full baseline parameters
    
    # Metadata
    name = Column(String(255))  # Optional name for the baseline
    is_active = Column(Boolean, default=True)  # Allow multiple baselines, one active
    
    # Relationship
    user = relationship("User", back_populates="baselines")


class ExplorationHistory(Base):
    """User's exploration history for tracking and comparison"""
    __tablename__ = "exploration_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Exploration parameters
    input_parameters = Column(JSON, nullable=False)
    
    # Results
    result_data = Column(JSON, nullable=False)  # Store full result
    
    # Quick access fields (denormalized for queries)
    performance_score = Column(Float)
    durability_score = Column(Float)
    economic_score = Column(Float)
    
    # Delta from baseline (if baseline was set)
    delta_performance = Column(Float)
    delta_durability = Column(Float)
    delta_economic = Column(Float)
    
    # Metadata
    notes = Column(Text)
    
    # Relationship
    user = relationship("User", back_populates="exploration_history")
